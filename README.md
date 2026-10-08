# 🔴 PulseTrack - Screen Time Monitor v1.0.0

Real-time screen time and activity tracking for Windows, macOS, and Linux with a modern web dashboard.

## 🎯 Overview

**PulseTrack** monitors your desktop activity across **4 distinct states**:

- 🟢 **ACTIVE** - PC awake, unlocked, user actively typing or moving mouse
- 🟡 **IDLE** - PC awake & unlocked, but no interaction for ≥60 seconds  
- 🔴 **LOCKED** - Screen locked via Windows Lock Screen (or equivalent)
- 🟣 **SLEEP** - Computer suspended/hibernating/lid closed

For **ACTIVE** sessions, PulseTrack records the foreground application and window title, providing detailed application usage analytics.

## 📊 Features

✅ **Real-Time Monitoring** - 1-second polling cycle captures every state change  
✅ **Cross-Platform** - Native implementations for Windows, macOS, Linux  
✅ **SQLite Database** - Persistent storage with WAL mode for reliability  
✅ **Modern Web Dashboard** - Glassmorphism dark theme with real-time updates  
✅ **REST API** - Full-featured API for data access and exports  
✅ **CLI Tool** - Interactive command-line interface for power users  
✅ **Export Formats** - CSV and JSON data export  
✅ **Trend Analytics** - 7+ day historical trend analysis  
✅ **Application Ranking** - Top apps by usage duration  
✅ **Hourly Breakdown** - 24-hour hourly state distribution  

## 🚀 Quick Start

### Installation

```bash
# Clone or download the project
cd C:\arohak projects\ScreenTime

# Install Python dependencies
pip install -r requirements.txt

# Windows: Install pywin32 post-install
python -m pip install pywin32
python -m pip install --upgrade pywin32
```

### Run the Application

**Full Experience (Tracker + Web Dashboard):**
```bash
python main.py
```
This will:
1. Start the background tracker engine
2. Initialize the SQLite database
3. Launch the FastAPI web server
4. Automatically open the dashboard in your browser

**CLI Mode Only:**
```bash
python main.py --cli
```

**Server Without Browser:**
```bash
python main.py --server-only
```

## 📖 Usage Examples

