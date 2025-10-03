"""
Threshold Monitoring Service
Monitors SCADA data points against user-configured thresholds and generates alerts
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.database import db

logger = logging.getLogger(__name__)

class ThresholdMonitor:
    """Service for monitoring SCADA data against user-defined thresholds"""

    def __init__(self):
        self.last_alert_timestamps = {}  # Track last alert time for each component
        self.cooldown_seconds = 300  # 5 minutes cooldown between alerts for same component

    async def check_scada_data(self, scada_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check SCADA data points against configured thresholds

        Args:
            scada_data: Dictionary of SCADA data points with structure:
                {
                    'component_id': {
                        'value': float,
                        'quality': str,
                        'unit': str,
                        'timestamp': str
                    }
                }

        Returns:
            List of generated alerts
        """
        alerts_generated = []

        # Get all enabled thresholds
        thresholds = db.get_all_thresholds(enabled_only=True)

        if not thresholds:
            logger.debug("No thresholds configured")
            return alerts_generated

        # Check each threshold
        for threshold in thresholds:
            component_id = threshold['component_id']
            metric_name = threshold['metric_name']

            # Check if we have data for this component
            if component_id not in scada_data:
                continue

            data_point = scada_data[component_id]

            # Get the value to check
            value = data_point.get('value')
            if value is None:
                continue

            # Check threshold violations
            alert = await self._check_threshold_violation(
                threshold=threshold,
                value=value,
                data_point=data_point
            )

            if alert:
                alerts_generated.append(alert)

        return alerts_generated

    async def _check_threshold_violation(
        self,
        threshold: Dict[str, Any],
        value: float,
        data_point: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if a value violates the threshold and generate alert if needed"""

        component_id = threshold['component_id']
        threshold_min = threshold.get('threshold_min')
        threshold_max = threshold.get('threshold_max')
        severity = threshold.get('severity', 'medium')

        # Check for violation
        violated = False
        violation_type = None
        threshold_value = None

        if threshold_max is not None and value > threshold_max:
            violated = True
            violation_type = 'above_max'
            threshold_value = threshold_max
        elif threshold_min is not None and value < threshold_min:
            violated = True
            violation_type = 'below_min'
            threshold_value = threshold_min

        if not violated:
            return None

        # Check if there's already an active anomaly alert for this component
        # to avoid duplicate alerts
        recent_alerts = db.get_recent_alerts(limit=50, unresolved_only=True)
        for alert in recent_alerts:
            # Check if there's an anomaly alert for the same component
            if (alert.get('asset_id') == component_id and
                alert.get('alert_type', '').startswith('anomaly_')):
                logger.debug(f"Skipping threshold alert for {component_id} - anomaly alert already active")
                return None

        # Check cooldown to prevent alert spam
        cooldown_key = f"{component_id}:{threshold['metric_name']}"
        current_time = datetime.now().timestamp()

        if cooldown_key in self.last_alert_timestamps:
            time_since_last = current_time - self.last_alert_timestamps[cooldown_key]
            if time_since_last < self.cooldown_seconds:
                logger.debug(f"Alert cooldown active for {cooldown_key}")
                return None

        # Generate alert message
        if violation_type == 'above_max':
            message = f"{threshold['component_name']}: Value {value:.2f} {threshold.get('metric_unit', '')} exceeds maximum threshold {threshold_value:.2f} {threshold.get('metric_unit', '')}"
        else:
            message = f"{threshold['component_name']}: Value {value:.2f} {threshold.get('metric_unit', '')} below minimum threshold {threshold_value:.2f} {threshold.get('metric_unit', '')}"

        # Create alert in database
        try:
            alert_id = db.store_alert(
                alert_type='manual_alerts',  # Source type as requested by user
                severity=severity,
                asset_id=component_id,
                message=message,
                data={
                    'component_id': component_id,
                    'component_name': threshold['component_name'],
                    'component_type': threshold['component_type'],
                    'metric_name': threshold['metric_name'],
                    'metric_unit': threshold.get('metric_unit', ''),
                    'value': value,
                    'threshold_min': threshold_min,
                    'threshold_max': threshold_max,
                    'threshold_value': threshold_value,
                    'violation_type': violation_type,
                    'data_quality': data_point.get('quality'),
                    'system_state': {
                        'voltage': data_point.get('voltage'),
                        'current': data_point.get('current'),
                        'power': data_point.get('power'),
                        'temperature': data_point.get('temperature')
                    }
                }
            )

            # Update cooldown timestamp
            self.last_alert_timestamps[cooldown_key] = current_time

            logger.warning(f"Threshold alert created: {message}")

            return {
                'id': alert_id,
                'alert_type': 'manual_alerts',
                'severity': severity,
                'asset_id': component_id,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'threshold_id': threshold['id']
            }

        except Exception as e:
            logger.error(f"Failed to create threshold alert: {e}")
            return None

    async def check_and_alert(self, scada_data: Dict[str, Any]) -> int:
        """
        Convenience method to check thresholds and return count of alerts generated

        Args:
            scada_data: SCADA data dictionary

        Returns:
            Number of alerts generated
        """
        alerts = await self.check_scada_data(scada_data)
        return len(alerts)

# Global instance
threshold_monitor = ThresholdMonitor()
