from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid, jwt

from appwrite_client import users, db, DATABASE_ID, ADMIN_USER_ID

SECRET_KEY = "CHANGE_THIS_SECRET"
ALGORITHM = "HS256"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- JWT ----------------
def create_token(user_id: str):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(lambda: None)):
    if not token:
        raise HTTPException(401, "Missing token")
    try:
        payload = jwt.decode(token.replace("Bearer ", ""), SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except:
        raise HTTPException(401, "Invalid token")

# ---------------- SCHEMAS ----------------
class Register(BaseModel):
    email: str
    password: str
    referrerId: str | None = None

class Login(BaseModel):
    email: str
    password: str

class Invest(BaseModel):
    plan: str
    amount: float

class AmountOnly(BaseModel):
    amount: float

class BankDetails(BaseModel):
    bankName: str
    accountName: str
    accountNumber: str

# ---------------- AUTH ----------------
@app.post("/register")
def register(data: Register):
    user = users.create(str(uuid.uuid4()), data.email, data.password)

    db.create_document(DATABASE_ID, "wallets", str(uuid.uuid4()), {
        "userId": user["$id"],
        "balance": 0,
        "createdAt": datetime.utcnow().isoformat()
    })

    if data.referrerId:
        db.create_document(DATABASE_ID, "referrals", str(uuid.uuid4()), {
            "referrerId": data.referrerId,
            "referredId": user["$id"],
            "bonus": 1000,
            "status": "pending",
            "createdAt": datetime.utcnow().isoformat()
        })

    return {"message": "Registered"}

@app.post("/login")
def login(data: Login):
    session = users.create_email_password_session(data.email, data.password)
    token = create_token(session["userId"])
    return {"access_token": token, "user_id": session["userId"]}

# ---------------- WALLET ----------------
@app.get("/wallet")
def wallet(user_id=Depends(get_current_user)):
    w = db.list_documents(DATABASE_ID, "wallets", [f"userId={user_id}"])["documents"][0]
    return {"balance": w["balance"]}

# ---------------- INVESTMENTS ----------------
@app.post("/invest")
def invest(data: Invest, user_id=Depends(get_current_user)):
    wallet = db.list_documents(DATABASE_ID, "wallets", [f"userId={user_id}"])["documents"][0]
    if wallet["balance"] < data.amount:
        raise HTTPException(400, "Insufficient balance")

    db.update_document(DATABASE_ID, "wallets", wallet["$id"], {
        "balance": wallet["balance"] - data.amount
    })

    return db.create_document(DATABASE_ID, "investments", str(uuid.uuid4()), {
        "userId": user_id,
        "plan": data.plan,
        "amount": data.amount,
        "status": "active",
        "createdAt": datetime.utcnow().isoformat()
    })

@app.get("/investments")
def investments(user_id=Depends(get_current_user)):
    return db.list_documents(DATABASE_ID, "investments", [f"userId={user_id}"])["documents"]

# ---------------- BANK ----------------
@app.post("/bank-details")
def bank(data: BankDetails, user_id=Depends(get_current_user)):
    existing = db.list_documents(DATABASE_ID, "bank_details", [f"userId={user_id}"])
    payload = {**data.dict(), "userId": user_id}

    if existing["total"]:
        db.update_document(DATABASE_ID, "bank_details", existing["documents"][0]["$id"], payload)
    else:
        db.create_document(DATABASE_ID, "bank_details", str(uuid.uuid4()), payload)

    return {"message": "Bank saved"}

# ---------------- REQUESTS ----------------
@app.post("/request-funds")
def fund(data: AmountOnly, user_id=Depends(get_current_user)):
    return db.create_document(DATABASE_ID, "fund_requests", str(uuid.uuid4()), {
        "userId": user_id,
        "amount": data.amount,
        "status": "pending"
    })

@app.post("/request-withdrawal")
def withdraw(data: AmountOnly, user_id=Depends(get_current_user)):
    return db.create_document(DATABASE_ID, "withdrawal_requests", str(uuid.uuid4()), {
        "userId": user_id,
        "amount": data.amount,
        "status": "pending"
    })

# ---------------- ADMIN ----------------
def verify_admin(user_id: str):
    if user_id != ADMIN_USER_ID:
        raise HTTPException(403, "Admin only")

@app.get("/admin/referrals")
def admin_refs(user_id=Depends(get_current_user)):
    verify_admin(user_id)
    return db.list_documents(DATABASE_ID, "referrals", ["status=pending"])["documents"]

@app.post("/admin/approve-referral/{rid}")
def approve_ref(rid: str, user_id=Depends(get_current_user)):
    verify_admin(user_id)
    r = db.get_document(DATABASE_ID, "referrals", rid)

    w = db.list_documents(DATABASE_ID, "wallets", [f"userId={r['referrerId']}"])["documents"][0]
    db.update_document(DATABASE_ID, "wallets", w["$id"], {
        "balance": w["balance"] + r["bonus"]
    })

    db.update_document(DATABASE_ID, "referrals", rid, {
        "status": "approved",
        "approvedAt": datetime.utcnow().isoformat()
    })

    return {"message": "Approved"}