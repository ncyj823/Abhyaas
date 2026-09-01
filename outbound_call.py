"""
Places the actual outbound call. Run this AFTER telephony_server.py
is running and ngrok is exposing it publicly.

Run: python outbound_call.py
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

NGROK_HOST = os.getenv("NGROK_HOST", "your-ngrok-url.ngrok-free.app")
FROM_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # your bought Twilio number
TO_NUMBER = os.getenv("CALL_TO_NUMBER")  # who to call - your own number for testing

call = client.calls.create(
    to=TO_NUMBER,
    from_=FROM_NUMBER,
    url=f"https://{NGROK_HOST}/voice",
)

print(f"Call initiated! SID: {call.sid}")
print("Answer your phone now.")
