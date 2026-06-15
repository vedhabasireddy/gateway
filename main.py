from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models.schemas import SignupRequest, LoginRequest, ExpenseRequest
import httpx
import base64

app = FastAPI(title="Expense Tracker Gateway", version="2.0.0")

# Root endpoint
@app.get("/", tags=["Health"])
async def home():
    return {
        "status": "success",
        "message": "Expense Tracker Gateway Running"
    }

SPRING_BOOT_URL = "https://task2-o3f0.onrender.com"
NODE_URL = "https://expense-tracking-gzr0.onrender.com/expenses"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def decode_token(token: str) -> tuple:
    try:
        raw = token.replace("Bearer ", "").strip()
        decoded = base64.b64decode(raw).decode("utf-8")
        parts = decoded.split("|", 1)
        email = parts[0] if len(parts) > 0 else ""
        roles = parts[1] if len(parts) > 1 else ""
        return email, roles
    except Exception:
        return "", ""

def has_token(request: Request) -> bool:
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return False
    email, _ = decode_token(auth)
    return bool(email)

def is_admin(request: Request) -> bool:
    auth = request.headers.get("authorization", "")
    _, roles = decode_token(auth)
    return "ROLE_ADMIN" in roles

async def proxy(request: Request, path: str):
    url = f"{SPRING_BOOT_URL}/{path}"
    body = await request.body()

    headers = {}

    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]

    if "content-type" in request.headers:
        headers["Content-Type"] = request.headers["content-type"]

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                content=body,
                headers=headers,
                params=dict(request.query_params),
            )

            try:
                return JSONResponse(
                    content=resp.json(),
                    status_code=resp.status_code
                )
            except Exception:
                return JSONResponse(
                    content={"message": resp.text},
                    status_code=resp.status_code
                )

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Spring Boot unavailable"
            )

# Authentication

@app.post("/auth/signup", tags=["Authentication"])
async def signup(payload: SignupRequest, request: Request):
    return await proxy(request, "auth/signup")

@app.post("/auth/login", tags=["Authentication"])
async def login(payload: LoginRequest, request: Request):
    return await proxy(request, "auth/login")

# Expenses

@app.post("/expenses/add", tags=["Expenses"])
async def add_expense(payload: ExpenseRequest, request: Request):
    if not has_token(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await proxy(request, "expenses/add")

@app.get("/expenses/my", tags=["Expenses"])
async def get_my_expenses(request: Request):
    if not has_token(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await proxy(request, "expenses/my")

@app.get("/expenses/all", tags=["Expenses"])
async def get_all_expenses(request: Request):
    if not has_token(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await proxy(request, "expenses/all")

@app.delete("/expenses/delete/{id}", tags=["Expenses"])
async def delete_expense(id: int, request: Request):
    if not has_token(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await proxy(request, f"expenses/delete/{id}")

# Dashboard

@app.get("/dashboard/total", tags=["Dashboard"])
async def total_expense(request: Request):
    if not has_token(request):
        raise HTTPException(status_code=401, detail="Not authenticated")

    auth_header = request.headers.get("authorization", "")
    endpoint = "expenses/all" if is_admin(request) else "expenses/my"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(
                f"{SPRING_BOOT_URL}/{endpoint}",
                headers={"Authorization": auth_header}
            )

            data = r.json()
            total = sum(
                e.get("amount", 0)
                for e in data
            ) if isinstance(data, list) else 0

            return {"total_expense": total}

        except Exception:
            return {"total_expense": 0}

@app.get("/dashboard/category", tags=["Dashboard"])
async def category_expense(request: Request):
    if not has_token(request):
        raise HTTPException(status_code=401, detail="Not authenticated")

    auth_header = request.headers.get("authorization", "")
    endpoint = "expenses/all" if is_admin(request) else "expenses/my"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(
                f"{SPRING_BOOT_URL}/{endpoint}",
                headers={"Authorization": auth_header}
            )

            data = r.json()
            cats = {}

            if isinstance(data, list):
                for exp in data:
                    cat = exp.get("category", "Other")
                    cats[cat] = cats.get(cat, 0) + exp.get("amount", 0)

            return cats

        except Exception:
            return {}

# Profile / Admin

@app.get("/profile", tags=["Profile"])
async def get_profile(request: Request):
    if not has_token(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await proxy(request, "profile")

@app.get("/profile/all", tags=["Admin"])
async def get_all_users(request: Request):
    if not has_token(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await proxy(request, "profile/all")

@app.delete("/profile/{user_id}", tags=["Admin"])
async def delete_user(user_id: int, request: Request):
    if not has_token(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await proxy(request, f"profile/{user_id}")