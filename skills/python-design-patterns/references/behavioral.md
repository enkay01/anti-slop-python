# Behavioral Design Patterns in Modern Python

This guide covers behavioral design patterns featured across **ArjanCodes**, highlighting when to use them, anti-patterns to avoid, architectural trade-offs, and idiomatic Python adaptations.

---

## 1. Strategy Pattern

### Core Concept
The Strategy pattern defines a family of algorithms or business rules, encapsulates each one, and makes them interchangeable at runtime.

### When to Use (Green Flags)
- You need to switch between different algorithms or business rules dynamically at runtime based on configuration, user input, or environment (e.g., payment gateways: Stripe vs. PayPal; discount rules; export formats: JSON vs. CSV).
- You have multiple variations of an algorithm and want to avoid massive `if-elif` or `match` blocks in the consumer.
- You want to isolate algorithm-specific dependencies (e.g., external SDKs or heavy math libraries) from domain business logic.

### When to Avoid (Red Flags)
- You have only a single static algorithm or trivial branching logic that is unlikely to grow.
- The variants do not share a consistent input/output signature.
- Over-engineering trap: Creating a class hierarchy with an `ABC` when a simple lambda or pure function is sufficient.

### Trade-offs
- **Pros**: Cleanly decouples caller logic from algorithm variants; adheres to Open/Closed Principle (adding a new strategy requires zero changes to the caller).
- **Cons**: Adds an extra layer of indirection; callers must be aware of strategy differences to select the right one.

### Pythonic Adaptation
Instead of building heavyweight class hierarchies with abstract base classes (`abc.ABC`), use first-class callables (`Callable[[Input], Output]`) or closures.

```python
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

# 1. Define the Strategy signature as a Callable type alias
type DiscountStrategy = Callable[[Decimal], Decimal]

# 2. Strategies implemented as simple, pure functions
def standard_discount(amount: Decimal) -> Decimal:
    return amount * Decimal("0.05")

def vip_discount(amount: Decimal) -> Decimal:
    return amount * Decimal("0.20")

def tier_discount(rate: Decimal) -> DiscountStrategy:
    """Strategy generator using a closure for configurable rates."""
    return lambda amount: amount * rate

# 3. Context / Consumer accepting the callable strategy
@dataclass(frozen=True)
class Order:
    order_id: str
    total_amount: Decimal
    discount_strategy: DiscountStrategy = standard_discount

    @property
    def final_price(self) -> Decimal:
        discount = self.discount_strategy(self.total_amount)
        return max(Decimal("0.00"), self.total_amount - discount)

# Usage
order_standard = Order(order_id="ORD-01", total_amount=Decimal("100.00"))
order_vip = Order(
    order_id="ORD-02",
    total_amount=Decimal("100.00"),
    discount_strategy=vip_discount,
)
order_custom = Order(
    order_id="ORD-03",
    total_amount=Decimal("100.00"),
    discount_strategy=tier_discount(Decimal("0.15")),
)

print(order_standard.final_price)  # 95.00
print(order_vip.final_price)       # 80.00
print(order_custom.final_price)    # 85.00
```

---

## 2. Observer / Event-Driven Pattern

### Core Concept
The Observer pattern establishes a subscription mechanism to notify multiple independent consumers when state changes or events occur.

### When to Use (Green Flags)
- Multiple independent components need to react to a state change without hardcoding direct references (e.g., user signup triggering a welcome email, analytics tracking, and audit log write).
- You are building a modular plugin architecture or decoupled event pipeline.
- Cross-cutting concerns need to monitor business events without modifying core domain entities.

### When to Avoid (Red Flags)
- Execution order is strictly synchronous, deterministic, and linear (where control flow must be trivially traceable from top to bottom).
- Simple direct method calls between two closely coupled classes achieve the same goal.
- High-frequency event streams where callback overhead and unhandled handler exceptions risk destabilizing the application.

### Trade-offs
- **Pros**: High extensibility and loose coupling; new listeners can be attached without altering the subject.
- **Cons**: Makes execution flow harder to trace/debug; unmanaged subscriptions can cause subtle memory leaks if subscribers are never deregistered.

### Pythonic Adaptation
Implement lightweight typed publish/subscribe registries using dictionaries of event types mapped to lists of handler functions (`dict[type, list[Callable]]`). Use `@dataclass(frozen=True)` for event payloads.