### Web Dashboard
Open [http://localhost:8000](http://localhost:8000) to access:
- **Live Status Pill** - Current state with emoji indicator
- **4 Metric Cards** - Daily totals for each state
- **State Distribution Chart** - Donut chart of today's breakdown
- **24-Hour Timeline** - Hourly stacked bar chart
- **Application Ranking** - Top 15 apps by duration
- **Session Timeline** - Chronological log of all sessions
- **7-Day Trend** - Historical data visualization

### CLI Commands

```bash
# Show current status
python cli.py status

# Show today's summary
python cli.py today

# List top applications
python cli.py apps

# Show session timeline
python cli.py timeline

# Show 7-day trend
python cli.py week

# Export to CSV/JSON (default: today)
python cli.py export 2026-09-04 csv
python cli.py export 2026-09-04 json

# Live real-time monitoring
python cli.py live

# Show help
python cli.py help
```

### REST API Endpoints

```bash
# Current status
curl http://localhost:8000/api/status

# Daily summary
curl http://localhost:8000/api/summary?date=2026-09-04

# Timeline
curl http://localhost:8000/api/timeline?date=2026-09-04

# Top applications
curl http://localhost:8000/api/apps?date=2026-09-04&limit=10

# Hourly breakdown
curl http://localhost:8000/api/hourly?date=2026-09-04

# 7-day trend
curl http://localhost:8000/api/trend?days=7

# Export data
curl http://localhost:8000/api/export?date=2026-09-04&format=csv > data.csv
curl http://localhost:8000/api/export?date=2026-09-04&format=json > data.json

# Health check
curl http://localhost:8000/api/health
```

## 📁 Project Structure

```
PulseTrack/
├── config.py                 # Central configuration & constants
├── tracker.py               # Core tracking engine & state machine
├── database.py              # SQLite persistence & analytics
├── server.py                # FastAPI REST API backend
├── cli.py                   # Command-line interface
├── main.py                  # Application orchestrator & entry point
├── test_monitor.py          # Comprehensive test suite
│
├── platforms/               # Cross-platform hardware adapters
│   ├── base.py             # Abstract base class interface
│   ├── windows.py          # Windows (Win32 API) implementation
│   ├── macos.py            # macOS (CoreGraphics) implementation
│   ├── linux.py            # Linux (X11/D-Bus) implementation
│   └── __init__.py         # Platform factory function
│
├── static/                  # Web dashboard frontend
│   ├── index.html          # HTML5 structure
│   ├── style.css           # Dark glassmorphism styling
│   └── app.js              # Real-time polling & Chart.js visualization
│
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Configuration

Edit `config.py` to customize:

```python
POLL_INTERVAL_SECONDS = 1.0           # Tracking frequency
IDLE_THRESHOLD_SECONDS = 60.0         # Seconds before IDLE state
HEARTBEAT_GAP_THRESHOLD_SECONDS = 15.0 # Sleep detection gap
FLUSH_INTERVAL_SECONDS = 3.0          # Database flush interval

DATABASE_PATH = "screen_time.db"       # SQLite file location
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
DASHBOARD_REFRESH_INTERVAL_MS = 2000   # UI poll interval
```

## 🏗️ Architecture

### 1. **Platform Abstraction Layer** (`platforms/`)
- Shields core logic from OS differences
- Factory pattern for dynamic adapter selection
- Implements lock/unlock/sleep/wake detection
- Captures idle time and active window info

### 2. **Tracking Engine** (`tracker.py`)
- Singleton pattern ensuring single instance
- 1-second polling loop with state machine
- Heartbeat gap detection for unannounced sleep
- Live flushing to database every 3 seconds
- Thread-safe status snapshots for API

### 3. **Database Layer** (`database.py`)
- SQLite with WAL (Write-Ahead Logging) mode
- Thread-safe connection pooling
- Automatic midnight boundary splitting
- 3 primary tables:
  - `state_sessions` - State transitions & durations
  - `app_sessions` - Application usage per session
  - `system_events` - Audit log of all events
- Advanced analytics queries (daily, hourly, trending)

### 4. **Web Backend** (`server.py`)
- FastAPI for high-performance REST API
- Real-time status polling (2-second intervals)
- CSV/JSON export capabilities
- Static file serving for dashboard

### 5. **Web Dashboard** (`static/`)
- Responsive dark glassmorphism design
- Real-time Chart.js visualizations
- 4 state metric cards
- Live status indicator with emoji
- Timeline and application ranking tables
- Date picker and quick navigation

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_monitor.py
```

Tests include:
- Database operations
- Tracker state machine logic
- Configuration validation
- Platform adapter availability

## 🛠️ Troubleshooting

**Issue: `ModuleNotFoundError: No module named 'win32api'`**
```bash
pip install pywin32
python -m pip install --upgrade pywin32
```

**Issue: Database locked or corrupted**
```bash
rm screen_time.db  # Remove and let it reinitialize
```

**Issue: Dashboard not responding**
- Check if port 8000 is already in use
- Try: `python main.py --server-only --no-browser` to diagnose

**Issue: No data appearing after startup**
- Wait 30 seconds for first data to populate
- Lock/unlock your screen to trigger state change
- Check `pulsetrack.log` for errors

## 📊 Data Privacy

✅ **All data stored locally** - No cloud sync  
✅ **No external API calls** - Fully offline capable  
✅ **Transparent tracking** - See exactly what's recorded  
✅ **User control** - Delete database anytime  

## 📝 Development

### Adding a New Command to CLI
Edit `cli.py` and add a method `cmd_your_command()`, then update `run()`.

### Extending the API
Edit `server.py` and add new endpoint routes with `@app.get()` or `@app.post()`.

### Custom Platform Support
Implement a new adapter in `platforms/your_os.py` inheriting from `PlatformAdapter`.

## 📄 License

MIT License - Free for personal and commercial use.

## 🎓 Credits

**Built with:**
- FastAPI (web framework)
- SQLite (database)
- Chart.js (visualizations)
- pywin32 (Windows APIs)
- AppKit (macOS APIs)
- D-Bus (Linux APIs)

---

**Need help?** Check the inline code documentation or run `python cli.py help`.

**Want to contribute?** Star the repo and submit pull requests!

🔴 **PulseTrack v1.0.0** - *Know where your time goes*
