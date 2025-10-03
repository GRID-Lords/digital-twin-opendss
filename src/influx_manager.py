"""
InfluxDB client for timeseries data storage
Handles metrics storage and retrieval for the Digital Twin
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from src.config import Config

logger = logging.getLogger(__name__)

class InfluxDBManager:
    """Manages InfluxDB connections and operations for timeseries data"""

    def __init__(self):
        self.client = None
        self.write_api = None
        self.query_api = None
        self.bucket = Config.INFLUX_BUCKET
        self.org = Config.INFLUX_ORG

        try:
            self.client = InfluxDBClient(
                url=f"http://{Config.INFLUX_HOST}:{Config.INFLUX_PORT}",
                token=Config.INFLUX_TOKEN,
                org=self.org
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()

            # Test connection
            self.client.ping()
            logger.info(f"✓ InfluxDB connected: {Config.INFLUX_HOST}:{Config.INFLUX_PORT}")

        except Exception as e:
            logger.warning(f"InfluxDB connection failed: {e}. Timeseries storage disabled.")
            self.client = None

    def write_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Write metrics to InfluxDB"""
        if not self.client or not self.write_api:
            return False

        try:
            timestamp = metrics.get('timestamp', datetime.now().isoformat())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

            # Create point for system metrics
            point = Point("system_metrics") \
                .time(timestamp, WritePrecision.NS) \
                .field("total_power_mw", float(metrics.get('total_power_mw', 0))) \
                .field("total_load_mw", float(metrics.get('total_load_mw', 0))) \
                .field("generation_mw", float(metrics.get('generation_mw', 0))) \
                .field("voltage_400kv", float(metrics.get('voltage_400kv', 400.0))) \
                .field("voltage_220kv", float(metrics.get('voltage_220kv', 220.0))) \
                .field("frequency_hz", float(metrics.get('frequency_hz', 50.0))) \
                .field("power_factor", float(metrics.get('power_factor', 0.95)))

            # Add transformer metrics if available
            if 'transformers' in metrics:
                for tf_id, tf_data in metrics['transformers'].items():
                    tf_point = Point("transformer_metrics") \
                        .tag("transformer_id", tf_id) \
                        .time(timestamp, WritePrecision.NS) \
                        .field("load_percent", float(tf_data.get('load', 0))) \
                        .field("temperature_c", float(tf_data.get('temperature', 0))) \
                        .field("oil_level_percent", float(tf_data.get('oil_level', 0)))
                    self.write_api.write(bucket=self.bucket, org=self.org, record=tf_point)

            # Add breaker metrics if available
            if 'breakers' in metrics:
                for br_id, br_data in metrics['breakers'].items():
                    br_point = Point("breaker_metrics") \
                        .tag("breaker_id", br_id) \
                        .time(timestamp, WritePrecision.NS) \
                        .field("status", 1 if br_data.get('status') == 'closed' else 0) \
                        .field("operations", int(br_data.get('operations', 0)))
                    self.write_api.write(bucket=self.bucket, org=self.org, record=br_point)

            # Write system metrics point
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)

            return True

        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")
            return False

    def write_asset_metrics(self, asset_id: str, asset_data: Dict[str, Any]) -> bool:
        """Write asset-specific metrics to InfluxDB"""
        if not self.client or not self.write_api:
            return False

        try:
            timestamp = asset_data.get('timestamp', datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

            point = Point("asset_metrics") \
                .tag("asset_id", asset_id) \
                .tag("asset_type", asset_data.get('type', 'unknown')) \
                .time(timestamp, WritePrecision.NS) \
                .field("health_score", float(asset_data.get('health_score', 100))) \
                .field("voltage", float(asset_data.get('voltage', 0))) \
                .field("current", float(asset_data.get('current', 0))) \
                .field("power", float(asset_data.get('power', 0))) \
                .field("temperature", float(asset_data.get('temperature', 0)))

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True

        except Exception as e:
            logger.error(f"Error writing asset metrics to InfluxDB: {e}")
            return False

    def query_metrics(self, measurement: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Query metrics from InfluxDB"""
        if not self.client or not self.query_api:
            return []

        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -{hours}h)
                |> filter(fn: (r) => r._measurement == "{measurement}")
            '''

            tables = self.query_api.query(query, org=self.org)

            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        'time': record.get_time(),
                        'measurement': record.get_measurement(),
                        'field': record.get_field(),
                        'value': record.get_value(),
                        **record.values
                    })

            return results

        except Exception as e:
            logger.error(f"Error querying InfluxDB: {e}")
            return []

    def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """Get the most recent system metrics"""
        if not self.client or not self.query_api:
            return None

        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -1h)
                |> filter(fn: (r) => r._measurement == "system_metrics")
                |> last()
            '''

            tables = self.query_api.query(query, org=self.org)

            metrics = {}
            for table in tables:
                for record in table.records:
                    field = record.get_field()
                    metrics[field] = record.get_value()
                    metrics['timestamp'] = record.get_time()

            return metrics if metrics else None

        except Exception as e:
            logger.error(f"Error getting latest metrics from InfluxDB: {e}")
            return None

    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()
            logger.info("InfluxDB connection closed")

# Create global instance
influxdb_manager = InfluxDBManager()
