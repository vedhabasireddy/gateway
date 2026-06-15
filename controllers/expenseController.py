from fastapi import APIRouter, HTTPException, Header
from models.schemas import ExpenseRequest, ExpenseResponse, ExpenseData, DeleteResponse
from controllers.authenticationController import decode_token
from typing import Optional, List
import time

router = APIRouter(prefix="/expense", tags=["Expense"])

expenses_db: dict = {}


def get_current_user(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    return decode_token(token)


@router.post("/add", response_model=ExpenseResponse)
def add_expense(expense: ExpenseRequest, authorization: Optional[str] = Header(None)):
    user  = get_current_user(authorization)
    email = user["sub"]

    if email not in expenses_db:
        expenses_db[email] = []

    new_exp = ExpenseData(
        id=int(time.time() * 1000),
        expenseName=expense.expenseName,
        amount=expense.amount,
        category=expense.category,
        description=expense.description or "",
        date=expense.date or "",
        userEmail=email,
        userName=user.get("username", ""),
    )
    expenses_db[email].append(new_exp.dict())
    return ExpenseResponse(message="Expense added successfully", data=new_exp)


@router.get("/my", response_model=List[ExpenseData])
def get_my_expenses(authorization: Optional[str] = Header(None)):
    user  = get_current_user(authorization)
    email = user["sub"]
    return expenses_db.get(email, [])


@router.get("/all", response_model=List[ExpenseData])
def get_all_expenses(authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    if user.get("role") not in ("admin", "ADMIN", "ROLE_ADMIN"):
        raise HTTPException(status_code=403, detail="Admin access required")

    all_exp = []
    for exp_list in expenses_db.values():
        all_exp.extend(exp_list)
    return all_exp


@router.delete("/delete/{expense_id}", response_model=DeleteResponse)
def delete_expense(expense_id: int, authorization: Optional[str] = Header(None)):
    user  = get_current_user(authorization)
    email = user["sub"]
    role  = user.get("role", "user")

    if role in ("admin", "ADMIN", "ROLE_ADMIN"):
        for key in expenses_db:
            original_len = len(expenses_db[key])
            expenses_db[key] = [e for e in expenses_db[key] if e["id"] != expense_id]
            if len(expenses_db[key]) < original_len:
                return DeleteResponse(message="Expense deleted successfully")
    else:
        user_expenses = expenses_db.get(email, [])
        new_list = [e for e in user_expenses if e["id"] != expense_id]
        if len(new_list) == len(user_expenses):
            raise HTTPException(status_code=404, detail="Expense not found")
        expenses_db[email] = new_list
        return DeleteResponse(message="Expense deleted successfully")

    raise HTTPException(status_code=404, detail="Expense not found")


@router.put("/update/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense: ExpenseRequest,
    authorization: Optional[str] = Header(None),
):
    user  = get_current_user(authorization)
    email = user["sub"]

    user_expenses = expenses_db.get(email, [])
    for i, e in enumerate(user_expenses):
        if e["id"] == expense_id:
            user_expenses[i] = {
                **e,
                "expenseName": expense.expenseName,
                "amount":      expense.amount,
                "category":    expense.category,
                "description": expense.description or "",
                "date":        expense.date or e["date"],
            }
            return ExpenseResponse(
                message="Expense updated successfully",
                data=ExpenseData(**user_expenses[i]),
            )

    raise HTTPException(status_code=404, detail="Expense not found")