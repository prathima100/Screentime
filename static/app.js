/**
 * PulseTrack Dashboard - Frontend Application
 * Real-time state polling, Chart.js visualizations, and dynamic updates
 */

let currentDate = new Date().toISOString().split('T')[0];
let pollInterval = null;
let donutChart = null;
let hourlyChart = null;
let trendChart = null;

const STATE_COLORS = {
    'ACTIVE': '#00d084',
    'IDLE': '#ffa500',
    'LOCKED': '#ff6b6b',
    'SLEEP': '#9d5dff'
};

const STATE_EMOJIS = {
    'ACTIVE': '🟢',
    'IDLE': '🟡',
    'LOCKED': '🔴',
    'SLEEP': '🟣'
};

/**
 * Initialize dashboard and start polling
 */
function initDashboard() {
    // Set date picker to today
    document.getElementById('datePicker').valueAsDate = new Date();

    // Start polling
    pollData();
    pollInterval = setInterval(pollData, 2000);  // Poll every 2 seconds

    console.log("✅ PulseTrack Dashboard initialized");
}

/**
 * Format seconds to human-readable string
 */
function formatSeconds(secs) {
    const hours = Math.floor(secs / 3600);
    const minutes = Math.floor((secs % 3600) / 60);
    const seconds = Math.floor(secs % 60);
    return `${hours}h ${minutes}m ${seconds}s`;
}

/**
 * Poll data from API
 */
async function pollData() {
    try {
        // Get current status (for live info)
        const statusResponse = await fetch('/api/status');
        const status = await statusResponse.json();

        // Update status pill
        updateStatusPill(status);

        // Get daily summary
        const summaryResponse = await fetch(`/api/summary?date=${currentDate}`);
        const summary = await summaryResponse.json();

        // Update metrics
        updateMetrics(summary.state_totals || {});

        // Update charts
        updateCharts(summary);

        // Update timeline
        updateTimeline(currentDate);

        // Update apps
        updateAppsList(currentDate);

        // Update trend
        updateTrend();

        // Update timestamp
        document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();

    } catch (error) {
        console.error('Error polling data:', error);
    }
}

/**
 * Update status pill with current state
 */
function updateStatusPill(status) {
    const pill = document.getElementById('statusPill');
    const state = status.current_state || 'UNKNOWN';
    const emoji = STATE_EMOJIS[state] || '❓';

    pill.innerHTML = `
        <span class="status-icon">${emoji}</span>
        <span class="status-text">${state}</span>
    `;

    // Update color based on state
    const colors = {
        'ACTIVE': 'rgba(0, 208, 132, 0.2)',
        'IDLE': 'rgba(255, 165, 0, 0.2)',
        'LOCKED': 'rgba(255, 107, 107, 0.2)',
        'SLEEP': 'rgba(157, 93, 255, 0.2)'
    };

    pill.style.background = colors[state] || 'rgba(99, 102, 241, 0.2)';
}

/**
 * Update metrics cards
 */
function updateMetrics(stateTotals) {
    const formatters = {
        'ACTIVE': '#activeTime',
        'IDLE': '#idleTime',
        'LOCKED': '#lockedTime',
        'SLEEP': '#sleepTime'
    };

    for (const [state, selector] of Object.entries(formatters)) {
        const duration = stateTotals[state] || 0;
        document.querySelector(selector).textContent = formatSeconds(duration);
    }
}

/**
 * Update all charts
 */
function updateCharts(summary) {
    updateDonutChart(summary.state_totals || {});
    updateHourlyChart(summary.hourly || []);
}

/**
 * Update donut chart for state distribution
 */
