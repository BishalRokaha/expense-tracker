from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, List

from supabase import Client

from app.features.expenses.models import Expense
from app.features.expenses.exceptions import ExpenseRepositoryError

TABLE = "expenses"


class AbstractExpenseRepository(ABC):

    @abstractmethod
    def create(self, expense: Expense) -> Expense: ...

    @abstractmethod
    def get_by_id(self, expense_id: str) -> Optional[Expense]: ...

    @abstractmethod
    def list_expenses(
        self,
        user_id: str,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Expense], int]: ...

    @abstractmethod
    def delete(self, expense_id: str) -> bool: ...

    @abstractmethod
    def list_by_month(self, year: int, month: int, user_id: str) -> List[Expense]: ...


class SupabaseExpenseRepository(AbstractExpenseRepository):

    def __init__(self, client: Client):
        self._client = client

    @staticmethod
    def _row_to_expense(row: dict) -> Expense:
        return Expense(
            id=row["id"],
            title=row["title"],
            amount=float(row["amount"]),
            category=row["category"],
            date=date.fromisoformat(row["date"]),
            user_id=row["user_id"],         # ← map user_id from DB row
            description=row.get("description"),
        )

    def create(self, expense: Expense) -> Expense:
        try:
            payload = {
                "id": expense.id,
                "title": expense.title,
                "amount": expense.amount,
                "category": expense.category,
                "date": expense.date.isoformat(),
                "description": expense.description,
                "user_id": expense.user_id,  # ← store user_id in DB
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
        user_id: str,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Expense], int]:
        try:
            query = (
                self._client.table(TABLE)
                .select("*", count="exact")
                .eq("user_id", user_id)     # ← only this user's rows
            )
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
            return items, response.count or 0
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

    def list_by_month(self, year: int, month: int, user_id: str) -> List[Expense]:
        try:
            from calendar import monthrange
            _, last_day = monthrange(year, month)
            first = date(year, month, 1).isoformat()
            last = date(year, month, last_day).isoformat()

            response = (
                self._client.table(TABLE)
                .select("*")
                .eq("user_id", user_id)     # ← only this user's rows
                .gte("date", first)
                .lte("date", last)
                .execute()
            )
            return [self._row_to_expense(row) for row in response.data]
        except Exception as exc:
            raise ExpenseRepositoryError(str(exc)) from exc