from playsound import playsound
from paths import APP_DIR
import os

def notify_sound():
    notification_names = [
        "notification.mp3",
        "notification.wav"
    ]
    for name in notification_names:
        fp = os.path.join(APP_DIR, name)
        if os.path.exists(fp):
            playsound(fp, False)