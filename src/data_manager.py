"""
Optimized Data Manager for Digital Twin System
Handles real-time caching and periodic database storage
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
from collections import deque

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.config import Config
from src.database import db
from src.influx_manager import influxdb_manager

logger = logging.getLogger(__name__)

class DataManager:
    """Manages data storage strategy with caching and periodic persistence"""

    def __init__(self):
        self.config = Config
        self.redis_client = None
        self.realtime_cache = {}
        self.metrics_buffer = deque(maxlen=self.config.ANALYSIS_BATCH_SIZE)
        self.last_storage_time = time.time()
        self.storage_lock = asyncio.Lock()

        # Initialize Redis if available
        if REDIS_AVAILABLE and self.config.REDIS_HOST:
            try:
                self.redis_client = redis.Redis(
                    host=self.config.REDIS_HOST,
                    port=self.config.REDIS_PORT,
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info(f"Connected to Redis at {self.config.REDIS_HOST}:{self.config.REDIS_PORT}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
                self.redis_client = None

    async def store_realtime_data(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Store real-time data in cache with TTL
        This data is for immediate frontend display, not persisted
        """
        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()

            # Store in Redis if available
            if self.redis_client:
                try:
                    self.redis_client.setex(
                        f"realtime:{key}",
                        self.config.REALTIME_CACHE_TTL,
                        json.dumps(data)
                    )
                    logger.debug(f"Stored realtime data in Redis: {key}")
                except Exception as e:
                    logger.error(f"Redis storage error: {e}")

            # Always store in memory as backup
            self.realtime_cache[key] = {
                'data': data,
                'expires': time.time() + self.config.REALTIME_CACHE_TTL
            }

            return True

        except Exception as e:
            logger.error(f"Error storing realtime data: {e}")
            return False

    async def get_realtime_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get real-time data from cache"""
        try:
            # Try Redis first
            if self.redis_client:
                try:
                    data = self.redis_client.get(f"realtime:{key}")
                    if data:
                        return json.loads(data)
                except Exception as e:
                    logger.error(f"Redis retrieval error: {e}")

            # Fall back to memory cache
            if key in self.realtime_cache:
                cache_entry = self.realtime_cache[key]
                if time.time() < cache_entry['expires']:
                    return cache_entry['data']
                else:
                    # Clean up expired entry
                    del self.realtime_cache[key]

            return None

        except Exception as e:
            logger.error(f"Error getting realtime data: {e}")
            return None

    async def buffer_metrics(self, metrics: Dict[str, Any]):
        """
        Buffer metrics for batch storage
        Also immediately write to InfluxDB for real-time timeseries
        """
        try:
            # Write to InfluxDB immediately for real-time timeseries data
            influxdb_manager.write_metrics(metrics)

            # Add to buffer for PostgreSQL batch storage
            self.metrics_buffer.append({
                **metrics,
                'buffered_at': time.time()
            })

            # Check if it's time to persist to PostgreSQL
            current_time = time.time()
            time_since_last_storage = current_time - self.last_storage_time

            if time_since_last_storage >= self.config.METRICS_STORAGE_INTERVAL:
                await self.persist_metrics_batch()

        except Exception as e:
            logger.error(f"Error buffering metrics: {e}")

    async def persist_metrics_batch(self):
        """Persist buffered metrics to database for analysis"""
        async with self.storage_lock:
            try:
                if not self.metrics_buffer:
                    return

                # Calculate aggregated metrics for the batch
                batch_data = list(self.metrics_buffer)

                # Aggregate metrics
                aggregated = self._aggregate_metrics(batch_data)

                # Store aggregated metrics to PostgreSQL for analysis
                db.store_metrics(aggregated)

                # Store detailed metrics to InfluxDB for timeseries analysis
                influx_success_count = 0
                for metric in batch_data:
                    if influxdb_manager.write_metrics(metric):
                        influx_success_count += 1

                    # Also store significant events to PostgreSQL
                    if self._is_significant_event(metric):
                        db.store_metrics(metric)

                logger.info(f"Persisted {len(batch_data)} metrics to PostgreSQL, {influx_success_count} to InfluxDB")

                # Clear buffer and update timestamp
                self.metrics_buffer.clear()
                self.last_storage_time = time.time()

            except Exception as e:
                logger.error(f"Error persisting metrics batch: {e}")

    def _aggregate_metrics(self, batch: List[Dict]) -> Dict[str, Any]:
        """Aggregate a batch of metrics for storage"""
        if not batch:
            return {}

        # Calculate aggregations
        total_power_values = [m.get('total_power', 0) for m in batch if 'total_power' in m]
        efficiency_values = [m.get('efficiency', 0) for m in batch if 'efficiency' in m]
        power_factor_values = [m.get('power_factor', 0) for m in batch if 'power_factor' in m]

        aggregated = {
            'timestamp': datetime.now().isoformat(),
            'aggregation_type': 'hourly',
            'sample_count': len(batch),
            'total_power': sum(total_power_values) / len(total_power_values) if total_power_values else 0,
            'total_power_max': max(total_power_values) if total_power_values else 0,
            'total_power_min': min(total_power_values) if total_power_values else 0,
            'efficiency': sum(efficiency_values) / len(efficiency_values) if efficiency_values else 0,
            'power_factor': sum(power_factor_values) / len(power_factor_values) if power_factor_values else 0,
            'data': {
                'batch_size': len(batch),
                'aggregation_window': self.config.METRICS_STORAGE_INTERVAL
            }
        }

        return aggregated

    def _is_significant_event(self, metric: Dict) -> bool:
        """Determine if a metric represents a significant event worth storing"""
        # Store if there are alerts
        if metric.get('alerts') and len(metric['alerts']) > 0:
            return True

        # Store if anomaly detected
        if metric.get('predictions', {}).get('anomaly_detected'):
            return True

        # Store if failure probability is high
        failure_prob = metric.get('predictions', {}).get('failure_probability', 0)
        if failure_prob > 0.7:
            return True

        # Store if efficiency is below threshold
        if metric.get('efficiency', 100) < 85:
            return True

        # Store if power factor is poor
        if metric.get('power_factor', 1.0) < 0.9:
            return True

        return False

    async def get_historical_metrics(self, hours: int = 24) -> List[Dict]:
        """Get historical metrics for analysis"""
        try:
            # Get from database
            metrics = db.get_metrics_history(hours=hours)

            # Filter to only include aggregated and significant events
            return [m for m in metrics if
                    m.get('aggregation_type') == 'hourly' or
                    self._is_significant_event(m)]

        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}")
            return []

    async def cleanup_old_data(self):
        """Clean up old data from database"""
        try:
            # Keep detailed data for 7 days, aggregated data for 30 days
            db.cleanup_old_data(days_to_keep=30)
            logger.info("Cleaned up old data from database")

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

    async def get_realtime_summary(self) -> Dict[str, Any]:
        """Get summary of all real-time data for dashboard"""
        summary = {}

        try:
            # Get all realtime keys from Redis
            if self.redis_client:
                try:
                    keys = self.redis_client.keys("realtime:*")
                    for key in keys:
                        data = self.redis_client.get(key)
                        if data:
                            key_name = key.replace("realtime:", "")
                            summary[key_name] = json.loads(data)
                except Exception as e:
                    logger.error(f"Redis summary error: {e}")

            # Merge with memory cache
            current_time = time.time()
            for key, cache_entry in self.realtime_cache.items():
                if current_time < cache_entry['expires'] and key not in summary:
                    summary[key] = cache_entry['data']

        except Exception as e:
            logger.error(f"Error getting realtime summary: {e}")

        return summary

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            'redis_connected': self.redis_client is not None,
            'memory_cache_size': len(self.realtime_cache),
            'buffer_size': len(self.metrics_buffer),
            'last_storage': datetime.fromtimestamp(self.last_storage_time).isoformat(),
            'storage_interval': self.config.METRICS_STORAGE_INTERVAL,
            'cache_ttl': self.config.REALTIME_CACHE_TTL
        }

        if self.redis_client:
            try:
                stats['redis_keys'] = len(self.redis_client.keys("realtime:*"))
            except:
                stats['redis_keys'] = 0

        return stats

# Create global instance
data_manager = DataManager()