from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.features.expenses.schemas import (
    ExpenseCreate,
    ExpenseResponse,
    PaginatedExpenses,
    ExpenseSummary,
)
from app.features.expenses.service import ExpenseService
from app.features.expenses.exceptions import ExpenseNotFoundError
from app.dependencies import get_expense_service, get_current_user

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"]
    )


# POST /expenses 
@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    service: ExpenseService = Depends(get_expense_service),
    current_user: str = Depends(get_current_user),   # ← protected
):
    return service.create_expense(payload, user_id=current_user)


# GET /expenses/summary 
@router.get("/summary", response_model=ExpenseSummary)
def get_summary(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000, le=2100),
    service: ExpenseService = Depends(get_expense_service),
    current_user: str = Depends(get_current_user),   # ← protected
):
    return service.get_summary(year=year, month=month, user_id=current_user)


# GET /expenses 
@router.get("/", response_model=PaginatedExpenses)
def list_expenses(
    category: Optional[str] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: ExpenseService = Depends(get_expense_service),
    current_user: str = Depends(get_current_user),   # ← protected
):
    return service.list_expenses(
        category=category,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
        user_id=current_user,
    )


#  GET /expenses/{id} 
@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: str,
    service: ExpenseService = Depends(get_expense_service),
    current_user: str = Depends(get_current_user),   # ← protected
):
    try:
        return service.get_expense(expense_id, user_id=current_user)
    except ExpenseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# DELETE /expenses/{id} 
@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: str,
    service: ExpenseService = Depends(get_expense_service),
    current_user: str = Depends(get_current_user),   # ← protected
):
    try:
        service.delete_expense(expense_id, user_id=current_user)
    except ExpenseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))