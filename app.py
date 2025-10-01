import os, json, sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, abort
import stripe
from rules_engine import score_rules
from scorer import ml_score

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")           # set later in env
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")  # set later in env

if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY
else:
    print("⚠️  STRIPE_API_KEY not set (ok for now if only testing /health).")

app = Flask(__name__)
DB = "transactions.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stripe_id TEXT,
        event_type TEXT,
        created_at TEXT,
        payload TEXT,
        email TEXT,
        ip TEXT,
        amount INTEGER,
        currency TEXT,
        risk_score REAL,
        reason TEXT
    );
    """)
    conn.commit()
    conn.close()

# Ensure DB exists on import (for gunicorn too)
init_db()

def save_event(stripe_id, event_type, payload, email, ip, amount, currency, risk_score, reason):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    INSERT INTO events (stripe_id, event_type, created_at, payload, email, ip, amount, currency, risk_score, reason)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (stripe_id, event_type, datetime.utcnow().isoformat(), json.dumps(payload), email, ip, amount, currency, risk_score, reason))
    conn.commit()
    conn.close()

@app.route("/", methods=["GET"])
def index():
    return jsonify({"app": "fraud-guard", "status": "running"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    # Verify signature
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        print("❌ Webhook verification failed:", e)
        return abort(400)

    event_type = event["type"]
    data = event["data"]["object"]
    stripe_id = data.get("id")

    # Extract common fields defensively
    email = (
        data.get("receipt_email")
        or (data.get("billing_details") or {}).get("email")
        or data.get("customer_email")
        or None
    )
    ip = data.get("client_ip")  # may be None depending on event type
    amount = data.get("amount") or data.get("amount_received") or 0
    currency = (data.get("currency") or "").upper()

    context = {"email": email, "ip": ip, "amount": amount, "currency": currency, "payload": data}

    rule_score, rule_reason = score_rules(context)

    try:
        ml_prob = ml_score(context)  # 0..1 or None
    except Exception as e:
        print("ML scorer error:", e)
        ml_prob = None

    if ml_prob is not None:
        combined = 0.5 * rule_score + 0.5 * ml_prob
        reason = f"rules:{rule_reason}; ml:{ml_prob:.2f}"
    else:
        combined = rule_score
        reason = f"{rule_reason} (no ML)"

    # Persist audit record
    save_event(stripe_id, event_type, data, email, ip, amount, currency, combined, reason)

    # Action thresholds (demo)
    if combined >= 0.8:
        print(f"[ALERT] HIGH RISK {stripe_id} score={combined:.2f} reason={reason}")
        # e.g., notify Slack, create ticket, optionally stripe.Refund.create(...)
    elif combined >= 0.5:
        print(f"[WARN]  MEDIUM RISK {stripe_id} score={combined:.2f} reason={reason}")
    else:
        print(f"[INFO]  LOW RISK {stripe_id} score={combined:.2f}")

    return jsonify({"received": True})
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
