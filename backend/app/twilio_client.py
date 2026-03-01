import os
from twilio.rest import Client
from .config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER, TWILIO_WHATSAPP
import logging
logging.basicConfig(level=logging.INFO)

def get_twilio():
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise RuntimeError("Set TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN")
    logging.info(f"HELLOOOO {TWILIO_ACCOUNT_SID} {TWILIO_AUTH_TOKEN},{TWILIO_NUMBER}")
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_sms_direct(to_phone: str, body: str):
    from_number = TWILIO_NUMBER
    client = get_twilio()
    logging.info(f"HELLOOOO {to_phone} {from_number} {body}")
    msg = client.messages.create(body=body, from_=from_number, to=to_phone)
    return msg

def send_whatsapp(to_phone: str, body: str):
    from_number = f"whatsapp:{TWILIO_WHATSAPP}"  # Twilio WhatsApp number
    to_number = f"whatsapp:{to_phone}"         # Recipient's WhatsApp number
    client = get_twilio()
    logging.info(f"Sending WhatsApp: {to_number} {from_number} {body}")
    msg = client.messages.create(
        body=body,
        from_=from_number,
        to=to_number
    )
    return msg