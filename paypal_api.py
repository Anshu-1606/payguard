import os, requests
from dotenv import load_dotenv

load_dotenv()
BASE = os.getenv("PAYPAL_BASE")
CLIENT = os.getenv("PAYPAL_CLIENT_ID")
SECRET = os.getenv("PAYPAL_SECRET")


def get_token():
    r = requests.post(f"{BASE}/v1/oauth2/token", auth=(CLIENT, SECRET),
                      data={"grant_type": "client_credentials"})
    r.raise_for_status()
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def create_checkout(token, amount, return_url, cancel_url):
    """Create a real sandbox order that sends the buyer back to our app after paying."""
    body = {
        "intent": "CAPTURE",
        "purchase_units": [{"amount": {"currency_code": "USD", "value": amount}}],
        "payment_source": {"paypal": {"experience_context": {
            "return_url": return_url,
            "cancel_url": cancel_url,
            "user_action": "PAY_NOW",
            "shipping_preference": "NO_SHIPPING"}}},
    }
    r = requests.post(f"{BASE}/v2/checkout/orders", headers=_headers(token), json=body)
    r.raise_for_status()
    data = r.json()
    link = next(l["href"] for l in data["links"] if l["rel"] in ("payer-action", "approve"))
    return data["id"], link


def capture_order(token, order_id):
    r = requests.post(f"{BASE}/v2/checkout/orders/{order_id}/capture", headers=_headers(token))
    r.raise_for_status()
    data = r.json()
    cap = data["purchase_units"][0]["payments"]["captures"][0]
    return {"status": data["status"], "capture_id": cap["id"]}


def refund_capture(token, capture_id):
    r = requests.post(f"{BASE}/v2/payments/captures/{capture_id}/refund",
                      headers=_headers(token), json={})
    r.raise_for_status()
    return r.json()