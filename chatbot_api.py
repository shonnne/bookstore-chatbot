from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import urllib.request
import json
import ssl

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    token: str | None = None
    username: str | None = None

def fetch_json(url, token=None):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url)
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, context=ctx) as res:
            return json.loads(res.read().decode("utf-8"))
    except:
        return None

@app.post("/chat")
def chat(request: ChatRequest):
    # Fetch books (public endpoint)
    books = fetch_json("https://localhost:7251/api/books")

    # Fetch user data if logged in
    user_info = loans = purchases = wallet = None
    if request.username and request.token:
        user_info  = fetch_json(f"https://localhost:7251/api/customers/{request.username}", request.token)
        loans      = fetch_json(f"https://localhost:7251/api/customers/{request.username}/loans", request.token)
        purchases  = fetch_json(f"https://localhost:7251/api/customers/{request.username}/purchases", request.token)
        wallet     = fetch_json(f"https://localhost:7251/api/wallet/{request.username}", request.token)

   # Build context
    context = """You are a helpful assistant for an online bookstore called BookStore.
You help customers with questions about books, loans, purchases, and their account.
Keep answers short and friendly.

HOW THE STORE WORKS:
- Customers can browse and search all available books
- Each book can be borrowed (loan) or purchased outright

HOW LOANS WORK:
- Customers can borrow a book for a limited period
- Each loan has a due date by which the book must be returned
- If a book is not returned by the due date it becomes overdue
- Overdue loans may result in the customer being blocked from borrowing more books
- To return a book go to My Loans and click Return

HOW PURCHASES WORK:
- Customers can buy books outright using their wallet balance
- Purchased books are permanently owned and visible in My Purchases
- There are no refunds on purchases

HOW THE WALLET WORKS:
- The wallet holds your balance which is used to buy books
- To add funds go to My Wallet and submit a top-up request
- An admin must approve the request before funds appear in your balance
- You cannot purchase books if your balance is insufficient

ACCOUNT & BLOCKING:
- Accounts can be blocked by an admin due to overdue loans
- Blocked accounts cannot borrow new books
- Contact support if you believe your account was blocked unfairly

GENERAL:
- For any issues not covered here please contact the store admin\n\n"""

    if books:
        context += f"AVAILABLE BOOKS: {json.dumps(books)}\n\n"
    if user_info:
        context += f"CUSTOMER INFO: {json.dumps(user_info)}\n\n"
    if loans:
        context += f"CUSTOMER LOANS: {json.dumps(loans)}\n\n"
    if purchases:
        context += f"CUSTOMER PURCHASES: {json.dumps(purchases)}\n\n"
    if wallet:
        context += f"CUSTOMER WALLET: {json.dumps(wallet)}\n\n"
    # Send to Ollama
    data = json.dumps({
        "model": "llama3.2",
        "prompt": f"{context}Customer question: {request.message}",
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))
        return {"reply": result["response"]}