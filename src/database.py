"""
Database module for storing digital twin metrics and historical data.
Uses PostgreSQL for production-grade storage with SQLite fallback.
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

from src.config import Config

logger = logging.getLogger(__name__)

class DigitalTwinDatabase:
    def __init__(self, db_path: str = "digital_twin.db"):
        self.db_path = db_path
        self.local = threading.local()
        self.use_postgres = POSTGRES_AVAILABLE and Config.DB_TYPE == 'postgresql'

        if self.use_postgres:
            logger.info("Using PostgreSQL database")
            self.conn_params = {
                'host': Config.DB_HOST,
                'port': Config.DB_PORT,
                'database': Config.DB_NAME,
                'user': Config.DB_USER,
                'password': Config.DB_PASSWORD
            }
        else:
            logger.info(f"Using SQLite database: {db_path}")

        self.init_database()

    @property
    def placeholder(self):
        """Get the appropriate SQL placeholder for the current database"""
        return '%s' if self.use_postgres else '?'

    @contextmanager
    def get_connection(self):
        """Thread-safe database connection."""
        if not hasattr(self.local, 'connection') or self.local.connection is None:
            if self.use_postgres:
                try:
                    self.local.connection = psycopg2.connect(**self.conn_params, cursor_factory=RealDictCursor)
                except Exception as e:
                    logger.error(f"PostgreSQL connection failed: {e}, falling back to SQLite")
                    self.use_postgres = False
                    self.local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
                    self.local.connection.row_factory = sqlite3.Row
            else:
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
        """Initialize database tables - compatible with both PostgreSQL and SQLite."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # SQL syntax that works for both PostgreSQL and SQLite
            if self.use_postgres:
                # PostgreSQL syntax
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metrics (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_power REAL,
                        efficiency REAL,
                        power_factor REAL,
                        frequency REAL,
                        total_load REAL,
                        generation REAL,
                        losses REAL,
                        data JSONB
                    )
                ''')
            else:
                # SQLite syntax
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
            if self.use_postgres:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS asset_states (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        asset_id TEXT,
                        asset_type TEXT,
                        status TEXT,
                        health_score REAL,
                        voltage REAL,
                        current REAL,
                        power REAL,
                        temperature REAL,
                        data JSONB
                    )
                ''')
            else:
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
            if self.use_postgres:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        alert_type TEXT,
                        severity TEXT,
                        asset_id TEXT,
                        message TEXT,
                        acknowledged BOOLEAN DEFAULT FALSE,
                        resolved BOOLEAN DEFAULT FALSE,
                        assignee TEXT,
                        status TEXT DEFAULT 'pending',
                        data JSONB
                    )
                ''')
            else:
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
                        assignee TEXT,
                        status TEXT DEFAULT 'pending',
                        data JSON
                    )
                ''')

            # AI Analysis results table
            if self.use_postgres:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_analysis (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        analysis_type TEXT,
                        asset_id TEXT,
                        anomaly_score REAL,
                        prediction TEXT,
                        recommendation TEXT,
                        data JSONB
                    )
                ''')
            else:
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

            # Threshold Configuration table for user-defined alert thresholds
            if self.use_postgres:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS threshold_config (
                        id SERIAL PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        component_id TEXT NOT NULL,
                        component_name TEXT NOT NULL,
                        component_type TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_unit TEXT,
                        threshold_min REAL,
                        threshold_max REAL,
                        severity TEXT DEFAULT 'medium',
                        enabled BOOLEAN DEFAULT TRUE,
                        description TEXT,
                        UNIQUE(component_id, metric_name)
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS threshold_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        component_id TEXT NOT NULL,
                        component_name TEXT NOT NULL,
                        component_type TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_unit TEXT,
                        threshold_min REAL,
                        threshold_max REAL,
                        severity TEXT DEFAULT 'medium',
                        enabled BOOLEAN DEFAULT TRUE,
                        description TEXT,
                        UNIQUE(component_id, metric_name)
                    )
                ''')

            # DSS File Versions table for versioning DSS files
            if self.use_postgres:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dss_file_versions (
                        id SERIAL PRIMARY KEY,
                        version_number INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT DEFAULT 'system',
                        description TEXT,
                        is_active BOOLEAN DEFAULT FALSE,
                        file_hash TEXT,
                        component_count INTEGER,
                        validation_status TEXT DEFAULT 'valid',
                        validation_errors TEXT
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dss_file_versions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version_number INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT DEFAULT 'system',
                        description TEXT,
                        is_active BOOLEAN DEFAULT FALSE,
                        file_hash TEXT,
                        component_count INTEGER,
                        validation_status TEXT DEFAULT 'valid',
                        validation_errors TEXT
                    )
                ''')

            # Migrate existing alerts table to add new columns if they don't exist
            try:
                # Check if assignee column exists
                cursor.execute("PRAGMA table_info(alerts)" if not self.use_postgres else
                              "SELECT column_name FROM information_schema.columns WHERE table_name='alerts'")
                columns = cursor.fetchall()
                column_names = [col[1] if not self.use_postgres else col[0] for col in columns]

                if 'assignee' not in column_names:
                    logger.info("Adding assignee column to alerts table")
                    cursor.execute('ALTER TABLE alerts ADD COLUMN assignee TEXT')

                if 'status' not in column_names:
                    logger.info("Adding status column to alerts table")
                    cursor.execute("ALTER TABLE alerts ADD COLUMN status TEXT DEFAULT 'pending'")
            except Exception as e:
                logger.warning(f"Could not migrate alerts table (table may not exist yet): {e}")

            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_asset_states_timestamp ON asset_states(timestamp DESC, asset_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC, severity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_analysis_timestamp ON ai_analysis(timestamp DESC, analysis_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_threshold_config_component ON threshold_config(component_id, enabled)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dss_versions_active ON dss_file_versions(is_active, created_at DESC)')

    def store_metrics(self, metrics: Dict[str, Any]):
        """Store system metrics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            ph = self.placeholder
            if self.use_postgres:
                cursor.execute(f'''
                    INSERT INTO metrics (
                        total_power, efficiency, power_factor, frequency,
                        total_load, generation, losses, data
                    ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    RETURNING id
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
                result = cursor.fetchone()
                return result[0] if result else None
            else:
                cursor.execute(f'''
                    INSERT INTO metrics (
                        total_power, efficiency, power_factor, frequency,
                        total_load, generation, losses, data
                    ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
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
            ph = self.placeholder

            if self.use_postgres:
                cursor.execute(f'''
                    INSERT INTO asset_states (
                        asset_id, asset_type, status, health_score,
                        voltage, current, power, temperature, data
                    ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    RETURNING id
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
                result = cursor.fetchone()
                return result[0] if result else None
            else:
                cursor.execute(f'''
                    INSERT INTO asset_states (
                        asset_id, asset_type, status, health_score,
                        voltage, current, power, temperature, data
                    ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
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
            ph = self.placeholder

            if self.use_postgres:
                cursor.execute(f'''
                    INSERT INTO alerts (alert_type, severity, asset_id, message, data)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph})
                    RETURNING id
                ''', (alert_type, severity, asset_id, message, json.dumps(data or {})))
                result = cursor.fetchone()
                if result:
                    # With RealDictCursor (PostgreSQL), result is a dict
                    return result.get('id') if hasattr(result, 'get') else result[0]
                return None
            else:
                cursor.execute(f'''
                    INSERT INTO alerts (alert_type, severity, asset_id, message, data)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph})
                ''', (alert_type, severity, asset_id, message, json.dumps(data or {})))
                return cursor.lastrowid

    def store_ai_analysis(self, analysis_type: str, asset_id: str, results: Dict[str, Any]):
        """Store AI analysis results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            ph = self.placeholder

            if self.use_postgres:
                cursor.execute(f'''
                    INSERT INTO ai_analysis (
                        analysis_type, asset_id, anomaly_score,
                        prediction, recommendation, data
                    ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    RETURNING id
                ''', (
                    analysis_type,
                    asset_id,
                    results.get('anomaly_score', 0),
                    results.get('prediction', ''),
                    results.get('recommendation', ''),
                    json.dumps(results)
                ))
                result = cursor.fetchone()
                return result[0] if result else None
            else:
                cursor.execute(f'''
                    INSERT INTO ai_analysis (
                        analysis_type, asset_id, anomaly_score,
                        prediction, recommendation, data
                    ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
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

            query = f'''
                SELECT * FROM alerts
                WHERE 1=1
            '''
            params = []

            if unresolved_only:
                query += ' AND resolved = FALSE'

            query += f' ORDER BY timestamp DESC LIMIT {self.placeholder}'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def acknowledge_alert(self, alert_id: int):
        """Mark an alert as acknowledged."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            ph = self.placeholder
            cursor.execute(f'''
                UPDATE alerts SET acknowledged = TRUE
                WHERE id = {ph}
            ''', (alert_id,))

    def resolve_alert(self, alert_id: int):
        """Mark an alert as resolved."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            ph = self.placeholder
            cursor.execute(f'''
                UPDATE alerts SET resolved = TRUE, status = 'resolved'
                WHERE id = {ph}
            ''', (alert_id,))

    def update_alert_assignee(self, alert_id: int, assignee: str):
        """Update the assignee for an alert."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            ph = self.placeholder
            cursor.execute(f'''
                UPDATE alerts SET assignee = {ph}
                WHERE id = {ph}
            ''', (assignee, alert_id))

    def update_alert_status(self, alert_id: int, status: str):
        """Update the status of an alert."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            ph = self.placeholder
            # Also update resolved flag if status is 'resolved'
            if status == 'resolved':
                cursor.execute(f'''
                    UPDATE alerts SET status = {ph}, resolved = TRUE
                    WHERE id = {ph}
                ''', (status, alert_id))
            else:
                cursor.execute(f'''
                    UPDATE alerts SET status = {ph}
                    WHERE id = {ph}
                ''', (status, alert_id))

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

    # ===== Threshold Configuration Methods =====

    def create_threshold(self, threshold_data: Dict[str, Any]) -> Optional[int]:
        """Create a new threshold configuration."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            ph = self.placeholder

            try:
                if self.use_postgres:
                    cursor.execute(f'''
                        INSERT INTO threshold_config (
                            component_id, component_name, component_type,
                            metric_name, metric_unit, threshold_min, threshold_max,
                            severity, enabled, description
                        ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                        RETURNING id
                    ''', (
                        threshold_data['component_id'],
                        threshold_data['component_name'],
                        threshold_data['component_type'],
                        threshold_data['metric_name'],
                        threshold_data.get('metric_unit', ''),
                        threshold_data.get('threshold_min'),
                        threshold_data.get('threshold_max'),
                        threshold_data.get('severity', 'medium'),
                        threshold_data.get('enabled', True),
                        threshold_data.get('description', '')
                    ))
                    result = cursor.fetchone()
                    if result:
                        # psycopg2 RealDict cursor returns dict-like objects
                        return result['id'] if isinstance(result, dict) or hasattr(result, '__getitem__') and 'id' in result else result[0]
                    return None
                else:
                    cursor.execute(f'''
                        INSERT INTO threshold_config (
                            component_id, component_name, component_type,
                            metric_name, metric_unit, threshold_min, threshold_max,
                            severity, enabled, description
                        ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    ''', (
                        threshold_data['component_id'],
                        threshold_data['component_name'],
                        threshold_data['component_type'],
                        threshold_data['metric_name'],
                        threshold_data.get('metric_unit', ''),
                        threshold_data.get('threshold_min'),
                        threshold_data.get('threshold_max'),
                        threshold_data.get('severity', 'medium'),
                        threshold_data.get('enabled', True),
                        threshold_data.get('description', '')
                    ))
                    return cursor.lastrowid
            except Exception as e:
                logger.error(f"Error creating threshold: {e}")
                raise

    def get_all_thresholds(self, enabled_only: bool = False) -> List[Dict]:
        """Get all threshold configurations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM threshold_config'
            params = []

            if enabled_only:
                query += f' WHERE enabled = {self.placeholder}'
                params.append(True)

            query += ' ORDER BY component_id, metric_name'

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_threshold_by_id(self, threshold_id: int) -> Optional[Dict]:
        """Get a specific threshold by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'SELECT * FROM threshold_config WHERE id = {self.placeholder}',
                (threshold_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_thresholds_for_component(self, component_id: str) -> List[Dict]:
        """Get all thresholds for a specific component."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'SELECT * FROM threshold_config WHERE component_id = {self.placeholder} AND enabled = {self.placeholder}',
                (component_id, True)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_threshold(self, threshold_id: int, threshold_data: Dict[str, Any]) -> bool:
        """Update an existing threshold configuration."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            ph = self.placeholder

            try:
                update_fields = []
                params = []

                # Build dynamic UPDATE query based on provided fields
                for field in ['component_name', 'component_type', 'metric_name', 'metric_unit',
                             'threshold_min', 'threshold_max', 'severity', 'enabled', 'description']:
                    if field in threshold_data:
                        update_fields.append(f'{field} = {ph}')
                        params.append(threshold_data[field])

                # Always update the updated_at timestamp
                if self.use_postgres:
                    update_fields.append('updated_at = CURRENT_TIMESTAMP')
                else:
                    update_fields.append('updated_at = CURRENT_TIMESTAMP')

                params.append(threshold_id)

                query = f'''
                    UPDATE threshold_config
                    SET {', '.join(update_fields)}
                    WHERE id = {ph}
                '''

                cursor.execute(query, params)
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"Error updating threshold: {e}")
                raise

    def delete_threshold(self, threshold_id: int) -> bool:
        """Delete a threshold configuration."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'DELETE FROM threshold_config WHERE id = {self.placeholder}',
                (threshold_id,)
            )
            return cursor.rowcount > 0

    def upsert_threshold(self, threshold_data: Dict[str, Any]) -> int:
        """Create or update threshold (upsert based on component_id + metric_name)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            ph = self.placeholder

            try:
                if self.use_postgres:
                    logger.debug(f"Upserting threshold for {threshold_data.get('component_id')}/{threshold_data.get('metric_name')}")
                    cursor.execute(f'''
                        INSERT INTO threshold_config (
                            component_id, component_name, component_type,
                            metric_name, metric_unit, threshold_min, threshold_max,
                            severity, enabled, description
                        ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                        ON CONFLICT (component_id, metric_name)
                        DO UPDATE SET
                            component_name = EXCLUDED.component_name,
                            component_type = EXCLUDED.component_type,
                            metric_unit = EXCLUDED.metric_unit,
                            threshold_min = EXCLUDED.threshold_min,
                            threshold_max = EXCLUDED.threshold_max,
                            severity = EXCLUDED.severity,
                            enabled = EXCLUDED.enabled,
                            description = EXCLUDED.description,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING id
                    ''', (
                        threshold_data['component_id'],
                        threshold_data['component_name'],
                        threshold_data['component_type'],
                        threshold_data['metric_name'],
                        threshold_data.get('metric_unit', ''),
                        threshold_data.get('threshold_min'),
                        threshold_data.get('threshold_max'),
                        threshold_data.get('severity', 'medium'),
                        threshold_data.get('enabled', True),
                        threshold_data.get('description', '')
                    ))
                    result = cursor.fetchone()
                    if result:
                        # psycopg2 RealDict cursor returns dict-like objects
                        threshold_id = result['id'] if isinstance(result, dict) or hasattr(result, '__getitem__') and 'id' in result else result[0]
                        return threshold_id
                    return None
                else:
                    # SQLite: Check if exists, then update or insert
                    cursor.execute(f'''
                        SELECT id FROM threshold_config
                        WHERE component_id = {ph} AND metric_name = {ph}
                    ''', (threshold_data['component_id'], threshold_data['metric_name']))

                    existing = cursor.fetchone()

                    if existing:
                        # Update existing
                        threshold_id = existing[0] if isinstance(existing, tuple) else existing['id']
                        self.update_threshold(threshold_id, threshold_data)
                        return threshold_id
                    else:
                        # Insert new
                        return self.create_threshold(threshold_data)
            except Exception as e:
                logger.error(f"Error upserting threshold: {e}")
                raise

    # ===== DSS File Version Methods =====

    def create_dss_version(self, content: str, created_by: str = 'user', description: str = '') -> Optional[int]:
        """Create a new DSS file version."""
        import hashlib

        with self.get_connection() as conn:
            cursor = conn.cursor()
            ph = self.placeholder

            try:
                # Calculate file hash
                file_hash = hashlib.sha256(content.encode()).hexdigest()

                # Count components (lines starting with "New ")
                component_count = len([line for line in content.split('\n') if line.strip().startswith('New ')])

                # Get next version number
                cursor.execute('SELECT MAX(version_number) FROM dss_file_versions')
                result = cursor.fetchone()
                next_version = (result[0] if result and result[0] is not None else 0) + 1

                # Deactivate all previous versions
                cursor.execute('UPDATE dss_file_versions SET is_active = FALSE')

                # Insert new version
                if self.use_postgres:
                    cursor.execute(f'''
                        INSERT INTO dss_file_versions (
                            version_number, content, created_by, description,
                            is_active, file_hash, component_count, validation_status
                        ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                        RETURNING id
                    ''', (next_version, content, created_by, description, True, file_hash, component_count, 'valid'))
                    result = cursor.fetchone()
                    return result['id'] if isinstance(result, dict) or hasattr(result, '__getitem__') and 'id' in result else result[0]
                else:
                    cursor.execute(f'''
                        INSERT INTO dss_file_versions (
                            version_number, content, created_by, description,
                            is_active, file_hash, component_count, validation_status
                        ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    ''', (next_version, content, created_by, description, True, file_hash, component_count, 'valid'))
                    return cursor.lastrowid
            except Exception as e:
                logger.error(f"Error creating DSS version: {e}")
                raise

    def get_active_dss_version(self) -> Optional[Dict]:
        """Get the currently active DSS file version."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM dss_file_versions
                WHERE is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_dss_versions(self, limit: int = 50) -> List[Dict]:
        """Get all DSS file versions."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT id, version_number, created_at, created_by, description,
                       is_active, file_hash, component_count, validation_status,
                       LENGTH(content) as content_size
                FROM dss_file_versions
                ORDER BY version_number DESC
                LIMIT {self.placeholder}
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_dss_version_by_id(self, version_id: int) -> Optional[Dict]:
        """Get a specific DSS file version by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT * FROM dss_file_versions
                WHERE id = {self.placeholder}
            ''', (version_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def activate_dss_version(self, version_id: int) -> bool:
        """Activate a specific DSS file version."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            ph = self.placeholder

            try:
                # Deactivate all versions
                cursor.execute('UPDATE dss_file_versions SET is_active = FALSE')

                # Activate the specified version
                cursor.execute(f'''
                    UPDATE dss_file_versions
                    SET is_active = TRUE
                    WHERE id = {ph}
                ''', (version_id,))

                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"Error activating DSS version: {e}")
                raise

# Create global database instance
db = DigitalTwinDatabase()