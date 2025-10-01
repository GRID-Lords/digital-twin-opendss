"""
Database module for storing digital twin metrics and historical data.
Uses SQLite for simplicity - can be upgraded to TimescaleDB or InfluxDB for production.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
from contextlib import contextmanager

class DigitalTwinDatabase:
    def __init__(self, db_path: str = "digital_twin.db"):
        self.db_path = db_path
        self.local = threading.local()
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Thread-safe database connection."""
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.local.connection.row_factory = sqlite3.Row
        try:
            yield self.local.connection
        except Exception as e:
            self.local.connection.rollback()
            raise e
        else:
            self.local.connection.commit()

    def init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Metrics table for time-series data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_power REAL,
                    efficiency REAL,
                    power_factor REAL,
                    frequency REAL,
                    total_load REAL,
                    generation REAL,
                    losses REAL,
                    data JSON
                )
            ''')

            # Assets table for asset states over time
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS asset_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    asset_id TEXT,
                    asset_type TEXT,
                    status TEXT,
                    health_score REAL,
                    voltage REAL,
                    current REAL,
                    power REAL,
                    temperature REAL,
                    data JSON
                )
            ''')

            # Alerts/Events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alert_type TEXT,
                    severity TEXT,
                    asset_id TEXT,
                    message TEXT,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    resolved BOOLEAN DEFAULT FALSE,
                    data JSON
                )
            ''')

            # AI Analysis results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    analysis_type TEXT,
                    asset_id TEXT,
                    anomaly_score REAL,
                    prediction TEXT,
                    recommendation TEXT,
                    data JSON
                )
            ''')

            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_asset_states_timestamp ON asset_states(timestamp DESC, asset_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC, severity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_analysis_timestamp ON ai_analysis(timestamp DESC, analysis_type)')

    def store_metrics(self, metrics: Dict[str, Any]):
        """Store system metrics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO metrics (
                    total_power, efficiency, power_factor, frequency,
                    total_load, generation, losses, data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.get('total_power', 0),
                metrics.get('efficiency', 0),
                metrics.get('power_factor', 0),
                metrics.get('frequency', 50),
                metrics.get('total_load', 0),
                metrics.get('generation', 0),
                metrics.get('losses', 0),
                json.dumps(metrics)
            ))
            return cursor.lastrowid

    def store_asset_state(self, asset_id: str, asset_data: Dict[str, Any]):
        """Store asset state snapshot."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO asset_states (
                    asset_id, asset_type, status, health_score,
                    voltage, current, power, temperature, data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                asset_id,
                asset_data.get('type', 'unknown'),
                asset_data.get('status', 'unknown'),
                asset_data.get('health_score', 100),
                asset_data.get('voltage', 0),
                asset_data.get('current', 0),
                asset_data.get('power', 0),
                asset_data.get('temperature', 0),
                json.dumps(asset_data)
            ))
            return cursor.lastrowid

    def store_alert(self, alert_type: str, severity: str, asset_id: str, message: str, data: Dict = None):
        """Store an alert/event."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (alert_type, severity, asset_id, message, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (alert_type, severity, asset_id, message, json.dumps(data or {})))
            return cursor.lastrowid

    def store_ai_analysis(self, analysis_type: str, asset_id: str, results: Dict[str, Any]):
        """Store AI analysis results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ai_analysis (
                    analysis_type, asset_id, anomaly_score,
                    prediction, recommendation, data
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                analysis_type,
                asset_id,
                results.get('anomaly_score', 0),
                results.get('prediction', ''),
                results.get('recommendation', ''),
                json.dumps(results)
            ))
            return cursor.lastrowid

    def get_metrics_history(self, hours: int = 24, limit: int = 1000) -> List[Dict]:
        """Get historical metrics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM metrics
                WHERE timestamp >= datetime('now', ? || ' hours')
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f'-{hours}', limit))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_asset_history(self, asset_id: str, hours: int = 24) -> List[Dict]:
        """Get asset state history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM asset_states
                WHERE asset_id = ? AND timestamp >= datetime('now', ? || ' hours')
                ORDER BY timestamp DESC
            ''', (asset_id, f'-{hours}'))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_recent_alerts(self, limit: int = 50, unresolved_only: bool = False) -> List[Dict]:
        """Get recent alerts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT * FROM alerts
                WHERE 1=1
            '''
            params = []

            if unresolved_only:
                query += ' AND resolved = FALSE'

            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def acknowledge_alert(self, alert_id: int):
        """Mark an alert as acknowledged."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alerts SET acknowledged = TRUE
                WHERE id = ?
            ''', (alert_id,))

    def resolve_alert(self, alert_id: int):
        """Mark an alert as resolved."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alerts SET resolved = TRUE
                WHERE id = ?
            ''', (alert_id,))

    def get_aggregated_metrics(self, hours: int = 24, interval_minutes: int = 60) -> List[Dict]:
        """Get aggregated metrics over time intervals."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                    AVG(total_power) as avg_power,
                    AVG(efficiency) as avg_efficiency,
                    AVG(power_factor) as avg_power_factor,
                    MAX(total_power) as max_power,
                    MIN(total_power) as min_power,
                    COUNT(*) as sample_count
                FROM metrics
                WHERE timestamp >= datetime('now', ? || ' hours')
                GROUP BY hour
                ORDER BY hour DESC
            ''', (f'-{hours}',))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to prevent database growth."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = f'-{days_to_keep} days'

            # Clean up old metrics
            cursor.execute('''
                DELETE FROM metrics
                WHERE timestamp < datetime('now', ?)
            ''', (cutoff_date,))

            # Clean up old asset states
            cursor.execute('''
                DELETE FROM asset_states
                WHERE timestamp < datetime('now', ?)
            ''', (cutoff_date,))

            # Clean up old resolved alerts (keep unresolved ones)
            cursor.execute('''
                DELETE FROM alerts
                WHERE resolved = TRUE AND timestamp < datetime('now', ?)
            ''', (cutoff_date,))

            # Clean up old AI analysis
            cursor.execute('''
                DELETE FROM ai_analysis
                WHERE timestamp < datetime('now', ?)
            ''', (cutoff_date,))

            # Vacuum to reclaim space
            cursor.execute('VACUUM')

# Create global database instance
db = DigitalTwinDatabase()