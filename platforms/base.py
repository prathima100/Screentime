"""
Platform Abstraction Layer - Base Class
Defines the interface every OS adapter must implement
"""
from abc import ABC, abstractmethod
from typing import Tuple, Optional


class PlatformAdapter(ABC):
    """
    Abstract Base Class for platform-specific implementations.
    Each OS adapter (Windows, macOS, Linux) must inherit and implement these methods.
    """

    @abstractmethod
    def get_idle_seconds(self) -> float:
        """
        Get the seconds since the last user input (keyboard/mouse).
        Returns: Float representing idle time in seconds
        """
        pass

    @abstractmethod
    def get_active_window_info(self) -> Tuple[str, str]:
        """
        Get information about the currently active/foreground window.
        Returns: Tuple[app_name, window_title]
                 Example: ("code.exe", "main.py - Visual Studio Code")
        """
        pass

    @abstractmethod
    def is_locked(self) -> bool:
        """
        Check if the system is locked (e.g., Windows Lock Screen engaged).
        Returns: Boolean indicating lock state
        """
        pass

    @abstractmethod
    def is_sleeping(self) -> bool:
        """
        Check if the system is in sleep/suspend/hibernate mode.
        Returns: Boolean indicating sleep state
        """
        pass

    @abstractmethod
    def start_listener(self) -> None:
        """
        Start the background event listener for lock/unlock/sleep/wake events.
        This should run in a separate thread or via event loop.
        """
        pass

    @abstractmethod
    def stop_listener(self) -> None:
        """
        Stop the background event listener gracefully.
        """
        pass

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Check if the listener is currently running."""
        pass
