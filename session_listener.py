import requests
import asyncio
import threading
import time
import winsound

import win32gui
import win32ts

import os
import ctypes
from ctypes import wintypes
import uuid

from dotenv import load_dotenv

load_dotenv()

from winsdk.windows.ui.notifications.management import UserNotificationListener

from winsdk.windows.ui.notifications import NotificationKinds

# =========================================================
# WINDOWS CONSTANTS
# =========================================================

WM_WTSSESSION_CHANGE = 0x02B1

WTS_SESSION_LOCK = 0x7
WTS_SESSION_UNLOCK = 0x8
WM_POWERBROADCAST = 0x0218
PBT_POWERSETTINGCHANGE = 0x8013

DEVICE_NOTIFY_WINDOW_HANDLE = 0x00000000

GUID_LIDSWITCH_STATE_CHANGE = uuid.UUID("{BA3E0F4D-B817-4094-A2D1-D56379E6A0F3}")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def send_telegram(message):

    try:

        url = f"https://api.telegram.org/" f"bot{BOT_TOKEN}/sendMessage"

        data = {"chat_id": CHAT_ID, "text": message}

        requests.post(url, data=data, timeout=5)

    except Exception as e:

        print("❌ Telegram send error:", e)


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class POWERBROADCAST_SETTING(ctypes.Structure):
    _fields_ = [
        ("PowerSetting", GUID),
        ("DataLength", wintypes.DWORD),
        ("Data", ctypes.c_ubyte * 1),
    ]


def uuid_to_guid(u):
    return GUID(
        u.time_low,
        u.time_mid,
        u.time_hi_version,
        (ctypes.c_ubyte * 8)(
            (u.clock_seq_hi_variant << 8 | u.clock_seq_low) >> 8,
            (u.clock_seq_hi_variant << 8 | u.clock_seq_low) & 0xFF,
            *u.node.to_bytes(6, "big"),
        ),
    )


