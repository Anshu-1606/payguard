# PayGuard: AI fraud guard for small merchants

PayGuard watches PayPal payments, scores each one for fraud risk with a machine learning model,
explains the risk in plain English with an LLM, and lets the merchant approve, hold or refund.

## How it works
1. Payments are created as real PayPal Sandbox orders (PayPal Orders API).
2. A Random Forest model scores each payment (recall [X], precision [X], ROC-AUC [X]).
3. Gemini writes a short explanation and recommends an action.
4. The merchant reviews on a dashboard. Flagged captured payments can be refunded through the PayPal Refund API.

## Tech
Python, FastAPI, scikit-learn, Gemini API, PayPal Sandbox REST API.

## Setup
1. `pip install -r requirements.txt`
2. Create `.env` with PAYPAL_CLIENT_ID, PAYPAL_SECRET, PAYPAL_BASE=https://api-m.sandbox.paypal.com, GEMINI_API_KEY
3. `python generate_data.py` then `python train_model.py`
4. `uvicorn main:app --reload` and open http://127.0.0.1:8000

## Notes
- Training data is **simulated**; real-world performance would differ.
- Payment buyer attributes (account age, etc.) are simulated; the PayPal orders, captures and refunds are real Sandbox calls.
- Built with help from AI tools: Claude (coding assistance), Gemini (runtime explanations).