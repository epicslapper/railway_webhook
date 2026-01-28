# FILENAME: app.py
# ACTION: Universal Webhook (Mollie + Local Test)
# TEACHING: If 'member_id' is missing from the request (Mollie's default),
# we pull it from Mollie's metadata. If it's there (your cURL), we use it directly.

import os
from flask import Flask, request
from mollie.api.client import Client
from supabase import create_client

app = Flask(__name__)

# --- CONFIG ---
MOLLIE_KEY = "test_GQGaRypbVSE5PGQsThJCx68mTbR5gd"
SUPABASE_URL = "https://privljymqcqgykkwrsfd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByaXZsanltcWNxZ3lra3dyc2ZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxOTc3NjgsImV4cCI6MjA4NDc3Mzc2OH0.M_Mv8Zx-bMfjhGnS5Oh3BEOizyVBeXC6rwXrHoNX-xM"

mollie = Client()
mollie.set_api_key(MOLLIE_KEY)
db = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/webhook", methods=["POST"])
def webhook():
    # 1. Get the Payment ID (Always sent by Mollie and cURL)
    payment_id = request.form.get("id")

    # 2. Check if member_id was sent directly (your cURL test)
    # If not, we will have to get it from Mollie's metadata later
    m_id = request.form.get("member_id")

    print(f"\n--- ⚡ SIGNAL RECEIVED: {payment_id} ---")

    try:
        # 3. IF MOLLIE TEST: We need to fetch the payment to see if it's paid
        # and to get the member_id from metadata if it wasn't in the request.
        if "REAL_TEST" not in payment_id:
            payment = mollie.payments.get(payment_id)
            if not payment.is_paid():
                print(f"Status is {payment.status}, skipping.")
                return "Not Paid", 200

            # Get member_id from the metadata we set in the Main App
            m_id = payment.metadata.get("member_id")
            print(f"Mollie Metadata found member_id: {m_id}")

        # 4. DATA SNAPSHOT (The part that was failing)
        # We now have the m_id. Let's get the name/email.
        res = db.table("members").select("name, email").eq("relatiecode", m_id).execute()

        if res.data:
            member = res.data[0]
            order_data = {
                "mollie_id": payment_id,
                "member_id": m_id,
                "member_name": member.get('name'),
                "member_email": member.get('email'),
                "amount": 10.00,
                "status": "paid"
            }

            # 5. DB WRITE
            db.table("orders").upsert(order_data, on_conflict="mollie_id").execute()
            print(f"🚀 SUCCESS: Snapshot created for {member.get('name')}")
            return "OK", 200
        else:
            print(f"❌ ERROR: Member {m_id} not found in members table.")
            return "Member Not Found", 404

    except Exception as e:
        print(f"🔥 FATAL ERROR: {e}")
        return str(e), 500


if __name__ == "__main__":
    app.run(port=5000)