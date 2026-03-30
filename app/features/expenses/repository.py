from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, List
import uuid

from supabase import Client

from app.features.expenses.models import Expense
from app.features.expenses.exceptions import ExpenseRepositoryError

TABLE = "expenses"


# Abstract interface 
class AbstractExpenseRepository(ABC):

    @abstractmethod
    def create(self, expense: Expense) -> Expense:
        ...

    @abstractmethod
    def get_by_id(self, expense_id: str) -> Optional[Expense]:
        ...

    @abstractmethod
    def list_expenses(
        self,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Expense], int]:
        """Returns (items, total_count)."""
        ...

    @abstractmethod
    def delete(self, expense_id: str) -> bool:
        """Returns True if the row existed and was deleted, False otherwise."""
        ...

    @abstractmethod
    def list_by_month(self, year: int, month: int) -> List[Expense]:
        """Returns all expenses for the given month/year (used for summary)."""
        ...


# Concrete Supabase implementation 
class SupabaseExpenseRepository(AbstractExpenseRepository):

    def __init__(self, client: Client):
        self._client = client

    # helpers 
    @staticmethod
    def _row_to_expense(row: dict) -> Expense:
        return Expense(
            id=row["id"],
            title=row["title"],
            amount=float(row["amount"]),
            category=row["category"],
            date=date.fromisoformat(row["date"]),
            description=row.get("description"),
        )

    # interface implementation 
    def create(self, expense: Expense) -> Expense:
        try:
            payload = {
                "id": expense.id,
                "title": expense.title,
                "amount": expense.amount,
                "category": expense.category,
                "date": expense.date.isoformat(),
                "description": expense.description,
            }
            response = self._client.table(TABLE).insert(payload).execute()
            return self._row_to_expense(response.data[0])
        except Exception as exc:
            raise ExpenseRepositoryError(str(exc)) from exc

    def get_by_id(self, expense_id: str) -> Optional[Expense]:
        try:
            response = (
                self._client.table(TABLE)
                .select("*")
                .eq("id", expense_id)
                .execute()
            )
            if not response.data:
                return None
            return self._row_to_expense(response.data[0])
        except Exception as exc:
            raise ExpenseRepositoryError(str(exc)) from exc

    def list_expenses(
        self,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Expense], int]:
        try:
            query = self._client.table(TABLE).select("*", count="exact")

            if category:
                query = query.eq("category", category)
            if start_date:
                query = query.gte("date", start_date.isoformat())
            if end_date:
                query = query.lte("date", end_date.isoformat())

            offset = (page - 1) * page_size
            query = query.order("date", desc=True).range(offset, offset + page_size - 1)

            response = query.execute()
            items = [self._row_to_expense(row) for row in response.data]
            total = response.count or 0
            return items, total
        except Exception as exc:
            raise ExpenseRepositoryError(str(exc)) from exc

    def delete(self, expense_id: str) -> bool:
        try:
            response = (
                self._client.table(TABLE)
                .delete()
                .eq("id", expense_id)
                .execute()
            )
            return len(response.data) > 0
        except Exception as exc:
            raise ExpenseRepositoryError(str(exc)) from exc

    def list_by_month(self, year: int, month: int) -> List[Expense]:
        try:
            # Building first and last day of the month for filtering
            from calendar import monthrange
            _, last_day = monthrange(year, month)
            first = date(year, month, 1).isoformat()
            last = date(year, month, last_day).isoformat()

            response = (
                self._client.table(TABLE)
                .select("*")
                .gte("date", first)
                .lte("date", last)
                .execute()
            )
            return [self._row_to_expense(row) for row in response.data]
        except Exception as exc:
            raise ExpenseRepositoryError(str(exc)) from exc
