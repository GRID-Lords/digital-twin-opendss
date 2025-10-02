"""
Time-series Database for Historical Data Storage
Implements efficient storage and retrieval of substation metrics
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from contextlib import contextmanager
import numpy as np

logger = logging.getLogger(__name__)

class TimeSeriesDB:
    """Manages time-series data storage with automatic aggregation"""

    def __init__(self, db_path: str = "timeseries.db"):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Raw metrics table (high-resolution data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics_raw (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    asset_id TEXT,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics_raw(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_asset_metric ON metrics_raw(asset_id, metric_name, timestamp)")

            # Hourly aggregated data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics_hourly (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hour_timestamp DATETIME NOT NULL,
                    asset_id TEXT,
                    metric_name TEXT NOT NULL,
                    min_value REAL,
                    max_value REAL,
                    avg_value REAL,
                    sum_value REAL,
                    count INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(hour_timestamp, asset_id, metric_name)
                )
            """)

            # Daily aggregated data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics_daily (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    asset_id TEXT,
                    metric_name TEXT NOT NULL,
                    min_value REAL,
                    max_value REAL,
                    avg_value REAL,
                    sum_value REAL,
                    count INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, asset_id, metric_name)
                )
            """)

            # System events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT,
                    asset_id TEXT,
                    description TEXT,
                    metadata TEXT,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_at DATETIME,
                    acknowledged_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_timestamp ON system_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON system_events(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_asset ON system_events(asset_id)")

            # Asset health history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_health_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    asset_id TEXT NOT NULL,
                    health_score REAL,
                    temperature REAL,
                    load_percent REAL,
                    efficiency REAL,
                    status TEXT,
                    alarms TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_health_timestamp ON asset_health_history(asset_id, timestamp)")

            # Power flow history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS power_flow_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    active_power REAL,
                    reactive_power REAL,
                    apparent_power REAL,
                    power_factor REAL,
                    frequency REAL,
                    voltage_400kv REAL,
                    voltage_220kv REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_power_timestamp ON power_flow_history(timestamp)")

            conn.commit()
            logger.info("Time-series database initialized")

    def insert_metric(self, metric_name: str, value: float,
                     asset_id: Optional[str] = None,
                     timestamp: Optional[datetime] = None,
                     metadata: Optional[Dict] = None):
        """Insert a single metric value"""
        if timestamp is None:
            timestamp = datetime.now()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO metrics_raw (timestamp, asset_id, metric_name, value, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, asset_id, metric_name, value,
                  json.dumps(metadata) if metadata else None))
            conn.commit()

    def insert_bulk_metrics(self, metrics: List[Dict[str, Any]]):
        """Insert multiple metrics efficiently"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            for metric in metrics:
                cursor.execute("""
                    INSERT INTO metrics_raw (timestamp, asset_id, metric_name, value, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    metric.get('timestamp', datetime.now()),
                    metric.get('asset_id'),
                    metric['metric_name'],
                    metric['value'],
                    json.dumps(metric.get('metadata')) if metric.get('metadata') else None
                ))

            conn.commit()

    def insert_power_flow(self, data: Dict[str, float], timestamp: Optional[datetime] = None):
        """Insert power flow data"""
        if timestamp is None:
            timestamp = datetime.now()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO power_flow_history
                (timestamp, active_power, reactive_power, apparent_power,
                 power_factor, frequency, voltage_400kv, voltage_220kv)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                data.get('active_power'),
                data.get('reactive_power'),
                data.get('apparent_power'),
                data.get('power_factor'),
                data.get('frequency'),
                data.get('voltage_400kv'),
                data.get('voltage_220kv')
            ))
            conn.commit()

    def insert_asset_health(self, asset_id: str, health_data: Dict[str, Any],
                           timestamp: Optional[datetime] = None):
        """Insert asset health record"""
        if timestamp is None:
            timestamp = datetime.now()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO asset_health_history
                (timestamp, asset_id, health_score, temperature, load_percent,
                 efficiency, status, alarms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                asset_id,
                health_data.get('health_score'),
                health_data.get('temperature'),
                health_data.get('load_percent'),
                health_data.get('efficiency'),
                health_data.get('status'),
                json.dumps(health_data.get('alarms', []))
            ))
            conn.commit()

    def insert_event(self, event_type: str, description: str,
                    severity: str = "info",
                    asset_id: Optional[str] = None,
                    metadata: Optional[Dict] = None,
                    timestamp: Optional[datetime] = None):
        """Insert system event"""
        if timestamp is None:
            timestamp = datetime.now()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_events
                (timestamp, event_type, severity, asset_id, description, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                event_type,
                severity,
                asset_id,
                description,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()

    def get_metrics(self, metric_name: str,
                   start_time: datetime,
                   end_time: datetime,
                   asset_id: Optional[str] = None,
                   resolution: str = "raw") -> List[Dict]:
        """Retrieve metrics for a time range"""

        with self.get_connection() as conn:
            cursor = conn.cursor()

            if resolution == "raw":
                query = """
                    SELECT timestamp, value, metadata
                    FROM metrics_raw
                    WHERE metric_name = ?
                    AND timestamp BETWEEN ? AND ?
                """
                params = [metric_name, start_time, end_time]

                if asset_id:
                    query += " AND asset_id = ?"
                    params.append(asset_id)

                query += " ORDER BY timestamp"

            elif resolution == "hourly":
                query = """
                    SELECT hour_timestamp as timestamp,
                           min_value, max_value, avg_value, sum_value, count
                    FROM metrics_hourly
                    WHERE metric_name = ?
                    AND hour_timestamp BETWEEN ? AND ?
                """
                params = [metric_name, start_time, end_time]

                if asset_id:
                    query += " AND asset_id = ?"
                    params.append(asset_id)

                query += " ORDER BY hour_timestamp"

            elif resolution == "daily":
                query = """
                    SELECT date as timestamp,
                           min_value, max_value, avg_value, sum_value, count
                    FROM metrics_daily
                    WHERE metric_name = ?
                    AND date BETWEEN ? AND ?
                """
                params = [metric_name, start_time.date(), end_time.date()]

                if asset_id:
                    query += " AND asset_id = ?"
                    params.append(asset_id)

                query += " ORDER BY date"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def get_power_flow_history(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Get power flow history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM power_flow_history
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """, (start_time, end_time))

            return [dict(row) for row in cursor.fetchall()]

    def get_asset_health_history(self, asset_id: str,
                                 start_time: datetime,
                                 end_time: datetime) -> List[Dict]:
        """Get asset health history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM asset_health_history
                WHERE asset_id = ?
                AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """, (asset_id, start_time, end_time))

            rows = cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                if result.get('alarms'):
                    result['alarms'] = json.loads(result['alarms'])
                results.append(result)

            return results

    def get_events(self, start_time: datetime,
                  end_time: datetime,
                  event_type: Optional[str] = None,
                  asset_id: Optional[str] = None) -> List[Dict]:
        """Get system events"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT * FROM system_events
                WHERE timestamp BETWEEN ? AND ?
            """
            params = [start_time, end_time]

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            if asset_id:
                query += " AND asset_id = ?"
                params.append(asset_id)

            query += " ORDER BY timestamp DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                result = dict(row)
                if result.get('metadata'):
                    result['metadata'] = json.loads(result['metadata'])
                results.append(result)

            return results

    def aggregate_hourly(self, up_to_timestamp: Optional[datetime] = None):
        """Aggregate raw metrics to hourly"""
        if up_to_timestamp is None:
            up_to_timestamp = datetime.now()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Find last aggregation time
            cursor.execute("""
                SELECT MAX(hour_timestamp) FROM metrics_hourly
            """)
            last_aggregation = cursor.fetchone()[0]

            if last_aggregation:
                start_time = datetime.fromisoformat(last_aggregation) + timedelta(hours=1)
            else:
                # Start from oldest raw data
                cursor.execute("SELECT MIN(timestamp) FROM metrics_raw")
                start_time = cursor.fetchone()[0]
                if start_time:
                    start_time = datetime.fromisoformat(start_time).replace(minute=0, second=0, microsecond=0)

            if not start_time:
                return

            # Aggregate hour by hour
            current_hour = start_time
            while current_hour < up_to_timestamp:
                next_hour = current_hour + timedelta(hours=1)

                cursor.execute("""
                    INSERT OR REPLACE INTO metrics_hourly
                    (hour_timestamp, asset_id, metric_name, min_value, max_value,
                     avg_value, sum_value, count)
                    SELECT
                        ? as hour_timestamp,
                        asset_id,
                        metric_name,
                        MIN(value) as min_value,
                        MAX(value) as max_value,
                        AVG(value) as avg_value,
                        SUM(value) as sum_value,
                        COUNT(*) as count
                    FROM metrics_raw
                    WHERE timestamp >= ? AND timestamp < ?
                    GROUP BY asset_id, metric_name
                """, (current_hour, current_hour, next_hour))

                current_hour = next_hour

            conn.commit()
            logger.info(f"Aggregated hourly metrics up to {up_to_timestamp}")

    def cleanup_old_data(self, retention_days: int = 30):
        """Clean up old raw data while keeping aggregated data"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Delete old raw metrics
            cursor.execute("""
                DELETE FROM metrics_raw
                WHERE timestamp < ?
            """, (cutoff_date,))

            deleted_metrics = cursor.rowcount

            # Delete old events (keep important ones)
            cursor.execute("""
                DELETE FROM system_events
                WHERE timestamp < ?
                AND severity = 'info'
            """, (cutoff_date,))

            deleted_events = cursor.rowcount

            conn.commit()

            logger.info(f"Cleaned up {deleted_metrics} old metrics and {deleted_events} old events")

# Global instance
timeseries_db = TimeSeriesDB()