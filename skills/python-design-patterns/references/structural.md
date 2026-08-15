# Structural Design Patterns in Modern Python

This guide covers structural design patterns featured across **ArjanCodes**, highlighting when to use them, anti-patterns to avoid, architectural trade-offs, and idiomatic Python adaptations.

---

## 1. Adapter Pattern

### Core Concept
The Adapter pattern allows incompatible interfaces to collaborate by converting the interface of a service into an interface that clients expect.

### When to Use (Green Flags)
- Integrating third-party APIs, legacy libraries, or incompatible external SDKs without polluting your core domain models.
- You want to standardize multiple external service providers (e.g., Stripe SDK vs. PayPal SDK vs. Adyen SDK) behind a clean, domain-specific contract.
- You want to decouple domain business logic from breaking changes in external dependencies.

### When to Avoid (Red Flags)
- You have full control over the source code and can directly refactor the target interface to match your domain.
- The interface difference is trivial (e.g., a single function argument rename easily handled by `functools.partial` or a wrapper keyword argument).

### Trade-offs
- **Pros**: Isolates external dependencies behind clean boundaries; enables seamless swapping and mocking of third-party systems.
- **Cons**: Adds an extra translation layer and maintenance overhead if the external API changes frequently.

### Pythonic Adaptation
Define a `typing.Protocol` for your domain's expected interface. Write thin wrapper classes or functions that conform to the protocol structurally without explicit subclassing.

```python
from typing import Protocol
from dataclasses import dataclass

# 1. Domain Protocol (What your application expects)
class PaymentProcessor(Protocol):
    def process_payment(self, amount_cents: int, currency: str) -> bool: ...

# 2. Third-Party Incompatible SDK (Simulated external vendor)
class StripeSDK:
    def charge_card(self, token: str, amount_dollars: float) -> dict[str, str | int]:
        print(f"Stripe: charged ${amount_dollars:.2f} using token {token}")
        return {"status": 200, "charge_id": "ch_stripe_123"}

class PayPalSDK:
    def execute_payment(self, recipient_email: str, cents: int, curr: str) -> str:
        print(f"PayPal: paid {cents} {curr} to {recipient_email}")
        return "SUCCESS_PAYPAL"

# 3. Thin Domain Adapters conforming structurally to PaymentProcessor
@dataclass(frozen=True)
class StripeAdapter:
    client: StripeSDK
    card_token: str = "tok_default"

    def process_payment(self, amount_cents: int, currency: str) -> bool:
        amount_dollars = amount_cents / 100.0
        response = self.client.charge_card(token=self.card_token, amount_dollars=amount_dollars)
        return response.get("status") == 200

@dataclass(frozen=True)
class PayPalAdapter:
    client: PayPalSDK
    recipient_email: str

    def process_payment(self, amount_cents: int, currency: str) -> bool:
        res = self.client.execute_payment(
            recipient_email=self.recipient_email,
            cents=amount_cents,
            curr=currency,
        )
        return res == "SUCCESS_PAYPAL"

# 4. Domain Service (Depends strictly on the Protocol)
class CheckoutService:
    def __init__(self, processor: PaymentProcessor) -> None:
        self.processor = processor

    def checkout(self, total_cents: int) -> None:
        success = self.processor.process_payment(total_cents, "USD")
        if not success:
            raise RuntimeError("Payment failed during checkout.")
        print("Checkout completed successfully.")

# Usage
stripe_service = CheckoutService(StripeAdapter(StripeSDK()))
stripe_service.checkout(4999)

paypal_service = CheckoutService(PayPalAdapter(PayPalSDK(), recipient_email="store@domain.com"))
paypal_service.checkout(2500)
```

---

## 2. Decorator Pattern

### Core Concept
The Decorator pattern dynamically attaches additional responsibilities or behaviors to an object or function without modifying its core code.

### When to Use (Green Flags)
- Adding cross-cutting concerns (logging, timing, rate-limiting, caching, retry logic, authorization) without modifying the underlying function or class.
- You need composable, modular behavior layers that can be toggled via configuration.

### When to Avoid (Red Flags)
- Adding core domain business logic that belongs inside the entity or function itself.
- Over-decorating functions to the point where call stack traces and debug signatures become obscured.

