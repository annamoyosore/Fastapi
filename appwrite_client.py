from appwrite.client import Client
from appwrite.services.users import Users
from appwrite.services.databases import Databases

# ================= APPWRITE CORE CONFIG =================

APPWRITE_ENDPOINT = "https://nyc.cloud.appwrite.io/v1"
PROJECT_ID = "696f9104001dfedc5e1a"
API_KEY = "standard_32f1ce4738058dfa49b22aae1683bc807ed22d9f1afef58f9a2351146458ba7fd1abaf004d268195b4899964b97e07ad2c20d07c3244017b33231d6c582b859471c17816df070036fad1fc4f720cffc56c3d4500179f6f58cb77a82ff78301825d2bc424b70de6246f08d961de6ede899025c865c5ef6e8b94d07a7bd6ce5b76"

DATABASE_ID = "6970722d00269d80304f"

# ================= COLLECTION IDS =================

USERS_COLLECTION = "users_collections"
WALLETS_COLLECTION = "wallets"
BANK_DETAILS_COLLECTION = "bank_details"
INVESTMENTS_COLLECTION = "investment"
FUND_REQUESTS_COLLECTION = "fundrequest"
WITHDRAWAL_REQUESTS_COLLECTION = "withdraw_request"

# ================= ADMIN =================

ADMIN_USER_ID = "6977659e001ca8cb8dd7"

# ================= CLIENT INIT =================

client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(PROJECT_ID)
client.set_key(API_KEY)

# ================= SERVICES =================

users = Users(client)
db = Databases(client))