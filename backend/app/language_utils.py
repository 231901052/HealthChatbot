from langdetect import detect, DetectorFactory
from googletrans import Translator


DetectorFactory.seed = 0
translator = Translator()

def detect_lang(text: str) -> str:
    try:
        if len(text.strip().split()) < 3:  # treat very short texts as English
            return "en"
        return detect(text)
    except:
        return "en"

def translate_text(text: str, src: str, dest: str) -> str:
    try:
        if src == dest:
            return text
        return translator.translate(text, dest=dest).text
    except Exception:
        return text
