import os
import time
import cv2
import requests
from dotenv import load_dotenv

load_dotenv()  # .env la irundhu TELEGRAM_TOKEN, TELEGRAM_CHAT_ID edukkum

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
COOLDOWN_SECONDS = 15        # High/Critical-ku idhukkoru thadava mattum alert
ALERT_LEVELS = {"High", "Critical"}

_last_alert_time = 0.0       # module-level, so app oda endha part call pannalum same cooldown


def configured():
    """Token/Chat ID .env la irukka nu check pannum, UI la kaattradhukku."""
    return bool(TOKEN) and bool(CHAT_ID)


def _cooldown_ok():
    return (time.time() - _last_alert_time) >= COOLDOWN_SECONDS


def send_alert(frame, level, score):
    """
    frame: BGR numpy image (cv2 frame) — snapshot-ku, illa None
    level: "Normal" / "Low" / "Medium" / "High" / "Critical"
    score: float, 0-100 illa 0-1 range la irukkura threat score
    Return: (sent: bool, reason: str) — UI la feedback kaattradhukku use pannalaam
    """
    global _last_alert_time

    if level not in ALERT_LEVELS:
        return False, f"level '{level}' is below alert threshold"

    if not configured():
        return False, "Telegram not configured (.env missing TOKEN/CHAT_ID)"

    if not _cooldown_ok():
        remaining = COOLDOWN_SECONDS - (time.time() - _last_alert_time)
        return False, f"cooldown active ({remaining:.0f}s left)"

    timestamp = time.strftime("%H:%M:%S")
    caption = f"🚨 {level.upper()} THREAT\nScore: {score:.2f}\nTime: {timestamp}"

    try:
        if frame is not None:
            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                raise ValueError("frame encode failed")
            files = {"photo": ("snapshot.jpg", buf.tobytes(), "image/jpeg")}
            resp = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
                data={"chat_id": CHAT_ID, "caption": caption},
                files=files, timeout=10,
            )
        else:
            resp = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": caption}, timeout=10,
            )
    except requests.RequestException as e:
        return False, f"network error: {e}"

    if resp.status_code != 200:
        return False, f"Telegram API error {resp.status_code}: {resp.text[:120]}"

    _last_alert_time = time.time()
    return True, "sent"
def status_text():
    """UI la kaattradhukku readable status."""
    if not configured():
        return "Not configured", "#D64545"
    return "Configured", "#2E8B57"