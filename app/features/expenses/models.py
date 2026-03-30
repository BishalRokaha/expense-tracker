from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Expense:
    id: str
    title: str
    amount: float
    category: str
    date: date
    description: Optional[str] = None
