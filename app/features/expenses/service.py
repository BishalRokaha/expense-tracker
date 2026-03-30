from collections import defaultdict
from datetime import date
from typing import Optional, List
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

    # Create 
    def create_expense(self, data: ExpenseCreate) -> ExpenseResponse:
        expense = Expense(
            id=str(uuid.uuid4()),
            title=data.title,
            amount=data.amount,
            category=data.category,
            date=data.date,
            description=data.description,
        )
        created = self._repo.create(expense)
        return _expense_to_response(created)

    # Read (list) 

    def list_expenses(
        self,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedExpenses:
        items, total = self._repo.list_expenses(
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

    # Read (single) 

    def get_expense(self, expense_id: str) -> ExpenseResponse:
        expense = self._repo.get_by_id(expense_id)
        if expense is None:
            raise ExpenseNotFoundError(expense_id)
        return _expense_to_response(expense)

    # Delete 
    def delete_expense(self, expense_id: str) -> None:
        deleted = self._repo.delete(expense_id)
        if not deleted:
            raise ExpenseNotFoundError(expense_id)

    # Summary 
    def get_summary(self, year: int, month: int) -> ExpenseSummary:
        
        expenses = self._repo.list_by_month(year=year, month=month)

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
