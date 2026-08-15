# Creational Design Patterns in Modern Python

This guide covers creational design patterns featured across **ArjanCodes**, highlighting when to use them, anti-patterns to avoid, architectural trade-offs, and idiomatic Python adaptations.

---

## 1. Factory / Abstract Factory Pattern

### Core Concept
The Factory pattern provides an interface or function for creating objects without specifying the exact concrete class at compile time, delegating instantiation decisions to runtime inputs.

### When to Use (Green Flags)
- The exact concrete type or strategy to instantiate depends on runtime input (e.g., config file strings, CLI flags, database records, HTTP request parameters).
- Object creation involves non-trivial initialization, parsing, validation, or conditional wiring that should not clutter business logic.
- You are building a plugin system where third parties register new classes dynamically.

### When to Avoid (Red Flags)
- Direct instantiation with `MyClass()` is straightforward and concrete types are known statically at compile time.
- Adding an abstract factory interface when there is only one concrete factory implementation (premature abstraction).

### Trade-offs
- **Pros**: Encapsulates complex creation logic away from business workflows; enables runtime polymorphism and plugin architectures.
- **Cons**: Adds unnecessary indirection when simple constructor calls would do.

### Pythonic Adaptation
Instead of building verbose Abstract Factory class hierarchies (`AbstractExporterFactory`, `JsonExporterFactory`, `CsvExporterFactory`), use **dictionary registries** or simple factory functions.

```python
from typing import Protocol
from collections.abc import Callable
from dataclasses import dataclass

# 1. Product Protocol
class DataExporter(Protocol):
    def export(self, data: dict[str, str]) -> str: ...

# 2. Concrete Products
class JsonExporter:
    def export(self, data: dict[str, str]) -> str:
        import json
        return json.dumps(data)

class CsvExporter:
    def export(self, data: dict[str, str]) -> str:
        return ",".join(f"{k}={v}" for k, v in data.items())

# 3. Pythonic Factory: Dictionary Dispatcher Registry
type ExporterCreator = Callable[[], DataExporter]

EXPORTER_REGISTRY: dict[str, ExporterCreator] = {
    "json": JsonExporter,
    "csv": CsvExporter,
}

def register_exporter(format_name: str, creator: ExporterCreator) -> None:
    """Plugin registration seam for external extensions."""
    EXPORTER_REGISTRY[format_name.lower()] = creator

def create_exporter(format_name: str) -> DataExporter:
    """Factory function with descriptive error handling."""
    creator = EXPORTER_REGISTRY.get(format_name.lower())
    if creator is None:
        valid_formats = ", ".join(EXPORTER_REGISTRY.keys())
        raise ValueError(f"Unknown exporter format '{format_name}'. Available: {valid_formats}")
    return creator()

# Usage
exporter = create_exporter("json")
print(exporter.export({"user": "ian", "role": "admin"}))
```

---

## 2. Builder Pattern

### Core Concept
The Builder pattern separates the construction of a complex object from its representation, allowing the same construction process to create various configurations while avoiding sprawling constructors.

### When to Use (Green Flags)
- Constructing complex objects with 5+ configuration parameters that have inter-field dependencies and validation rules across steps.
- You need to prevent incomplete or invalid intermediate states during multi-step object assembly.
- Constructing immutable query strings, HTTP requests, or database specs with fluent chaining.

### When to Avoid (Red Flags)
- Objects are simple dataclasses with standard default values.
- Creating a separate `UserBuilder` class simply to assign 3 fields on a `User` class (Java anti-pattern).

### Trade-offs
- **Pros**: Produces clean, readable fluent APIs and enforces valid construction at step boundaries.
- **Cons**: Requires maintaining separate builder structures and synchronized property sets.

### Pythonic Adaptation
1. First, leverage `@dataclass(kw_only=True)` or Pydantic models with default factories.
2. If multi-step fluent validation is genuinely needed, use a lightweight builder returning `Self`.

