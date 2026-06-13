import threading
import time
import winsound

from telegram_bot.sender import send_telegram_alert


class AlarmManager:

    def __init__(self):

        self.alarm_running = False

        self.last_telegram_sent = 0

        self.snoozed = False

        self.snooze_until = 0

        self.session_locked = False

        self.lid_closed = False

        threading.Thread(target=self.snooze_watchdog_thread, daemon=True).start()

    # ==========================================
    # Alarm
    # ==========================================

    def start_alarm(self):

        if self.alarm_running:
            return

        self.alarm_running = True

        threading.Thread(target=self.alarm_loop, daemon=True).start()

    def stop_alarm(self):

        self.alarm_running = False

    def alarm_loop(self):

        print("🔊 Alarm started")

        while self.alarm_running and (self.session_locked or self.lid_closed):

            current_time = time.strftime("%Y-%m-%d %H:%M:%S")

            winsound.Beep(1500, 300)

            now = time.time()

            if now - self.last_telegram_sent >= 30:

                print(f"[{current_time}] " f"📨 Sending Telegram alert")

                send_telegram_alert(
                    f"⚠️ LOCK ALERT\n"
                    f"Time: {current_time}\n"
                    f"Message: Check Tele RK"
                )

                self.last_telegram_sent = now

            time.sleep(0.5)

        print("🛑 Alarm stopped")

    # ==========================================
    # Snooze
    # ==========================================

    def snooze_alarm(self, minutes=5):

        self.snoozed = True

        self.snooze_until = time.time() + minutes * 60

        print(
            f"⏰ Alarm snoozed for {minutes} minutes "
            f"until "
            f"{time.strftime('%H:%M:%S', time.localtime(self.snooze_until))}"
        )

        self.stop_alarm()

    def snooze_watchdog_thread(self):

        while True:

            try:

                if self.snoozed:

                    if time.time() >= self.snooze_until:

                        print("⏰ Snoozed expired")

                        self.snoozed = False

                        if self.session_locked or self.lid_closed:

                            print("🔔 Restarting alarm")

                            self.start_alarm()

            except Exception as e:

                print("❌ Snooze watchdog error:", e)

            time.sleep(1)

    # ==========================================
    # Event handlers
    # ==========================================

    def handle_lock(self):

        self.session_locked = True

    def handle_unlock(self):

        self.session_locked = False

        self.stop_alarm()

        self.snoozed = False

    def handle_lid_closed(self):

        self.lid_closed = True

    def handle_lid_opened(self):

        self.lid_closed = False

        self.stop_alarm()

        self.snoozed = False

    def handle_notification(self):

        if self.snoozed:

            if time.time() < self.snooze_until:

                print("⏰ Notification ignored (snoozed)")

                return

            self.snoozed = False

        if self.session_locked or self.lid_closed:

            print("⚠️ LOCKED/CLOSED + notification detected")

            self.start_alarm()
