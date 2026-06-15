from pydantic import BaseModel
from typing import Optional, List


# ── REQUEST MODELS ────────────────────────────────────

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "user"

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "secret123",
                "role": "user",
            }
        }


class LoginRequest(BaseModel):
    email: str
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "secret123",
            }
        }


class ExpenseRequest(BaseModel):
    expenseName: str
    amount: float
    category: str
    description: Optional[str] = ""
    date: Optional[str] = ""

    class Config:
        json_schema_extra = {
            "example": {
                "expenseName": "Coffee",
                "amount": 4.50,
                "category": "Food",
                "description": "Morning coffee",
                "date": "2024-06-15",
            }
        }


# ── RESPONSE MODELS ───────────────────────────────────

class AuthResponse(BaseModel):
    message: str
    token: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None


class ExpenseData(BaseModel):
    id: Optional[int] = None
    expenseName: str
    amount: float
    category: str
    description: Optional[str] = ""
    date: Optional[str] = ""
    userEmail: Optional[str] = None
    userName: Optional[str] = None


class ExpenseResponse(BaseModel):
    message: str
    data: Optional[ExpenseData] = None


class DeleteResponse(BaseModel):
    message: str