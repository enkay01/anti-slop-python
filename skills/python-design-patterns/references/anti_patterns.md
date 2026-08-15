# Anti-Patterns & Rationalization Buster

This guide provides coding agents with a structured rubric to detect over-engineering, resist classic OOP rationalizations, and write clean, maintainable Python code.

---

## The Rationalization Buster

When planning or evaluating code, agents frequently fall into classical OOP over-engineering traps borrowed from Java or C++. Use this table to counter those instincts:

| Agent Rationalization | The Reality & Pythonic Solution |
| :--- | :--- |
| *"I should create an `AbstractFactory` class with `ABC` just in case we add more providers later."* | **YAGNI (You Aren't Gonna Need It).** Start with a simple factory function or dictionary registry (`REGISTRY: dict[str, type]`). Refactor only when the third variant arrives. |
| *"I will implement a `Singleton` class overriding `__new__` to manage the database connection or logger."* | **Anti-pattern.** Classical Singletons act as hidden global state, break parallel unit test isolation, and cause synchronization bugs. Use Python **modules** (naturally cached in `sys.modules`) or pass instances explicitly via **Dependency Injection**. |
| *"I should use a deep class inheritance hierarchy with `TemplateMethod` to share code."* | **Inheritance couples subclasses to base class implementation details.** Favor **composition over inheritance**: pass step callables (`Callable[[Input], Output]`) or use `typing.Protocol`. |
| *"I need a full `Builder` class with `.set_name()`, `.set_age()`, etc., for this entity."* | **Python has keyword arguments.** Use `@dataclass(kw_only=True, frozen=True)` or Pydantic models. Builders are only justified for complex multi-step validation or fluent DSLs (e.g., query builders). |
| *"I will use `unittest.mock.patch` to mock internal functions during testing."* | **Testing smell.** Relying heavily on monkeypatching indicates tight coupling to I/O. Refactor the component to accept a `typing.Protocol` via constructor injection and pass a fast, in-memory fake in tests. |
| *"I'll wrap this single pure function in a class to make it more object-oriented."* | **Python functions are first-class citizens.** A class with only `__init__` and `execute()` (and no mutating state) should almost always be a plain function. |
| *"I need to use `isinstance()` checks in 6 different methods to handle different types."* | **Code smell.** Refactor to **Strategy** (injecting specific callables) or structural pattern matching (`match/case`) over a tagged union. |
| *"Passing 8 arguments to this function is fine since they are typed."* | **Signature smell.** Sprawling parameter lists cause argument transposition bugs and make updates painful. Group related arguments into an immutable **Parameter Object** (`@dataclass(frozen=True)`). |

---

## Red Flags Checklist (Code Smells to Refactor)

When auditing Python code, stop and evaluate if you see any of these indicators:

### 1. The God Class Smell
- **Symptom**: A single class spanning 500+ lines with 15+ methods handling database queries, business rules, serialization, and email notifications.
- **Remedy**: Split using **Facade** (for orchestration), **Repository** (for storage), and **Strategy** (for distinct algorithms).

### 2. Sprawling `if/elif/else` Cascades
- **Symptom**: Repeated branching on string tags (e.g., `if format == "json": ... elif format == "csv": ... elif format == "xml": ...`) across multiple functions.
- **Remedy**: Replace with a **Strategy Dictionary Registry** (`EXPORTERS: dict[str, Callable] = {"json": ..., "csv": ...}`).

### 3. Untestable I/O in Core Logic
- **Symptom**: Domain classes calling `requests.post()`, `datetime.now()`, or direct SQL drivers in the middle of business calculations.
- **Remedy**: Apply **Dependency Injection** with `typing.Protocol` interfaces.

### 4. Deep Inheritance Trees (>2 Levels)
- **Symptom**: `class BaseWorker` -> `class HttpWorker(BaseWorker)` -> `class AuthenticatedHttpWorker(HttpWorker)` -> `class RetryableAuthenticatedHttpWorker(...)`.
- **Remedy**: Flatten using **Decorator** for retry/auth and **Composition** for HTTP clients.

### 5. Anemic Domain Model with Procedural Manager
- **Symptom**: Dataclasses with raw fields modified directly across dozens of helper functions without invariant enforcement.
- **Remedy**: Encapsulate domain invariants inside the entity or apply the **State Pattern** if transitions are constrained.

---

## When to Stop Refactoring

Refactoring is a tool to eliminate active friction, not an intellectual exercise in pattern insertion:
1. If the code is readable, modular, and easily unit-testable with in-memory doubles, **do not add more patterns**.
2. If an abstraction is only used in one place and has no planned second implementation, **keep it concrete**.
3. Always prefer standard Python idioms (list comprehensions, generator expressions, `@dataclass`, `typing.Protocol`, pattern matching) over custom framework wrappers.
