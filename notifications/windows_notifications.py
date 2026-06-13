import asyncio
import threading
import time

from winsdk.windows.ui.notifications.management import (
    UserNotificationListener,
)

from winsdk.windows.ui.notifications import (
    NotificationKinds,
)


class WindowsNotificationListener:

    def __init__(self, alarm):

        self.alarm = alarm

        threading.Thread(
            target=self.notification_listener_thread,
            daemon=True,
        ).start()

    def notification_listener_thread(self):

        asyncio.run(self.notification_listener())

    async def notification_listener(self):

        listener = UserNotificationListener.current

        access = await listener.request_access_async()

        print(f"🔔 Notification access status: " f"{access}")

        known_notifications = set()

        while True:

            try:

                notifications = await listener.get_notifications_async(
                    NotificationKinds.TOAST
                )

                for notification in notifications:

                    notif_id = notification.id

                    # =====================
                    # Skip duplicates
                    # =====================

                    if notif_id in known_notifications:
                        continue

                    known_notifications.add(notif_id)

                    # =====================
                    # App name
                    # =====================

                    app_name = notification.app_info.display_info.display_name

                    allowed_apps = [
                        "Telegram",
                        "Lark",
                    ]

                    matched = any(app in app_name for app in allowed_apps)

                    if not matched:
                        continue

                    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

                    print(f"[{current_time}] " f"📩 Notification from: " f"{app_name}")

                    self.alarm.handle_notification()

                await asyncio.sleep(2)

            except Exception as e:

                print(
                    "❌ Notification listener error:",
                    e,
                )

                await asyncio.sleep(5)