### Trade-offs
- **Pros**: Highly reusable, clean separation of concerns; composable at call sites.
- **Cons**: Stacked wrappers can complicate stack traces and debugging unless `functools.wraps` is consistently applied.

### Pythonic Adaptation
Use Python's built-in `@decorator` syntax with `functools.wraps` to preserve function metadata, type hints, and docstrings.

```python
import functools
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def timed_retry(max_attempts: int = 3, delay_seconds: float = 0.5) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Parameterized decorator adding timing and automatic retry capability."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_err: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    elapsed = (time.perf_counter() - start_time) * 1000
                    print(f"[{func.__name__}] Attempt {attempt} succeeded in {elapsed:.2f}ms")
                    return result
                except Exception as err:
                    elapsed = (time.perf_counter() - start_time) * 1000
                    print(f"[{func.__name__}] Attempt {attempt} failed ({err}) after {elapsed:.2f}ms")
                    last_err = err
                    if attempt < max_attempts:
                        time.sleep(delay_seconds)
            if last_err is not None:
                raise last_err
            raise RuntimeError("Operation failed with unknown error.")
        return wrapper
    return decorator

# Usage
@timed_retry(max_attempts=3, delay_seconds=0.1)
def fetch_api_data(endpoint: str) -> dict[str, str]:
    """Fetch remote data with transient network failure simulation."""
    return {"endpoint": endpoint, "status": "ok"}

data = fetch_api_data("/users/42")
```

---

## 3. Composite Pattern

### Core Concept
The Composite pattern composes objects into tree structures to represent part-whole hierarchies, allowing clients to treat individual objects (leaves) and compositions (containers) uniformly.

### When to Use (Green Flags)
- You are modeling nested hierarchical structures (e.g., file systems with files and directories, nested UI component trees, organization charts, complex task breakdown graphs).
- Clients need to perform aggregate calculations (e.g., total file size, rendering layout, computing budget totals) across mixed leaves and groups uniformly.

### When to Avoid (Red Flags)
- Your data model is purely flat.
- Leaves and containers have drastically different interfaces or responsibilities where forcing a uniform API requires dummy methods or runtime type checks.

### Trade-offs
- **Pros**: Simplifies client code by making recursive operations uniform; easy to add new node types.
- **Cons**: Can make strict type-checking more complex when certain operations apply only to leaf nodes or container nodes.

### Pythonic Adaptation
Define a `typing.Protocol` representing the tree component contract. Implement recursive operations directly across leaf and composite classes.

```python
from typing import Protocol
from dataclasses import dataclass, field

class FileSystemItem(Protocol):
    @property
    def name(self) -> str: ...
    def get_size_bytes(self) -> int: ...

@dataclass(frozen=True)
class File:
    name: str
    size_bytes: int

    def get_size_bytes(self) -> int:
        return self.size_bytes

@dataclass
class Directory:
    name: str
    children: list[FileSystemItem] = field(default_factory=list)

    def add(self, item: FileSystemItem) -> None:
        self.children.append(item)

    def get_size_bytes(self) -> int:
        return sum(child.get_size_bytes() for child in self.children)

# Usage
root = Directory(name="root")
docs = Directory(name="docs")
docs.add(File(name="report.pdf", size_bytes=1024))
docs.add(File(name="notes.txt", size_bytes=256))

root.add(docs)
root.add(File(name="main.py", size_bytes=512))

print(f"Total directory size: {root.get_size_bytes()} bytes")  # 1792 bytes
```

---

## 4. Facade Pattern

### Core Concept
The Facade pattern provides a simplified, higher-level interface to an otherwise complex or verbose subsystem of classes, libraries, or workflows.

### When to Use (Green Flags)
- Providing a simplified, unified entry point to a complex multi-step subsystem (e.g., video rendering pipeline: audio extraction -> frame resizing -> subtitle overlay -> encoding -> export).
- You want to reduce coupling between client code and the internal details of multiple subsystem classes.

### When to Avoid (Red Flags)
- Callers genuinely need fine-grained, low-level control over every parameter in the subsystem.
- The facade risks becoming a bloated "god class" containing hundreds of unrelated helper methods.

### Trade-offs
- **Pros**: Drastically lowers cognitive load and decouples clients from subsystem internals.
- **Cons**: Can become a maintenance bottleneck if too many miscellaneous conveniences are packed into it.

