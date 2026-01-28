from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from appwrite_client import users, db, DATABASE_ID, ADMIN_USER_ID
import uuid
from datetime import datetime, timedelta

app = FastAPI()

# ---------------- SCHEMAS ----------------
class Register(BaseModel):
    email: str
    password: str

class Login(BaseModel):
    email: str
    password: str

class Invest(BaseModel):
    userId: str
    plan: str
    amount: float

class FundRequest(BaseModel):
    userId: str
    amount: float

class WithdrawalRequest(BaseModel):
    userId: str
    amount: float

class BankDetails(BaseModel):
    userId: str
    bankName: str
    accountName: str
    accountNumber: str

# ---------------- INVESTMENT PLANS ----------------
INVESTMENT_PLANS = {
    "Crypto": {"roi": 12, "duration": 30},
    "Real Estate": {"roi": 8, "duration": 60},
    "Forex": {"roi": 10, "duration": 30},
    "Agriculture": {"roi": 7, "duration": 45},
    "Technology": {"roi": 15, "duration": 30},
    "Gold": {"roi": 6, "duration": 60},
}

# ---------------- ADMIN VERIFY ----------------
def verify_admin(userId: str):
    if userId != ADMIN_USER_ID:
        raise HTTPException(status_code=403, detail="Access forbidden: Admin only")
    return True

# ---------------- USER AUTH ----------------
@app.post("/register")
def register(data: Register):
    try:
        user = users.create(
            user_id=str(uuid.uuid4()),
            email=data.email,
            password=data.password
        )
        db.create_document(
            DATABASE_ID,
            "users",
            str(uuid.uuid4()),
            {
                "userId": user["$id"],
                "email": data.email,
                "balance": 0,
                "createdAt": datetime.utcnow().isoformat()
            }
        )
        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
def login(data: Login):
    try:
        session = users.create_email_password_session(
            email=data.email,
            password=data.password
        )
        user_id = session["userId"]

        wallets = db.list_documents(
            DATABASE_ID,
            "wallets",
            queries=[f"userId={user_id}"]
        )

        if wallets["total"] == 0:
            db.create_document(
                DATABASE_ID,
                "wallets",
                str(uuid.uuid4()),
                {
                    "userId": user_id,
                    "balance": 0,
                    "createdAt": datetime.utcnow().isoformat()
                }
            )
        return {"userId": user_id}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# ---------------- BANK DETAILS ----------------
@app.post("/bank-details")
def save_bank_details(data: BankDetails):
    existing = db.list_documents(
        DATABASE_ID,
        "bank_details",
        queries=[f"userId={data.userId}"]
    )

    payload = {
        "userId": data.userId,
        "bankName": data.bankName,
        "accountName": data.accountName,
        "accountNumber": data.accountNumber,
        "updatedAt": datetime.utcnow().isoformat()
    }

    if existing["total"] > 0:
        db.update_document(
            DATABASE_ID,
            "bank_details",
            existing["documents"][0]["$id"],
            payload
        )
    else:
        payload["createdAt"] = datetime.utcnow().isoformat()
        db.create_document(
            DATABASE_ID,
            "bank_details",
            str(uuid.uuid4()),
            payload
        )

    return {"message": "Bank details saved"}

# ---------------- INVEST ----------------
@app.post("/invest")
def invest(data: Invest):
    if data.plan not in INVESTMENT_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    wallet = db.list_documents(
        DATABASE_ID,
        "wallets",
        queries=[f"userId={data.userId}"]
    )["documents"][0]

    if wallet["balance"] < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    db.update_document(
        DATABASE_ID,
        "wallets",
        wallet["$id"],
        {"balance": wallet["balance"] - data.amount}
    )

    plan_info = INVESTMENT_PLANS[data.plan]
    expected_return = round(
        data.amount * (1 + plan_info["roi"] / 100), 2
    )

    return db.create_document(
        DATABASE_ID,
        "investments",
        str(uuid.uuid4()),
        {
            "userId": data.userId,
            "plan": data.plan,
            "amount": data.amount,
            "expected_return": expected_return,
            "roi_percent": plan_info["roi"],
            "duration_days": plan_info["duration"],
            "status": "active",
            "createdAt": datetime.utcnow().isoformat()
        }
    )

@app.get("/investments")
def get_investments(userId: str):
    return db.list_documents(
        DATABASE_ID,
        "investments",
        queries=[f"userId={userId}"]
    )["documents"]

# ---------------- WALLET ----------------
@app.get("/wallet/{userId}")
def wallet(userId: str):
    wallet = db.list_documents(
        DATABASE_ID,
        "wallets",
        queries=[f"userId={userId}"]
    )["documents"][0]
    return {"balance": wallet["balance"]}

# ---------------- FUND REQUEST ----------------
@app.post("/request-funds")
def request_funds(data: FundRequest):
    return db.create_document(
        DATABASE_ID,
        "fund_requests",
        str(uuid.uuid4()),
        {
            "userId": data.userId,
            "amount": data.amount,
            "status": "pending",
            "createdAt": datetime.utcnow().isoformat()
        }
    )

# ---------------- WITHDRAWAL REQUEST (BANK AWARE) ----------------
@app.post("/request-withdrawal")
def request_withdrawal(data: WithdrawalRequest):
    bank = db.list_documents(
        DATABASE_ID,
        "bank_details",
        queries=[f"userId={data.userId}"]
    )

    if bank["total"] == 0:
        raise HTTPException(
            status_code=400,
            detail="Add bank details before withdrawing"
        )

    b = bank["documents"][0]

    return db.create_document(
        DATABASE_ID,
        "withdrawal_requests",
        str(uuid.uuid4()),
        {
            "userId": data.userId,
            "amount": data.amount,
            "status": "pending",
            "bankName": b["bankName"],
            "accountName": b["accountName"],
            "accountNumber": b["accountNumber"],
            "createdAt": datetime.utcnow().isoformat()
        }
    )

# ---------------- ADMIN ENDPOINTS ----------------
@app.get("/admin/fund-requests")
def admin_fund_requests(userId: str, verified: bool = Depends(verify_admin)):
    return db.list_documents(
        DATABASE_ID,
        "fund_requests",
        queries=["status=pending"]
    )["documents"]

@app.get("/admin/withdrawal-requests")
def admin_withdrawal_requests(userId: str, verified: bool = Depends(verify_admin)):
    return db.list_documents(
        DATABASE_ID,
        "withdrawal_requests",
        queries=["status=pending"]
    )["documents"]

@app.post("/admin/approve-withdrawal/{request_id}")
def approve_withdrawal(
    request_id: str,
    userId: str,