"""
macOS Platform Adapter
Implementation using CoreGraphics and IOKit
"""
import threading
import time
from typing import Tuple
from .base import PlatformAdapter


class MacOSAdapter(PlatformAdapter):
    """macOS-specific implementation using CoreGraphics and IOKit"""

    def __init__(self):
        self._listener_thread = None
        self._running = False
        self._is_locked = False
        self._is_sleeping = False

    def get_idle_seconds(self) -> float:
        """
        Get idle time using macOS CoreGraphics API.
        """
        try:
            from Quartz import CGEventSourceSecondsSinceLastEventType, kCGEventSourceStateHIDSystemState

            idle_ms = CGEventSourceSecondsSinceLastEventType(
                kCGEventSourceStateHIDSystemState, -1  # All event types
            ) * 1000
            return idle_ms / 1000.0
        except ImportError:
            print("CoreGraphics not available on this system")
            return 0.0

    def get_active_window_info(self) -> Tuple[str, str]:
        """
        Get the active foreground window's app name and title.
        Uses AppKit to access the active application.
        """
        try:
            from AppKit import NSWorkspace, NSRunningApplication

            ws = NSWorkspace.sharedWorkspace()
            active_app = ws.activeApplication()

            app_name = active_app.get("NSApplicationName", "Unknown")

            # Try to get window title (requires additional accessibility)
            try:
                from PyObjCTools import AppHelper
                # This is a simplified version; full implementation requires accessibility API
                window_title = "macOS Application"
            except:
                window_title = "Unknown"

            return (app_name, window_title)
        except Exception as e:
            print(f"Error getting active window on macOS: {e}")
            return ("Unknown", "Unknown")

    def is_locked(self) -> bool:
        """Return current lock state"""
        return self._is_locked

    def is_sleeping(self) -> bool:
        """Return current sleep state"""
        return self._is_sleeping

    def start_listener(self) -> None:
        """Start background listener thread for macOS events"""
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
        Main listener loop using NSDistributedNotificationCenter.
        Listens for screen lock/unlock and sleep/wake notifications.
        """
        try:
            from Foundation import NSDistributedNotificationCenter, NSObject
            from AppKit import NSDistributedNotificationCenter as AppKitCenter
            import PyObjCTools.AppHelper

            class EventObserver(NSObject):
                def __init__(self, adapter):
                    super().__init__()
                    self.adapter = adapter

                def screenLocked_(self, notification):
                    self.adapter._is_locked = True

                def screenUnlocked_(self, notification):
                    self.adapter._is_locked = False

                def screenSleeping_(self, notification):
                    self.adapter._is_sleeping = True

                def screenWaking_(self, notification):
                    self.adapter._is_sleeping = False

            observer = EventObserver.alloc().init()
            observer.adapter = self
            nc = AppKitCenter.defaultCenter()

            nc.addObserver_selector_name_object_(
                observer, "screenLocked:", "com.apple.screenIsLocked", None
            )
            nc.addObserver_selector_name_object_(
                observer, "screenUnlocked:", "com.apple.screenIsUnlocked", None
            )
            nc.addObserver_selector_name_object_(
                observer, "screenSleeping:", "com.apple.screensaver.didstart", None
            )
            nc.addObserver_selector_name_object_(
                observer, "screenWaking:", "com.apple.screensaver.didstop", None
            )

            # Keep the event loop running
            while self._running:
                time.sleep(1)

        except Exception as e:
            print(f"Error in macOS listener: {e}")