```python
from dataclasses import dataclass, field
from typing import Self

# Option A: Idiomatic Python Dataclass with keyword-only arguments (Default choice)
@dataclass(kw_only=True, frozen=True)
class DatabaseConnectionConfig:
    host: str
    port: int = 5432
    database: str
    user: str
    password: str
    timeout_seconds: int = 30
    ssl_enabled: bool = True
    pool_size: int = 10

# Option B: Fluent Builder with assembly-time validation (When multi-step construction is required)
class SqlQueryBuilder:
    def __init__(self) -> None:
        self._table: str = ""
        self._columns: list[str] = []
        self._where_clauses: list[str] = []
        self._limit: int | None = None

    def from_table(self, table: str) -> Self:
        self._table = table
        return self

    def select(self, *columns: str) -> Self:
        self._columns.extend(columns)
        return self

    def where(self, condition: str) -> Self:
        self._where_clauses.append(condition)
        return self

    def limit(self, count: int) -> Self:
        self._limit = count
        return self

    def build(self) -> str:
        if not self._table:
            raise ValueError("Query must specify a table via 'from_table'.")
        cols = ", ".join(self._columns) if self._columns else "*"
        query = f"SELECT {cols} FROM {self._table}"
        if self._where_clauses:
            query += " WHERE " + " AND ".join(self._where_clauses)
        if self._limit is not None:
            query += f" LIMIT {self._limit}"
        return query

# Usage
query = (
    SqlQueryBuilder()
    .from_table("users")
    .select("id", "email", "created_at")
    .where("is_active = TRUE")
    .where("role = 'admin'")
    .limit(10)
    .build()
)
print(query)
# SELECT id, email, created_at FROM users WHERE is_active = TRUE AND role = 'admin' LIMIT 10
```

---

## 3. Singleton Pattern

### Core Concept
The Singleton pattern ensures that a class has only one instance and provides a global point of access to it.

### When to Use (Green Flags)
- Strictly one physical resource coordinator must exist globally across the application process (e.g., hardware device lock, physical sensor interface, global thread pool).

### When to Avoid (Red Flags)
- Storing general application state, cached entities, or configuration settings.
- Creating a classical `Singleton` class with `__new__` magic or metaclasses to hold loggers, database handles, or user sessions.
- **Why it is an Anti-Pattern in Python**:
  - Acts as a hidden global variable, obscuring component dependencies.
  - Destroys unit test isolation (state leaks between test cases).
  - Introduces multi-threading race conditions and synchronization hazards.

### Trade-offs
- **Pros**: Centralized resource management for hardware or lock coordination.
- **Cons**: Hidden coupling, tight global state, breaks parallel test suites.

### Pythonic Adaptation
1. **Module-level Singletons**: Python modules are cached in `sys.modules` upon first import and executed only once. A module-level instance or state provides a natural, idiomatic singleton without boilerplate.
2. **Explicit Dependency Injection**: Instantiate the shared coordinator at the application root and pass it explicitly into consumers.

```python
# --- Approach 1: Module-level Singleton (Pythonic & Simple) ---
# file: app/database.py
class DatabaseClient:
    def __init__(self, connection_url: str) -> None:
        self.connection_url = connection_url
        print(f"Connected to {connection_url}")

    def query(self, sql: str) -> list[str]:
        return [f"result for {sql}"]

# Global shared instance initialized at module load or via init helper
_default_client: DatabaseClient | None = None

def get_database_client() -> DatabaseClient:
    global _default_client
    if _default_client is None:
        _default_client = DatabaseClient("sqlite:///prod.db")
    return _default_client


# --- Approach 2: Explicit Dependency Injection (Best for Testability) ---
# file: app/services.py
from typing import Protocol

class DatabaseProtocol(Protocol):
    def query(self, sql: str) -> list[str]: ...

class UserService:
    """Consumer receives the shared database client explicitly via constructor."""
    def __init__(self, db: DatabaseProtocol) -> None:
        self.db = db

    def get_users(self) -> list[str]:
        return self.db.query("SELECT * FROM users")

# In production (app composition root):
db = get_database_client()
service = UserService(db=db)

# In tests (isolated fake instance, no monkeypatching required):
class FakeDatabase:
    def query(self, sql: str) -> list[str]:
        return ["fake_user_1", "fake_user_2"]

test_service = UserService(db=FakeDatabase())
assert len(test_service.get_users()) == 2
```
