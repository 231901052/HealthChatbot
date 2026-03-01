from fastapi import FastAPI, Request, BackgroundTasks, Header, HTTPException
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from .rasa_client import parse_message_rasa, converse_with_rasa
from .language_utils import detect_lang, translate_text
from .tasks import send_outbound_sms
from .db import SessionLocal, engine
from .models import Base, User, Message, Escalation
from .config import ASHA_ESC_URL, ASHA_API_KEY, TWILIO_AUTH_TOKEN
import os, json, requests
from .twilio_client import send_sms_direct,send_whatsapp
import logging
from .gemini_bro import gemini
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
# create tables (dev convenience)
Base.metadata.create_all(bind=engine)
user_first_message = {}
count = 0
app = FastAPI(title="Health Chatbot Backend")

def save_inbound(phone: str, text: str, intent=None, confidence=None):
    db = SessionLocal()
    m = Message(phone=phone, direction="inbound", text=text, intent=intent, confidence=confidence)
    db.add(m)
    db.commit()
    db.close()

def is_first_message(phone: str) -> bool:
    db = SessionLocal()
    count = db.query(Message).filter(Message.phone == phone).count()
    db.close()
    return count == 0


def save_escalation(phone: str, payload: dict):
    db = SessionLocal()
    esc = Escalation(phone=phone, payload=json.dumps(payload), notified=False)
    db.add(esc)
    db.commit()
    db.close()

def notify_asha(payload: dict):
    if not ASHA_ESC_URL:
        print("ASHA URL not configured, skipping.")
        return False
    headers = {"Content-Type": "application/json"}
    if ASHA_API_KEY:
        headers["X-API-KEY"] = ASHA_API_KEY
    try:
        r = requests.post(ASHA_ESC_URL, json=payload, headers=headers, timeout=8.0)
        print("ASHA notify status:", r.status_code)
        return r.status_code >= 200 and r.status_code < 300
    except Exception as e:
        print("ASHA notify error:", e)
        return False

@app.post("/sms")
async def sms_webhook(request: Request, background_tasks: BackgroundTasks, x_twilio_signature: str = Header(None)):
    # Twilio posts form-encoded data
    form = await request.form()
    From = form.get("From")
    Body = form.get("Body", "")
    if not From:
        raise HTTPException(status_code=400, detail="Missing From")

    background_tasks.add_task(process_inbound_message, From, Body)


def process_inbound_message(phone: str, text: str):
    parsed = {}  
    intent = None
    conf = None
    is_whatsapp=False
    logging.info(f"Background task triggered for {phone}: {text}")
    if phone.startswith("whatsapp:"):
        is_whatsapp = True
        phone = phone.replace("whatsapp:", "")
    try:
        user_lang = detect_lang(text)
        translated = translate_text(text, src=user_lang, dest="en") 
        logging.info(f"{user_lang} {text} deiiiii")
        parsed = parse_message_rasa(translated)
        intent = parsed.get("intent", {}).get("name")
        conf = parsed.get("intent", {}).get("confidence")
    except Exception as e:
        logging.exception("Language detection/translation failed",e)
    
    parsed = parse_message_rasa(translated)
    intent = parsed.get("intent", {}).get("name")
    conf = parsed.get("intent", {}).get("confidence")

    if intent == "emergency" or ("emergency" in (parsed.get("intent", {}).get("name") or "")):
                payload = {"phone": phone, "message": text, "intent": intent}
                save_escalation(phone, payload)
                notify_asha(payload)
                reply_text = "I will connect you with your local ASHA worker."
                reply_user_lang = translate_text(reply_text, src="en", dest=user_lang)
                if is_whatsapp:
                    #send_whatsapp(phone, reply_user_lang)
                    logging.info(f"THE MESSAGE IS {reply_user_lang}")
                else:send_sms_direct(phone, reply_user_lang)

    if not user_first_message.get(phone, False):
        try:
            user_first_message[phone] = True
            save_inbound(phone, text, intent=intent, confidence=str(conf))            
            bot_messages = converse_with_rasa(translated, sender_id=phone)
            # bot_messages is a list of messages { "recipient_id":..., "text": "..." }
            # take first non-empty text; translate back to user language
            if bot_messages:
                bot_text = next((m.get("text") for m in bot_messages if m.get("text")), "Sorry, I don't understand.")
            else:
                bot_text = "Sorry, I don't understand."
            
        except Exception as e:
            print("Rasa converse failed:", e)
            bot_text = "Sorry, I couldn't process that."

    else:
        try:
            logging.info(f"in gemini")
            bot_text = gemini(phone,translated)  # <-- you’ll implement this
        except Exception as e:
            logging.info("Gemini handling failed",e)
            bot_text = "Sorry, I couldn't process that."

    reply_user_lang = translate_text(bot_text, src="en", dest=user_lang)
    logging.info(f"THE MESSAGE IS {reply_user_lang}")
    # enqueue outbound send
    #send_outbound_sms.delay(phonein, reply_user_lang)
    #if is_whatsapp:send_whatsapp(phone, reply_user_lang)
    #else:send_sms_direct(phone, reply_user_lang)