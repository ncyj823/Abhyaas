"""
Sends WhatsApp messages via Twilio's sandbox.

Day 4: this replaces the placeholder print statements in app/graph.py's
whatsapp_node. Two message types:
- fire_midcall_whatsapp(): sent when classification hits HOT, mid-call
- send_followup_whatsapp(): sent after the call ends, with full context +
  resume + number + architecture diagram (per assignment Section 06)

Note: TWILIO_WHATSAPP_TO is fixed to whoever joined the sandbox (yourself
for testing now, the recruiter's number for the real submission - they
need to send "join twilio-trial" to the sandbox number first).
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

FROM_NUMBER = os.getenv("TWILIO_WHATSAPP_FROM")
TO_NUMBER = os.getenv("TWILIO_WHATSAPP_TO")


def send_whatsapp(body: str) -> str:
    """Low-level send. Returns the Twilio message SID."""
    message = client.messages.create(
        from_=FROM_NUMBER,
        to=TO_NUMBER,
        body=body,
    )
    return message.sid


def fire_midcall_whatsapp(history: list[dict], classification: str, reasoning: str) -> str:
    """
    Called when the lead goes HOT, mid-call. Summarizes what's been
    discussed so far - written like a person would text, not a log dump.
    """
    # Pull just the user's messages for a quick context summary
    user_said = [msg["content"] for msg in history if msg["role"] == "user"]
    context_summary = " / ".join(user_said[-3:])  # last few things they said

    body = (
        f"Hi! Great talking just now - sounds like you're ready to move forward "
        f"on the e-commerce site. Based on what you shared ({context_summary}), "
        f"I'll get a proposal over to you shortly. Talk soon!"
    )
    return send_whatsapp(body)


def send_followup_whatsapp(
    history: list[dict],
    classification: str,
    your_name: str = "Nancy",
    your_number: str = "+91XXXXXXXXXX",
    resume_link: str = "https://github.com/ncyj823",
) -> str:
    """
    Called after the call ends. Must contain (per assignment Section 06):
    1. Real context from the call
    2. Written like a person, not a log
    3. Your mobile number
    4. An image of the architecture (sent as a separate media message)
    """
    user_said = [msg["content"] for msg in history if msg["role"] == "user"]
    context_summary = " / ".join(user_said)

    body = (
        f"Hey, thanks for the call! Just recapping what we discussed: {context_summary}. "
        f"I've noted everything down and will follow up with next steps. "
        f"You can reach me directly at {your_number} anytime. "
        f"Here's a bit about me: {resume_link}"
    )
    return send_whatsapp(body)


def send_architecture_image(image_url: str) -> str:
    """
    Sends the architecture diagram as a media message.
    image_url must be a publicly accessible URL (e.g. hosted on GitHub,
    or a temporary hosting link) - Twilio can't send local files directly.
    """
    message = client.messages.create(
        from_=FROM_NUMBER,
        to=TO_NUMBER,
        media_url=[image_url],
    )
    return message.sid
