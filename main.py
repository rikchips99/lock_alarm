import win32gui
import time

from alarm.alarm_manager import AlarmManager
from windows.session_listener import SessionListener
from notifications.windows_notifications import WindowsNotificationListener
from telegram_bot.listener import TelegramListener


def main():

    alarm = AlarmManager()

    session = SessionListener(alarm)

    notifications = WindowsNotificationListener(alarm)

    telegram = TelegramListener(alarm)

    print("🚀 System started")
    print("Listening for:")
    print("   - Screen locked/unlocked")
    print("   - Lid closed/opened")
    print("   - Windows notifications")
    print("   - Telegram alerts")

    while True:
        win32gui.PumpWaitingMessages()
        time.sleep(0.1)


if __name__ == "__main__":
    main()
