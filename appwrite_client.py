from appwrite.client import Client
from appwrite.services.users import Users
from appwrite.services.databases import Databases

# ================= APPWRITE CORE CONFIG =================

APPWRITE_ENDPOINT = ""
PROJECT_ID = ""
API_KEY = ""

DATABASE_ID = ""

# ================= COLLECTION IDS =================

USERS_COLLECTION = ""
WALLETS_COLLECTION = ""
BANK_DETAILS_COLLECTION = ""
INVESTMENTS_COLLECTION = ""
FUND_REQUESTS_COLLECTION = ""
WITHDRAWAL_REQUESTS_COLLECTION = ""

# ================= ADMIN =================

ADMIN_USER_ID = ""

# ================= CLIENT INIT =================

client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(PROJECT_ID)
client.set_key(API_KEY)

# ================= SERVICES =================

users = Users(client)
db = Databases(client))