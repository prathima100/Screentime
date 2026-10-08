"""
PulseTrack - Screen Time Monitor
Main Application Orchestrator & Entrypoint

Usage:
    python main.py              # Start with web dashboard
    python main.py --cli        # Start CLI only
    python main.py --server     # Start server only
    python main.py --help       # Show help
"""

import sys
import argparse
import webbrowser
from threading import Thread
import time

from tracker import ScreenTimeTracker
from server import app, run_server
from config import SERVER_HOST, SERVER_PORT


def print_banner():
    """Print startup banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                   🔴 PULSETRACK v1.0.0                    ║
║          Real-Time Screen Time Monitor for Desktop         ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def start_tracker():
    """Start the background tracking engine"""
    print("🚀 Initializing Tracker Engine...")
    tracker = ScreenTimeTracker()
    tracker.start()
    return tracker


def start_server():
    """Start the FastAPI web server"""
    print(f"🌐 Starting Web Server on http://{SERVER_HOST}:{SERVER_PORT}")
    run_server()


def open_dashboard():
    """Open the dashboard in default browser"""
    time.sleep(2)  # Wait for server to start
    url = f"http://{SERVER_HOST}:{SERVER_PORT}/"
    print(f"📊 Opening dashboard at {url}")
    webbrowser.open(url)


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="PulseTrack - Real-Time Screen Time Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                  # Run full application (tracker + dashboard)
    python main.py --cli            # Run CLI interface only
    python main.py --server-only    # Run server without opening browser
    python main.py --help           # Show this help message
        """
    )

    parser.add_argument(
        "--cli",
        action="store_true",
        help="Start CLI interface only (no dashboard)"
    )
    parser.add_argument(
        "--server-only",
        action="store_true",
        help="Start server without opening browser"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start without opening browser"
    )

    args = parser.parse_args()

    print_banner()

    if args.cli:
        # CLI mode only
        print("🖥️  Starting CLI Interface...")
        from cli import PulseTrackCLI
        cli = PulseTrackCLI()
        cli.cmd_today()
        return

    # Start tracker in background
    tracker = start_tracker()

    try:
        # Start server
        server_thread = Thread(target=start_server, daemon=True)
        server_thread.start()

        # Open dashboard in browser (unless --no-browser)
        if not args.no_browser and not args.server_only:
            browser_thread = Thread(target=open_dashboard, daemon=True)
            browser_thread.start()

        # Keep the main thread alive
        print("\n✅ PulseTrack is running. Press Ctrl+C to exit.\n")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        tracker.stop()
        print("✅ PulseTrack stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
