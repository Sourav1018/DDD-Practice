# DDD Wallet & Transfer System (JS & Python)

This project aims to teach Domain-Driven Design (DDD) by implementing a real-life money transfer service in both **JavaScript (TypeScript)** and **Python**. We will structure the directories cleanly into Domain, Application, and Infrastructure layers, write the code, and solve two critical real-life issues that separate junior backend developers from the top 1%:

1. **Idempotency Protection** (preventing duplicate transactions due to network retries or double-clicks).
2. **Concurrency Invariant Protection** (preventing race conditions that allow balance to drop below zero using Optimistic Locking).

---

## The DDD Architecture & Folder Structure

DDD enforces a strict separation of concerns, decoupling core business logic from database details, framework details, and transport layers.

```
/home/appycodes-06/personal/BACKEND-DDD/
├── js/                       # TypeScript/Node.js implementation
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── domain/           # Pure business logic (Entities, Value Objects, Domain Services)
│   │   ├── application/      # Orchestration (Use Cases, DTOs, interfaces)
│   │   ├── infrastructure/   # Details (Express, repositories, concrete implementations)
│   │   └── main.ts
│   └── tests/
└── py/                       # Python implementation
    ├── requirements.txt
    ├── src/
    │   ├── domain/           # Pure business logic
    │   ├── application/      # Orchestration
    │   ├── infrastructure/   # Details (FastAPI, database implementations)
    │   └── main.py
    └── tests/
```

### Folder Breakdown

1. **Domain Layer (`domain/`)**:
   * Contains the heart of the business logic.
   * **Entities**: Objects with distinct identities that change state over time (e.g., `Wallet`, `Transaction`).
   * **Value Objects**: Immutable objects defined by their attributes, with no identity (e.g., `Money`, `Currency`).
   * **Aggregate Roots**: Root entities that maintain consistency boundaries (e.g., `Wallet`). All access to inside entities goes through the Aggregate Root.
   * **Domain Services**: Logic that doesn't naturally fit into a single entity (e.g., `TransferService` which updates two different wallets).
   * **Repository Interfaces**: Define the contracts for data persistence. **The domain does not know how data is saved.**
2. **Application Layer (`application/`)**:
   * Coordinates the flow of data. It does not contain business rules; it delegates to the domain.
   * **Use Cases (Command Handlers)**: Executes a specific business flow (e.g., `TransferMoneyUseCase`). It loads aggregates from repositories, executes domain logic, and persists results.
   * **DTOs (Data Transfer Objects)**: Data shapes for input/output.
3. **Infrastructure Layer (`infrastructure/`)**:
   * Contains concrete implementations of interfaces defined in the domain and application layers.
   * Express/FastAPI controllers, database repositories (SQL/NoSQL/In-memory), external API clients, logger implementations, etc.

---

## Real-Life Issues to Solve ("Top 1%")

To understand DDD's power, we will start with a naive implementation that contains two critical real-life flaws, then fix them inside the DDD boundaries:

### 1. Request Idempotency (Application Layer)

* **Problem**: A client sends a `TransferMoney` request, but the network drops before receiving a response. The client retries. Without idempotency, a second transfer is processed, deducting double the money.
* **DDD Solution**: We will implement an `IdempotencyService` in the Application layer, backed by an `IdempotencyRepository` in Infrastructure. The use case will check the presence of the `idempotencyKey` and return the cached response if it exists, ensuring the domain transaction only runs once.

### 2. Concurrency Race Conditions & Invariant Violation (Domain + Repository)

* **Problem**: `Wallet A` has $100. Two transfer requests of $80 are received at the exact same millisecond.
  1. Thread 1 reads `Wallet A` balance ($100).
  2. Thread 2 reads `Wallet A` balance ($100).
  3. Thread 1 checks invariant ($100 >= $80) -> OK. Deducts $80.
  4. Thread 2 checks invariant ($100 >= $80) -> OK. Deducts $80.
  5. Both threads write back. Wallet A balance becomes -$60! The business invariant `balance >= 0` is violated.
* **DDD Solution**: We will implement **Optimistic Locking** on the `Wallet` Aggregate Root.
  * We add a `version: number` attribute to `Wallet`.
  * When updating, the repository executes a conditional write: `UPDATE wallets SET balance = :new_balance, version = :new_version WHERE id = :id AND version = :old_version`.
  * If the version in the database changed in the split second between read and write, the update fails (returns 0 rows affected), throwing a `ConcurrencyException`. The Use Case catches this and rolls back or retries, maintaining aggregate integrity.

---

## Proposed Implementation Plan

### Step 1: Project Setup (JS/TS & Python)

* Initialize `package.json` and `tsconfig.json` in `/js`.
* Setup `requirements.txt` and virtualenv configuration in `/py`.

### Step 2: Implement Domain Layer

* Create value objects (`Money`, `Currency`).
* Create aggregate roots/entities (`Wallet`, `Transaction`).
* Create repository contracts/interfaces.
* Create domain services (`TransferService`).

### Step 3: Implement Application Layer

* Create use case `TransferMoneyUseCase`.
* Define DTOs and exception classes.
* Define `Idempotency` interfaces.

### Step 4: Implement Infrastructure Layer

* Create memory-based `WalletRepository` and `IdempotencyRepository`.
* Create API/Console controllers to trigger transfers.
* Add simulated concurrency delays to expose the race conditions.

### Step 5: Write Tests & Demonstrate the Bugs

* Write a test that sends duplicate requests (shows idempotency failure).
* Write a test that sends parallel requests (shows concurrency race conditions).

### Step 6: Fix and Verify the Bugs

* Implement the Idempotency check.
* Implement the Versioning check (Optimistic Locking).
* Run the tests to show successful mitigation of both issues.

---

## Verification Plan

### Automated Tests

* **TypeScript**: Run `npm test` using Jest.
  * Test: `should prevent double transfer of same idempotency key`.
  * Test: `should reject second concurrent transaction when version mismatch occurs`.
* **Python**: Run `pytest` or `python -m unittest`.
  * Identical tests asserting proper rejection of duplicate idempotency keys and concurrent version mismatches.

### Manual Verification

* We will write run scripts `npm run start` and `python main.py` that demonstrate the step-by-step lifecycle of a transfer, showing logs from both the Domain, Application, and Infrastructure layers.
