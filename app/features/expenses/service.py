from collections import defaultdict
from datetime import date
from typing import Optional
import uuid

from app.features.expenses.models import Expense
from app.features.expenses.repository import AbstractExpenseRepository
from app.features.expenses.schemas import (
    ExpenseCreate,
    ExpenseResponse,
    PaginatedExpenses,
    ExpenseSummary,
    CategoryBreakdown,
)
from app.features.expenses.exceptions import ExpenseNotFoundError


def _expense_to_response(expense: Expense) -> ExpenseResponse:
    return ExpenseResponse(
        id=expense.id,
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        date=expense.date,
        description=expense.description,
    )


class ExpenseService:

    def __init__(self, repository: AbstractExpenseRepository):
        self._repo = repository

    def create_expense(self, data: ExpenseCreate, user_id: str) -> ExpenseResponse:
        expense = Expense(
            id=str(uuid.uuid4()),
            title=data.title,
            amount=data.amount,
            category=data.category,
            date=data.date,
            description=data.description,
            user_id=user_id,        
        )
        created = self._repo.create(expense)
        return _expense_to_response(created)

    def list_expenses(
        self,
        user_id: str,               
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedExpenses:
        items, total = self._repo.list_expenses(
            user_id=user_id,
            category=category,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )
        return PaginatedExpenses(
            items=[_expense_to_response(e) for e in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_expense(self, expense_id: str, user_id: str) -> ExpenseResponse:
        expense = self._repo.get_by_id(expense_id)
        # Check it exists AND belongs to this user
        if expense is None or expense.user_id != user_id:
            raise ExpenseNotFoundError(expense_id)
        return _expense_to_response(expense)

    def delete_expense(self, expense_id: str, user_id: str) -> None:
        expense = self._repo.get_by_id(expense_id)
        # Check it exists AND belongs to this user before deleting
        if expense is None or expense.user_id != user_id:
            raise ExpenseNotFoundError(expense_id)
        self._repo.delete(expense_id)

    def get_summary(self, year: int, month: int, user_id: str) -> ExpenseSummary:
        expenses = self._repo.list_by_month(year=year, month=month, user_id=user_id)

        total_spending = 0.0
        category_totals: dict[str, float] = defaultdict(float)
        category_counts: dict[str, int] = defaultdict(int)

        for expense in expenses:
            total_spending += expense.amount
            category_totals[expense.category] += expense.amount
            category_counts[expense.category] += 1

        breakdown = [
            CategoryBreakdown(
                category=cat,
                total=round(category_totals[cat], 2),
                count=category_counts[cat],
            )
            for cat in sorted(category_totals)
        ]

        return ExpenseSummary(
            month=month,
            year=year,
            total_spending=round(total_spending, 2),
            breakdown=breakdown,
        )