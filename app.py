# FILENAME: app.py
# ACTION: Cloud-Proofed Webhook with Verification Logic

from flask import Flask, request, jsonify
from mollie.api.client import Client
from supabase import create_client
import os

app = Flask(__name__)

# --- 1. CONFIGURATION (The "Cloud Armor" way) ---
# It tries to find the key in Railway Variables first; falls back to your string.
MOLLIE_KEY = os.getenv("MOLLIE_KEY", "test_GQGaRypbVSE5PGQsThJCx68mTbR5gd")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://privljymqcqgykkwrsfd.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

mollie_client = Client()
mollie_client.set_api_key(MOLLIE_KEY)
db = create_client(SUPABASE_URL, SUPABASE_KEY)

# Incrementing the version so your Dashboard sees the change!
VERSION = "v1.4 - 2026-01-29 - Verified Webhook"

# --- 2. HEALTH CHECK ---
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "online",
        "version": VERSION,
        "environment": "Railway" if os.environ.get("PORT") else "Local"
    })

# --- 3. THE VERIFIED WEBHOOK ---
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        payment_id = request.form.get("id")
        if not payment_id:
            return "Missing ID", 400

        print(f"⚡ SIGNAL RECEIVED: {payment_id}")

        # 🚩 STEP: Ask Mollie for the real status (Security check)
        payment = mollie_client.payments.get(payment_id)
        new_status = payment.status # 'paid', 'expired', etc.

        # 🚩 STEP: Update Supabase
        db.table("verkoop") \
            .update({"betaal_status": new_status}) \
            .eq("transactie_id", payment_id) \
            .execute()

        print(f"✅ DATABASE UPDATED: {payment_id} is now {new_status}")
        return "OK", 200

    except Exception as e:
        print(f"❌ WEBHOOK ERROR: {e}")
        return str(e), 500

# --- 4. THE PORT BINDER ---
if __name__ == "__main__":
    # This must remain exactly like this for Railway to work!
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)