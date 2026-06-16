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
                
                # Step 1
                self.answer_callback(callback["id"])
                # Step 2
                chat_id = callback["message"]["chat"]["id"]
                message_id = callback["message"]["message_id"]
                until_time = time.strftime(
                    "%H:%M:%S",
                    time.localtime(
                        self.alarm.snooze_until
                    )
                )
                # Step 3
                self.edit_message_snoozed(chat_id, message_id, until_time)

    def answer_callback(self, callback_query_id):
        
        url = (
            f"https://api.telegram.org/"
            f"bot{BOT_TOKEN}/answerCallbackQuery"
        )
        
        requests.post(
            url,
            json={
                "callback_query_id": callback_query_id,
                "text": "Alarm snoozed for 5 minutes",
                "show_alert": False
            },
            timeout=10
        )
        
    # def remove_keyboard(self, chat_id, message_id):
        
    #     url = (
    #         f"https://api.telegram.org/"
    #         f"bot{BOT_TOKEN}/editMessageReplyMarkup"
    #     )
        
    #     requests.post(
    #         url,
    #         json={
    #             "chat_id": chat_id,
    #             "message_id": message_id,
    #             "reply_markup": {
    #                 "inline_keyboard": []
    #             }
    #         },
    #         timeout=10
    #     )
    
    def edit_message_snoozed(self, chat_id, message_id, until_time):
        url = (
            f"https://api.telegram.org/"
            f"bot{BOT_TOKEN}/editMessageText"
        )
        
        requests.post(
            url,
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": (
                    "⚠️ LOCK ALERT\n\n"
                    f"⏰ Alarm will go off at {until_time} "
                )
            },
            timeout=10
        )
        