"""
Command Line Interface (CLI) Tool
Interactive console commands for reporting and analysis
"""
import sys
from datetime import datetime, timedelta
from typing import Optional

from tracker import ScreenTimeTracker
from config import STATE_EMOJIS


class PulseTrackCLI:
    """Command-line interface for PulseTrack"""

    def __init__(self):
        self.tracker = ScreenTimeTracker()

    def print_header(self, title: str) -> None:
        """Print formatted section header"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)

    def format_seconds(self, secs: float) -> str:
        """Format seconds to human-readable string"""
        hours = int(secs // 3600)
        minutes = int((secs % 3600) // 60)
        seconds = int(secs % 60)
        return f"{hours}h {minutes}m {seconds}s"

    def cmd_status(self) -> None:
        """Show current instantaneous status"""
        self.print_header("CURRENT STATUS")

        status = self.tracker.get_status()
        print(f"\n  Current State:       {STATE_EMOJIS.get(status['current_state'], '?')} {status['current_state']}")
        print(f"  Active App:          {status['current_app'] or 'None'}")
        print(f"  Window Title:        {status['current_window_title'] or 'None'}")
        print(f"  State Duration:      {self.format_seconds(status['state_duration_seconds'])}")
        print(f"  App Duration:        {self.format_seconds(status['app_duration_seconds'])}")
        print(f"  Timestamp:           {status['timestamp']}")

    def cmd_today(self) -> None:
        """Show today's summary"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.print_header(f"TODAY'S SUMMARY ({date_str})")

        summary = self.tracker.get_daily_summary(date_str)
        state_totals = summary.get("state_totals", {})

        print(f"\n  📊 STATE BREAKDOWN:")
        for state in ["ACTIVE", "IDLE", "LOCKED", "SLEEP"]:
            duration = state_totals.get(state, 0)
            emoji = STATE_EMOJIS.get(state, "?")
            print(f"     {emoji} {state:8} : {self.format_seconds(duration)}")

        total_awake = state_totals.get("ACTIVE", 0) + state_totals.get("IDLE", 0)
        total_locked = state_totals.get("LOCKED", 0)
        total_sleep = state_totals.get("SLEEP", 0)

        print(f"\n  ⏰ CUMULATIVE:")
        print(f"     • Total Awake & Unlocked: {self.format_seconds(total_awake)}")
        print(f"     • Total Locked:          {self.format_seconds(total_locked)}")
        print(f"     • Total Sleep:           {self.format_seconds(total_sleep)}")

    def cmd_apps(self) -> None:
        """Show top applications"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.print_header(f"TOP APPLICATIONS ({date_str})")

        apps = self.tracker.database.get_app_ranking(date_str, limit=15)

        if not apps:
            print("\n  No application data available.")
            return

        print(f"\n  {'Rank':<6} {'Application':<30} {'Duration':<15} {'Window Title'}")
        print("  " + "-" * 76)

        for i, app in enumerate(apps, 1):
            duration_str = self.format_seconds(app["duration_seconds"])
            window_title = app.get("window_title", "Unknown")[:30]
            print(f"  {i:<6} {app['app_name']:<30} {duration_str:<15} {window_title}")

    def cmd_timeline(self) -> None:
        """Show session timeline"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.print_header(f"SESSION TIMELINE ({date_str})")

        timeline = self.tracker.database.get_timeline(date_str)

        if not timeline:
            print("\n  No session data available.")
            return

        print(f"\n  {'Start Time':<10} {'End Time':<10} {'State':<8} {'Duration'}")
        print("  " + "-" * 50)

        for session in timeline:
            start_time = session["start_time"].split("T")[1][:5]
            end_time = session["end_time"].split("T")[1][:5]
            state = session["state"]
            duration = self.format_seconds(session["duration_seconds"])
            emoji = STATE_EMOJIS.get(state, "?")

            print(f"  {start_time:<10} {end_time:<10} {emoji} {state:<6} {duration}")

    def cmd_week(self) -> None:
        """Show 7-day trend"""
        self.print_header("7-DAY TREND")

        trend = self.tracker.database.get_trend(days=7)

        if not trend:
            print("\n  No trend data available.")
            return

        print(f"\n  {'Date':<12} {'Active':<15} {'Idle':<15} {'Locked':<15} {'Sleep':<15}")
        print("  " + "-" * 72)

        for day in trend:
            date = day["date"]
            active = self.format_seconds(day.get("ACTIVE", 0))
            idle = self.format_seconds(day.get("IDLE", 0))
            locked = self.format_seconds(day.get("LOCKED", 0))
            sleep = self.format_seconds(day.get("SLEEP", 0))

            print(f"  {date:<12} {active:<15} {idle:<15} {locked:<15} {sleep:<15}")

    def cmd_export(self, date: Optional[str] = None, format: str = "csv") -> None:
        """Export data to file"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        self.print_header(f"EXPORT DATA ({date})")

        if format == "csv":
            content = self.tracker.database.export_csv(date)
            filename = f"pulsetrack_{date}.csv"
        else:
            import json
            summary = self.tracker.get_daily_summary(date)
            content = json.dumps(summary, indent=2)
            filename = f"pulsetrack_{date}.json"

        if content:
            with open(filename, "w") as f:
                f.write(content)
            print(f"\n  ✅ Exported to: {filename}")
        else:
            print(f"\n  ❌ Export failed.")

    def cmd_live(self) -> None:
        """Show live real-time monitoring"""
        self.print_header("LIVE MONITORING (Press Ctrl+C to exit)")

        import time

        try:
            while True:
                # Clear screen
                os.system("cls" if sys.platform == "win32" else "clear")

                self.print_header("🔴 LIVE PULSE TRACKING")

                status = self.tracker.get_status()
                state = status["current_state"]
                emoji = STATE_EMOJIS.get(state, "?")

                print(f"\n  State:       {emoji} {state}")
                print(f"  App:         {status['current_app'] or 'None'}")
                print(f"  Duration:    {self.format_seconds(status['state_duration_seconds'])}")
                print(f"  Updated:     {datetime.now().strftime('%H:%M:%S')}")

                # Today's summary
                date_str = datetime.now().strftime("%Y-%m-%d")
                summary = self.tracker.get_daily_summary(date_str)
                state_totals = summary.get("state_totals", {})

                print(f"\n  Today's Stats:")
                for s in ["ACTIVE", "IDLE", "LOCKED", "SLEEP"]:
                    duration = state_totals.get(s, 0)
                    e = STATE_EMOJIS.get(s, "?")
                    print(f"    {e} {s}: {self.format_seconds(duration)}")

                print("\n  (Updates every 2 seconds)")

                time.sleep(2)
        except KeyboardInterrupt:
            print("\n\n  Exiting live monitor.")

    def cmd_help(self) -> None:
        """Show help information"""
        self.print_header("PULSETRACK CLI - HELP")

        print("""
  Available Commands:

    python cli.py status       - Show current instantaneous status
    python cli.py today        - Show today's summary statistics
    python cli.py apps         - Show top applications by duration
    python cli.py timeline     - Show session timeline for today
    python cli.py week         - Show 7-day trend analysis
    python cli.py export [date] [format]  - Export data (date: YYYY-MM-DD, format: csv|json)
    python cli.py live         - Show live real-time monitoring
    python cli.py help         - Show this help message

  Examples:

    python cli.py today
    python cli.py export 2026-09-04 json
    python cli.py week
        """)

    def run(self, command: Optional[str] = None) -> None:
        """Execute a CLI command"""
        if not command or command == "help":
            self.cmd_help()
        elif command == "status":
            self.cmd_status()
        elif command == "today":
            self.cmd_today()
        elif command == "apps":
            self.cmd_apps()
        elif command == "timeline":
            self.cmd_timeline()
        elif command == "week":
            self.cmd_week()
        elif command == "export":
            # Handle export with optional date and format
            date = sys.argv[2] if len(sys.argv) > 2 else None
            format = sys.argv[3] if len(sys.argv) > 3 else "csv"
            self.cmd_export(date, format)
        elif command == "live":
            self.cmd_live()
        else:
            print(f"❌ Unknown command: {command}")
            self.cmd_help()


import os


def main():
    """Main CLI entry point"""
    cli = PulseTrackCLI()
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    cli.run(command)


if __name__ == "__main__":
    main()
