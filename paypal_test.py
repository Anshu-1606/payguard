import os, requests
from dotenv import load_dotenv

load_dotenv()
BASE = os.getenv("PAYPAL_BASE")
CLIENT = os.getenv("PAYPAL_CLIENT_ID")
SECRET = os.getenv("PAYPAL_SECRET")

def get_token():
    r = requests.post(f"{BASE}/v1/oauth2/token",
                      auth=(CLIENT, SECRET),
                      data={"grant_type": "client_credentials"})
    r.raise_for_status()
    return r.json()["access_token"]

def create_order(token, amount="25.00"):
    r = requests.post(
        f"{BASE}/v2/checkout/orders",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json={"intent": "CAPTURE",
              "purchase_units": [{"amount": {"currency_code": "USD",
                                             "value": amount}}]})
    r.raise_for_status()
    return r.json()

def capture_order(token, order_id):
    r = requests.post(
        f"{BASE}/v2/checkout/orders/{order_id}/capture",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"})
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    token = get_token()
    print("Got token OK")
    order = create_order(token)
    print("Order ID:", order["id"], "| Status:", order["status"])
    for link in order["links"]:
        if link["rel"] in ("approve", "payer-action"):
            print("Open this link and log in as the BUYER:", link["href"])
    input("After approving the payment in the browser, press Enter...")
    result = capture_order(token, order["id"])
    print("Final status:", result["status"])