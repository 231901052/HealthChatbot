from .celery_app import celery
from .twilio_client import send_sms_direct
from .db import SessionLocal
from .models import Message

@celery.task(bind=True, max_retries=3, default_retry_delay=10)
def send_outbound_sms(self, phone: str, text: str):
    """
    Celery task to send SMS and record DB entry.
    Retries on failure.
    """
    try:
        res = send_sms_direct(phone, text)
        # save outbound message to DB
        db = SessionLocal()
        m = Message(phone=phone, direction="outbound", text=text, intent=None, confidence=None)
        db.add(m)
        db.commit()
        db.close()
        return {"status": "sent", "sid": getattr(res, "sid", None)}
    except Exception as exc:
        try:
            self.retry(exc=exc)
        except Exception:
            raise
