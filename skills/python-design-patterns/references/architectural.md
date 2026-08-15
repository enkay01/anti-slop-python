# Modern Architectural & Clean Code Idioms in Python

This guide covers modern architectural patterns and idioms featured across **ArjanCodes**, highlighting when to use them, anti-patterns to avoid, practical trade-offs, and idiomatic Python adaptations.

---

## 1. Dependency Injection

### Core Concept
Dependency Injection (DI) is a technique where an object receives its dependencies (collaborating objects, database connections, API clients, clocks) from the outside rather than creating them internally.

### When to Use (Green Flags)
- Building components that perform I/O (databases, HTTP APIs, file systems, clocks) where unit tests need to run fast and deterministically without touching external infrastructure.
- Decoupling business logic from concrete infrastructure vendors.
- Allowing different execution environments (production, staging, test, CLI) to supply different implementations of a service.

### When to Avoid (Red Flags)
- Simple standalone utility scripts or small scripts where manual wiring creates unnecessary setup ceremony.
- Introducing heavyweight DI framework containers (e.g., injector) when plain constructor arguments (`__init__`) suffice.

### Trade-offs
- **Pros**: Drastically boosts testability, eliminates monkeypatching / `unittest.mock.patch`, and keeps components decoupled.
- **Cons**: Requires wiring dependencies together at the application entry point (composition root).

### Pythonic Adaptation
Use constructor injection with `typing.Protocol`. Pass dependencies explicitly as arguments in `__init__`. In tests, pass lightweight in-memory fake implementations.

```python
from typing import Protocol
from dataclasses import dataclass
from datetime import datetime, timezone

# 1. Interface Protocol
class Clock(Protocol):
    def now(self) -> datetime: ...

class NotificationSender(Protocol):
    def send(self, recipient: str, message: str) -> None: ...

# 2. Production Implementations
class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

class EmailNotificationSender:
    def send(self, recipient: str, message: str) -> None:
        print(f"Delivering email to {recipient}: {message}")

# 3. Domain Service receiving dependencies via Constructor Injection
class ReminderService:
    def __init__(self, clock: Clock, notifier: NotificationSender) -> None:
        self.clock = clock
        self.notifier = notifier

    def send_daily_reminder(self, user_email: str) -> None:
        current_time = self.clock.now()
        msg = f"Reminder sent at {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        self.notifier.send(user_email, msg)

# 4. In-Memory Test Doubles for unit tests (zero mocking frameworks needed)
class FakeClock:
    def __init__(self, fixed_time: datetime) -> None:
        self.fixed_time = fixed_time

    def now(self) -> datetime:
        return self.fixed_time

class FakeNotifier:
    def __init__(self) -> None:
        self.sent_messages: list[tuple[str, str]] = []

    def send(self, recipient: str, message: str) -> None:
        self.sent_messages.append((recipient, message))

# Test Example
fixed_dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
fake_clock = FakeClock(fixed_dt)
fake_notifier = FakeNotifier()

service = ReminderService(clock=fake_clock, notifier=fake_notifier)
service.send_daily_reminder("test@domain.com")

assert len(fake_notifier.sent_messages) == 1
assert fake_notifier.sent_messages[0] == ("test@domain.com", "Reminder sent at 2026-01-01 12:00:00")
```

---

## 2. Repository / Unit of Work

### Core Concept
The Repository pattern mediates between the domain business logic and data mapping layers, acting like an in-memory domain object collection.

### When to Use (Green Flags)
- Decoupling domain business logic from database- or ORM-specific details (e.g., enabling clean migration between SQLite, PostgreSQL, DynamoDB, or in-memory stores).
- Creating fast, reliable unit tests that operate against pure in-memory collections without spinning up a test database.
- Centralizing complex query logic and data mapping away from domain models.

### When to Avoid (Red Flags)
- Simple CRUD apps where the ORM (e.g., SQLModel, Django ORM) is already the primary data model and business logic is minimal.
- When the repository merely duplicates standard ORM methods without providing architectural isolation.

### Trade-offs
- **Pros**: Keeps domain logic clean, testable, and storage-agnostic.
- **Cons**: Adds a layer of mapping and interface code; duplicates query capabilities already built into modern ORMs.

### Pythonic Adaptation
Define a `typing.Protocol` specifying collection-like methods (`add`, `get_by_id`, `list_all`, `delete`). Provide separate production and in-memory implementations.

```python
from typing import Protocol
from dataclasses import dataclass

@dataclass(frozen=True)
class Customer:
    customer_id: str
    name: str
    email: str
    is_active: bool = True

# 1. Repository Protocol
class CustomerRepository(Protocol):
    def add(self, customer: Customer) -> None: ...
    def get(self, customer_id: str) -> Customer | None: ...
    def list_active(self) -> list[Customer]: ...

# 2. In-Memory Fake Implementation (Used in unit tests and local dev)
class InMemoryCustomerRepository:
    def __init__(self) -> None:
        self._storage: dict[str, Customer] = {}

    def add(self, customer: Customer) -> None:
        self._storage[customer.customer_id] = customer

    def get(self, customer_id: str) -> Customer | None:
        return self._storage.get(customer_id)

    def list_active(self) -> list[Customer]:
        return [c for c in self._storage.values() if c.is_active]

# 3. Domain Service using the Repository
class CustomerService:
    def __init__(self, repo: CustomerRepository) -> None:
        self.repo = repo

    def register(self, customer_id: str, name: str, email: str) -> Customer:
        existing = self.repo.get(customer_id)
        if existing is not None:
            raise ValueError(f"Customer {customer_id} already exists.")
        new_customer = Customer(customer_id=customer_id, name=name, email=email)
        self.repo.add(new_customer)
        return new_customer

# Usage in tests
repo = InMemoryCustomerRepository()
service = CustomerService(repo=repo)
customer = service.register("c101", "Alice Smith", "alice@example.com")
assert repo.get("c101") == customer
```

