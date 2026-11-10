import joblib, random
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import paypal_api as pp
from paypal_test import create_order          # simulated orders (already working)
from agent import explain

SERVER = "http://127.0.0.1:8000"
app = FastAPI(title="PayGuard")
bundle = joblib.load("fraud_model.joblib")
model, FEATURES = bundle["model"], bundle["features"]
ORDERS = {}


def make_payment(fraud_like: bool):
    if fraud_like:
        return {"amount": round(random.lognormvariate(5.0, 0.8), 2),
                "hour": random.choice([0, 1, 2, 3, 4, 23]),
                "account_age_days": random.randint(0, 20),
                "orders_last_hour": random.randint(1, 7),
                "country_mismatch": int(random.random() < 0.75),
                "past_orders": random.randint(0, 2),
                "disposable_email": int(random.random() < 0.55)}
    return {"amount": round(random.lognormvariate(3.6, 0.7), 2),
            "hour": random.randint(7, 22),
            "account_age_days": random.randint(10, 1500),
            "orders_last_hour": random.randint(0, 2),
            "country_mismatch": int(random.random() < 0.06),
            "past_orders": random.randint(0, 39),
            "disposable_email": int(random.random() < 0.03)}


def risk_level(score):
    return "HIGH" if score >= 0.5 else "MEDIUM" if score >= 0.2 else "LOW"


def score_features(f):
    return float(model.predict_proba(pd.DataFrame([f])[FEATURES])[0][1])


@app.get("/", include_in_schema=False)
def home():
    return FileResponse("static/index.html")


@app.post("/api/simulate")
def simulate(n: int = 8):
    token = pp.get_token()
    created = []
    for _ in range(n):
        f = make_payment(random.random() < 0.35)
        order = create_order(token, f"{max(f['amount'], 1):.2f}")
        score = score_features(f)
        ORDERS[order["id"]] = {
            "order_id": order["id"], "features": f, "score": round(score, 3),
            "risk": risk_level(score), "live": False, "capture_id": None, "refunded": False,
            "status": "HELD" if score >= 0.5 else "REVIEW" if score >= 0.2 else "APPROVED"}
        created.append(ORDERS[order["id"]])
    return created


@app.post("/api/checkout")
def checkout(amount: float = 49.99, profile: str = "normal"):
    """Create a LIVE sandbox checkout. The buyer pays on PayPal, then returns to /paypal/return."""
    f = make_payment(profile == "suspicious")
    f["amount"] = round(amount, 2)
    token = pp.get_token()
    order_id, url = pp.create_checkout(token, f"{amount:.2f}",
                                       f"{SERVER}/paypal/return", f"{SERVER}/paypal/cancel")
    score = score_features(f)
    ORDERS[order_id] = {"order_id": order_id, "features": f, "score": round(score, 3),
                        "risk": risk_level(score), "live": True, "capture_id": None,
                        "refunded": False, "status": "AWAITING PAYMENT"}
    return {"order_id": order_id, "approve_url": url}


@app.get("/paypal/return", include_in_schema=False)
def paypal_return(token: str):
    """PayPal sends the buyer here after approval. We capture the money."""
    o = ORDERS.get(token)
    if o:
        result = pp.capture_order(pp.get_token(), token)
        o["capture_id"] = result["capture_id"]
        o["status"] = "PAID" if o["risk"] == "LOW" else "PAID - FLAGGED"
    return RedirectResponse("/")


@app.get("/paypal/cancel", include_in_schema=False)
def paypal_cancel():
    return RedirectResponse("/")


@app.post("/api/orders/{order_id}/refund")
def refund(order_id: str):
    o = ORDERS.get(order_id)
    if not o or not o.get("capture_id"):
        raise HTTPException(400, "Order has no captured payment to refund")
    pp.refund_capture(pp.get_token(), o["capture_id"])
    o["refunded"] = True
    o["status"] = "REFUNDED"
    return o


@app.get("/api/orders")
def list_orders():
    return sorted(ORDERS.values(), key=lambda o: -o["score"])


@app.delete("/api/orders")
def clear_orders():
    ORDERS.clear()
    return {"cleared": True}


@app.post("/api/orders/{order_id}/decision")
def decide(order_id: str, action: str):
    if order_id not in ORDERS:
        raise HTTPException(404, "Unknown order")
    if action not in ("approve", "hold"):
        raise HTTPException(400, "action must be approve or hold")
    ORDERS[order_id]["status"] = "APPROVED" if action == "approve" else "HELD"
    return ORDERS[order_id]


@app.get("/api/orders/{order_id}/explain")
def explain_order(order_id: str):
    if order_id not in ORDERS:
        raise HTTPException(404, "Unknown order")
    result = explain(ORDERS[order_id])
    ORDERS[order_id]["explanation"] = result
    return result