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
from .config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER, TWILIO_WHATSAPP
from .audio_to_text import convert_audio_to_text
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
from .vaccine import *
import threading
import time

# create tables (dev convenience)
Base.metadata.create_all(bind=engine)
user_first_message = {}
count = 0
app = FastAPI(title="Health Chatbot Backend")
MEDIA_DIR = "./downloads"
os.makedirs(MEDIA_DIR, exist_ok=True)
user_language_store = {}
user_pending_language_choice = {}
user_state = {} 


def start_vaccine_reminder(interval_seconds=10):
    def run():
        while True:
            try:
                check_and_notify_vaccines()
                logging.info("WORKING THREADING")
            except Exception as e:
                print("Error in vaccine reminder:", e)
            time.sleep(interval_seconds)  # wait before next check
    thread = threading.Thread(target=run, daemon=True)
    thread.start()

start_vaccine_reminder(interval_seconds=10)

LANGUAGES = {
    "1": {"code": "en", "name": "English"},
    "2": {"code": "hi", "name": "हिन्दी"},
    "3": {"code": "ta", "name": "தமிழ்"},
    "4": {"code": "or", "name": "ଓଡ଼ିଆ"},
    "5": {"code": "pa", "name": "ਪੰਜਾਬੀ"},
    "6": {"code": "bn", "name": "বাংলা"},
    "7": {"code": "mr", "name": "मराठी"},
    "8": {"code": "gu", "name": "ગુજરાતી"},
    "9": {"code": "kn", "name": "ಕನ್ನಡ"},
    "10": {"code": "as", "name": "অসমীয়া"}
}

LANGUAGE_PROMPTS = {
    "en": "1 Send 1 to converse in English",
    "hi": "2 भेजें हिन्दी में बात करने के लिए",
    "ta": "3 ஐ அனுப்பவும் தமிழில் பேச",
    "or": "4 ପଠାନ୍ତୁ ଓଡ଼ିଆରେ କଥା ହେବାକୁ",
    "pa": "5 ਭੇਜੋ ਪੰਜਾਬੀ ਵਿੱਚ ਗੱਲ ਕਰਨ ਲਈ",
    "bn": "6 পাঠান বাংলায় কথা বলার জন্য",
    "mr": "7 पाठवा मराठीत बोलण्यासाठी",
    "gu": "8 મોકલો ગુજરાતીમાં વાત કરવા માટે",
    "kn": "9 ಕಳುಹಿಸಿ ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಲು",
    "as": "10 পঠিয়াওক অসমীয়াত কথা বলিবলৈ"
}

def get_language_prompt():
    prompt = "Please choose your language:\n"
    for num, lang_info in LANGUAGES.items():
        lang_name = lang_info["code"]
        prompt += f"{LANGUAGE_PROMPTS.get(lang_name, lang_name)}\n"
    return prompt

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
    ASHA_DASHBOARD_URL = "http://asha_dashboard:5000/alert" 
    
    headers = {"Content-Type": "application/json"}
    
    try:
        r = requests.post(ASHA_DASHBOARD_URL, json=payload, headers=headers, timeout=8.0)
        logging.info(f"ASHA dashboard notify status: {r.status_code}")
        return r.status_code >= 200 and r.status_code < 300
    except Exception as e:
        logging.error(f"ASHA dashboard notify error: {e}")
        return False