class SessionListener:

    def __init__(self):

        # =================================================
        # STATE
        # =================================================

        # self.locked = False
        self.session_locked = False
        self.lid_closed = False
        self.alarm_running = False
        self.last_telegram_sent = 0

        # =================================================
        # CREATE HIDDEN WINDOW
        # =================================================

        self.hinst = win32gui.GetModuleHandle(None)

        wndclass = win32gui.WNDCLASS()
        wndclass.lpfnWndProc = self.wnd_proc
        wndclass.lpszClassName = "SessionListenerClass"
        wndclass.hInstance = self.hinst

        self.class_atom = win32gui.RegisterClass(wndclass)

        self.hwnd = win32gui.CreateWindow(
            self.class_atom, "Session Listener", 0, 0, 0, 0, 0, 0, 0, self.hinst, None
        )

        # =================================================
        # REGISTER SESSION EVENTS
        # =================================================

        win32ts.WTSRegisterSessionNotification(
            self.hwnd, win32ts.NOTIFY_FOR_THIS_SESSION
        )
        
        guid = uuid_to_guid(
            GUID_LIDSWITCH_STATE_CHANGE
        )

        ctypes.windll.user32.RegisterPowerSettingNotification(
            self.hwnd,
            ctypes.byref(guid),
            DEVICE_NOTIFY_WINDOW_HANDLE,
        )

        # =================================================
        # START NOTIFICATION LISTENER
        # =================================================

        threading.Thread(target=self.notification_listener_thread, daemon=True).start()

    # =====================================================
    # WINDOWS MESSAGE LOOP
    # =====================================================

    def wnd_proc(self, hwnd, msg, wparam, lparam):

        if msg == WM_WTSSESSION_CHANGE:

            if wparam == WTS_SESSION_LOCK:
                self.on_lock()

            elif wparam == WTS_SESSION_UNLOCK:
                self.on_unlock()

            return 0

        elif msg == WM_POWERBROADCAST:

            if wparam == PBT_POWERSETTINGCHANGE:

                setting = ctypes.cast(
                    lparam,
                    ctypes.POINTER(
                        POWERBROADCAST_SETTING
                    )
                ).contents

                guid = uuid_to_guid(
                    GUID_LIDSWITCH_STATE_CHANGE
                )

                if (
                    ctypes.string_at(
                        ctypes.byref(setting.PowerSetting),
                        ctypes.sizeof(GUID)
                    )
                    ==
                    ctypes.string_at(
                        ctypes.byref(guid),
                        ctypes.sizeof(GUID)
                    )
                ):

                    lid_state = setting.Data[0]

                    if lid_state == 0:
                        self.on_lid_closed()

                    elif lid_state == 1:
                        self.on_lid_opened()

            return 1

        return win32gui.DefWindowProc(
            hwnd,
            msg,
            wparam,
            lparam
        )

    # =====================================================
    # LOCK / UNLOCK EVENTS / LID CLOSED / LID OPENED
    # =====================================================

    def on_lock(self):
        # self.locked = True
        self.session_locked = True
        print("🔒 SCREEN LOCKED")

    def on_unlock(self):
        # self.locked = False
        self.session_locked = False
        print("🔓 SCREEN UNLOCKED")
        self.stop_alarm()

    def on_lid_closed(self):
        self.lid_closed = True
        print("🔴 LID CLOSED")

    def on_lid_opened(self):
        self.lid_closed = False
        print("🟢 LID OPENED")
        self.stop_alarm()

    # =====================================================
    # ALARM ENGINE
    # =====================================================

    def start_alarm(self):

        if self.alarm_running:
            return

        self.alarm_running = True

        threading.Thread(target=self.alarm_loop, daemon=True).start()

    def stop_alarm(self):

        self.alarm_running = False

    def alarm_loop(self):

        print("🔊 Alarm started")

        # while self.alarm_running and self.locked:
        while self.alarm_running and (self.session_locked or self.lid_closed):
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")

            winsound.Beep(1500, 300)

            now = time.time()
            if now - self.last_telegram_sent >= 30:
                print(f"[{current_time}] " f"📨 Sending Telegram alert")

                send_telegram(
                    f"⚠️ LOCK ALERT\n"
                    f"Time: {current_time}\n"
                    f"Message: Check Tele RK"
                )

                self.last_telegram_sent = now

            time.sleep(0.5)

        print("🛑 Alarm stopped")

    # =====================================================
    # NOTIFICATION LISTENER THREAD
    # =====================================================

    def notification_listener_thread(self):

        asyncio.run(self.notification_listener())

    # =====================================================
    # WINDOWS NOTIFICATION LISTENER
    # =====================================================

    async def notification_listener(self):

        listener = UserNotificationListener.current

        access = await listener.request_access_async()

        print(f"🔔 Notification access status: {access}")

        known_notifications = set()

        while True:

            try:

                notifications = await listener.get_notifications_async(
                    NotificationKinds.TOAST
                )

                for notification in notifications:

                    notif_id = notification.id

                    # =================================
                    # SKIP DUPLICATES
                    # =================================

                    if notif_id in known_notifications:
                        continue

                    known_notifications.add(notif_id)

                    # =================================
                    # GET APP NAME
                    # =================================

                    app_name = notification.app_info.display_info.display_name

                    # =====================================
                    # ONLY TELEGRAM + LARK
                    # actually Lark not work
                    # =====================================

                    allowed_apps = ["Telegram", "Lark"]

                    matched = any(app in app_name for app in allowed_apps)

                    if not matched:
                        continue

                    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

                    print(f"[{current_time}] " f"📩 Notification from: {app_name}")

                    # =====================================
                    # ALARM IF LOCKED
                    # =====================================

                    # if self.locked:
                    if self.session_locked or self.lid_closed:
                        print(f"[{current_time}] " f"⚠️ LOCKED + notification detected")
                        self.start_alarm()

                await asyncio.sleep(2)

            except Exception as e:

                print("❌ Notification listener error:", e)

                await asyncio.sleep(5)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    listener = SessionListener()

    print("🚀 System started")
    print("Listening for:")
    print("   - Screen locked/unlocked")
    print("   - Lid closed/opened")
    print("   - Windows notifications")
    print("   - Telegram alerts")

    while True:
        win32gui.PumpWaitingMessages()
        time.sleep(0.1)
