# FILENAME: app.py
# ACTION: Mollie Webhook listener for Railway deployment
import os
from flask import Flask, request
from mollie.api.client import Client
from supabase import create_client

app = Flask(__name__)

# --- CONFIG ---
# TEACHING: For your first Railway deploy, hardcode these.
# Once it works, we will move them to Railway's 'Variables' tab for security.
MOLLIE_KEY = "test_GQGaRypbVSE5PGQsThJCx68mTbR5gd"
SUPABASE_URL = "https://privljymqcqgykkwrsfd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByaXZsanltcWNxZ3lra3dyc2ZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxOTc3NjgsImV4cCI6MjA4NDc3Mzc2OH0.M_Mv8Zx-bMfjhGnS5Oh3BEOizyVBeXC6rwXrHoNX-xM"

mollie = Client()
mollie.set_api_key(MOLLIE_KEY)
db = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/webhook", methods=["POST"])
def mollie_webhook():
    # 1. Capture the ID from Mollie's POST request
    payment_id = request.form.get("id")
    if not payment_id:
        print("❌ Webhook received without an ID")
        return "Missing ID", 400

    try:
        # 2. Fetch the latest status from Mollie
        payment = mollie.payments.get(payment_id)
        member_id = payment.metadata.get("member_id")

        print(f"🔄 Processing {payment_id} | Member: {member_id} | Status: {payment.status}")

        # 3. If paid, sync to Supabase
        if payment.is_paid():
            # TEACHING: 'upsert' with 'on_conflict' ensures that if Mollie
            # pings us twice, we only have ONE row in the database.
            db.table("orders").upsert(
                {
                    "member_id": member_id,
                    "mollie_id": payment_id,
                    "status": "paid"
                },
                on_conflict="mollie_id"
            ).execute()

            print(f"✅ DB UPDATED: Member {member_id} is marked as PAID.")
            return "OK", 200
        else:
            print(f"⚠️ Payment not paid. Current status: {payment.status}")
            return "Status acknowledged", 200

    except Exception as e:
        print(f"🔥 ERROR in Webhook: {str(e)}")
        return "Internal Error", 500


if __name__ == "__main__":
    # TEACHING: Railway tells the app which port to use via the PORT variable.
    # On your Mac, it will default to 5000.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)