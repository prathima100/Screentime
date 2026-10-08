"""
FastAPI Web Backend & REST API
Serves the web dashboard and provides REST endpoints for data access
"""
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

from config import SERVER_HOST, SERVER_PORT
from tracker import ScreenTimeTracker

app = FastAPI(title="PulseTrack", version="1.0.0")

# Initialize tracker
tracker = ScreenTimeTracker()

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# =====================================================================
# ROOT ENDPOINTS
# =====================================================================
@app.get("/")
async def root():
    """Serve the main dashboard"""
    return FileResponse(os.path.join(static_dir, "index.html"))


# =====================================================================
# STATUS & LIVE DATA
# =====================================================================
@app.get("/api/status")
async def get_status() -> Dict:
    """
    Get current instantaneous status.
    Returns: Current state, active app, durations, and live daily totals.
    """
    status = tracker.get_status()
    date_str = datetime.now().strftime("%Y-%m-%d")
    daily_summary = tracker.get_daily_summary(date_str)

    return {
        **status,
        "daily_summary": daily_summary,
    }


@app.get("/api/summary")
async def get_summary(date: str = Query(None)) -> Dict:
    """
    Get daily summary metrics.
    
    Query Parameters:
    - date: YYYY-MM-DD format (default: today)
    
    Returns: State totals, app totals, and hourly breakdown
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    return tracker.get_daily_summary(date)


@app.get("/api/timeline")
async def get_timeline(date: str = Query(None)) -> Dict:
    """
    Get chronological session timeline.
    
    Query Parameters:
    - date: YYYY-MM-DD format (default: today)
    
    Returns: Ordered list of state sessions with timestamps
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    timeline = tracker.database.get_timeline(date)
    return {"date": date, "sessions": timeline}


@app.get("/api/apps")
async def get_apps(date: str = Query(None), limit: int = Query(10)) -> Dict:
    """
    Get top N applications by usage duration.
    
    Query Parameters:
    - date: YYYY-MM-DD format (default: today)
    - limit: Number of top apps to return (default: 10)
    
    Returns: Ranked list of applications with durations
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    apps = tracker.database.get_app_ranking(date, limit)
    return {"date": date, "apps": apps}


@app.get("/api/hourly")
async def get_hourly(date: str = Query(None)) -> Dict:
    """
    Get 24-hour hourly breakdown.
    
    Query Parameters:
    - date: YYYY-MM-DD format (default: today)
    
    Returns: Array of 24 hourly buckets with state distributions
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    summary = tracker.get_daily_summary(date)
    hourly = summary.get("hourly", [])
    return {"date": date, "hourly": hourly}


@app.get("/api/trend")
async def get_trend(days: int = Query(7)) -> Dict:
    """
    Get multi-day trend analytics.
    
    Query Parameters:
    - days: Number of days to include (default: 7)
    
    Returns: Array of daily summaries for trend analysis
    """
    trend = tracker.database.get_trend(days)
    return {"days": days, "trend": trend}


# =====================================================================
# EXPORT ENDPOINTS
# =====================================================================
@app.get("/api/export")
async def export_data(
    date: str = Query(None),
    format: str = Query("csv")
) -> StreamingResponse:
    """
    Export daily data in CSV or JSON format.
    
    Query Parameters:
    - date: YYYY-MM-DD format (default: today)
    - format: 'csv' or 'json' (default: csv)
    
    Returns: Downloadable file
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    if format == "csv":
        content = tracker.database.export_csv(date)
        filename = f"pulsetrack_{date}.csv"
        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:  # json
        summary = tracker.get_daily_summary(date)
        content = json.dumps(summary, indent=2)
        filename = f"pulsetrack_{date}.json"
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )


# =====================================================================
# HEALTH CHECK
# =====================================================================
@app.get("/api/health")
async def health_check() -> Dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tracker_running": tracker._running,
    }


# =====================================================================
# ERROR HANDLERS
# =====================================================================
@app.exception_handler(Exception)
async def exception_handler(request, exc):
    """Global exception handler"""
    return {
        "error": str(exc),
        "timestamp": datetime.now().isoformat(),
    }


def run_server():
    """Start the FastAPI server"""
    import uvicorn

    print(f"🚀 Starting PulseTrack Web Server on http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"📊 Dashboard: http://{SERVER_HOST}:{SERVER_PORT}/")
    print(f"📡 API: http://{SERVER_HOST}:{SERVER_PORT}/api/")

    uvicorn.run(
        app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()