```python
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

# 1. Define immutable event payloads
@dataclass(frozen=True)
class UserRegisteredEvent:
    user_id: str
    email: str
    timestamp: datetime

# 2. Lightweight Event Bus Registry
type EventHandler[E] = Callable[[E], None]

class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable]] = defaultdict(list)

    def subscribe[E](self, event_type: type[E], handler: EventHandler[E]) -> None:
        self._subscribers[event_type].append(handler)

    def unsubscribe[E](self, event_type: type[E], handler: EventHandler[E]) -> None:
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def publish[E](self, event: E) -> None:
        for handler in self._subscribers[type(event)]:
            handler(event)

# 3. Independent Handlers (Functions or Methods)
def send_welcome_email(event: UserRegisteredEvent) -> None:
    print(f"Sending welcome email to {event.email}")

def record_audit_log(event: UserRegisteredEvent) -> None:
    print(f"Audit: user {event.user_id} registered at {event.timestamp}")

# Usage
bus = EventBus()
bus.subscribe(UserRegisteredEvent, send_welcome_email)
bus.subscribe(UserRegisteredEvent, record_audit_log)

new_user_event = UserRegisteredEvent(
    user_id="usr_123",
    email="alice@example.com",
    timestamp=datetime.now(timezone.utc),
)
bus.publish(new_user_event)
```

---

## 3. State Pattern

### Core Concept
The State pattern allows an object to alter its behavior when its internal state changes, appearing to change its class while enforcing valid transitions.

### When to Use (Green Flags)
- An entity's behavior fundamentally changes based on its current state, and transitions follow strict state machine rules (e.g., order lifecycle: `Pending` -> `Paid` -> `Shipped` -> `Delivered`).
- You have methods filled with sprawling `if self.state == ...` checks that duplicate the same checks across 5+ operations.
- Invalid state transitions must be rejected centrally and predictably.

### When to Avoid (Red Flags)
- The object has only 1-2 simple binary flags (e.g., `is_active: bool`, `is_verified: bool`).
- Transitions have no side effects, business rules, or validation constraints.

### Trade-offs
- **Pros**: Eliminates sprawling conditional branches spread across dozens of methods; centralizes state transition rules.
- **Cons**: Increases structural overhead if over-applied to simple status indicators.

### Pythonic Adaptation
Combine `enum.Enum` with a transition table and pattern matching (`match/case`) instead of creating full class-per-state class hierarchies.

```python
from enum import Enum, auto
from dataclasses import dataclass

class OrderState(Enum):
    PENDING = auto()
    PAID = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()

# Valid transitions map: source_state -> allowed target states
VALID_TRANSITIONS: dict[OrderState, set[OrderState]] = {
    OrderState.PENDING: {OrderState.PAID, OrderState.CANCELLED},
    OrderState.PAID: {OrderState.SHIPPED, OrderState.CANCELLED},
    OrderState.SHIPPED: {OrderState.DELIVERED},
    OrderState.DELIVERED: set(),
    OrderState.CANCELLED: set(),
}

class InvalidStateTransitionError(Exception):
    pass

@dataclass
class Order:
    order_id: str
    state: OrderState = OrderState.PENDING

    def transition_to(self, new_state: OrderState) -> None:
        allowed = VALID_TRANSITIONS.get(self.state, set())
        if new_state not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition order {self.order_id} from {self.state.name} to {new_state.name}."
            )
        self.state = new_state

    def cancel(self) -> None:
        self.transition_to(OrderState.CANCELLED)

    def pay(self) -> None:
        self.transition_to(OrderState.PAID)

    def ship(self) -> None:
        self.transition_to(OrderState.SHIPPED)

    def deliver(self) -> None:
        self.transition_to(OrderState.DELIVERED)

# Usage
order = Order(order_id="ORD-99")
order.pay()
order.ship()
order.deliver()
# order.cancel()  # Raises InvalidStateTransitionError
```

---

## 4. Command Pattern

### Core Concept
The Command pattern encapsulates a request or operation as an object, enabling parameterization of clients with queues, logs, and undoable operations.

### When to Use (Green Flags)
- You need to encapsulate operations into invokable objects to support undo/redo stacks, execution queues, job scheduling, or delayed batch processing.
- You need to track history, audits, or progress of executable transactions.
- You want to decouple the invoker (e.g., UI button or task runner) from the receiver (domain service).

