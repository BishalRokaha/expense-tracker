class ExpenseNotFoundError(Exception):
    """Raised by the service layer when an expense ID does not exist."""

    def __init__(self, expense_id: str):
        self.expense_id = expense_id
        super().__init__(f"Expense with id '{expense_id}' was not found.")


class ExpenseRepositoryError(Exception):
    """Raised when a database operation fails unexpectedly."""
