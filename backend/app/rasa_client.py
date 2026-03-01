import requests
from .config import RASA_URL
import logging
logging.basicConfig(level=logging.INFO)

def parse_message_rasa(text: str, sender_id: str = "default"):
    url = f"{RASA_URL}/model/parse"
    r = requests.post(url, json={"text": text})
    r.raise_for_status()
    return r.json()

def converse_with_rasa(text: str, sender_id: str = "default"):
    url = f"{RASA_URL}/webhooks/rest/webhook"
    r = requests.post(url, json={"sender": sender_id, "message": text})
    r.raise_for_status()
    logging.info(f"DEIIIII {r.json()}")
    return r.json()
