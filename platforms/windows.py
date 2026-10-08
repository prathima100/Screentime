"""
Windows Platform Adapter
Implementation using Win32 API via ctypes and pywin32
"""
import ctypes
import threading
import time
from typing import Tuple
from .base import PlatformAdapter

try:
    import win32api
    import win32gui
    import win32con
except ImportError:
    raise ImportError("pywin32 is required for Windows. Install with: pip install pywin32")


class WindowsAdapter(PlatformAdapter):
    """Windows-specific implementation using Win32 API"""

    def __init__(self):
        self._listener_thread = None
        self._running = False
        self._is_locked = False
        self._is_sleeping = False
        self._hwnd = None

    def get_idle_seconds(self) -> float:
        """
        Get idle time using Windows GetLastInputInfo API.
        This avoids keylogging by using system-level input timestamp.
        """
        try:
            class LastInputInfo(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

            lii = LastInputInfo()
            lii.cbSize = ctypes.sizeof(LastInputInfo)

            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
            current_ticks = ctypes.windll.kernel32.GetTickCount64()
            idle_ms = current_ticks - lii.dwTime
            return idle_ms / 1000.0
        except Exception as e:
            print(f"Error getting idle time: {e}")
            return 0.0

    def get_active_window_info(self) -> Tuple[str, str]:
        """
        Get the active foreground window's app name and title.
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)

            # Get process ID and name
            _, pid = win32gui.GetWindowThreadProcessId(hwnd)
            try:
                import psutil
                app_name = psutil.Process(pid).name()
            except:
                app_name = "Unknown"

            return (app_name, window_title)
        except Exception as e:
            print(f"Error getting active window: {e}")
            return ("Unknown", "Unknown")

    def is_locked(self) -> bool:
        """Return current lock state"""
        return self._is_locked

    def is_sleeping(self) -> bool:
        """Return current sleep state"""
        return self._is_sleeping

    def start_listener(self) -> None:
        """Start background listener thread for Windows events"""
        if self._running:
            return

        self._running = True
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listener_thread.start()

    def stop_listener(self) -> None:
        """Stop the listener thread"""
        self._running = False
        if self._listener_thread:
            self._listener_thread.join(timeout=5)

    @property
    def is_running(self) -> bool:
        """Check if listener is running"""
        return self._running

    def _listen_loop(self) -> None:
        """
        Main listener loop using Win32 Window Message Queue.
        Registers for WM_WTSSESSION_CHANGE and WM_POWERBROADCAST events.
        """
        try:
            # Create a hidden window
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self._wnd_proc
            wc.lpszClassName = "PulseTrackMonitorClass"
            hinst = wc.hInstance = win32api.GetModuleHandle(None)
            class_atom = win32gui.RegisterClass(wc)
            self._hwnd = win32gui.CreateWindow(
                class_atom, "PulseTrack Monitor", 0, 0, 0, 0, 0, 0, 0, hinst, None
            )

            # Register for session notifications (Lock/Unlock)
            ctypes.windll.wtsapi32.WTSRegisterSessionNotification(self._hwnd, 0)

            # Message pump loop
            while self._running:
                win32gui.PumpWaitingMessages()
                time.sleep(0.1)
        except Exception as e:
            print(f"Error in Windows listener: {e}")

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure callback for event handling"""
        if msg == 0x02B1:  # WM_WTSSESSION_CHANGE
            if wparam == 0x7:  # WTS_SESSION_LOCK
                self._is_locked = True
            elif wparam == 0x8:  # WTS_SESSION_UNLOCK
                self._is_locked = False
        elif msg == 0x0218:  # WM_POWERBROADCAST
            if wparam == 0x4:  # PBT_APMSUSPEND
                self._is_sleeping = True
            elif wparam == 0x7:  # PBT_APMRESUMESUSPEND
                self._is_sleeping = False

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
