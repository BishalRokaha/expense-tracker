# Expense Tracker API

A production grade REST API built with **FastAPI** and **Supabase** that demonstrates clean layered architecture, dependency injection, and thorough testing.

---

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Setup & Running Locally](#setup--running-locally)
- [Running Tests](#running-tests)
- [API Endpoints](#api-endpoints)
- [Architectural Decisions](#architectural-decisions)

---

## Architecture Overview

The project is organised into strict layers. Each layer has **one job** and only talks to the layer directly below it.

```
HTTP Request
     │
     ▼
┌─────────────┐
│   Router    │  Knows HTTP. Parses params, calls service, returns response.
│  (FastAPI)  │  Zero business logic.
└──────┬──────┘
       │ calls
       ▼
┌─────────────┐
│   Service   │  Owns all business rules (summary aggregation, ID generation,
│             │  validation logic). Raises domain exceptions, not HTTP errors.
└──────┬──────┘
       │ calls
       ▼
┌─────────────┐
│ Repository  │  Abstracts the database. Translates between domain models
│ (Interface) │  and DB rows. Supabase implementation is swappable.
└──────┬──────┘
       │ uses
       ▼
┌─────────────┐
│  Supabase   │  Hosted . Accessed only through the repository.
└─────────────┘
```

**Dependency flow (via FastAPI `Depends`):**

```
get_expense_service
    └── get_expense_repository
            └── get_supabase_client
                    └── create_supabase_client()  ← reads from .env
```

---

## Project Structure

```
expense_tracker/
├── app/
│   ├── main.py              # FastAPI app, global exception handlers, router registration
│   ├── config.py            # Pydantic-settings: loads SUPABASE_URL and SUPABASE_KEY from .env
│   ├── dependencies.py      # All FastAPI Depends wiring 
│   ├── database/
│   │   └── supabase_client.py   # Factory that creates the Supabase Client
│   └── features/
│       └── expenses/
│           ├── router.py        # HTTP layer — routes, request/response only
│           ├── service.py       # Business logic layer
│           ├── repository.py    # Data access layer (abstract + Supabase concrete)
│           ├── schemas.py       # Pydantic v2 request/response models
│           ├── models.py        # Internal domain dataclass (Expense)
│           └── exceptions.py    # Domain exceptions (ExpenseNotFoundError, etc.)
├── tests/
│   ├── test_expense_service.py  # Unit tests (FakeRepository, no DB)
│   └── test_expense_router.py   # Integration tests (TestClient + DI override)
├── .env.example
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Setup & Running Locally

### Prerequisites
- Python 3.11 or higher
- A free [Supabase](https://supabase.com) account

### Step 1 — Clone the repo

```bash
git clone <your-repo-url>
cd expense_tracker
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv

# On macOS / Linux:
source venv/bin/activate

# On Windows (PowerShell):
venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Create your Supabase table

1. Go to [supabase.com](https://supabase.com) and sign in.
2. Create a new project.
3. Open the **SQL Editor** and run the following:

```sql
CREATE TABLE expenses (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    amount      NUMERIC(12, 2) NOT NULL,
    category    TEXT NOT NULL,
    date        DATE NOT NULL,
    description TEXT
);
```

### Step 5 — Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your Supabase credentials:

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key
```

You can find both values in your Supabase project under **Settings → API**.

### Step 6 — Run the server

```bash
uvicorn app.main:app --reload
```

The API will be live at **http://127.0.0.1:8000**

Visit **http://127.0.0.1:8000/docs** for the interactive Swagger UI.

---

## Running Tests

Tests use an **in-memory fake repository** — no real database is required. You can run them without a `.env` file.

```bash
pytest
```

To see detailed output:

```bash
pytest -v
```

To run only service tests:

```bash
pytest tests/test_expense_service.py -v
```

To run only router tests:

```bash
pytest tests/test_expense_router.py -v
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/expenses/` | Create a new expense |
| `GET` | `/expenses/` | List expenses (filter by category, date range, paginate) |
| `GET` | `/expenses/summary` | Monthly spending summary with category breakdown |
| `GET` | `/expenses/{id}` | Get a single expense |
| `DELETE` | `/expenses/{id}` | Delete an expense |
| `GET` | `/health` | Health check |

### Example: Create an expense

```bash
curl -X POST http://127.0.0.1:8000/expenses/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Lunch",
    "amount": 750.00,
    "category": "Food",
    "date": "2024-03-15",
    "description": "Monthly team lunch"
  }'
```

### Example: Get monthly summary

```bash
curl "http://127.0.0.1:8000/expenses/summary?month=3&year=2024"
```

### Example: List with filters

```bash
curl "http://127.0.0.1:8000/expenses/?category=Food&start_date=2024-03-01&end_date=2024-03-31&page=1&page_size=10"
```

---

## Architectural Decisions

- Strict 3-layer architecture:- Router, Service, Repository
- Router contains zero business logic
- Domain model (Expense dataclass) kept separate from Pydantic API schemas
- Summary/aggregation logic lives in the service, not in SQL or the router
- All dependencies injected via FastAPI Depends, nothing created inline
- Supabase client created via a factory function, never imported as a global
- Secrets loaded through pydantic-settings from a .env file
- FakeExpenseRepository used in tests instead of mocking
- Service tests have zero HTTP or database dependencies
- Router tests use FastAPI TestClient with dependency overrides