---

## 3. Parameter / Context Object

### Core Concept
The Parameter Object pattern groups cohesive sets of method arguments into a single structured object.

### When to Use (Green Flags)
- Functions or methods with 4+ parameters that frequently travel together or are passed across multiple layers.
- Functions where parameter order is prone to bugs (e.g., multiple `str` or `int` arguments in sequence: `def create(name, city, country, postal_code, region)`).
- You want to add new optional parameters in the future without breaking existing function signatures.

### When to Avoid (Red Flags)
- Functions taking 1-2 self-explanatory primitive arguments.
- Creating a parameter object for unrelated variables that just happen to be used in one place.

### Trade-offs
- **Pros**: Cleans up function signatures, enables immutability and schema validation, simplifies data passing across layers.
- **Cons**: Requires defining dedicated dataclass types.

### Pythonic Adaptation
Use `@dataclass(frozen=True, kw_only=True)` with sensible defaults.

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

# Refactoring: Sprawling 6-parameter signature -> Clean Parameter Object
# Before: def search_transactions(user_id, start_date, end_date, min_amount, max_amount, status, page, page_size)

# After: Dedicated Parameter Object
@dataclass(frozen=True, kw_only=True)
class TransactionFilter:
    user_id: str
    start_date: date | None = None
    end_date: date | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    status: str = "completed"
    page: int = 1
    page_size: int = 50

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be >= 1")
        if self.min_amount and self.max_amount and self.min_amount > self.max_amount:
            raise ValueError("min_amount cannot exceed max_amount")

def search_transactions(criteria: TransactionFilter) -> list[dict[str, str]]:
    print(f"Searching for user {criteria.user_id} with status={criteria.status}, page={criteria.page}")
    return [{"tx_id": "tx_101", "status": criteria.status}]

# Usage
filter_params = TransactionFilter(
    user_id="usr_888",
    min_amount=Decimal("50.00"),
    status="settled",
)
results = search_transactions(filter_params)
```

---

## 4. Rule / Policy Engine

### Core Concept
A Rule / Policy Engine isolates complex, rapidly evolving business qualification or validation logic into pluggable, independent rule objects or predicates.

### When to Use (Green Flags)
- Business domains with complex, evolving eligibility or validation criteria (e.g., loan approval, discount qualification, fraud detection, insurance underwriting).
- You want each rule to be independently testable, documented, and selectively enabled/disabled.
- You need structured audit reports explaining exactly which rules passed or failed.

### When to Avoid (Red Flags)
- Static validation logic that fits into a simple 2-line boolean expression (`if age >= 18 and has_id:`).
- Creating dynamic evaluation engines when simple functions or Pydantic validators are sufficient.

### Trade-offs
- **Pros**: Makes complex rules modular, composable, and independently testable; gives clear diagnostic feedback.
- **Cons**: More classes/callables to manage compared to raw procedural conditional blocks.

### Pythonic Adaptation
Define rules as pure callables returning a structured `RuleResult` with success status and reason.

```python
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class LoanApplication:
    applicant_id: str
    credit_score: int
    monthly_income: Decimal
    requested_amount: Decimal
    existing_debt: Decimal

@dataclass(frozen=True)
class RuleResult:
    rule_name: str
    passed: bool
    reason: str

type LoanRule = Callable[[LoanApplication], RuleResult]

# 1. Independent, modular rule predicates
def min_credit_score_rule(app: LoanApplication) -> RuleResult:
    passed = app.credit_score >= 650
    return RuleResult(
        rule_name="CreditScoreCheck",
        passed=passed,
        reason="Credit score meets minimum threshold of 650" if passed else f"Credit score {app.credit_score} is below 650",
    )

def debt_to_income_rule(app: LoanApplication) -> RuleResult:
    dti = (app.existing_debt / app.monthly_income) if app.monthly_income > 0 else Decimal("1.0")
    passed = dti <= Decimal("0.40")
    return RuleResult(
        rule_name="DebtToIncomeCheck",
        passed=passed,
        reason=f"DTI ratio {dti:.1%} is acceptable" if passed else f"DTI ratio {dti:.1%} exceeds 40% limit",
    )

# 2. Rule Engine Evaluator
@dataclass(frozen=True)
class LoanEvaluationEngine:
    rules: list[LoanRule]

    def evaluate(self, app: LoanApplication) -> tuple[bool, list[RuleResult]]:
        results = [rule(app) for rule in self.rules]
        all_passed = all(r.passed for r in results)
        return all_passed, results

# Usage
engine = LoanEvaluationEngine(rules=[min_credit_score_rule, debt_to_income_rule])

app = LoanApplication(
    applicant_id="app_555",
    credit_score=720,
    monthly_income=Decimal("8000.00"),
    requested_amount=Decimal("20000.00"),
    existing_debt=Decimal("1500.00"),
)

approved, audit_log = engine.evaluate(app)
print(f"Application Approved: {approved}")
for entry in audit_log:
    print(f" - [{entry.rule_name}] {'PASS' if entry.passed else 'FAIL'}: {entry.reason}")
```
