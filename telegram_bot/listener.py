import threading
import requests
import time

from config.settings import BOT_TOKEN


class TelegramListener:

    def __init__(self, alarm):

        self.alarm = alarm

        self.telegram_update_offset = 0

        threading.Thread(target=self.telegram_listener_thread, daemon=True).start()

    def telegram_listener_thread(self):

        while True:

            try:

                self.check_telegram_updates()

            except Exception as e:

                print("❌ Telegram listener error:", e)

            time.sleep(2)

    def check_telegram_updates(self):

        url = f"https://api.telegram.org/" f"bot{BOT_TOKEN}/getUpdates"

        response = requests.get(
            url,
            params={"offset": self.telegram_update_offset, "timeout": 5},
            timeout=10,
        )

        data = response.json()

        if not data["ok"]:
            return

        for update in data["result"]:

            self.telegram_update_offset = update["update_id"] + 1

            callback = update.get("callback_query")

            if not callback:
                continue

            callback_data = callback["data"]

            if callback_data == "SNOOZE_5":

                print("⏰ Snooze requested from Telegram")

                self.alarm.snooze_alarm(5)