### When to Avoid (Red Flags)
- A standard direct function call executes immediately without needing metadata, queuing, retry logic, or rollback capability.
- Creating command objects adds boilerplate wrappers without providing undo or scheduling benefits.

### Trade-offs
- **Pros**: Decouples invoker from receiver; simplifies queue and history management; makes undo/redo trivial.
- **Cons**: Introduces extra object allocations and wrapper classes for simple operations.

### Pythonic Adaptation
Use `@dataclass` implementing a `typing.Protocol` with `execute()` and `undo()` methods. For simple commands without undo, use `Callable[[], None]` or `functools.partial`.

```python
from typing import Protocol
from dataclasses import dataclass, field

class Command(Protocol):
    def execute(self) -> None: ...
    def undo(self) -> None: ...

@dataclass
class Document:
    text: str = ""

@dataclass
class InsertTextCommand:
    document: Document
    text_to_insert: str

    def execute(self) -> None:
        self.document.text += self.text_to_insert

    def undo(self) -> None:
        if self.document.text.endswith(self.text_to_insert):
            cut_idx = len(self.document.text) - len(self.text_to_insert)
            self.document.text = self.document.text[:cut_idx]

class CommandInvoker:
    def __init__(self) -> None:
        self._history: list[Command] = []
        self._redo_stack: list[Command] = []

    def run(self, command: Command) -> None:
        command.execute()
        self._history.append(command)
        self._redo_stack.clear()

    def undo(self) -> None:
        if not self._history:
            return
        command = self._history.pop()
        command.undo()
        self._redo_stack.append(command)

    def redo(self) -> None:
        if not self._redo_stack:
            return
        command = self._redo_stack.pop()
        command.execute()
        self._history.append(command)

# Usage
doc = Document()
invoker = CommandInvoker()

invoker.run(InsertTextCommand(doc, "Hello, "))
invoker.run(InsertTextCommand(doc, "World!"))
print(doc.text)  # "Hello, World!"

invoker.undo()
print(doc.text)  # "Hello, "

invoker.redo()
print(doc.text)  # "Hello, World!"
```

---

## 5. Template Method Pattern

### Core Concept
The Template Method pattern defines the skeleton of an algorithm in a base workflow, deferring some steps to specific variants without changing the algorithm's overall structure.

### When to Use (Green Flags)
- You have a fixed multi-step workflow where the overall skeleton must remain invariant, but specific sub-steps vary between variants (e.g., data ETL pipeline: extract -> parse -> validate -> load).
- Multiple workflows share identical boilerplate steps with minor customizations in 1-2 phases.

### When to Avoid (Red Flags)
- Subclasses constantly need to override the execution sequence itself rather than just individual steps.
- The steps are trivial and do not benefit from a shared pipeline structure.

### Trade-offs
- **Pros**: Enforces workflow consistency and eliminates duplicate boilerplate across similar pipelines.
- **Cons**: Classical inheritance makes subclasses tightly coupled to base class internals.

### Pythonic Adaptation
Prefer **dependency injection of step callables (composition)** over class inheritance. Construct the pipeline using typed step functions.

```python
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")

# 1. Define step callables
type Extractor[T] = Callable[[], T]
type Transformer[T, R] = Callable[[T], R]
type Loader[R] = Callable[[R], None]

# 2. Pipeline engine composed of callables
@dataclass(frozen=True)
class Pipeline[T, R]:
    extractor: Extractor[T]
    transformer: Transformer[T, R]
    loader: Loader[R]

    def run(self) -> None:
        print("Starting pipeline execution...")
        raw_data = self.extractor()
        transformed = self.transformer(raw_data)
        self.loader(transformed)
        print("Pipeline execution complete.")

# 3. Step implementations (easily reusable and independently testable)
def extract_csv() -> list[str]:
    return ["alice,30", "bob,25"]

def transform_csv_to_records(raw: list[str]) -> list[dict[str, str | int]]:
    records = []
    for line in raw:
        name, age = line.split(",")
        records.append({"name": name, "age": int(age)})
    return records

def load_to_stdout(records: list[dict[str, str | int]]) -> None:
    print(f"Loaded {len(records)} records into storage: {records}")

# Usage
csv_pipeline = Pipeline(
    extractor=extract_csv,
    transformer=transform_csv_to_records,
    loader=load_to_stdout,
)
csv_pipeline.run()
```
