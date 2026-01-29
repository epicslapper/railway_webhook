# FILENAME: app.py
# ACTION: Hardcoded Recovery (No Railway Variables Needed)

from flask import Flask, request, jsonify
from mollie.api.client import Client
from supabase import create_client
import os

app = Flask(__name__)

# --- 1. CONFIGURATION (HARDCODED RECOVERY) ---
# We are putting the keys back inside the file to stop the "NoneType" crashes.
MOLLIE_KEY = "test_GQGaRypbVSE5PGQsThJCx68mTbR5gd"
SUPABASE_URL = "https://privljymqcqgykkwrsfd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByaXZsanltcWNxZ3lra3dyc2ZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxOTc3NjgsImV4cCI6MjA4NDc3Mzc2OH0.M_Mv8Zx-bMfjhGnS5Oh3BEOizyVBeXC6rwXrHoNX-xM"

# Initialize clients immediately with hardcoded strings
mollie_client = Client()
mollie_client.set_api_key(MOLLIE_KEY)
db = create_client(SUPABASE_URL, SUPABASE_KEY)

VERSION = "v1.6 - EMERGENCY HARDCODE RECOVERY"

# --- 2. HEALTH CHECK ---
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "online",
        "version": VERSION,
        "note": "Back to basics. No cloud variables used."
    })

# --- 3. THE WEBHOOK ---
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        payment_id = request.form.get("id")
        if not payment_id:
            return "Missing ID", 400

        print(f"⚡ SIGNAL RECEIVED: {payment_id}")

        # Retrieve status from Mollie
        payment = mollie_client.payments.get(payment_id)
        new_status = payment.status

        # Update Supabase
        db.table("verkoop") \
            .update({"betaal_status": new_status}) \
            .eq("transactie_id", payment_id) \
            .execute()

        print(f"✅ DATABASE UPDATED: {payment_id} is now {new_status}")
        return "OK", 200

    except Exception as e:
        print(f"❌ WEBHOOK ERROR: {e}")
        return str(e), 500

# --- 4. PORT BINDER ---
if __name__ == "__main__":
    # We keep this for Railway's sake, but it will work locally too.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)