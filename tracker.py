"""
Core Tracking Engine
Main state machine and session manager
"""
import threading
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

from config import (
    POLL_INTERVAL_SECONDS,
    IDLE_THRESHOLD_SECONDS,
    HEARTBEAT_GAP_THRESHOLD_SECONDS,
    FLUSH_INTERVAL_SECONDS,
    STATE_ACTIVE,
    STATE_IDLE,
    STATE_LOCKED,
    STATE_SLEEP,
    VALID_STATES,
)
from platforms import get_platform_adapter
from database import Database


class ScreenTimeTracker:
    """
    Core tracking engine managing state transitions, app sessions, and data flushing.
    Implements Singleton pattern to ensure only one instance runs.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self.platform_adapter = get_platform_adapter()
        self.database = Database()

        # State tracking
        self._current_state = STATE_ACTIVE
        self._current_app = None
        self._current_window_title = None
        self._state_start_time = datetime.now()
        self._app_start_time = datetime.now()
        self._last_flush_time = datetime.now()
        self._last_heartbeat_time = datetime.now()

        # Thread management
        self._running = False
        self._loop_thread = None

    def start(self) -> None:
        """Start the tracking engine"""
        if self._running:
            return

        self._running = True
        self.database.initialize()
        self.platform_adapter.start_listener()

        # Log system boot event
        self.database.record_system_event("BOOT", "System started")

        # Start main tracking loop
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()

        print("✅ ScreenTimeTracker started")

    def stop(self) -> None:
        """Stop the tracking engine"""
        if not self._running:
            return

        self._running = False

        # Flush final session
        self._flush_active_sessions()

        # Cleanup
        if self._loop_thread:
            self._loop_thread.join(timeout=5)
        self.platform_adapter.stop_listener()
        self.database.close()

        print("✅ ScreenTimeTracker stopped")

    def _run_loop(self) -> None:
        """Main tracking loop - runs every POLL_INTERVAL_SECONDS"""
        while self._running:
            try:
                # Detect sleep/wake via heartbeat gap
                self._detect_sleep_gap()

                # Get current system state
                idle_seconds = self.platform_adapter.get_idle_seconds()
                is_locked = self.platform_adapter.is_locked()
                is_sleeping = self.platform_adapter.is_sleeping()

                # Determine target state
                target_state = self._determine_state(idle_seconds, is_locked, is_sleeping)

                # Handle state transitions
                if target_state != self._current_state:
                    self._on_state_change(target_state)

                # Get active app (only if ACTIVE state)
                if self._current_state == STATE_ACTIVE:
                    app_name, window_title = self.platform_adapter.get_active_window_info()
                    if app_name != self._current_app:
                        self._on_app_change(app_name, window_title)

                # Flush to database periodically
                time_since_flush = (datetime.now() - self._last_flush_time).total_seconds()
                if time_since_flush >= FLUSH_INTERVAL_SECONDS:
                    self._flush_active_sessions()

                time.sleep(POLL_INTERVAL_SECONDS)

            except Exception as e:
                print(f"Error in tracking loop: {e}")
                time.sleep(POLL_INTERVAL_SECONDS)

    def _detect_sleep_gap(self) -> None:
        """
        Detect unannounced sleep/hibernation via system time jump.
        If system time jumped by > HEARTBEAT_GAP_THRESHOLD_SECONDS, assume sleep occurred.
        """
        now = datetime.now()
        gap = (now - self._last_heartbeat_time).total_seconds()

        if gap > HEARTBEAT_GAP_THRESHOLD_SECONDS:
            # Unannounced sleep detected
            sleep_duration = gap - 1  # Approximate sleep duration
            self.database.record_state_session(
                STATE_SLEEP,
                self._last_heartbeat_time,
                now - timedelta(seconds=1),
                sleep_duration,
            )

        self._last_heartbeat_time = now

    def _determine_state(self, idle_seconds: float, is_locked: bool, is_sleeping: bool) -> str:
        """
        State machine logic: determine target state based on inputs.
        Priority: SLEEP > LOCKED > IDLE/ACTIVE
        """
        if is_sleeping:
            return STATE_SLEEP
        elif is_locked:
            return STATE_LOCKED
        elif idle_seconds >= IDLE_THRESHOLD_SECONDS:
            return STATE_IDLE
        else:
            return STATE_ACTIVE

    def _on_state_change(self, new_state: str) -> None:
        """Handle state transition"""
        if self._current_state not in VALID_STATES or new_state not in VALID_STATES:
            return

        # Calculate duration of previous state
        duration = (datetime.now() - self._state_start_time).total_seconds()

        # Save previous state session
        self.database.record_state_session(
            self._current_state,
            self._state_start_time,
            datetime.now(),
            duration,
        )

        # Update state
        self._current_state = new_state
        self._state_start_time = datetime.now()

        # Log event
        self.database.record_system_event(
            "STATE_CHANGE",
            f"{self._current_state} -> {new_state}"
        )

        print(f"🔄 State: {self._current_state}")

    def _on_app_change(self, app_name: str, window_title: str) -> None:
        """Handle active application change"""
        # Save previous app session
        if self._current_app:
            duration = (datetime.now() - self._app_start_time).total_seconds()
            self.database.record_app_session(
                self._current_app,
                self._current_window_title or "Unknown",
                self._app_start_time,
                datetime.now(),
                duration,
            )

        # Update current app
        self._current_app = app_name
        self._current_window_title = window_title
        self._app_start_time = datetime.now()

        print(f"📱 App: {app_name}")

    def _flush_active_sessions(self) -> None:
        """
        Flush uncommitted active sessions to database.
        This is called periodically to ensure real-time persistence.
        """
        try:
            # Record current state session (uncommitted portion)
            duration = (datetime.now() - self._state_start_time).total_seconds()
            if duration > 0:
                self.database.record_state_session(
                    self._current_state,
                    self._state_start_time,
                    datetime.now(),
                    duration,
                    commit_only=True,  # Don't reset the ongoing session
                )

            # Record current app session (uncommitted portion)
            if self._current_app:
                duration = (datetime.now() - self._app_start_time).total_seconds()
                if duration > 0:
                    self.database.record_app_session(
                        self._current_app,
                        self._current_window_title or "Unknown",
                        self._app_start_time,
                        datetime.now(),
                        duration,
                        commit_only=True,
                    )

            self._last_flush_time = datetime.now()
        except Exception as e:
            print(f"Error flushing sessions: {e}")

    def get_status(self) -> Dict:
        """
        Get current instantaneous status (thread-safe snapshot).
        Used by Web API and CLI.
        """
        now = datetime.now()
        current_duration = (now - self._state_start_time).total_seconds()
        current_app_duration = (now - self._app_start_time).total_seconds() if self._current_app else 0

        return {
            "current_state": self._current_state,
            "current_app": self._current_app,
            "current_window_title": self._current_window_title,
            "state_duration_seconds": current_duration,
            "app_duration_seconds": current_app_duration,
            "timestamp": now.isoformat(),
        }

    def get_daily_summary(self, date_str: str) -> Dict:
        """Get daily summary statistics"""
        return self.database.get_daily_summary(date_str)


from datetime import timedelta
