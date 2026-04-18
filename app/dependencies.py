from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client

from app.database.supabase_client import create_supabase_client
from app.features.expenses.repository import SupabaseExpenseRepository
from app.features.expenses.service import ExpenseService
from app.features.auth.service import AuthService
from app.features.auth.exceptions import InvalidTokenError

bearer_scheme = HTTPBearer()


#  Database client 

def get_supabase_client() -> Client:
    return create_supabase_client()


# Auth dependencies 
def get_auth_service(
    client: Client = Depends(get_supabase_client),
) -> AuthService:
    return AuthService(client)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> str:
    """
    Extracts and validates the Bearer token from the request header.
    Returns the user_id if valid.
    Raises 401 if the token is missing, expired, or invalid.

    Add this as a dependency to any route you want to protect:
        current_user: str = Depends(get_current_user)
    """
    try:
        user_id = auth_service.verify_token(credentials.credentials)
        return user_id
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


#  Expense dependencies 
def get_expense_repository(
    client: Client = Depends(get_supabase_client),
) -> SupabaseExpenseRepository:
    return SupabaseExpenseRepository(client)


def get_expense_service(
    repo: SupabaseExpenseRepository = Depends(get_expense_repository),
) -> ExpenseService:
    return ExpenseService(repo)