### Pythonic Adaptation
Create a clean facade class or module-level orchestration functions that coordinate well-focused subsystem components.

```python
from dataclasses import dataclass

# Subsystem components
class VideoDecoder:
    def decode(self, file_path: str) -> str:
        print(f"Decoding video file: {file_path}")
        return "raw_video_stream"

class AudioExtractor:
    def extract_audio(self, stream: str) -> str:
        print("Extracting audio channels...")
        return "raw_audio_stream"

class WatermarkApplier:
    def apply(self, stream: str, text: str) -> str:
        print(f"Applying watermark '{text}'...")
        return "watermarked_stream"

class VideoEncoder:
    def encode(self, video_stream: str, audio_stream: str, output_path: str) -> None:
        print(f"Encoding finalized video to {output_path}")

# Facade
@dataclass(frozen=True)
class VideoProcessingFacade:
    decoder: VideoDecoder = VideoDecoder()
    audio_extractor: AudioExtractor = AudioExtractor()
    watermarker: WatermarkApplier = WatermarkApplier()
    encoder: VideoEncoder = VideoEncoder()

    def process_and_export(self, source_file: str, output_file: str, watermark: str) -> None:
        """High-level one-step execution method for callers."""
        raw_video = self.decoder.decode(source_file)
        audio = self.audio_extractor.extract_audio(raw_video)
        watermarked_video = self.watermarker.apply(raw_video, watermark)
        self.encoder.encode(watermarked_video, audio, output_file)

# Usage: Caller only interacts with the clean facade
facade = VideoProcessingFacade()
facade.process_and_export("input.mov", "output.mp4", "Acme Corp")
```

---

## 5. Bridge Pattern

### Core Concept
The Bridge pattern decouples an abstraction from its implementation so that the two can vary independently across orthogonal dimensions.

### When to Use (Green Flags)
- You have two independent dimensions of variation and want to avoid an exponential explosion of subclasses ($M \times N \to M + N$). For example:
  - Abstraction: `Shape` (Circle, Square, Polygon)
  - Implementation: `Renderer` (VectorRenderer, RasterRenderer, WebGLRenderer)
  - Subclasses without Bridge: $3 \times 3 = 9$ classes (`VectorCircle`, `RasterCircle`, etc.)
  - With Bridge: $3 + 3 = 6$ classes.
- You need to switch implementation backends at runtime.

### When to Avoid (Red Flags)
- You only have one dimension of variation (simple polymorphism or inheritance suffices).
- The abstraction and implementation are tightly coupled and will never vary independently.

### Trade-offs
- **Pros**: Prevents class explosion; separates platform-independent abstractions from platform-dependent engines.
- **Cons**: Increases initial structural indirection.

### Pythonic Adaptation
Define a `typing.Protocol` for the implementation provider and inject it into the abstraction class hierarchy.

```python
from typing import Protocol
from dataclasses import dataclass

# 1. Implementation Dimension (Renderer Protocol)
class Renderer(Protocol):
    def render_circle(self, radius: float) -> str: ...
    def render_square(self, side: float) -> str: ...

# Concrete Implementations
class VectorRenderer:
    def render_circle(self, radius: float) -> str:
        return f"Drawing SVG circle with radius {radius}"

    def render_square(self, side: float) -> str:
        return f"Drawing SVG square with side {side}"

class RasterRenderer:
    def render_circle(self, radius: float) -> str:
        return f"Drawing pixelated raster circle of radius {radius}"

    def render_square(self, side: float) -> str:
        return f"Drawing pixelated raster square of side {side}"

# 2. Abstraction Dimension (Shape Hierarchy)
@dataclass(frozen=True)
class Shape:
    renderer: Renderer

@dataclass(frozen=True)
class Circle(Shape):
    radius: float

    def draw(self) -> str:
        return self.renderer.render_circle(self.radius)

@dataclass(frozen=True)
class Square(Shape):
    side: float

    def draw(self) -> str:
        return self.renderer.render_square(self.side)

# Usage: Orthogonal combination
vector_renderer = VectorRenderer()
raster_renderer = RasterRenderer()

circle = Circle(renderer=vector_renderer, radius=5.0)
square = Square(renderer=raster_renderer, side=10.0)

print(circle.draw())  # "Drawing SVG circle with radius 5.0"
print(square.draw())  # "Drawing pixelated raster square of side 10.0"
```
