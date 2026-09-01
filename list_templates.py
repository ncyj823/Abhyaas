"""
Lists content templates already available on your Twilio account.
Trial accounts often can't CREATE new ones, but pre-built ones
(like Appointment Reminders) usually already exist and are usable.

Run: python list_templates.py
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

contents = client.content.v1.contents.list(limit=20)

if not contents:
    print("No content templates found on this account.")
else:
    for c in contents:
        print(f"Name: {c.friendly_name}")
        print(f"  SID: {c.sid}")
        print(f"  Language: {c.language}")
        print(f"  Types: {list(c.types.keys())}")
        print()
