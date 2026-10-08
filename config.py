"""
PulseTrack Configuration Hub
Central settings and constants for the Screen Time Monitor
"""

# =====================================================================
# TRACKING PARAMETERS
# =====================================================================
POLL_INTERVAL_SECONDS = 1.0  # Main loop frequency (1 second)
IDLE_THRESHOLD_SECONDS = 60.0  # Seconds of inactivity before IDLE state
HEARTBEAT_GAP_THRESHOLD_SECONDS = 15.0  # Sleep detection gap threshold
FLUSH_INTERVAL_SECONDS = 3.0  # How often to flush data to database

# =====================================================================
# STATE DEFINITIONS
# =====================================================================
STATE_ACTIVE = "ACTIVE"  # PC awake, unlocked, user actively typing/moving
STATE_IDLE = "IDLE"  # PC awake, unlocked, but no input for >= 60 seconds
STATE_LOCKED = "LOCKED"  # Screen locked via Windows Lock Screen
STATE_SLEEP = "SLEEP"  # Computer suspended/hibernating/lid closed

# All valid states
VALID_STATES = [STATE_ACTIVE, STATE_IDLE, STATE_LOCKED, STATE_SLEEP]

# =====================================================================
# STATE COLORS (Hex codes for UI/Terminal)
# =====================================================================
STATE_COLORS = {
    STATE_ACTIVE: "#00D084",  # Green
    STATE_IDLE: "#FFA500",    # Amber
    STATE_LOCKED: "#FF6B6B",  # Red
    STATE_SLEEP: "#9D5DFF",   # Purple
}

STATE_EMOJIS = {
    STATE_ACTIVE: "🟢",
    STATE_IDLE: "🟡",
    STATE_LOCKED: "🔴",
    STATE_SLEEP: "🟣",
}

# =====================================================================
# DATABASE CONFIGURATION
# =====================================================================
DATABASE_PATH = "screen_time.db"
DATABASE_TIMEOUT = 30.0  # SQLite timeout in seconds
DATABASE_JOURNAL_MODE = "WAL"  # Write-Ahead Logging for concurrent access

# =====================================================================
# WEB SERVER CONFIGURATION
# =====================================================================
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
SERVER_LOG_LEVEL = "info"
SERVER_RELOAD = False

# =====================================================================
# WEB DASHBOARD CONFIGURATION
# =====================================================================
DASHBOARD_AUTO_OPEN = True
DASHBOARD_REFRESH_INTERVAL_MS = 2000  # UI polls every 2 seconds

# =====================================================================
# EXPORT & REPORTING CONFIGURATION
# =====================================================================
EXPORT_DATE_FORMAT = "%Y-%m-%d"
EXPORT_TIME_FORMAT = "%H:%M:%S"
TIMEZONE_OFFSET_HOURS = 0  # Adjust for local timezone

# =====================================================================
# LOGGING & DEBUG
# =====================================================================
LOG_LEVEL = "INFO"
DEBUG_MODE = False
LOG_TO_FILE = True
LOG_FILE_PATH = "pulsetrack.log"
