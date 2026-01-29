# FILENAME: app.py
# ACTION: Universal Webhook for Railway & Local Testing

from flask import Flask, request, jsonify
from mollie.api.client import Client
from supabase import create_client
import os

app = Flask(__name__)

# --- 1. CONFIGURATION (Cloud-Aware) ---
# Logic: Checks Railway Variables first. If missing, uses the local string.
MOLLIE_KEY = os.getenv("MOLLIE_KEY", "test_GQGaRypbVSE5PGQsThJCx68mTbR5gd")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://privljymqcqgykkwrsfd.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByaXZsanltcWNxZ3lra3dyc2ZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxOTc3NjgsImV4cCI6MjA4NDc3Mzc2OH0.M_Mv8Zx-bMfjhGnS5Oh3BEOizyVBeXC6rwXrHoNX-xM")

# Initialize Mollie & Supabase
mollie_client = Client()
mollie_client.set_api_key(MOLLIE_KEY)
db = create_client(SUPABASE_URL, SUPABASE_KEY)

# Version Tracking (Crucial for Ghost-Busting!)
VERSION = "v1.5 - 2026-01-29 - Env Var Integration"

# --- 2. THE PULSE (Health Check) ---
@app.route("/", methods=["GET"])
def index():
    # Tells your Dev Dashboard if this server is alive and which version it's running
    return jsonify({
        "status": "online",
        "version": VERSION,
        "environment": "Railway/Production" if os.environ.get("PORT") else "Local/Development"
    })

# --- 3. THE VERIFIED WEBHOOK ---
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # 1. Capture the ID sent by Mollie
        payment_id = request.form.get("id")
        if not payment_id:
            print("⚠️ WEBHOOK WARNING: Received request without ID")
            return "Missing ID", 400

        print(f"⚡ SIGNAL RECEIVED: {payment_id}")

        # 2. Ask Mollie for the 'Official Truth' (Security check)
        payment = mollie_client.payments.get(payment_id)
        new_status = payment.status # e.g., 'paid', 'expired', 'canceled'

        # 3. Update Supabase based on the verified status
        # Note: Per your instruction [2026-01-25], we don't handle 'pending'
        db.table("verkoop") \
            .update({"betaal_status": new_status}) \
            .eq("transactie_id", payment_id) \
            .execute()

        print(f"✅ DATABASE UPDATED: {payment_id} is now {new_status}")
        return "OK", 200

    except Exception as e:
        print(f"❌ WEBHOOK SYSTEM ERROR: {e}")
        return str(e), 500

# --- 4. THE ENGINE START ---
if __name__ == "__main__":
    # Railway assigns a dynamic port; locally we use 5000
    port = int(os.environ.get("PORT", 5000))
    # host='0.0.0.0' is mandatory for Railway to accept external traffic
    app.run(host="0.0.0.0", port=port)