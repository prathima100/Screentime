"""
SQLite Database & Persistence
Thread-safe database operations with WAL mode
"""
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from config import (
    DATABASE_PATH,
    DATABASE_TIMEOUT,
    DATABASE_JOURNAL_MODE,
    STATE_ACTIVE,
    STATE_IDLE,
    STATE_LOCKED,
    STATE_SLEEP,
    EXPORT_DATE_FORMAT,
)


class Database:
    """
    Thread-safe SQLite database handler.
    Manages all persistence and analytical queries.
    """

    def __init__(self):
        self._db_path = DATABASE_PATH
        self._conn = None
        self._lock = threading.Lock()

    def initialize(self) -> None:
        """Create database and schema if not exists"""
        with self._lock:
            try:
                self._conn = sqlite3.connect(
                    self._db_path,
                    timeout=DATABASE_TIMEOUT,
                    check_same_thread=False,
                )
                self._conn.execute(f"PRAGMA journal_mode = {DATABASE_JOURNAL_MODE}")
                self._conn.row_factory = sqlite3.Row

                self._create_schema()
                print(f"✅ Database initialized: {self._db_path}")
            except Exception as e:
                print(f"❌ Database initialization failed: {e}")
                raise

    def close(self) -> None:
        """Close database connection"""
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None

    def _create_schema(self) -> None:
        """Create database tables"""
        cursor = self._conn.cursor()

        # State Sessions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state TEXT NOT NULL CHECK(state IN ('ACTIVE', 'IDLE', 'LOCKED', 'SLEEP')),
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration_seconds REAL NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_state_sessions_date ON state_sessions(date)
        """)

        # App Sessions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                window_title TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration_seconds REAL NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_app_sessions_date ON app_sessions(date)
        """)

        # System Events Table (Audit Log)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_events_date ON system_events(date)
        """)

        self._conn.commit()

    def record_state_session(
        self,
        state: str,
        start_time: datetime,
        end_time: datetime,
        duration_seconds: float,
        commit_only: bool = False,
    ) -> None:
        """Record a state session (ACTIVE, IDLE, LOCKED, SLEEP)"""
        with self._lock:
            try:
                cursor = self._conn.cursor()
                date_str = start_time.strftime(EXPORT_DATE_FORMAT)

                # Handle midnight boundary crossing
                if start_time.date() != end_time.date():
                    # Split into two sessions
                    midnight = datetime.combine(start_time.date(), datetime.max.time())
                    duration1 = (midnight - start_time).total_seconds()
                    duration2 = (end_time - datetime.combine(end_time.date(), datetime.min.time())).total_seconds()

                    cursor.execute(
                        """
                        INSERT INTO state_sessions
                        (state, start_time, end_time, duration_seconds, date)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (state, start_time.isoformat(), midnight.isoformat(), duration1, date_str),
                    )

                    date_str2 = end_time.strftime(EXPORT_DATE_FORMAT)
                    cursor.execute(
                        """
                        INSERT INTO state_sessions
                        (state, start_time, end_time, duration_seconds, date)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (state, datetime.combine(end_time.date(), datetime.min.time()).isoformat(), end_time.isoformat(), duration2, date_str2),
                    )
                else:
                    # Single date session
                    cursor.execute(
                        """
                        INSERT INTO state_sessions
                        (state, start_time, end_time, duration_seconds, date)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (state, start_time.isoformat(), end_time.isoformat(), duration_seconds, date_str),
                    )

                self._conn.commit()
            except Exception as e:
                print(f"Error recording state session: {e}")

    def record_app_session(
        self,
        app_name: str,
        window_title: str,
        start_time: datetime,
        end_time: datetime,
        duration_seconds: float,
        commit_only: bool = False,
    ) -> None:
        """Record an app session"""
        with self._lock:
            try:
                cursor = self._conn.cursor()
                date_str = start_time.strftime(EXPORT_DATE_FORMAT)

                cursor.execute(
                    """
                    INSERT INTO app_sessions
                    (app_name, window_title, start_time, end_time, duration_seconds, date)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (app_name, window_title, start_time.isoformat(), end_time.isoformat(), duration_seconds, date_str),
                )

                self._conn.commit()
            except Exception as e:
                print(f"Error recording app session: {e}")

    def record_system_event(self, event_type: str, details: str = None) -> None:
        """Record a system event (BOOT, STATE_CHANGE, etc.)"""
        with self._lock:
            try:
                cursor = self._conn.cursor()
                now = datetime.now()
                date_str = now.strftime(EXPORT_DATE_FORMAT)

                cursor.execute(
                    """
                    INSERT INTO system_events
                    (event_type, details, timestamp, date)
                    VALUES (?, ?, ?, ?)
                    """,
                    (event_type, details, now.isoformat(), date_str),
                )

                self._conn.commit()
            except Exception as e:
                print(f"Error recording system event: {e}")

    def get_daily_summary(self, date_str: str) -> Dict:
        """Get comprehensive daily summary statistics"""
        with self._lock:
            try:
                cursor = self._conn.cursor()

                # Get state totals
                cursor.execute(
                    """
                    SELECT state, SUM(duration_seconds) as total_duration
                    FROM state_sessions
                    WHERE date = ?
                    GROUP BY state
                    """,
                    (date_str,),
                )

                state_totals = {}
                for row in cursor.fetchall():
                    state_totals[row["state"]] = row["total_duration"] or 0.0

                # Get app totals
                cursor.execute(
                    """
                    SELECT app_name, window_title, SUM(duration_seconds) as total_duration
                    FROM app_sessions
                    WHERE date = ?
                    GROUP BY app_name
                    ORDER BY total_duration DESC
                    """,
                    (date_str,),
                )

                app_totals = []
                for row in cursor.fetchall():
                    app_totals.append({
                        "app_name": row["app_name"],
                        "window_title": row["window_title"],
                        "duration_seconds": row["total_duration"],
                    })

                # Get hourly breakdown
                hourly = self._get_hourly_breakdown(cursor, date_str)

                return {
                    "date": date_str,
                    "state_totals": state_totals,
                    "app_totals": app_totals,
                    "hourly": hourly,
                }
            except Exception as e:
                print(f"Error getting daily summary: {e}")
                return {}

    def _get_hourly_breakdown(self, cursor: sqlite3.Cursor, date_str: str) -> List[Dict]:
        """Get hourly breakdown for a date"""
        try:
            hourly = [{"hour": i, "ACTIVE": 0, "IDLE": 0, "LOCKED": 0, "SLEEP": 0} for i in range(24)]

            cursor.execute(
                """
                SELECT
                    CAST(strftime('%H', start_time) AS INTEGER) as hour,
                    state,
                    SUM(duration_seconds) as duration
                FROM state_sessions
                WHERE date = ?
                GROUP BY hour, state
                """,
                (date_str,),
            )

            for row in cursor.fetchall():
                hour = row["hour"]
                if 0 <= hour < 24:
                    hourly[hour][row["state"]] = row["duration"]

            return hourly
        except Exception as e:
            print(f"Error getting hourly breakdown: {e}")
            return []

    def get_timeline(self, date_str: str) -> List[Dict]:
        """Get chronological timeline of sessions"""
        with self._lock:
            try:
                cursor = self._conn.cursor()
                cursor.execute(
                    """
                    SELECT state, start_time, end_time, duration_seconds
                    FROM state_sessions
                    WHERE date = ?
                    ORDER BY start_time
                    """,
                    (date_str,),
                )

                timeline = []
                for row in cursor.fetchall():
                    timeline.append({
                        "state": row["state"],
                        "start_time": row["start_time"],
                        "end_time": row["end_time"],
                        "duration_seconds": row["duration_seconds"],
                    })

                return timeline
            except Exception as e:
                print(f"Error getting timeline: {e}")
                return []

    def get_app_ranking(self, date_str: str, limit: int = 10) -> List[Dict]:
        """Get top N applications by duration"""
        with self._lock:
            try:
                cursor = self._conn.cursor()
                cursor.execute(
                    """
                    SELECT app_name, window_title, SUM(duration_seconds) as total_duration
                    FROM app_sessions
                    WHERE date = ?
                    GROUP BY app_name
                    ORDER BY total_duration DESC
                    LIMIT ?
                    """,
                    (date_str, limit),
                )

                ranking = []
                for row in cursor.fetchall():
                    ranking.append({
                        "app_name": row["app_name"],
                        "window_title": row["window_title"],
                        "duration_seconds": row["total_duration"],
                    })

                return ranking
            except Exception as e:
                print(f"Error getting app ranking: {e}")
                return []

    def get_trend(self, days: int = 7) -> List[Dict]:
        """Get trend data for last N days"""
        with self._lock:
            try:
                cursor = self._conn.cursor()
                start_date = (datetime.now() - timedelta(days=days)).strftime(EXPORT_DATE_FORMAT)

                cursor.execute(
                    """
                    SELECT
                        date,
                        state,
                        SUM(duration_seconds) as total_duration
                    FROM state_sessions
                    WHERE date >= ?
                    GROUP BY date, state
                    ORDER BY date, state
                    """,
                    (start_date,),
                )

                trend_dict = {}
                for row in cursor.fetchall():
                    date = row["date"]
                    if date not in trend_dict:
                        trend_dict[date] = {
                            "date": date,
                            "ACTIVE": 0,
                            "IDLE": 0,
                            "LOCKED": 0,
                            "SLEEP": 0,
                        }
                    trend_dict[date][row["state"]] = row["total_duration"]

                trend = list(trend_dict.values())
                trend.sort(key=lambda x: x["date"])
                return trend
            except Exception as e:
                print(f"Error getting trend: {e}")
                return []

    def export_csv(self, date_str: str) -> str:
        """Export daily data as CSV"""
        with self._lock:
            try:
                import csv
                from io import StringIO

                output = StringIO()
                writer = csv.writer(output)

                # Header
                writer.writerow(["Type", "Start Time", "End Time", "Duration (sec)", "Duration (formatted)"])

                # State sessions
                cursor = self._conn.cursor()
                cursor.execute(
                    """
                    SELECT state, start_time, end_time, duration_seconds
                    FROM state_sessions
                    WHERE date = ?
                    ORDER BY start_time
                    """,
                    (date_str,),
                )

                for row in cursor.fetchall():
                    duration_sec = row["duration_seconds"]
                    duration_fmt = self._format_seconds(duration_sec)
                    writer.writerow([
                        f"STATE:{row['state']}",
                        row["start_time"],
                        row["end_time"],
                        duration_sec,
                        duration_fmt,
                    ])

                # App sessions
                cursor.execute(
                    """
                    SELECT app_name, start_time, end_time, duration_seconds
                    FROM app_sessions
                    WHERE date = ?
                    ORDER BY start_time
                    """,
                    (date_str,),
                )

                for row in cursor.fetchall():
                    duration_sec = row["duration_seconds"]
                    duration_fmt = self._format_seconds(duration_sec)
                    writer.writerow([
                        f"APP:{row['app_name']}",
                        row["start_time"],
                        row["end_time"],
                        duration_sec,
                        duration_fmt,
                    ])

                return output.getvalue()
            except Exception as e:
                print(f"Error exporting CSV: {e}")
                return ""

    @staticmethod
    def _format_seconds(secs: float) -> str:
        """Format seconds as human-readable string"""
        hours = int(secs // 3600)
        minutes = int((secs % 3600) // 60)
        seconds = int(secs % 60)
        return f"{hours}h {minutes}m {seconds}s"
