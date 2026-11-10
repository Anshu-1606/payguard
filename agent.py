import os
from dotenv import load_dotenv

load_dotenv()

NORMAL = {"amount": 60, "orders_last_hour": 1, "account_age_days": 400, "past_orders": 15}


def top_reasons(f):
    """Plain-language red flags, computed from the payment features."""
    r = []
    if f["amount"] > 3 * NORMAL["amount"]:
        r.append(f"order amount ${f['amount']:.2f} is much higher than typical (~${NORMAL['amount']})")
    if f["orders_last_hour"] >= 3:
        r.append(f"{f['orders_last_hour']} orders from this buyer in the last hour")
    if f["account_age_days"] < 30:
        r.append(f"buyer account is only {f['account_age_days']} days old")
    if f["past_orders"] <= 2:
        r.append(f"buyer has only {f['past_orders']} previous order" + ("" if f['past_orders'] == 1 else "s"))
    if f["country_mismatch"]:
        r.append("billing and shipping countries do not match")
    if f["disposable_email"]:
        r.append("buyer uses a disposable email address")
    if f["hour"] in (0, 1, 2, 3, 4, 23):
        r.append(f"order placed at an unusual hour ({f['hour']}:00)")
    return r


def build_prompt(order, reasons):
    return (
        "You are a fraud analyst assistant for a small online shop owner with no "
        "technical background.\n"
        f"A payment has a fraud risk score of {order['score']} (0 to 1, risk level {order['risk']}).\n"
        f"Red flags found: {reasons if reasons else 'none'}.\n"
        "Write 2 short sentences in plain English explaining the risk. Then on a new "
        "line write exactly one of: ACTION: approve, ACTION: review, ACTION: hold. "
        "Do not invent facts beyond the red flags given."
    )


def parse_reply(text):
    """Split the model reply into explanation text and a recommended action."""
    text = text.strip()
    action = "review"
    for line in text.splitlines():
        if line.upper().startswith("ACTION:"):
            value = line.split(":", 1)[1].strip().lower()
            if value in ("approve", "review", "hold"):
                action = value
    body = "\n".join(
        l for l in text.splitlines() if not l.upper().startswith("ACTION:")
    ).strip()
    return body, action


def explain(order):
    reasons = top_reasons(order["features"])
    fallback = (
        "No clear red flags."
        if not reasons
        else "Flagged because: " + "; ".join(reasons[:3]) + "."
    )
    prompt = build_prompt(order, reasons)

    # 1) Gemini (free tier)
    gkey = os.getenv("GEMINI_API_KEY")
    if gkey:
        try:
            from google import genai

            client = genai.Client(api_key=gkey)
            resp = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            body, action = parse_reply(resp.text)
            return {"explanation": body, "recommended_action": action, "source": "gemini"}
        except Exception as e:
            err = f"gemini error: {type(e).__name__}"
    else:
        err = None

    # 2) Claude (only if you add ANTHROPIC_API_KEY)
    akey = os.getenv("ANTHROPIC_API_KEY")
    if akey:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=akey)
            msg = client.messages.create(
                model="claude-haiku-5-5",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            body, action = parse_reply(msg.content[0].text)
            return {"explanation": body, "recommended_action": action, "source": "claude"}
        except Exception as e:
            err = f"claude error: {type(e).__name__}"

    # 3) Free rule-based fallback
    source = f"rules ({err})" if err else "rules"
    return {"explanation": fallback, "recommended_action": "review", "source": source}