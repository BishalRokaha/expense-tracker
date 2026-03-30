from functools import lru_cache

from fastapi import Depends
from supabase import Client

from app.database.supabase_client import create_supabase_client
from app.features.expenses.repository import SupabaseExpenseRepository
from app.features.expenses.service import ExpenseService


def get_supabase_client() -> Client:
    """
    Creates a Supabase client.
    FastAPI calls this once per request.
    """
    return create_supabase_client()


def get_expense_repository(
    client: Client = Depends(get_supabase_client),
) -> SupabaseExpenseRepository:
    """Inject the repository with the database client."""
    return SupabaseExpenseRepository(client)


def get_expense_service(
    repo: SupabaseExpenseRepository = Depends(get_expense_repository),
) -> ExpenseService:
    """Inject the service with the repository."""
    return ExpenseService(repo)
