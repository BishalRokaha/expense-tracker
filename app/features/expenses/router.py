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
from app.dependencies import get_expense_service

router = APIRouter(prefix="/expenses", tags=["expenses"])


# POST /expenses 

@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    service: ExpenseService = Depends(get_expense_service),
):
    """Create a new expense."""
    return service.create_expense(payload)


# GET /expenses/summary  

@router.get("/summary", response_model=ExpenseSummary)
def get_summary(
    month: int = Query(..., ge=1, le=12, description="Month number (1–12)"),
    year: int = Query(..., ge=2000, le=2100, description="Four-digit year"),
    service: ExpenseService = Depends(get_expense_service),
):
    """Return total spending and category breakdown for a given month."""
    return service.get_summary(year=year, month=month)


# GET /expenses 
@router.get("/", response_model=PaginatedExpenses)
def list_expenses(
    category: Optional[str] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: ExpenseService = Depends(get_expense_service),
):
    """List expenses with optional filters and pagination."""
    return service.list_expenses(
        category=category,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


#  GET /expenses/{id} 
@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: str,
    service: ExpenseService = Depends(get_expense_service),
):
    """Fetch a single expense by ID."""
    try:
        return service.get_expense(expense_id)
    except ExpenseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# DELETE /expenses/{id} 
@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: str,
    service: ExpenseService = Depends(get_expense_service),
):
    """Delete an expense by ID."""
    try:
        service.delete_expense(expense_id)
    except ExpenseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
