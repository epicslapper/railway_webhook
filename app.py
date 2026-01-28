# FILENAME: app.py
# ACTION: Full Snapshot Webhook - Fixed Lookup
# TEACHING: We explicitly map 'name' from public.members to 'member_name' in public.orders.

import os
from flask import Flask, request
from supabase import create_client

app = Flask(__name__)

# --- CONFIG ---
SUPABASE_URL = "https://privljymqcqgykkwrsfd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByaXZsanltcWNxZ3lra3dyc2ZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxOTc3NjgsImV4cCI6MjA4NDc3Mzc2OH0.M_Mv8Zx-bMfjhGnS5Oh3BEOizyVBeXC6rwXrHoNX-xM"

db = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/webhook", methods=["POST"])
def webhook():
    # 1. Capture IDs
    m_id = request.form.get("member_id")
    tr_id = request.form.get("id")

    print(f"\n--- ⚡ WEBHOOK SIGNAL: Member {m_id} ---")

    # 2. LOOKUP: Fetch Name/Email from members table using relatiecode
    member_data = db.table("members").select("name", "email").eq("relatiecode", m_id).execute()

    # Initialize variables to avoid NULL errors
    found_name = "Not Found"
    found_email = "Not Found"

    if member_data.data:
        found_name = member_data.data[0].get('name')
        found_email = member_data.data[0].get('email')
        print(f"✅ STEP 1: Found Member '{found_name}'")
    else:
        print(f"❌ STEP 1 FAILED: relatiecode '{m_id}' not found in database.")

    # 3. INSERT: Shove the snapshot into the orders table
    order_row = {
        "mollie_id": tr_id,
        "member_id": m_id,
        "member_name": found_name,  # Mapping 'name' to 'member_name'
        "member_email": found_email,  # Mapping 'email' to 'member_email'
        "amount": 10.00,
        "status": "paid"
    }

    print(f"📝 STEP 2: Writing Row to Orders: {order_row}")

    try:
        res = db.table("orders").insert(order_row).execute()
        print(f"🚀 STEP 3 SUCCESS: Row Created with ID {res.data[0]['id']}")
        return "OK", 200
    except Exception as e:
        print(f"🔥 STEP 3 FAILED: {str(e)}")
        return "Internal Error", 500


if __name__ == "__main__":
    app.run(port=5000)