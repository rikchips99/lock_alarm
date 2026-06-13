import requests
from config.settings import BOT_TOKEN, CHAT_ID


def send_telegram(message):

    try:

        url = f"https://api.telegram.org/" f"bot{BOT_TOKEN}/sendMessage"

        data = {"chat_id": CHAT_ID, "text": message}

        requests.post(url, data=data, timeout=5)

    except Exception as e:

        print("❌ Telegram send error:", e)


def send_telegram_alert(message):

    try:

        url = f"https://api.telegram.org/" f"bot{BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": "⏰ Snooze 5 minutes", "callback_data": "SNOOZE_5"}]
                ]
            },
        }

        r = requests.post(url, json=payload, timeout=5)

        print("Telegram send:", r.status_code, r.text)

    except Exception as e:

        print("❌ Telegram send error:", e)
