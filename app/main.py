from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.features.expenses.router import router as expenses_router
from app.features.expenses.exceptions import ExpenseNotFoundError, ExpenseRepositoryError

app = FastAPI(
    title="Expense Tracker API",
    description="A production-grade Expense Tracker built with FastAPI and Supabase.",
    version="1.0.0",
)

@app.exception_handler(ExpenseNotFoundError)
async def not_found_handler(request: Request, exc: ExpenseNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ExpenseRepositoryError)
async def repo_error_handler(request: Request, exc: ExpenseRepositoryError):
    return JSONResponse(status_code=500, content={"detail": "A database error occurred."})


# Routers 

app.include_router(expenses_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