@app.post("/sms")
async def sms_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_twilio_signature: str = Header(None)
):
    form = await request.form()
    From = form.get("From")
    Body = form.get("Body", "")
    NumMedia = int(form.get("NumMedia", "0"))

    if not From:
        raise HTTPException(status_code=400, detail="Missing From")

    # Check for WhatsApp prefix
    is_whatsapp = False
    if From.startswith("whatsapp:"):
        is_whatsapp = True
        From = From.replace("whatsapp:", "")

    phone = From
    text = Body
    if phone not in user_language_store:
        if phone not in user_pending_language_choice:
            # First message: send language prompt
            user_pending_language_choice[phone] = True
            prompt = get_language_prompt()
            send_whatsapp(phone, prompt)
            logging.info(f"PROMPT {prompt}")
            return {"status": "ok", "message": "Prompted user for language selection"}

        # Step 2: Expect serial number 1-10
        if text not in LANGUAGES:
            send_whatsapp(phone, "Please send a number between 1 and 10 to select your language.")
            logging.info(f"TEXT {text}")
            return {"status": "ok", "message": "Waiting for valid language choice"}

        # Store chosen language
        chosen_lang_code = LANGUAGES[text]["code"]
        chosen_lang_name = LANGUAGES[text]["name"]
        user_language_store[phone] = chosen_lang_code

        del user_pending_language_choice[phone]
        # Prepare introduction in chosen language
        INTRO_MESSAGES = {
            "en": "🌸 Hello! I'm your health assistant 🤗. I can give wellness tips, home remedies, and guide you to nearby hospitals. Let's chat! 🏥💊",
            "hi": "🌸 नमस्ते! मैं आपका स्वास्थ्य सहायक हूँ 🤗. मैं आपको स्वास्थ्य सुझाव, घरेलू उपाय, और पास के अस्पताल की जानकारी दे सकता हूँ। बात करें! 🏥💊",
            "ta": "🌸 வணக்கம்! நான் உங்கள் ஆரோக்கிய உதவியாளர் 🤗. நான் உங்களுக்கு நலனுக்கான குறிப்புகள், வீட்டுமுறை சிகிச்சைகள், அருகிலுள்ள மருத்துவமனை பற்றிய தகவலை வழங்க முடியும். பேசுங்கள்! 🏥💊",
            "or": "🌸 ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କର ସ୍ୱାସ୍ଥ୍ୟ ସହାୟକ 🤗. ମୁଁ ଆପଣଙ୍କୁ ସ୍ୱାସ୍ଥ୍ୟ ସୁପାରିସ, ଘରୋଇ ଉପଚାର, ନିକଟସ୍ଥ ହସ୍ପିଟାଲ୍ ସମ୍ପର୍କରେ ଜାଣକାରୀ ଦେଇପାରିବି। ଆଲୋଚନା କରନ୍ତୁ! 🏥💊",
            "pa": "🌸 ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ ਸਿਹਤ ਸਹਾਇਕ ਹਾਂ 🤗. ਮੈਂ ਤੁਹਾਨੂੰ ਤੰਦਰੁਸਤੀ ਦੇ ਸੁਝਾਅ, ਘਰੇਲੂ ਉਪਚਾਰ, ਅਤੇ ਨੇੜਲੇ ਹਸਪਤਾਲਾਂ ਬਾਰੇ ਜਾਣਕਾਰੀ ਦੇ ਸਕਦਾ ਹਾਂ। ਗੱਲ ਕਰੋ! 🏥💊",
            "bn": "🌸 হ্যালো! আমি আপনার স্বাস্থ্য সহকারী 🤗. আমি আপনাকে সুস্থতার পরামর্শ, ঘরোয়া প্রতিকার এবং নিকটস্থ হাসপাতাল সম্পর্কে তথ্য দিতে পারি। কথা বলুন! 🏥💊",
            "mr": "🌸 नमस्कार! मी तुमचा आरोग्य सहाय्यक आहे 🤗. मी तुम्हाला आरोग्य सल्ला, घरगुती उपाय, आणि जवळच्या हॉस्पिटल्सची माहिती देऊ शकतो. बोला! 🏥💊",
            "gu": "🌸 નમસ્તે! હું તમારો આરોગ્ય સહાયક છું 🤗. હું તમને વેલનેસ ટિપ્સ, ઘરેલું ઉપચાર, અને નજીકના હસ્પિટલની માહિતી આપી શકું છું. વાત કરો! 🏥💊",
            "kn": "🌸 કಳುહಿಸಿ ಕನ್ನಡમાં વાત કરવા માટે 🏥💊",
            "as": "🌸 নমস্কাৰ! মই আপোনাৰ স্বাস্থ্য সহায়ক 🤗. মই আপোনাক স্বাস্থ্য পৰামৰ্শ, ঘৰমুৱা ব্যৱস্থা, আৰু ওচৰৰ হাস্পতালৰ তথ্য দিব পাৰো। কতা বলক! 🏥💊"
        }
        intro_msg = INTRO_MESSAGES.get(chosen_lang_code, INTRO_MESSAGES["en"])
        logging.info(f"User {phone} chose {chosen_lang_name}")
        logging.info(f"INTRO MESSAGE: {intro_msg}")
        send_whatsapp(phone, intro_msg)
        return {"status": "ok", "message": f"User language set to {chosen_lang_name}", "intro": intro_msg}
        
    logging.info(f"{text} outsideeeeee {'/vacination' in text}")
    if "/vaccine" in text:
        users = load_users()
        logging.info(f"{text} {users} insideeeeeeee")
        if phone not in users:
            user_state[phone] = "awaiting_child_details"
            send_whatsapp(phone, "👩‍👧 Please send child details: ChildName,DOB(YYYY-MM-DD)")
            return {"status": "ok"}
        else:
            send_whatsapp(phone, "Data Already Submitted.")
            return

    if user_state.get(phone) == "awaiting_child_details":
        # Parse child details
        try:
            name, dob = text.split(",")
            logging.info(f"BEFORE REGISTERING {name} {dob}")
            register_child(phone, name.strip(), dob.strip())  # function you define
            user_state[phone] = "default"
            send_whatsapp(phone, f"✅ Registered {name}, DOB {dob}")
        except Exception as e:
            logging.info("ERRRORRRR",e)
        return {"status": "ok"}


    if text.lower().startswith("done"):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            idx = int(parts[1]) - 1
            users = load_users()
            logging.info(f"deoiiiiiiiii {idx},{users}")
            if phone in users:
                for child in users[phone]["children"]:
                    logging.info(f"deoiiiiiiiii {idx},{child}")
                    due_vaccines = get_due_vaccines(phone,child["name"], load_vaccine_schedule())
                    logging.info(f"deeeeee {due_vaccines}")
                    if 0 <= idx < len(due_vaccines):
                        vaccine_name = due_vaccines[idx]["vaccine"]
                        mark_vaccine_done(phone, child["name"], vaccine_name)
                        send_whatsapp(phone, f"✅ Marked {vaccine_name} as completed for {child['name']}")
                        return {"status": "ok"}
        send_whatsapp(phone, "❌ Invalid command. Use: done <number>")
        return {"status": "ok"}


    media_files = []
    if NumMedia > 0:
        for i in range(NumMedia):
            media_url = form.get(f"MediaUrl{i}")
            media_type = form.get(f"MediaContentType{i}")
            ext = media_type.split("/")[-1]  # get file extension
            filename = f"{From}_{i}.{ext}"
            filepath = os.path.join(MEDIA_DIR, filename)
            if media_url:
                r = requests.get(media_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
                if r.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(r.content)
                    print(f"Saved: {filename}")
                else:
                    print(f"Failed to download: {resp.status_code}, {resp.text}")
                media_files.append(filepath)
        # Optional: You can convert audio to text here and update Body
        # Body = convert_audio_to_text(media_files[0])

    background_tasks.add_task(process_inbound_message, From, Body, media_files, is_whatsapp)
    return {"status": "ok", "media_received": len(media_files)}

def process_inbound_message(phone: str, text: str,media_files=None,is_whatsapp=False):
    parsed = {}  
    intent = None
    conf = None
    logging.info(f"Background task triggered for {phone}: {text}")
    if phone.startswith("whatsapp:"):
        is_whatsapp = True
        phone = phone.replace("whatsapp:", "")
    if media_files:
        logging.info(f"Media files received: {media_files}")
        audio_text = convert_audio_to_text(media_files[0])
        logging.info(f"Transcribed audio: {audio_text}")
        text += f"{audio_text}"

    # Get user's preferred language directly
    user_lang = user_language_store.get(phone, "en") 

    try:
        translated = translate_text(text, src=user_lang, dest="en") 
        logging.info(f"{user_lang} {text} {translated} deiiiii")
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
                logging.info(f"PAYLOADDDDDD {payload}")
                notify_asha(payload)
                reply_text = "I will connect you with your local ASHA worker."
                reply_user_lang = translate_text(reply_text, src="en", dest=user_lang)
                if is_whatsapp:
                    send_whatsapp(phone, reply_user_lang)
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
    if is_whatsapp:send_whatsapp(phone, reply_user_lang)
    else:send_sms_direct(phone, reply_user_lang)