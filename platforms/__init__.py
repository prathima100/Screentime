"""
Platform Abstraction Layer - Factory
Dynamically selects the correct OS adapter
"""
import platform
from .base import PlatformAdapter


def get_platform_adapter() -> PlatformAdapter:
    """
    Factory function that returns the appropriate platform adapter
    based on the operating system.
    """
    system = platform.system().lower()

    if "windows" in system:
        from .windows import WindowsAdapter
        return WindowsAdapter()
    elif "darwin" in system:
        from .macos import MacOSAdapter
        return MacOSAdapter()
    elif "linux" in system:
        from .linux import LinuxAdapter
        return LinuxAdapter()
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


__all__ = ["PlatformAdapter", "get_platform_adapter"]
