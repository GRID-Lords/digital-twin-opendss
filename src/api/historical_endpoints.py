"""
Historical Data API Endpoints for Digital Twin
Provides time-series data for charts and analytics
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import numpy as np
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/historical", tags=["historical"])

# Data models
class TimeSeriesData(BaseModel):
    timestamp: datetime
    value: float

class HistoricalRequest(BaseModel):
    asset_id: Optional[str] = None
    metric: str
    start_time: datetime
    end_time: datetime
    resolution: Optional[str] = "1h"  # 1m, 5m, 15m, 1h, 1d

class AggregatedData(BaseModel):
    timestamp: datetime
    min: float
    max: float
    avg: float
    count: int

# Global reference to data manager
_data_manager = None
_asset_manager = None

def set_managers(data_manager, asset_manager):
    """Set manager instances from main app"""
    global _data_manager, _asset_manager
    _data_manager = data_manager
    _asset_manager = asset_manager

def get_data_manager():
    """Dependency to get data manager"""
    if _data_manager is None:
        raise HTTPException(status_code=503, detail="Data manager not initialized")
    return _data_manager

def get_asset_manager():
    """Dependency to get asset manager"""
    if _asset_manager is None:
        raise HTTPException(status_code=503, detail="Asset manager not initialized")
    return _asset_manager

@router.get("/power-flow")
async def get_power_flow_history(
    hours: int = Query(24, description="Number of hours of history"),
    resolution: str = Query("15m", description="Data resolution (1m, 5m, 15m, 1h)"),
    data_manager = Depends(get_data_manager)
):
    """Get historical power flow data for charts"""

    # Use IST timezone (UTC+5:30)
    from datetime import timezone
    IST = timezone(timedelta(hours=5, minutes=30))

    end_time = datetime.now(IST)
    start_time = end_time - timedelta(hours=hours)

    # Try to get data from database first
    try:
        from timeseries_db import timeseries_db
        db_data = timeseries_db.get_power_flow_history(
            start_time.replace(tzinfo=None),  # Remove timezone for DB query
            end_time.replace(tzinfo=None)
        )

        if db_data and len(db_data) > 0:
            # Use database data and format for frontend
            data_points = []
            for record in db_data:
                # Parse timestamp and add IST timezone
                ts = datetime.fromisoformat(str(record['timestamp']))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=IST)

                data_points.append({
                    "timestamp": ts.isoformat(),
                    "activePower": round(record.get('active_power', 0), 2),
                    "reactivePower": round(record.get('reactive_power', 0), 2),
                    "apparentPower": round(record.get('apparent_power', 0), 2),
                    "powerFactor": round(record.get('power_factor', 0.95), 3)
                })

            logger.info(f"Returning {len(data_points)} power flow records from database")

            return {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "resolution": resolution,
                "data": data_points,
                "summary": {
                    "avgActivePower": round(np.mean([d["activePower"] for d in data_points]), 2) if data_points else 0,
                    "maxActivePower": round(max((d["activePower"] for d in data_points), default=0), 2),
                    "minActivePower": round(min((d["activePower"] for d in data_points), default=0), 2),
                    "totalEnergy": round(sum(d["activePower"] for d in data_points) * 1, 2)  # MWh (approximate)
                }
            }
    except Exception as e:
        logger.warning(f"Failed to fetch from database, generating fallback data: {e}")

    # Fallback: Generate time series based on resolution with IST timestamps
    timestamps = []
    current = start_time

    resolution_minutes = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "2h": 120, "6h": 360, "1d": 1440
    }.get(resolution, 15)

    delta = timedelta(minutes=resolution_minutes)

    data_points = []
    while current <= end_time:
        timestamps.append(current)
        current += delta

    # Generate realistic power flow data with daily patterns
    for i, ts in enumerate(timestamps):
        hour = ts.hour

        # Create daily load pattern (low at night, peaks at 10am and 7pm) - IST hours
        base_load = 250  # MW

        # Morning ramp (6am - 10am)
        if 6 <= hour < 10:
            load_factor = 0.7 + (hour - 6) * 0.075
        # Peak morning (10am - 12pm)
        elif 10 <= hour < 12:
            load_factor = 1.0
        # Afternoon dip (12pm - 5pm)
        elif 12 <= hour < 17:
            load_factor = 0.85
        # Evening peak (5pm - 9pm)
        elif 17 <= hour < 21:
            load_factor = 0.95
        # Night (9pm - 6am)
        else:
            load_factor = 0.6

        # Use deterministic variation based on timestamp
        minute_hash = hash(ts.isoformat()) % 100 / 50.0 - 1.0  # Deterministic [-1, 1]
        active_power = base_load * load_factor + minute_hash * 10
        reactive_power = active_power * 0.3

        # Calculate power factor
        apparent_power = np.sqrt(active_power**2 + reactive_power**2)
        power_factor = active_power / apparent_power if apparent_power > 0 else 0.95

        data_points.append({
            "timestamp": ts.isoformat(),
            "activePower": round(active_power, 2),
            "reactivePower": round(reactive_power, 2),
            "apparentPower": round(apparent_power, 2),
            "powerFactor": round(power_factor, 3)
        })

    logger.info(f"Returning {len(data_points)} generated power flow records (fallback)")

    return {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "resolution": resolution,
        "data": data_points,
        "summary": {
            "avgActivePower": round(np.mean([d["activePower"] for d in data_points]), 2),
            "maxActivePower": round(max(d["activePower"] for d in data_points), 2),
            "minActivePower": round(min(d["activePower"] for d in data_points), 2),
            "totalEnergy": round(sum(d["activePower"] for d in data_points) * resolution_minutes / 60, 2)  # MWh
        }
    }

@router.get("/voltage-profile")
async def get_voltage_profile_history(
    bus: str = Query("400kV", description="Bus identifier (400kV or 220kV)"),
    hours: int = Query(24, description="Number of hours of history"),
    resolution: str = Query("5m", description="Data resolution")
):
    """Get historical voltage profile data"""

    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    resolution_minutes = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60
    }.get(resolution, 5)

    timestamps = []
    current = start_time
    delta = timedelta(minutes=resolution_minutes)

    while current <= end_time:
        timestamps.append(current)
        current += delta

    # Generate voltage data based on bus level
    nominal_voltage = 400 if "400" in bus else 220

    data_points = []
    for ts in timestamps:
        # Voltage varies slightly throughout the day
        hour = ts.hour

        # Voltage tends to be lower during peak hours
        if 10 <= hour < 12 or 17 <= hour < 21:
            voltage_pu = 0.98  # Slightly below nominal during peaks
        else:
            voltage_pu = 1.01  # Slightly above nominal during off-peak

        # Use deterministic phase variations based on timestamp
        time_hash = hash(ts.isoformat())
        phase_a = nominal_voltage * voltage_pu + (time_hash % 10 - 5) * 0.1
        phase_b = nominal_voltage * voltage_pu + ((time_hash // 10) % 10 - 5) * 0.1
        phase_c = nominal_voltage * voltage_pu + ((time_hash // 100) % 10 - 5) * 0.1

        # Calculate imbalance
        avg_voltage = (phase_a + phase_b + phase_c) / 3
        max_dev = max(abs(phase_a - avg_voltage), abs(phase_b - avg_voltage), abs(phase_c - avg_voltage))
        imbalance = (max_dev / avg_voltage) * 100

        data_points.append({
            "timestamp": ts.isoformat(),
            "phaseA": round(phase_a, 2),
            "phaseB": round(phase_b, 2),
            "phaseC": round(phase_c, 2),
            "average": round(avg_voltage, 2),
            "imbalance": round(imbalance, 3),
            "frequency": round(50.0 + (time_hash % 5 - 2.5) * 0.01, 3)  # Deterministic freq variation
        })

    return {
        "bus": bus,
        "nominalVoltage": nominal_voltage,
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "resolution": resolution,
        "data": data_points,
        "summary": {
            "avgVoltage": round(np.mean([d["average"] for d in data_points]), 2),
            "maxVoltage": round(max(d["average"] for d in data_points), 2),
            "minVoltage": round(min(d["average"] for d in data_points), 2),
            "avgImbalance": round(np.mean([d["imbalance"] for d in data_points]), 3),
            "voltageCompliance": "Within limits" if all(0.95 * nominal_voltage <= d["average"] <= 1.05 * nominal_voltage for d in data_points) else "Out of limits"
        }
    }

@router.get("/asset-health")
async def get_asset_health_history(
    asset_id: str = Query(..., description="Asset ID"),
    days: int = Query(7, description="Number of days of history"),
    asset_manager = Depends(get_asset_manager)
):
    """Get historical health data for a specific asset"""

    # Verify asset exists
    asset = asset_manager.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    # Generate daily health scores
    data_points = []
    current = start_time

    while current <= end_time:
        # Simulate gradual health degradation with maintenance events
        days_old = (current - asset.commissioned_date).days
        base_health = 100 - (days_old / 365) * 2  # 2% degradation per year

        # Add maintenance boost (every 90 days)
        if days_old % 90 < 7:
            base_health += 5  # Post-maintenance improvement

        # Add random daily variation
        daily_health = min(100, max(0, base_health + np.random.normal(0, 2)))

        data_points.append({
            "timestamp": current.isoformat(),
            "health": round(daily_health, 2),
            "status": "operational" if daily_health > 70 else "maintenance" if daily_health > 50 else "critical",
            "temperature": round(65 + np.random.normal(0, 5), 1),
            "load": round(75 + np.random.normal(0, 10), 1),
            "efficiency": round(92 + np.random.normal(0, 2), 1)
        })

        current += timedelta(days=1)

    return {
        "assetId": asset_id,
        "assetName": asset.name,
        "assetType": asset.asset_type.value,
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "data": data_points,
        "summary": {
            "currentHealth": data_points[-1]["health"] if data_points else 0,
            "avgHealth": round(np.mean([d["health"] for d in data_points]), 2),
            "minHealth": round(min(d["health"] for d in data_points), 2),
            "trend": "declining" if data_points[-1]["health"] < data_points[0]["health"] else "stable",
            "maintenanceRecommended": data_points[-1]["health"] < 75
        }
    }

@router.get("/transformer-loading")
async def get_transformer_loading_history(
    transformer_id: str = Query("TR1", description="Transformer ID"),
    hours: int = Query(48, description="Hours of history"),
    asset_manager = Depends(get_asset_manager)
):
    """Get transformer loading history"""

    # Get transformer asset
    transformer = asset_manager.get_asset(transformer_id)
    if not transformer:
        # Create default response for known transformers
        if transformer_id not in ["TR1", "TR2"]:
            raise HTTPException(status_code=404, detail=f"Transformer {transformer_id} not found")
        rating_mva = 315  # Default rating
    else:
        rating_mva = getattr(transformer, 'power_rating_mva', 315)

    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    # Generate hourly data
    data_points = []
    current = start_time

    while current <= end_time:
        hour = current.hour

        # Create realistic loading pattern
        if 6 <= hour < 10:
            load_factor = 0.75 + (hour - 6) * 0.05
        elif 10 <= hour < 14:
            load_factor = 0.95  # Peak morning
        elif 14 <= hour < 17:
            load_factor = 0.85
        elif 17 <= hour < 21:
            load_factor = 0.90  # Evening peak
        else:
            load_factor = 0.65  # Night load

        load_mva = rating_mva * load_factor + np.random.normal(0, 10)
        loading_percent = (load_mva / rating_mva) * 100

        # Temperature rises with load
        oil_temp = 55 + loading_percent * 0.2 + np.random.normal(0, 2)
        winding_temp = oil_temp + 10 + np.random.normal(0, 2)

        data_points.append({
            "timestamp": current.isoformat(),
            "loadMVA": round(load_mva, 2),
            "loadingPercent": round(loading_percent, 1),
            "oilTemperature": round(oil_temp, 1),
            "windingTemperature": round(winding_temp, 1),
            "coolingStage": 1 if loading_percent < 70 else 2 if loading_percent < 90 else 3,
            "efficiency": round(98 - (100 - loading_percent) * 0.02, 2)  # Efficiency drops at low load
        })

        current += timedelta(hours=1)

    return {
        "transformerId": transformer_id,
        "ratingMVA": rating_mva,
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "data": data_points,
        "summary": {
            "avgLoading": round(np.mean([d["loadingPercent"] for d in data_points]), 1),
            "maxLoading": round(max(d["loadingPercent"] for d in data_points), 1),
            "minLoading": round(min(d["loadingPercent"] for d in data_points), 1),
            "avgTemperature": round(np.mean([d["windingTemperature"] for d in data_points]), 1),
            "overloadEvents": sum(1 for d in data_points if d["loadingPercent"] > 100),
            "totalEnergy": round(sum(d["loadMVA"] for d in data_points), 2)  # MVAh
        }
    }

@router.get("/system-events")
async def get_system_events(
    days: int = Query(7, description="Days of history"),
    event_type: Optional[str] = Query(None, description="Filter by event type")
):
    """Get system events and alarms history"""

    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    # Generate realistic events
    events = []
    event_types = ["alarm", "fault", "maintenance", "operation", "warning"]

    # Generate random events over the period
    num_events = np.random.poisson(5 * days)  # Average 5 events per day

    for _ in range(num_events):
        event_time = start_time + timedelta(
            seconds=np.random.uniform(0, (end_time - start_time).total_seconds())
        )

        event_category = np.random.choice(event_types, p=[0.3, 0.1, 0.2, 0.3, 0.1])

        if event_type and event_category != event_type:
            continue

        # Generate event details based on type
        if event_category == "alarm":
            descriptions = [
                "High temperature alarm on Transformer TR1",
                "Low SF6 pressure warning on CB4",
                "Voltage imbalance detected on Bus 220kV",
                "Overload warning on Feeder 3"
            ]
        elif event_category == "fault":
            descriptions = [
                "Ground fault detected on Line 2",
                "Phase-to-phase fault cleared by protection",
                "Breaker failure on CB3"
            ]
        elif event_category == "maintenance":
            descriptions = [
                "Scheduled maintenance completed on TR2",
                "Oil sampling performed on TR1",
                "CB2 contact resistance test completed"
            ]
        elif event_category == "operation":
            descriptions = [
                "CB1 operated successfully",
                "Tap changer moved to position 8",
                "Capacitor bank switched on"
            ]
        else:  # warning
            descriptions = [
                "DGA analysis shows elevated gas levels",
                "Battery voltage low on DC system",
                "Communication loss with RTU2"
            ]

        events.append({
            "timestamp": event_time.isoformat(),
            "type": event_category,
            "severity": "high" if event_category == "fault" else "medium" if event_category in ["alarm", "warning"] else "low",
            "description": np.random.choice(descriptions),
            "acknowledged": bool(np.random.choice([True, False], p=[0.8, 0.2])),
            "duration": int(np.random.randint(1, 120)) if event_category in ["fault", "alarm"] else None
        })

    # Sort events by timestamp
    events.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "totalEvents": len(events),
        "events": events,
        "summary": {
            "alarms": sum(1 for e in events if e["type"] == "alarm"),
            "faults": sum(1 for e in events if e["type"] == "fault"),
            "maintenanceEvents": sum(1 for e in events if e["type"] == "maintenance"),
            "operations": sum(1 for e in events if e["type"] == "operation"),
            "warnings": sum(1 for e in events if e["type"] == "warning"),
            "unacknowledged": sum(1 for e in events if not e.get("acknowledged", True))
        }
    }

@router.get("/energy-consumption")
async def get_energy_consumption(
    days: int = Query(30, description="Days of history"),
    resolution: str = Query("daily", description="Resolution: hourly, daily, weekly, monthly")
):
    """Get energy consumption statistics"""

    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    data_points = []

    if resolution == "hourly":
        current = start_time
        while current <= end_time:
            hour = current.hour
            # Higher consumption during day
            base_consumption = 350 if 6 <= hour <= 22 else 250
            consumption = base_consumption + np.random.normal(0, 20)

            data_points.append({
                "timestamp": current.isoformat(),
                "consumption": round(consumption, 2),
                "cost": round(consumption * 5.5, 2),  # Rs 5.5 per unit
                "carbonEmission": round(consumption * 0.82, 2)  # kg CO2 per MWh
            })
            current += timedelta(hours=1)

    elif resolution == "daily":
        current = start_time.replace(hour=0, minute=0, second=0)
        while current <= end_time:
            # Daily pattern
            daily_consumption = 24 * 300 + np.random.normal(0, 200)

            data_points.append({
                "date": current.date().isoformat(),
                "consumption": round(daily_consumption, 2),
                "peakDemand": round(daily_consumption / 24 * 1.3, 2),
                "avgDemand": round(daily_consumption / 24, 2),
                "cost": round(daily_consumption * 5.5, 2),
                "carbonEmission": round(daily_consumption * 0.82, 2)
            })
            current += timedelta(days=1)

    return {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "resolution": resolution,
        "data": data_points,
        "summary": {
            "totalConsumption": round(sum(d.get("consumption", 0) for d in data_points), 2),
            "avgDailyConsumption": round(sum(d.get("consumption", 0) for d in data_points) / max(days, 1), 2),
            "totalCost": round(sum(d.get("cost", 0) for d in data_points), 2),
            "totalEmissions": round(sum(d.get("carbonEmission", 0) for d in data_points), 2),
            "peakDemand": round(max((d.get("consumption", 0) for d in data_points), default=0), 2)
        }
    }

@router.get("/metrics/trends")
async def get_metric_trends(
    metrics: str = Query("power,voltage,frequency", description="Comma-separated metrics"),
    hours: int = Query(6, description="Hours of history")
):
    """Get multiple metric trends for dashboard"""

    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    requested_metrics = metrics.split(",")
    trends = {}

    # Generate 5-minute interval data
    timestamps = []
    current = start_time
    while current <= end_time:
        timestamps.append(current)
        current += timedelta(minutes=5)

    for metric in requested_metrics:
        if metric == "power":
            trends["power"] = [
                {
                    "timestamp": ts.isoformat(),
                    "value": 350 + np.random.normal(0, 15) + 50 * np.sin(ts.hour * np.pi / 12)
                }
                for ts in timestamps
            ]
        elif metric == "voltage":
            trends["voltage"] = [
                {
                    "timestamp": ts.isoformat(),
                    "value": 400 + np.random.normal(0, 2)
                }
                for ts in timestamps
            ]
        elif metric == "frequency":
            trends["frequency"] = [
                {
                    "timestamp": ts.isoformat(),
                    "value": 50 + np.random.normal(0, 0.02)
                }
                for ts in timestamps
            ]
        elif metric == "powerFactor":
            trends["powerFactor"] = [
                {
                    "timestamp": ts.isoformat(),
                    "value": 0.95 + np.random.normal(0, 0.01)
                }
                for ts in timestamps
            ]

    return {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "metrics": requested_metrics,
        "data": trends
    }

@router.get("/timeseries/power-flow")
async def get_timeseries_power_flow(
    time_range: str = Query("1h", description="Time range (1h, 6h, 24h, 7d)", alias="range"),
    resolution: str = Query("1m", description="Data resolution (1m, 5m, 15m)"),
    data_manager = Depends(get_data_manager)
):
    """Get high-resolution InfluxDB time-series data for Trends page"""

    # Parse time range
    range_mapping = {
        "1h": 60,
        "6h": 360,
        "24h": 1440,
        "7d": 10080
    }

    minutes = range_mapping.get(time_range, 60)

    # Use IST timezone (UTC+5:30)
    from datetime import timezone
    IST = timezone(timedelta(hours=5, minutes=30))

    end_time = datetime.now(IST)
    start_time = end_time - timedelta(minutes=minutes)

    # Try to get data from InfluxDB first
    try:
        from src.influx_manager import influxdb_manager
        from src.data_manager import data_manager

        # Query InfluxDB for system_metrics in the time range
        if not influxdb_manager.client:
            raise Exception("InfluxDB not connected")

        hours_ago = int((datetime.now(IST) - start_time).total_seconds() / 3600) + 1
        db_data = influxdb_manager.query_metrics("system_metrics", hours=hours_ago)

        # Get current metrics from Redis for real-time values
        current_metrics = await data_manager.get_realtime_data("current_metrics")

        if db_data and len(db_data) > 0:
            # InfluxDB returns records like: {'time': datetime, 'field': 'total_power_mw', 'value': 123.45, ...}
            # Group by timestamp to create combined data points
            from collections import defaultdict
            grouped_data = defaultdict(dict)

            for record in db_data:
                ts = record.get('time')
                if ts:
                    # InfluxDB returns UTC time - convert to IST
                    from datetime import timezone as tz
                    if ts.tzinfo is None:
                        # Assume UTC and convert to IST
                        ts = ts.replace(tzinfo=tz.utc).astimezone(IST)
                    elif ts.tzinfo != IST:
                        ts = ts.astimezone(IST)
                    ts_key = ts.isoformat()

                    field = record.get('field', record.get('_field'))
                    value = record.get('value', record.get('_value', 0))

                    if not grouped_data[ts_key]:
                        grouped_data[ts_key]['timestamp'] = ts_key

                    # Map InfluxDB field names to frontend expected names
                    if field == 'total_power_mw':
                        grouped_data[ts_key]['active_power'] = value
                    elif field == 'power_factor':
                        grouped_data[ts_key]['power_factor'] = value
                    elif field == 'voltage_400kv':
                        grouped_data[ts_key]['voltage_400kv'] = value
                    elif field == 'voltage_220kv':
                        grouped_data[ts_key]['voltage_220kv'] = value
                    elif field == 'frequency_hz':
                        grouped_data[ts_key]['frequency'] = value

            # Convert to list and fill in defaults
            all_points = []
            for ts_key in sorted(grouped_data.keys()):
                point = grouped_data[ts_key]

                # Use real power from current metrics if available, otherwise use stored value
                active_power = point.get('active_power', 0)
                if active_power == 0 and current_metrics:
                    active_power = current_metrics.get('total_power', 0)

                # Get power factor (default to typical value)
                power_factor = point.get('power_factor', 0.58)

                # Calculate reactive and apparent power from active power and power factor
                # P = S * pf, therefore S = P / pf
                # Q = sqrt(S^2 - P^2)
                import math
                if active_power > 0 and power_factor > 0:
                    apparent_power = active_power / power_factor
                    reactive_power = math.sqrt(max(0, apparent_power**2 - active_power**2))
                else:
                    apparent_power = 0
                    reactive_power = 0

                all_points.append({
                    "timestamp": point.get('timestamp'),
                    "active_power": round(active_power, 2),
                    "reactive_power": round(reactive_power, 2),
                    "apparent_power": round(apparent_power, 2),
                    "power_factor": round(power_factor, 3),
                    "voltage_400kv": round(point.get('voltage_400kv', 400), 2),
                    "voltage_220kv": round(point.get('voltage_220kv', 220), 2),
                    "frequency": round(point.get('frequency', 50.0), 2)
                })

            # Downsample based on resolution parameter
            resolution_minutes = 1 if resolution == "1m" else 5 if resolution == "5m" else 15
            data_points = []

            if resolution_minutes > 1 and len(all_points) > 0:
                # Group by resolution intervals and average
                interval_groups = {}
                for point in all_points:
                    ts = datetime.fromisoformat(point['timestamp'])
                    # Round down to nearest interval (preserve timezone)
                    interval_ts = ts.replace(minute=(ts.minute // resolution_minutes) * resolution_minutes, second=0, microsecond=0)
                    interval_key = interval_ts.isoformat()

                    if interval_key not in interval_groups:
                        interval_groups[interval_key] = []
                    interval_groups[interval_key].append(point)

                # Average each interval group
                for interval_ts_str in sorted(interval_groups.keys()):
                    points_in_interval = interval_groups[interval_ts_str]
                    data_points.append({
                        "timestamp": interval_ts_str,  # Already includes timezone
                        "active_power": round(sum(p['active_power'] for p in points_in_interval) / len(points_in_interval), 2),
                        "reactive_power": round(sum(p['reactive_power'] for p in points_in_interval) / len(points_in_interval), 2),
                        "apparent_power": round(sum(p['apparent_power'] for p in points_in_interval) / len(points_in_interval), 2),
                        "power_factor": round(sum(p['power_factor'] for p in points_in_interval) / len(points_in_interval), 3),
                        "voltage_400kv": round(sum(p['voltage_400kv'] for p in points_in_interval) / len(points_in_interval), 2),
                        "voltage_220kv": round(sum(p['voltage_220kv'] for p in points_in_interval) / len(points_in_interval), 2),
                        "frequency": round(sum(p['frequency'] for p in points_in_interval) / len(points_in_interval), 2)
                    })
            else:
                data_points = all_points

            logger.info(f"Returning {len(data_points)} InfluxDB timeseries records (downsampled from {len(all_points)} to {resolution})")

            return {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "range": time_range,
                "resolution": resolution,
                "source": "influxdb",
                "data": data_points
            }
    except Exception as e:
        logger.warning(f"InfluxDB not available, generating fallback data: {e}")

    # Fallback: Try PostgreSQL database before generating synthetic data
    try:
        from src.database import db
        pg_data = db.get_metrics_history(hours=int(minutes/60) if minutes < 1440 else 24, limit=1000)

        if pg_data and len(pg_data) > 0:
            logger.info(f"Found {len(pg_data)} records in PostgreSQL, using real data")

            # Format PostgreSQL data for frontend
            data_points = []
            for record in pg_data:
                ts_str = record.get('timestamp')
                if isinstance(ts_str, str):
                    ts = datetime.fromisoformat(ts_str)
                else:
                    ts = ts_str

                # Add IST timezone if needed
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=IST)

                # Parse data JSON if it exists
                data_json = record.get('data')
                if isinstance(data_json, str):
                    import json
                    try:
                        data_dict = json.loads(data_json)
                    except:
                        data_dict = {}
                else:
                    data_dict = data_json or {}

                data_points.append({
                    "timestamp": ts.isoformat(),
                    "active_power": round(record.get('total_power', 0), 2),
                    "reactive_power": round(record.get('total_power', 0) * 0.28, 2),
                    "apparent_power": round(record.get('total_power', 0) * 1.04, 2),
                    "power_factor": round(record.get('power_factor', 0.96), 3),
                    "voltage_400kv": round(data_dict.get('voltage_400kv', 400), 2),
                    "voltage_220kv": round(data_dict.get('voltage_220kv', 220), 2),
                    "frequency": round(data_dict.get('frequency', 50.0), 2)
                })

            if len(data_points) > 0:
                # Sort by timestamp
                data_points.sort(key=lambda x: x['timestamp'])

                return {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "range": time_range,
                    "resolution": resolution,
                    "source": "postgresql",
                    "data": data_points[-max_points:] if len(data_points) > 1000 else data_points
                }

    except Exception as db_error:
        logger.warning(f"Could not read from PostgreSQL: {db_error}")

    # Last resort: Generate realistic synthetic data
    # This uses OpenDSS-style calculations matching what real data would look like
    logger.info(f"Generating synthetic data with realistic patterns for {time_range} @ {resolution} resolution")

    resolution_minutes = 1 if resolution == "1m" else 5 if resolution == "5m" else 15
    max_points = min(minutes // resolution_minutes, 1000)

    timestamps = []
    current = start_time
    delta = timedelta(minutes=resolution_minutes)

    for i in range(max_points):
        if current > end_time:
            break
        timestamps.append(current)
        current += delta

    # Base values from typical Indian EHV substation operation (matching OpenDSS circuit)
    base_load = 420  # MW (medium-sized substation)

    data_points = []
    for i, ts in enumerate(timestamps):
        hour = ts.hour
        month = ts.month

        # ==== SEASONAL VARIATIONS (Indian Climate) ====
        # Summer (Mar-Jun): Peak AC load
        if 3 <= month <= 6:
            seasonal_factor = 1.15  # 15% higher load due to cooling
            base_voltage_400 = 397  # Voltage sags during high load
            base_voltage_220 = 218
        # Monsoon (Jul-Sep): Moderate load
        elif 7 <= month <= 9:
            seasonal_factor = 1.0  # Normal load
            base_voltage_400 = 400
            base_voltage_220 = 220
        # Winter (Nov-Feb): Lower load
        elif month >= 11 or month <= 2:
            seasonal_factor = 0.85  # 15% lower load, minimal heating
            base_voltage_400 = 403  # Voltage rises during low load
            base_voltage_220 = 222
        # Autumn (Oct): Transition
        else:
            seasonal_factor = 0.95
            base_voltage_400 = 401
            base_voltage_220 = 221

        # ==== DAILY LOAD PATTERN (Indian Substation) ====
        # Morning peak (6-9 AM): 80-90% load (offices/industries start)
        if 6 <= hour < 9:
            daily_factor = 0.85 + (hour - 6) * 0.05  # Gradual rise
        # Mid-morning (9-10 AM): Building up
        elif 9 <= hour < 10:
            daily_factor = 0.95
        # Midday peak (10-14): 90-100% load (full industrial/commercial)
        elif 10 <= hour < 14:
            daily_factor = 0.95 + (12 - abs(hour - 12)) * 0.05  # Peak at noon
        # Afternoon (14-17): Slight dip
        elif 14 <= hour < 17:
            daily_factor = 0.90
        # Evening peak (17-22): 100-110% load (residential + commercial)
        elif 17 <= hour < 22:
            daily_factor = 1.0 + (20 - abs(hour - 20)) * 0.05  # Peak at 8 PM
        # Late night (22-24): Declining
        elif 22 <= hour < 24:
            daily_factor = 0.70 - (hour - 22) * 0.05
        # Night valley (0-6 AM): 40-60% load
        else:
            daily_factor = 0.50 + hour * 0.02

        # Combine seasonal and daily factors
        load_factor = seasonal_factor * daily_factor

        # Deterministic variations based on timestamp hash (small random-like variations)
        minute_hash = hash(ts.isoformat()) % 100 / 50.0 - 1.0  # Range: -1 to 1

        # Calculate power values
        active_power = base_load * load_factor + minute_hash * 8
        reactive_power = active_power * 0.28 + minute_hash * 4  # Typical PF ~0.96
        apparent_power = (active_power**2 + reactive_power**2) ** 0.5
        power_factor = active_power / apparent_power if apparent_power > 0 else 0.96

        # ==== VOLTAGE VARIATIONS ====
        # Voltage inversely related to load (voltage drop during high load)
        load_effect = (1 - load_factor) * 3  # Higher load = lower voltage
        voltage_400kv = base_voltage_400 + load_effect + minute_hash * 2
        voltage_220kv = base_voltage_220 + load_effect * 0.55 + minute_hash * 1.2

        # Ensure voltages stay within Indian Grid Code limits (±5%)
        voltage_400kv = max(380, min(420, voltage_400kv))
        voltage_220kv = max(209, min(231, voltage_220kv))

        # Frequency: Indian grid is quite stable (49.9-50.05 Hz typical)
        frequency = 50.0 + minute_hash * 0.03

        data_points.append({
            "timestamp": ts.isoformat(),
            "active_power": round(active_power, 2),
            "reactive_power": round(reactive_power, 2),
            "apparent_power": round(apparent_power, 2),
            "power_factor": round(power_factor, 3),
            "voltage_400kv": round(voltage_400kv, 2),
            "voltage_220kv": round(voltage_220kv, 2),
            "frequency": round(frequency, 2)
        })

    return {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "range": time_range,
        "resolution": resolution,
        "source": "fallback",
        "data": data_points
    }