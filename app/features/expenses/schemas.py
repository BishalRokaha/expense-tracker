from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# Request schemas 
class ExpenseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0, description="Must be a positive number")
    category: str = Field(..., min_length=1, max_length=100)
    date: date
    description: Optional[str] = Field(default=None, max_length=500)

    @field_validator("category")
    @classmethod
    def category_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("category cannot be blank")
        return v.strip()


# Response schemas 
class ExpenseResponse(BaseModel):
    id: str
    title: str
    amount: float
    category: str
    date: date
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class PaginatedExpenses(BaseModel):
    items: List[ExpenseResponse]
    total: int
    page: int
    page_size: int


class CategoryBreakdown(BaseModel):
    category: str
    total: float
    count: int


class ExpenseSummary(BaseModel):
    month: int
    year: int
    total_spending: float
    breakdown: List[CategoryBreakdown]
