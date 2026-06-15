from fastapi import APIRouter, Header
from controllers.expenseController import expenses_db, get_current_user
from typing import Optional

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/total")
def total_expense(authorization: Optional[str] = Header(None)):
    user  = get_current_user(authorization)
    email = user["sub"]
    exps  = expenses_db.get(email, [])
    return {"total_expense": sum(e["amount"] for e in exps)}


@router.get("/category")
def category_expense(authorization: Optional[str] = Header(None)):
    user  = get_current_user(authorization)
    email = user["sub"]
    exps  = expenses_db.get(email, [])

    categories: dict = {}
    for exp in exps:
        cat = exp.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + exp["amount"]
    return categories