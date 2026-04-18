import pytest
from datetime import date
from typing import Optional, List
from calendar import monthrange

from app.features.expenses.models import Expense
from app.features.expenses.repository import AbstractExpenseRepository
from app.features.expenses.service import ExpenseService
from app.features.expenses.schemas import ExpenseCreate
from app.features.expenses.exceptions import ExpenseNotFoundError

FAKE_USER_ID = "user-123"
OTHER_USER_ID = "user-999"


class FakeExpenseRepository(AbstractExpenseRepository):

    def __init__(self):
        self._store: dict[str, Expense] = {}

    def create(self, expense: Expense) -> Expense:
        self._store[expense.id] = expense
        return expense

    def get_by_id(self, expense_id: str) -> Optional[Expense]:
        return self._store.get(expense_id)

    def list_expenses(
        self,
        user_id: str,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Expense], int]:
        items = [e for e in self._store.values() if e.user_id == user_id]
        if category:
            items = [e for e in items if e.category == category]
        if start_date:
            items = [e for e in items if e.date >= start_date]
        if end_date:
            items = [e for e in items if e.date <= end_date]
        total = len(items)
        offset = (page - 1) * page_size
        return items[offset: offset + page_size], total

    def delete(self, expense_id: str) -> bool:
        if expense_id in self._store:
            del self._store[expense_id]
            return True
        return False

    def list_by_month(self, year: int, month: int, user_id: str) -> List[Expense]:
        _, last_day = monthrange(year, month)
        first = date(year, month, 1)
        last = date(year, month, last_day)
        return [
            e for e in self._store.values()
            if first <= e.date <= last and e.user_id == user_id
        ]


@pytest.fixture
def repo():
    return FakeExpenseRepository()


@pytest.fixture
def service(repo):
    return ExpenseService(repo)


def make_create_payload(**kwargs) -> ExpenseCreate:
    defaults = dict(
        title="Lunch", amount=250.0, category="Food",
        date=date(2024, 3, 15), description=None,
    )
    defaults.update(kwargs)
    return ExpenseCreate(**defaults)


#  Create 
def test_create_expense_returns_response(service):
    result = service.create_expense(make_create_payload(title="Coffee"), user_id=FAKE_USER_ID)
    assert result.title == "Coffee"
    assert result.id is not None


def test_create_expense_assigns_unique_ids(service):
    id1 = service.create_expense(make_create_payload(), user_id=FAKE_USER_ID).id
    id2 = service.create_expense(make_create_payload(), user_id=FAKE_USER_ID).id
    assert id1 != id2


#  Get 
def test_get_expense_returns_correct_expense(service):
    created = service.create_expense(make_create_payload(title="Book"), user_id=FAKE_USER_ID)
    fetched = service.get_expense(created.id, user_id=FAKE_USER_ID)
    assert fetched.title == "Book"


def test_get_expense_raises_not_found_for_missing_id(service):
    with pytest.raises(ExpenseNotFoundError):
        service.get_expense("bad-id", user_id=FAKE_USER_ID)


def test_get_expense_raises_not_found_for_wrong_user(service):
    # User A creates an expense
    created = service.create_expense(make_create_payload(), user_id=FAKE_USER_ID)
    # User B tries to fetch it — should get 404, not User A's data
    with pytest.raises(ExpenseNotFoundError):
        service.get_expense(created.id, user_id=OTHER_USER_ID)


# List 
def test_list_expenses_only_returns_own_expenses(service):
    service.create_expense(make_create_payload(title="Mine"), user_id=FAKE_USER_ID)
    service.create_expense(make_create_payload(title="Theirs"), user_id=OTHER_USER_ID)
    result = service.list_expenses(user_id=FAKE_USER_ID)
    assert result.total == 1
    assert result.items[0].title == "Mine"


def test_list_expenses_filters_by_category(service):
    service.create_expense(make_create_payload(category="Food"), user_id=FAKE_USER_ID)
    service.create_expense(make_create_payload(category="Transport"), user_id=FAKE_USER_ID)
    result = service.list_expenses(user_id=FAKE_USER_ID, category="Transport")
    assert result.total == 1


def test_list_expenses_pagination(service):
    for i in range(5):
        service.create_expense(make_create_payload(title=f"E{i}"), user_id=FAKE_USER_ID)
    page1 = service.list_expenses(user_id=FAKE_USER_ID, page=1, page_size=3)
    page2 = service.list_expenses(user_id=FAKE_USER_ID, page=2, page_size=3)
    assert len(page1.items) == 3
    assert len(page2.items) == 2


# Delete 
def test_delete_expense_removes_it(service):
    created = service.create_expense(make_create_payload(), user_id=FAKE_USER_ID)
    service.delete_expense(created.id, user_id=FAKE_USER_ID)
    with pytest.raises(ExpenseNotFoundError):
        service.get_expense(created.id, user_id=FAKE_USER_ID)


def test_delete_expense_raises_not_found_for_wrong_user(service):
    # User A creates an expense, User B tries to delete it
    created = service.create_expense(make_create_payload(), user_id=FAKE_USER_ID)
    with pytest.raises(ExpenseNotFoundError):
        service.delete_expense(created.id, user_id=OTHER_USER_ID)


#  Summary 
def test_summary_only_includes_own_expenses(service):
    service.create_expense(make_create_payload(amount=100, date=date(2024, 3, 1)), user_id=FAKE_USER_ID)
    service.create_expense(make_create_payload(amount=999, date=date(2024, 3, 1)), user_id=OTHER_USER_ID)
    summary = service.get_summary(year=2024, month=3, user_id=FAKE_USER_ID)
    assert summary.total_spending == 100.0


def test_summary_calculates_breakdown(service):
    service.create_expense(make_create_payload(amount=100, category="Food", date=date(2024, 3, 1)), user_id=FAKE_USER_ID)
    service.create_expense(make_create_payload(amount=50, category="Transport", date=date(2024, 3, 5)), user_id=FAKE_USER_ID)
    summary = service.get_summary(year=2024, month=3, user_id=FAKE_USER_ID)
    assert summary.total_spending == 150.0
    assert len(summary.breakdown) == 2


def test_summary_empty_month(service):
    summary = service.get_summary(year=2024, month=6, user_id=FAKE_USER_ID)
    assert summary.total_spending == 0.0