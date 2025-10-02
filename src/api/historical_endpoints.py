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

        # Add some randomness
        active_power = base_load * load_factor + np.random.normal(0, 10)
        reactive_power = active_power * 0.3 + np.random.normal(0, 5)

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

        # Add realistic variations for each phase
        phase_a = nominal_voltage * voltage_pu + np.random.normal(0, 0.5)
        phase_b = nominal_voltage * voltage_pu + np.random.normal(0, 0.5)
        phase_c = nominal_voltage * voltage_pu + np.random.normal(0, 0.5)

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
            "frequency": round(50 + np.random.normal(0, 0.02), 3)
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