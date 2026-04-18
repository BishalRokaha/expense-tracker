from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.features.expenses.router import router as expenses_router
from app.features.auth.router import router as auth_router
from app.features.expenses.exceptions import ExpenseNotFoundError, ExpenseRepositoryError
from app.features.auth.exceptions import InvalidTokenError 

app = FastAPI(
    title="Expense Tracker API",
    description="A production-grade Expense Tracker built with FastAPI and Supabase.",
    version="2.0.0",
)

@app.exception_handler(ExpenseNotFoundError)
async def not_found_handler(request: Request, exc: ExpenseNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ExpenseRepositoryError)
async def repo_error_handler(request: Request, exc: ExpenseRepositoryError):
    return JSONResponse(status_code=500, content={"detail": "A database error occurred."})

@app.exception_handler(InvalidTokenError)
async def token_error_handler(request: Request, exc: InvalidTokenError):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )


# Routers 
app.include_router(auth_router)   
app.include_router(expenses_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