function updateDonutChart(stateTotals) {
    const ctx = document.getElementById('donutChart').getContext('2d');

    const labels = ['Active', 'Idle', 'Locked', 'Sleep'];
    const data = [
        stateTotals['ACTIVE'] || 0,
        stateTotals['IDLE'] || 0,
        stateTotals['LOCKED'] || 0,
        stateTotals['SLEEP'] || 0
    ];

    const colors = [
        STATE_COLORS['ACTIVE'],
        STATE_COLORS['IDLE'],
        STATE_COLORS['LOCKED'],
        STATE_COLORS['SLEEP']
    ];

    if (donutChart) {
        donutChart.data.datasets[0].data = data;
        donutChart.update();
    } else {
        donutChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: 'rgba(20, 26, 38, 0.8)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#b0b8c8',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Update hourly stacked bar chart
 */
function updateHourlyChart(hourly) {
    const ctx = document.getElementById('hourlyChart').getContext('2d');

    const hours = Array.from({length: 24}, (_, i) => `${String(i).padStart(2, '0')}:00`);
    const activeData = hourly.map(h => h['ACTIVE'] || 0);
    const idleData = hourly.map(h => h['IDLE'] || 0);
    const lockedData = hourly.map(h => h['LOCKED'] || 0);
    const sleepData = hourly.map(h => h['SLEEP'] || 0);

    if (hourlyChart) {
        hourlyChart.data.datasets[0].data = activeData;
        hourlyChart.data.datasets[1].data = idleData;
        hourlyChart.data.datasets[2].data = lockedData;
        hourlyChart.data.datasets[3].data = sleepData;
        hourlyChart.update();
    } else {
        hourlyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: hours,
                datasets: [
                    {
                        label: 'Active',
                        data: activeData,
                        backgroundColor: STATE_COLORS['ACTIVE']
                    },
                    {
                        label: 'Idle',
                        data: idleData,
                        backgroundColor: STATE_COLORS['IDLE']
                    },
                    {
                        label: 'Locked',
                        data: lockedData,
                        backgroundColor: STATE_COLORS['LOCKED']
                    },
                    {
                        label: 'Sleep',
                        data: sleepData,
                        backgroundColor: STATE_COLORS['SLEEP']
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: {
                        stacked: true,
                        ticks: { color: '#b0b8c8' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    y: {
                        stacked: true,
                        ticks: { color: '#b0b8c8' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#b0b8c8', font: { size: 12 } }
                    }
                }
            }
        });
    }
}

/**
 * Update timeline
 */
async function updateTimeline(date) {
    try {
        const response = await fetch(`/api/timeline?date=${date}`);
        const data = await response.json();

        const container = document.getElementById('timeline');
        const sessions = data.sessions || [];

        if (sessions.length === 0) {
            container.innerHTML = '<p class="loading">No sessions recorded for this date</p>';
            return;
        }

        container.innerHTML = sessions.map(session => {
            const startTime = new Date(session.start_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
            const endTime = new Date(session.end_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
            const duration = formatSeconds(session.duration_seconds);
            const emoji = STATE_EMOJIS[session.state] || '❓';

            return `
                <div class="timeline-item" style="border-left-color: ${STATE_COLORS[session.state]}">
                    <div>${emoji} <strong>${session.state}</strong></div>
                    <div class="timeline-time">${startTime} → ${endTime}</div>
                    <div class="timeline-duration">${duration}</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error updating timeline:', error);
    }
}

/**
 * Update applications list
 */
async function updateAppsList(date) {
    try {
        const response = await fetch(`/api/apps?date=${date}&limit=15`);
        const data = await response.json();

        const container = document.getElementById('appsList');
        const apps = data.apps || [];

        if (apps.length === 0) {
            container.innerHTML = '<p class="loading">No application data recorded</p>';
            return;
        }

        container.innerHTML = apps.map((app, index) => `
            <div class="app-item">
                <div class="app-rank">#${index + 1}</div>
                <div class="app-info">
                    <div class="app-name">${app.app_name}</div>
                    <div class="app-title">${app.window_title || 'Unknown'}</div>
                </div>
                <div class="app-duration">${formatSeconds(app.duration_seconds)}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error updating apps list:', error);
    }
}

/**
 * Update trend chart
 */
async function updateTrend() {
    try {
        const response = await fetch('/api/trend?days=7');
        const data = await response.json();
        const trend = data.trend || [];

        if (trend.length === 0) return;

        const ctx = document.getElementById('trendChart').getContext('2d');
        const labels = trend.map(d => d.date);
        const activeData = trend.map(d => d['ACTIVE'] || 0);
        const idleData = trend.map(d => d['IDLE'] || 0);
        const lockedData = trend.map(d => d['LOCKED'] || 0);
        const sleepData = trend.map(d => d['SLEEP'] || 0);

        if (trendChart) {
            trendChart.data.labels = labels;
            trendChart.data.datasets[0].data = activeData;
            trendChart.data.datasets[1].data = idleData;
            trendChart.data.datasets[2].data = lockedData;
            trendChart.data.datasets[3].data = sleepData;
            trendChart.update();
        } else {
            trendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Active',
                            data: activeData,
                            borderColor: STATE_COLORS['ACTIVE'],
                            backgroundColor: STATE_COLORS['ACTIVE'] + '20',
                            tension: 0.4
                        },
                        {
                            label: 'Idle',
                            data: idleData,
                            borderColor: STATE_COLORS['IDLE'],
                            backgroundColor: STATE_COLORS['IDLE'] + '20',
                            tension: 0.4
                        },
                        {
                            label: 'Locked',
                            data: lockedData,
                            borderColor: STATE_COLORS['LOCKED'],
                            backgroundColor: STATE_COLORS['LOCKED'] + '20',
                            tension: 0.4
                        },
                        {
                            label: 'Sleep',
                            data: sleepData,
                            borderColor: STATE_COLORS['SLEEP'],
                            backgroundColor: STATE_COLORS['SLEEP'] + '20',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            ticks: { color: '#b0b8c8' },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        },
                        x: {
                            ticks: { color: '#b0b8c8' },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: { color: '#b0b8c8', font: { size: 12 } }
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error updating trend:', error);
    }
}

/**
 * Set date and reload dashboard
 */
function setDate(period) {
    const today = new Date();
    let targetDate = new Date(today);

    if (period === 'yesterday') {
        targetDate.setDate(today.getDate() - 1);
    }

    currentDate = targetDate.toISOString().split('T')[0];
    document.getElementById('datePicker').valueAsDate = targetDate;
    pollData();
}

/**
 * Handle manual date picker change
 */
function handleDateChange() {
    const selected = document.getElementById('datePicker').value;
    if (selected) {
        currentDate = selected;
        pollData();
    }
}

/**
 * Export data as CSV or JSON
 */
async function exportData(format) {
    try {
        const response = await fetch(`/api/export?date=${currentDate}&format=${format}`);
        const blob = await response.blob();

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pulsetrack_${currentDate}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Error exporting data:', error);
        alert('Failed to export data');
    }
}

// Initialize dashboard when page loads
window.addEventListener('DOMContentLoaded', initDashboard);
