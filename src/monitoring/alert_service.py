"""
Alert Monitoring Service
Monitors device metrics and generates alerts based on thresholds
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.database import db

logger = logging.getLogger(__name__)

class AlertService:
    """Service for monitoring devices and generating alerts"""

    def __init__(self):
        # Define alert thresholds
        self.thresholds = {
            'voltage_high': 420,  # kV
            'voltage_low': 380,   # kV
            'temperature_high': 85,  # °C
            'temperature_critical': 95,  # °C
            'frequency_high': 50.5,  # Hz
            'frequency_low': 49.5,   # Hz
            'power_factor_low': 0.85,
            'loading_high': 90,  # %
            'loading_critical': 100,  # %
        }

        self.alert_cooldown = {}  # Prevent duplicate alerts
        self.cooldown_period = 300  # 5 minutes

    async def monitor_assets(self, assets: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Monitor all assets and generate alerts"""
        alerts_generated = []

        for asset_id, asset in assets.items():
            asset_alerts = await self.check_asset(asset_id, asset)
            alerts_generated.extend(asset_alerts)

        return alerts_generated

    async def check_asset(self, asset_id: str, asset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check a single asset for alert conditions"""
        alerts = []
        params = asset.get('parameters', {})

        # Check voltage
        voltage = params.get('hv_voltage') or params.get('lv_voltage')
        if voltage:
            if voltage > self.thresholds['voltage_high']:
                alert = await self.create_alert(
                    alert_type='voltage_high',
                    severity='high',
                    asset_id=asset_id,
                    message=f'High voltage detected: {voltage:.2f} kV (threshold: {self.thresholds["voltage_high"]} kV)',
                    data={'voltage': voltage, 'threshold': self.thresholds['voltage_high']}
                )
                if alert:
                    alerts.append(alert)
            elif voltage < self.thresholds['voltage_low']:
                alert = await self.create_alert(
                    alert_type='voltage_low',
                    severity='medium',
                    asset_id=asset_id,
                    message=f'Low voltage detected: {voltage:.2f} kV (threshold: {self.thresholds["voltage_low"]} kV)',
                    data={'voltage': voltage, 'threshold': self.thresholds['voltage_low']}
                )
                if alert:
                    alerts.append(alert)

        # Check temperature
        temperature = params.get('temperature')
        if temperature:
            if temperature > self.thresholds['temperature_critical']:
                alert = await self.create_alert(
                    alert_type='temperature_critical',
                    severity='high',
                    asset_id=asset_id,
                    message=f'Critical temperature: {temperature:.1f}°C (threshold: {self.thresholds["temperature_critical"]}°C)',
                    data={'temperature': temperature, 'threshold': self.thresholds['temperature_critical']}
                )
                if alert:
                    alerts.append(alert)
            elif temperature > self.thresholds['temperature_high']:
                alert = await self.create_alert(
                    alert_type='temperature_high',
                    severity='medium',
                    asset_id=asset_id,
                    message=f'High temperature: {temperature:.1f}°C (threshold: {self.thresholds["temperature_high"]}°C)',
                    data={'temperature': temperature, 'threshold': self.thresholds['temperature_high']}
                )
                if alert:
                    alerts.append(alert)

        # Check loading
        loading = params.get('loading_percent')
        if loading:
            if loading > self.thresholds['loading_critical']:
                alert = await self.create_alert(
                    alert_type='overload_critical',
                    severity='high',
                    asset_id=asset_id,
                    message=f'Critical overload: {loading:.1f}% (threshold: {self.thresholds["loading_critical"]}%)',
                    data={'loading': loading, 'threshold': self.thresholds['loading_critical']}
                )
                if alert:
                    alerts.append(alert)
            elif loading > self.thresholds['loading_high']:
                alert = await self.create_alert(
                    alert_type='overload_warning',
                    severity='medium',
                    asset_id=asset_id,
                    message=f'High loading: {loading:.1f}% (threshold: {self.thresholds["loading_high"]}%)',
                    data={'loading': loading, 'threshold': self.thresholds['loading_high']}
                )
                if alert:
                    alerts.append(alert)

        return alerts

    async def create_alert(
        self,
        alert_type: str,
        severity: str,
        asset_id: str,
        message: str,
        data: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Create an alert with cooldown check"""

        # Check if there's already an active manual_alerts (threshold) alert for this component
        # to avoid duplicate alerts
        recent_alerts = db.get_recent_alerts(limit=50, unresolved_only=True)
        for alert in recent_alerts:
            # Check if there's a threshold alert for the same component
            if (alert.get('asset_id') == asset_id and
                alert.get('alert_type') == 'manual_alerts'):
                logger.debug(f"Skipping {alert_type} alert for {asset_id} - threshold alert already active")
                return None

        # Check cooldown to prevent duplicate alerts
        cooldown_key = f"{asset_id}:{alert_type}"
        current_time = datetime.now().timestamp()

        if cooldown_key in self.alert_cooldown:
            last_alert_time = self.alert_cooldown[cooldown_key]
            if current_time - last_alert_time < self.cooldown_period:
                return None  # Still in cooldown period

        # Store alert in database
        try:
            alert_id = db.store_alert(
                alert_type=alert_type,
                severity=severity,
                asset_id=asset_id,
                message=message,
                data=data or {}
            )

            # Update cooldown
            self.alert_cooldown[cooldown_key] = current_time

            logger.info(f"Alert created: {alert_type} for {asset_id} - {message}")

            return {
                'id': alert_id,
                'alert_type': alert_type,
                'severity': severity,
                'asset_id': asset_id,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return None

    async def trigger_anomaly_alert(
        self,
        anomaly_type: str,
        asset_id: str,
        description: str,
        severity: str = 'high'
    ) -> Optional[Dict[str, Any]]:
        """Manually trigger an anomaly alert (from visualization page)"""

        message = f"Anomaly detected: {description}"

        # Store in database without cooldown check (user-triggered)
        try:
            alert_id = db.store_alert(
                alert_type=f'anomaly_{anomaly_type}',
                severity=severity,
                asset_id=asset_id,
                message=message,
                data={
                    'anomaly_type': anomaly_type,
                    'description': description,
                    'user_triggered': True
                }
            )

            logger.info(f"Anomaly alert triggered: {anomaly_type} for {asset_id}")

            return {
                'id': alert_id,
                'alert_type': f'anomaly_{anomaly_type}',
                'severity': severity,
                'asset_id': asset_id,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to trigger anomaly alert: {e}")
            return None

    def get_recent_alerts(self, limit: int = 50, unresolved_only: bool = False) -> List[Dict]:
        """Get recent alerts from database"""
        try:
            return db.get_recent_alerts(limit=limit, unresolved_only=unresolved_only)
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []

    def acknowledge_alert(self, alert_id: int):
        """Acknowledge an alert"""
        try:
            db.acknowledge_alert(alert_id)
            logger.info(f"Alert {alert_id} acknowledged")
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")

    def resolve_alert(self, alert_id: int):
        """Resolve an alert"""
        try:
            db.resolve_alert(alert_id)
            logger.info(f"Alert {alert_id} resolved")
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")

    def update_alert_assignee(self, alert_id: int, assignee: str):
        """Update the assignee for an alert"""
        try:
            db.update_alert_assignee(alert_id, assignee)
            logger.info(f"Alert {alert_id} assigned to {assignee}")
        except Exception as e:
            logger.error(f"Failed to update alert assignee: {e}")
            raise

    def update_alert_status(self, alert_id: int, status: str):
        """Update the status of an alert"""
        try:
            db.update_alert_status(alert_id, status)
            logger.info(f"Alert {alert_id} status updated to {status}")
        except Exception as e:
            logger.error(f"Failed to update alert status: {e}")
            raise

# Global instance
alert_service = AlertService()
