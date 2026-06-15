from fastapi import APIRouter, HTTPException
from models.schemas import SignupRequest, LoginRequest, AuthResponse
import jwt
import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])

users_db: dict = {}

SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM  = "HS256"


def create_token(email: str, username: str, role: str) -> str:
    payload = {
        "sub":      email,
        "username": username,
        "role":     role,
        "exp":      datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/signup", response_model=AuthResponse)
def signup(user: SignupRequest):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")

    users_db[user.email] = {
        "username": user.username,
        "password": user.password,
        "role":     user.role or "user",
    }

    token = create_token(user.email, user.username, user.role or "user")
    return AuthResponse(
        message="User signed up successfully",
        token=token,
        username=user.username,
        role=user.role or "user",
    )


@router.post("/login", response_model=AuthResponse)
def login(user: LoginRequest):
    db_user = users_db.get(user.email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if db_user["password"] != user.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user.email, db_user["username"], db_user["role"])
    return AuthResponse(
        message="Login successful",
        token=token,
        username=db_user["username"],
        role=db_user["role"],
    )