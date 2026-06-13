import ctypes

import win32gui
import win32ts

from windows.constants import (
    WM_WTSSESSION_CHANGE,
    WTS_SESSION_LOCK,
    WTS_SESSION_UNLOCK,
    WM_POWERBROADCAST,
    PBT_POWERSETTINGCHANGE,
    DEVICE_NOTIFY_WINDOW_HANDLE,
    GUID_LIDSWITCH_STATE_CHANGE,
)

from windows.structures import (
    GUID,
    POWERBROADCAST_SETTING,
)

from windows.power import (
    uuid_to_guid,
)


class SessionListener:

    def __init__(self, alarm):

        self.alarm = alarm

        self.hinst = win32gui.GetModuleHandle(None)

        wndclass = win32gui.WNDCLASS()

        wndclass.lpfnWndProc = self.wnd_proc
        wndclass.lpszClassName = "SessionListenerClass"
        wndclass.hInstance = self.hinst

        self.class_atom = win32gui.RegisterClass(wndclass)

        self.hwnd = win32gui.CreateWindow(
            self.class_atom,
            "Session Listener",
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            self.hinst,
            None,
        )

        # ======================================
        # Session notifications
        # ======================================

        win32ts.WTSRegisterSessionNotification(
            self.hwnd,
            win32ts.NOTIFY_FOR_THIS_SESSION,
        )

        # ======================================
        # Lid notifications
        # ======================================

        guid = uuid_to_guid(GUID_LIDSWITCH_STATE_CHANGE)

        ctypes.windll.user32.RegisterPowerSettingNotification(
            self.hwnd,
            ctypes.byref(guid),
            DEVICE_NOTIFY_WINDOW_HANDLE,
        )

    # ==========================================
    # Windows procedure
    # ==========================================

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
                    ctypes.POINTER(POWERBROADCAST_SETTING),
                ).contents

                guid = uuid_to_guid(GUID_LIDSWITCH_STATE_CHANGE)

                if ctypes.string_at(
                    ctypes.byref(setting.PowerSetting),
                    ctypes.sizeof(GUID),
                ) == ctypes.string_at(
                    ctypes.byref(guid),
                    ctypes.sizeof(GUID),
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
            lparam,
        )

    # ==========================================
    # Events
    # ==========================================

    def on_lock(self):

        print("🔒 Screen LOCKED")

        self.alarm.handle_lock()

    def on_unlock(self):

        print("🔓 Screen UNLOCKED")

        self.alarm.handle_unlock()

    def on_lid_closed(self):

        print("🔴 Lid CLOSED")

        self.alarm.handle_lid_closed()

    def on_lid_opened(self):

        print("🟢 Lid OPENED")

        self.alarm.handle_lid_opened()
