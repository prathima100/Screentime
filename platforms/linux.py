"""
Linux Platform Adapter
Implementation using X11/Wayland and D-Bus
"""
import threading
import time
from typing import Tuple
from .base import PlatformAdapter


class LinuxAdapter(PlatformAdapter):
    """Linux-specific implementation using X11 and D-Bus"""

    def __init__(self):
        self._listener_thread = None
        self._running = False
        self._is_locked = False
        self._is_sleeping = False

    def get_idle_seconds(self) -> float:
        """
        Get idle time using X11 XScreenSaver extension or GNOME Mutter.
        """
        try:
            import dbus

            # Try GNOME Mutter first
            try:
                bus = dbus.SessionBus()
                obj = bus.get_object("org.gnome.Mutter.IdleMonitor", "/org/gnome/Mutter/IdleMonitor/core")
                iface = dbus.Interface(obj, "org.gnome.Mutter.IdleMonitor")
                idle_ms = iface.GetIdletime()
                return idle_ms / 1000.0
            except:
                # Fallback to XScreenSaver
                import subprocess
                result = subprocess.run(
                    ["xscreensaver-command", "-time"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    # Parse output: "XScreenSaver 5.44.1 on since Thu Jan 01 00:00:00 2026\n
                    # idle for 42 seconds\n"
                    for line in result.stdout.split("\n"):
                        if "idle for" in line:
                            idle_str = line.split("idle for")[1].strip().split()[0]
                            return float(idle_str)
                return 0.0
        except Exception as e:
            print(f"Error getting idle time on Linux: {e}")
            return 0.0

    def get_active_window_info(self) -> Tuple[str, str]:
        """
        Get the active foreground window's app name and title.
        Uses xdotool or wmctrl for X11.
        """
        try:
            import subprocess

            # Get active window ID
            result = subprocess.run(
                ["xdotool", "getactivewindow"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode != 0:
                return ("Unknown", "Unknown")

            window_id = result.stdout.strip()

            # Get window name
            result = subprocess.run(
                ["xdotool", "getwindowname", window_id],
                capture_output=True,
                text=True,
                timeout=2
            )
            window_title = result.stdout.strip() if result.returncode == 0 else "Unknown"

            # Get application name using xprop
            result = subprocess.run(
                ["xprop", "-id", window_id, "WM_CLASS"],
                capture_output=True,
                text=True,
                timeout=2
            )
            app_name = "Unknown"
            if result.returncode == 0:
                # Parse WM_CLASS output
                output = result.stdout.strip()
                if ',' in output:
                    app_name = output.split('"')[1]

            return (app_name, window_title)
        except Exception as e:
            print(f"Error getting active window on Linux: {e}")
            return ("Unknown", "Unknown")

    def is_locked(self) -> bool:
        """Return current lock state"""
        return self._is_locked

    def is_sleeping(self) -> bool:
        """Return current sleep state"""
        return self._is_sleeping

    def start_listener(self) -> None:
        """Start background listener thread for Linux events"""
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
        Main listener loop using D-Bus and GNOME Mutter.
        Listens for lock/unlock and sleep/wake events.
        """
        try:
            import dbus
            from dbus.mainloop.glib import DBusGMainLoop

            def on_lock_changed(locked):
                self._is_locked = locked

            def on_sleep_changed(sleeping):
                self._is_sleeping = sleeping

            DBusGMainLoop(set_as_default=True)
            bus = dbus.SessionBus()

            # Listen for GNOME screen lock signal
            bus.add_signal_receiver(
                on_lock_changed,
                signal_name="ActiveChanged",
                dbus_interface="org.gnome.ScreenSaver",
                path="/org/gnome/ScreenSaver"
            )

            # Listen for SystemD sleep signals
            bus.add_signal_receiver(
                on_sleep_changed,
                signal_name="PrepareForSleep",
                dbus_interface="org.freedesktop.login1.Manager",
                path="/org/freedesktop/login1"
            )

            # Keep running
            import glib
            loop = glib.MainLoop()
            loop.run()

        except Exception as e:
            print(f"Error in Linux listener: {e}")
            # Fallback: just monitor idle time
            while self._running:
                time.sleep(1)
