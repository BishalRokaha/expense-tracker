"""
Unit tests for ExpenseService.

Uses a FakeExpenseRepository (in-memory) so NO real database is needed.
Tests cover:
- Creating expenses
- Fetching by ID
- Listing with filters and pagination
- Deleting expenses
- Generating monthly summaries  
"""
import pytest
from datetime import date
from typing import Optional, List
from calendar import monthrange

from app.features.expenses.models import Expense
from app.features.expenses.repository import AbstractExpenseRepository
from app.features.expenses.service import ExpenseService
from app.features.expenses.schemas import ExpenseCreate
from app.features.expenses.exceptions import ExpenseNotFoundError



class FakeExpenseRepository(AbstractExpenseRepository):
    """
    In-memory implementation of AbstractExpenseRepository.
    Identical contract to SupabaseExpenseRepository
    """

    def __init__(self):
        self._store: dict[str, Expense] = {}

    def create(self, expense: Expense) -> Expense:
        self._store[expense.id] = expense
        return expense

    def get_by_id(self, expense_id: str) -> Optional[Expense]:
        return self._store.get(expense_id)

    def list_expenses(
        self,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Expense], int]:
        items = list(self._store.values())
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

    def list_by_month(self, year: int, month: int) -> List[Expense]:
        _, last_day = monthrange(year, month)
        first = date(year, month, 1)
        last = date(year, month, last_day)
        return [e for e in self._store.values() if first <= e.date <= last]


#Fixtures 

@pytest.fixture
def repo():
    return FakeExpenseRepository()


@pytest.fixture
def service(repo):
    return ExpenseService(repo)


def make_create_payload(**kwargs) -> ExpenseCreate:
    defaults = dict(
        title="Lunch",
        amount=250.0,
        category="Food",
        date=date(2024, 3, 15),
        description=None,
    )
    defaults.update(kwargs)
    return ExpenseCreate(**defaults)


#Tests: create 
def test_create_expense_returns_response(service):
    payload = make_create_payload(title="Coffee", amount=50.0)
    result = service.create_expense(payload)

    assert result.title == "Coffee"
    assert result.amount == 50.0
    assert result.category == "Food"
    assert result.id is not None


def test_create_expense_assigns_unique_ids(service):
    id1 = service.create_expense(make_create_payload()).id
    id2 = service.create_expense(make_create_payload()).id
    assert id1 != id2


#Tests: get_expense
def test_get_expense_returns_correct_expense(service):
    created = service.create_expense(make_create_payload(title="Book"))
    fetched = service.get_expense(created.id)
    assert fetched.id == created.id
    assert fetched.title == "Book"


def test_get_expense_raises_not_found_for_missing_id(service):
    with pytest.raises(ExpenseNotFoundError):
        service.get_expense("non-existent-id")


#Tests: list_expenses 
def test_list_expenses_returns_all(service):
    service.create_expense(make_create_payload(title="A"))
    service.create_expense(make_create_payload(title="B"))
    result = service.list_expenses()
    assert result.total == 2


def test_list_expenses_filters_by_category(service):
    service.create_expense(make_create_payload(category="Food"))
    service.create_expense(make_create_payload(category="Transport"))
    result = service.list_expenses(category="Transport")
    assert result.total == 1
    assert result.items[0].category == "Transport"


def test_list_expenses_filters_by_date_range(service):
    service.create_expense(make_create_payload(date=date(2024, 1, 5)))
    service.create_expense(make_create_payload(date=date(2024, 3, 20)))
    result = service.list_expenses(
        start_date=date(2024, 3, 1), end_date=date(2024, 3, 31)
    )
    assert result.total == 1


def test_list_expenses_pagination(service):
    for i in range(5):
        service.create_expense(make_create_payload(title=f"Expense {i}"))
    page1 = service.list_expenses(page=1, page_size=3)
    page2 = service.list_expenses(page=2, page_size=3)
    assert len(page1.items) == 3
    assert len(page2.items) == 2
    assert page1.total == 5


#Tests: delete

def test_delete_expense_removes_it(service):
    created = service.create_expense(make_create_payload())
    service.delete_expense(created.id)
    with pytest.raises(ExpenseNotFoundError):
        service.get_expense(created.id)


def test_delete_expense_raises_not_found_for_missing_id(service):
    with pytest.raises(ExpenseNotFoundError):
        service.delete_expense("ghost-id")


# Tests: summary 
def test_summary_calculates_total_and_breakdown(service):
    service.create_expense(make_create_payload(amount=100, category="Food", date=date(2024, 3, 1)))
    service.create_expense(make_create_payload(amount=200, category="Food", date=date(2024, 3, 10)))
    service.create_expense(make_create_payload(amount=50, category="Transport", date=date(2024, 3, 5)))
    service.create_expense(make_create_payload(amount=999, category="Food", date=date(2024, 4, 1)))

    summary = service.get_summary(year=2024, month=3)

    assert summary.total_spending == 350.0
    assert summary.month == 3
    assert summary.year == 2024
    assert len(summary.breakdown) == 2

    food = next(b for b in summary.breakdown if b.category == "Food")
    assert food.total == 300.0
    assert food.count == 2

    transport = next(b for b in summary.breakdown if b.category == "Transport")
    assert transport.total == 50.0
    assert transport.count == 1


def test_summary_empty_month_returns_zero(service):
    summary = service.get_summary(year=2024, month=6)
    assert summary.total_spending == 0.0
    assert summary.breakdown == []
