from flask import Flask, request
from supabase import create_client
from mollie.api.client import Client
import os
import time
from datetime import datetime

# ────────────────────────────────────────────────────────────────
# VERSION / RESTART INDICATOR – change version number every edit 1
# ────────────────────────────────────────────────────────────────
VERSION = "2026-02-01 v1.10"  # ← CHANGE THIS EVERY TIME YOU EDIT THE FILE
print("\n" + "═"*70)
print(f"FLASK WEBHOOK STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}   VERSION: {VERSION}")
print("If version/date is old → you forgot to restart Flask!")
print("═"*70 + "\n")

app = Flask(__name__)

# ────────────────────────────────────────────────────────────────
# KEYS – prefer Railway env vars, fallback for local dev only
# ────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
MOLLIE_KEY = os.getenv("MOLLIE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, MOLLIE_KEY]):
    print("⚠️ Missing SUPABASE_URL / SUPABASE_KEY / MOLLIE_KEY in environment → using baked-in local defaults.")
    print("   Set env vars in Railway to avoid this fallback.")
    SUPABASE_URL = SUPABASE_URL or "https://privljymqcqgykkwrsfd.supabase.co"
    SUPABASE_KEY = SUPABASE_KEY or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByaXZsanltcWNxZ3lra3dyc2ZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxOTc3NjgsImV4cCI6MjA4NDc3Mzc2OH0.M_Mv8Zx-bMfjhGnS5Oh3BEOizyVBeXC6rwXrHoNX-xM"
    MOLLIE_KEY = MOLLIE_KEY or "test_GQGaRypbVSE5PGQsThJCx68mTbR5gd"

db = create_client(SUPABASE_URL, SUPABASE_KEY)
mollie = Client()
mollie.set_api_key(MOLLIE_KEY)

# ────────────────────────────────────────────────────────────────
# ROUTES – MUST COME AFTER app = Flask(...)
# ────────────────────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def mollie_webhook():
    print("\n" + "═"*70)
    print("WEBHOOK HIT", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("═"*70)

    try:
        # Accept both JSON and form-encoded bodies from Mollie
        content_type = request.headers.get("Content-Type")
        print(f"Content-Type: {content_type}")

        data = request.get_json(silent=True) or {}
        if not data:
            data = request.form.to_dict() or {}

        if not data and request.data:
            print(f"Raw body fallback: {request.data}")

        print(f"Received: {data}")
        
        id = data.get("id") or request.form.get("id")
        if not id:
            print("❌ Missing Mollie ID in webhook data")
            return "Missing Mollie id", 400
        
        print(f"Payment ID: {id}")


        # Get the payment status from Mollie using the transaction id
        payment = mollie.payments.get(id)
        status = getattr(payment, "status", None)

        print(f"✅ Payment status: {status}")
        
        # If status is open or pending, no action needed
        if status in ("open", "pending"):
            print("Payment status is open or pending — no action needed.")
            return "No action needed", 200
    

        # Get metadata from the Mollie payment
        metadata = getattr(payment, "metadata", {}) or {}
        bestelnummer = metadata.get("bestelnummer")
        relatiecode = metadata.get("relatiecode")   
        
        print(f"Metadata retrieved: bestelnummer={bestelnummer}, relatiecode={relatiecode}")    
    
        # Find the corresponding row in verkoop table
        if not bestelnummer:
            print("⚠️ No bestelnummer in metadata")
            return "OK", 200
        
        res = db.table("verkoop").select("*").eq("bestelnummer", bestelnummer).execute()
        row = res.data[0] if res.data else None

        # Update the row: ensure real Mollie id is stored (do NOT touch bestelnummer), then mark paid when appropriate
        if row:
            print(f"Found row: {row['id']}")

            # Replace dummy id with the real Mollie id if different
            if row.get("id") != id:
                try:
                    db.table("verkoop").update({"id": id}).eq("bestelnummer", bestelnummer).execute()
                    print(f"✅ Updated verkoop.id to Mollie id {id}")
                except Exception as update_err:
                    print(f"⚠️ Could not update verkoop.id: {update_err}")

            if status == "paid":
                db.table("verkoop").update({"status": "paid"}).eq("bestelnummer", bestelnummer).execute()
                print("✅ Updated status to paid")
            else:
                print(f"Payment status is {status} — no status update performed.")
        else:
            print("⚠️ No matching row found in verkoop table")  

        print("Returning 200")
        return "OK", 200
        
    except Exception as e:
        print(f"Webhook error: {e}")
        print("Returning 204")
        return "", 204        


@app.route("/")
def home():
    return "Webhook running locally"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)