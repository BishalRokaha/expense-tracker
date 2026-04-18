import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_expense_service, get_current_user
from app.features.expenses.service import ExpenseService
from tests.test_expense_service import FakeExpenseRepository

FAKE_USER_ID = "user-123"


@pytest.fixture
def client():
    fake_repo = FakeExpenseRepository()
    fake_service = ExpenseService(fake_repo)

    # Override the expense service with the fake
    app.dependency_overrides[get_expense_service] = lambda: fake_service
    # Override auth so tests don't need real JWT tokens
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER_ID

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


VALID_PAYLOAD = {
    "title": "Dinner",
    "amount": 350.0,
    "category": "Food",
    "date": "2024-03-15",
    "description": "Team dinner",
}


def create_one(client) -> dict:
    resp = client.post("/expenses/", json=VALID_PAYLOAD)
    assert resp.status_code == 201
    return resp.json()


def test_create_expense_returns_201(client):
    resp = client.post("/expenses/", json=VALID_PAYLOAD)
    assert resp.status_code == 201
    assert resp.json()["title"] == "Dinner"
    assert "id" in resp.json()


def test_create_expense_rejects_negative_amount(client):
    resp = client.post("/expenses/", json={**VALID_PAYLOAD, "amount": -10})
    assert resp.status_code == 422


def test_create_expense_rejects_missing_title(client):
    bad = {k: v for k, v in VALID_PAYLOAD.items() if k != "title"}
    resp = client.post("/expenses/", json=bad)
    assert resp.status_code == 422


def test_get_expense_by_id(client):
    created = create_one(client)
    resp = client.get(f"/expenses/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_expense_returns_404_for_unknown_id(client):
    resp = client.get("/expenses/does-not-exist")
    assert resp.status_code == 404


def test_list_expenses_returns_paginated_response(client):
    create_one(client)
    create_one(client)
    resp = client.get("/expenses/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert "page" in data


def test_list_expenses_filters_by_category(client):
    client.post("/expenses/", json={**VALID_PAYLOAD, "category": "Transport"})
    client.post("/expenses/", json={**VALID_PAYLOAD, "category": "Food"})
    resp = client.get("/expenses/?category=Transport")
    assert resp.json()["total"] == 1


def test_delete_expense_returns_204(client):
    created = create_one(client)
    resp = client.delete(f"/expenses/{created['id']}")
    assert resp.status_code == 204


def test_delete_expense_returns_404_when_not_found(client):
    resp = client.delete("/expenses/ghost-id")
    assert resp.status_code == 404


def test_get_summary(client):
    client.post("/expenses/", json={**VALID_PAYLOAD, "amount": 100, "date": "2024-03-01"})
    client.post("/expenses/", json={**VALID_PAYLOAD, "amount": 200, "date": "2024-03-20"})
    resp = client.get("/expenses/summary?month=3&year=2024")
    assert resp.status_code == 200
    assert resp.json()["total_spending"] == 300.0


def test_protected_route_without_token_returns_401(client):
    # Remove the auth override to simulate a real unauthenticated request
    app.dependency_overrides.pop(get_current_user, None)
    resp = client.get("/expenses/")
    assert resp.status_code == 403  # No token provided at all
    # Restore for other tests
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER_ID


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200