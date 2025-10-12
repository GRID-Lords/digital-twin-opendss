#!/usr/bin/env python3
"""
Indian EHV Substation Digital Twin - Integrated Backend Server
FastAPI server with WebSocket, SCADA integration, OpenDSS simulation, and AI/ML
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pytz

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our modules
from src.config import Config
from src.data_manager import data_manager
from src.integration.scada_integration import SCADAIntegrationManager
from src.simulation.load_flow import LoadFlowAnalysis
from src.models.ai_ml_models import SubstationAIManager
from src.models.asset_models import SubstationAssetManager  # Import asset manager
from src.monitoring.real_time_monitor import RealTimeMonitor
from src.visualization.circuit_visualizer import OpenDSSVisualizer as CircuitVisualizer
from src.api.anomaly_endpoints import router as anomaly_router
from src.api.asset_endpoints import router as asset_router
from src.api.historical_endpoints import router as historical_router
from src.api.alerts_endpoints import router as alerts_router
from src.api.threshold_endpoints import router as threshold_router
from src.api.dss_endpoints import router as dss_router
from src.api.circuit_topology_endpoints import router as circuit_router
from src.database import db  # Import database module
from src.monitoring import alert_service, ai_insights_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# IST timezone for all timestamps
IST = pytz.timezone('Asia/Kolkata')

# Initialize FastAPI app
app = FastAPI(
    title="Indian EHV Substation Digital Twin API",
    description="AI/ML enabled Digital Twin for 400/220 kV Substation",
    version="1.0.0"
)

# Include routers
app.include_router(anomaly_router)
app.include_router(asset_router)
app.include_router(historical_router)
app.include_router(alerts_router)
app.include_router(threshold_router)
app.include_router(dss_router)
app.include_router(circuit_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
scada = None
load_flow = None
ai_manager = None
monitor = None
visualizer = None
asset_manager = None  # Add asset manager instance
connected_websockets = []

# Data models
class AssetData(BaseModel):
    id: str
    name: str
    type: str
    status: str
    health: float
    parameters: Dict[str, Any]

class SimulationRequest(BaseModel):
    scenario: str
    parameters: Dict[str, Any]

class ControlCommand(BaseModel):
    asset_id: str
    command: str
    value: Any

# Initialize components
@app.on_event("startup")
async def startup_event():
    """Initialize all system components"""
    global scada, load_flow, ai_manager, monitor, visualizer, asset_manager

    try:
        logger.info("Initializing Digital Twin Backend...")

        # Initialize database tables
        logger.info("Initializing database tables...")
        db.init_database()
        logger.info("Database tables ready")

        # Initialize Asset Manager
        asset_manager = SubstationAssetManager()
        logger.info(f"Asset Manager initialized with {len(asset_manager.assets)} assets")

        # Set asset manager in asset endpoints
        from src.api.asset_endpoints import set_asset_manager
        set_asset_manager(asset_manager)

        # Set managers in historical endpoints
        from src.api.historical_endpoints import set_managers
        set_managers(data_manager, asset_manager)

        # Set services in alerts endpoints
        from src.api.alerts_endpoints import set_services
        set_services(alert_service, ai_insights_service, asset_manager)

        # Set database in threshold endpoints
        from src.api.threshold_endpoints import set_database
        set_database(db)

        # Initialize SCADA
        scada_config = {
            "modbus_host": "localhost",
            "modbus_port": 502,
            "polling_interval": 1.0,
            "database_path": "substation_scada.db"
        }
        scada = SCADAIntegrationManager(scada_config)
        logger.info("SCADA system initialized")

        # Initialize Load Flow Analysis
        load_flow = LoadFlowAnalysis()
        dss_path = Path(__file__).parent.parent / "src/models/IndianEHVSubstation.dss"
        if dss_path.exists():
            load_flow.load_circuit(str(dss_path))
            logger.info("OpenDSS circuit loaded")

            # Set DSS endpoints dependencies
            from src.api.dss_endpoints import set_dss_dependencies
            set_dss_dependencies(None, load_flow, dss_path)
            logger.info("DSS endpoints configured")

            # Set circuit topology endpoints dependencies
            from src.api.circuit_topology_endpoints import set_circuit_dependencies
            set_circuit_dependencies(load_flow, dss_path)
            logger.info("Circuit topology endpoints configured")

            # Initialize DSS versioning - create first version if none exists
            try:
                active_version = db.get_active_dss_version()
                if not active_version:
                    logger.info("No DSS versions found, creating initial version...")
                    original_content = dss_path.read_text()
                    version_id = db.create_dss_version(
                        content=original_content,
                        created_by='system',
                        description='Initial version from original DSS file'
                    )
                    logger.info(f"Created initial DSS version with ID {version_id}")
                else:
                    logger.info(f"Active DSS version found: v{active_version['version_number']}")
            except Exception as e:
                logger.error(f"Error initializing DSS versioning: {e}")
        else:
            logger.warning(f"DSS file not found at {dss_path}")

        # Initialize AI/ML Manager
        ai_manager = SubstationAIManager()

        # If models are already trained, they will be loaded automatically
        # Otherwise, initialize with synthetic data
        if not ai_manager.is_initialized:
            logger.info("No pre-trained models found, using synthetic data")
            ai_manager.initialize_with_synthetic_data()

        logger.info("AI/ML models initialized")

        # Initialize AI Insights Service with AI Manager
        ai_insights_service.ai_manager = ai_manager
        logger.info("AI Insights Service initialized")

        # Initialize Real-time Monitor
        monitor = RealTimeMonitor()
        logger.info("Real-time monitor initialized")

        # Initialize Circuit Visualizer
        if dss_path.exists():
            visualizer = CircuitVisualizer(str(dss_path))
            logger.info("Circuit visualizer initialized")
        else:
            visualizer = None
            logger.warning("Circuit visualizer not initialized (no DSS file)")

        # Start background tasks
        asyncio.create_task(real_time_data_generator())
        asyncio.create_task(websocket_broadcaster())
        asyncio.create_task(asset_data_updater())  # Add asset updater task
        asyncio.create_task(alert_monitoring_loop())  # Add alert monitoring

        logger.info("Digital Twin Backend started successfully")

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if self.active_connections:
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to websocket: {e}")

manager = ConnectionManager()

# Background task for generating real-time data
async def real_time_data_generator():
    """Generate real-time data for simulation"""
    while True:
        try:
            # Generate synthetic SCADA data
            timestamp = datetime.now(IST)

            # Get real metrics from assets and load flow
            transformers_data = {}
            breakers_data = {}
            bus_voltages_data = {}

            # Extract transformer data from assets
            if asset_manager and asset_manager.assets:
                for asset_id, asset in asset_manager.assets.items():
                    if 'TR' in asset_id or 'T' in asset_id:
                        rt_data = asset.real_time_data
                        transformers_data[asset_id] = {
                            "load": rt_data.get('loading_percent', 75.0),
                            "temperature": rt_data.get('temperature_c', asset.thermal.operating_temperature_c),
                            "oil_level": rt_data.get('oil_level_percent', 95.0)
                        }
                    elif 'CB' in asset_id or 'Breaker' in asset_id:
                        rt_data = asset.real_time_data
                        breakers_data[asset_id] = {
                            "status": rt_data.get('status', 'closed'),
                            "operations": rt_data.get('operations', 1000)
                        }

            # Get bus voltages from load flow
            voltage_400kv = 400.0
            voltage_220kv = 220.0
            active_power = 350.0
            reactive_power = 120.0
            power_factor = 0.95

            if load_flow and load_flow.circuit:
                try:
                    flow_results = load_flow.solve()
                    voltage_400kv = flow_results.get('voltage_400kv', 400.0)
                    voltage_220kv = flow_results.get('voltage_220kv', 220.0)
                    active_power = flow_results.get('total_power_kw', 350000) / 1000  # Convert to MW
                    reactive_power = flow_results.get('total_power_kvar', 120000) / 1000
                    power_factor = flow_results.get('power_factor', 0.95)
                except:
                    pass

            bus_voltages_data = {
                "400kV": voltage_400kv,
                "220kV": voltage_220kv
            }

            # Fallback values if no assets available
            if not transformers_data:
                transformers_data = {
                    "T1": {"load": 85.0, "temperature": 65.0, "oil_level": 95.0},
                    "T2": {"load": 78.0, "temperature": 62.0, "oil_level": 93.0}
                }

            if not breakers_data:
                breakers_data = {
                    "CB1": {"status": "closed", "operations": 1250},
                    "CB2": {"status": "closed", "operations": 980},
                    "CB3": {"status": "open", "operations": 1100}
                }

            data = {
                "timestamp": timestamp.isoformat(),
                "transformers": transformers_data,
                "breakers": breakers_data,
                "bus_voltages": bus_voltages_data,
                "power_flow": {
                    "active_power": active_power,
                    "reactive_power": reactive_power,
                    "power_factor": power_factor
                }
            }

            # Store in SCADA if available (comment out for now)
            # if scada:
            #     for key, value in data["transformers"]["T1"].items():
            #         scada.store_data(f"T1_{key}", value, timestamp)

            await asyncio.sleep(2)  # Update every 2 seconds

        except Exception as e:
            logger.error(f"Error in data generator: {e}")
            await asyncio.sleep(5)

# Background task for updating asset data
async def asset_data_updater():
    """Update asset measurements periodically"""
    update_counter = 0

    while True:
        try:
            if asset_manager:
                # Simulate measurements for all assets
                asset_manager.simulate_asset_measurements()

                # Online learning: Update AI models with new asset data
                if ai_manager and ai_manager.is_initialized:
                    for asset_id, asset in asset_manager.assets.items():
                        # Get real-time data
                        rt_data = asset.real_time_data

                        # Prepare asset data for online learning
                        voltage = rt_data.get('voltage_kv', asset.electrical.voltage_rating_kv)
                        current = rt_data.get('current_a', asset.electrical.current_rating_a * 0.7)
                        power = voltage * current / 1000  # MW

                        # Calculate age in days (remove timezone for calculation)
                        age_delta = datetime.now(IST).replace(tzinfo=None) - asset.commissioned_date
                        age_days = age_delta.days

                        asset_data = {
                            'asset_type': asset.asset_type.value,
                            'voltage': voltage,
                            'current': current,
                            'power': power,
                            'temperature': asset.thermal.temperature_celsius,
                            'health_score': asset.health.overall_health,
                            'age_days': age_days
                        }

                        # Update models online
                        ai_manager.update_models_online(asset_id, asset_data)

                    # Periodically save updated models (every 100 updates = ~8 minutes)
                    update_counter += 1
                    if update_counter % 100 == 0:
                        ai_manager.save_models()
                        logger.info(f"💾 AI models saved after {update_counter} updates")

                # Log critical assets if any
                critical = asset_manager.get_critical_assets(health_threshold=70)
                if critical:
                    logger.warning(f"Found {len(critical)} critical assets")

            await asyncio.sleep(5)  # Update every 5 seconds

        except Exception as e:
            logger.error(f"Error in asset updater: {e}")
            await asyncio.sleep(10)

# Background task for WebSocket broadcasting
async def websocket_broadcaster():
    """Broadcast real-time updates to all connected clients"""
    while True:
        try:
            if manager.active_connections:
                # Get latest data
                metrics = await get_current_metrics()
                await manager.broadcast(metrics)

            await asyncio.sleep(1)  # Broadcast every second

        except Exception as e:
            logger.error(f"Error in websocket broadcaster: {e}")
            await asyncio.sleep(5)

async def alert_monitoring_loop():
    """Monitor assets and generate alerts"""
    # Track last alert IDs to detect new alerts
    if not hasattr(alert_monitoring_loop, '_last_alert_ids'):
        alert_monitoring_loop._last_alert_ids = set()

    while True:
        try:
            if asset_manager and alert_service:
                # Get all assets
                assets_dict = {}
                for asset_id in asset_manager.assets:
                    asset = asset_manager.get_asset(asset_id)
                    if asset:
                        # Convert asset to dict format expected by alert service
                        assets_dict[asset_id] = {
                            'name': asset.name,
                            'status': asset.status,
                            'health': asset.health_score,
                            'parameters': asset.__dict__.get('real_time_data', {})
                        }

                # Monitor and generate alerts
                alerts_generated = await alert_service.monitor_assets(assets_dict)

                # Collect all new alerts for broadcasting
                new_alerts_to_broadcast = []

                if alerts_generated:
                    logger.info(f"Generated {len(alerts_generated)} new alerts")
                    new_alerts_to_broadcast.extend(alerts_generated)

                # Monitor SCADA data against user-defined thresholds
                if scada:
                    from src.monitoring.threshold_monitor import threshold_monitor
                    scada_data = scada.get_integrated_data()
                    if scada_data and 'scada_data' in scada_data:
                        threshold_alerts = await threshold_monitor.check_scada_data(scada_data['scada_data'])
                        if threshold_alerts:
                            logger.info(f"Generated {len(threshold_alerts)} threshold alerts")
                            new_alerts_to_broadcast.extend(threshold_alerts)

                # Broadcast new alerts via WebSocket
                if new_alerts_to_broadcast:
                    for alert in new_alerts_to_broadcast:
                        # Determine notification type based on alert type and severity
                        is_anomaly = alert.get('alert_type', '').startswith('anomaly_')
                        notification_type = 'critical' if is_anomaly else 'medium'

                        notification_message = {
                            'type': 'alert_notification',
                            'notification_type': notification_type,
                            'alert': {
                                'id': alert.get('id'),
                                'message': alert.get('message'),
                                'severity': alert.get('severity'),
                                'alert_type': alert.get('alert_type'),
                                'asset_id': alert.get('asset_id'),
                                'timestamp': alert.get('timestamp')
                            }
                        }

                        # Broadcast to all connected clients
                        await manager.broadcast(notification_message)
                        logger.info(f"Broadcasted {notification_type} alert notification: {alert.get('message', '')[:50]}")

                # Periodically run AI analysis (every 5 minutes)
                if not hasattr(alert_monitoring_loop, '_last_ai_analysis'):
                    alert_monitoring_loop._last_ai_analysis = 0

                current_time = time.time()
                if current_time - alert_monitoring_loop._last_ai_analysis >= 300:  # 5 minutes
                    if ai_insights_service:
                        metrics = await get_current_metrics()
                        await ai_insights_service.analyze_system_health(assets_dict, metrics)
                        alert_monitoring_loop._last_ai_analysis = current_time
                        logger.info("AI system health analysis completed")

            await asyncio.sleep(60)  # Check every 60 seconds

        except Exception as e:
            logger.error(f"Error in alert monitoring loop: {e}")
            await asyncio.sleep(60)

async def run_opendss_and_update_assets():
    """Run OpenDSS power flow and update asset real-time data"""
    if not load_flow or not load_flow.dss:
        return None

    try:
        # Solve power flow
        flow_results = load_flow.solve()

        if not flow_results.get('converged', False):
            logger.warning("OpenDSS power flow did not converge")
            return flow_results

        # Update assets with OpenDSS results (using opendssdirect API)
        if asset_manager and load_flow.dss:
            # Get bus voltages
            bus_names = load_flow.dss.Circuit.AllBusNames()
            for bus_name in bus_names:
                load_flow.dss.Circuit.SetActiveBus(bus_name)
                v_pu = load_flow.dss.Bus.puVmagAngle()
                kv_base = load_flow.dss.Bus.kVBase()

                if v_pu and len(v_pu) > 0:
                    kv_actual = v_pu[0] * kv_base

                    # Update assets connected to this bus
                    for asset_id, asset in asset_manager.assets.items():
                        if bus_name.lower() in asset.location.lower() or bus_name in asset_id:
                            asset.real_time_data['voltage_kv'] = kv_actual

            # Get line/transformer currents and loadings
            element_names = load_flow.dss.Circuit.AllElementNames()
            for elem_name in element_names:
                if 'transformer' in elem_name.lower():
                    load_flow.dss.Circuit.SetActiveElement(elem_name)
                    currents = load_flow.dss.CktElement.Currents()
                    powers = load_flow.dss.CktElement.Powers()

                    # Find matching asset
                    for asset_id, asset in asset_manager.assets.items():
                        if 'TR' in asset_id or 'T' in asset_id:
                            if currents and len(currents) > 0:
                                asset.real_time_data['current_a'] = abs(currents[0])
                            if powers and len(powers) > 0:
                                asset.real_time_data['power_mw'] = abs(powers[0]) / 1000
                                # Calculate loading percentage if rated power available
                                if hasattr(asset.electrical, 'rated_power_mva') and asset.electrical.rated_power_mva:
                                    rated_power = asset.electrical.rated_power_mva * 1000  # Convert to kW
                                    loading_pct = (abs(powers[0]) / rated_power) * 100
                                    asset.real_time_data['loading_percent'] = min(100, loading_pct)

        return flow_results

    except Exception as e:
        logger.error(f"Error running OpenDSS: {e}")
        return None

async def get_current_metrics():
    """Get current system metrics from real OpenDSS power flow data"""
    timestamp = datetime.now(IST)

    # Run OpenDSS and update assets
    flow_results = await run_opendss_and_update_assets()

    # Calculate real metrics from OpenDSS results and assets
    total_power = 0
    total_health = 0
    asset_count = 0

    if asset_manager and asset_manager.assets:
        for asset_id, asset in asset_manager.assets.items():
            # Sum health scores
            total_health += asset.health.overall_health
            asset_count += 1

            # Get power from transformer real-time data (updated from OpenDSS)
            if 'TR' in asset_id:
                rt_data = asset.real_time_data
                power_mw = rt_data.get('power_mw', 0)
                if power_mw > 0:
                    total_power += power_mw

        # Calculate average system health from all assets
        system_health = total_health / asset_count if asset_count > 0 else 95

    else:
        # Fallback if asset manager not available
        total_power = 350
        system_health = 95

    # Use OpenDSS results from flow_results
    voltage_400kv = 0
    voltage_220kv = 0
    max_voltage_pu = 1.0
    min_voltage_pu = 1.0
    if flow_results:
        power_factor = flow_results.get('power_factor', 0.95)
        losses_mw = flow_results.get('total_losses_mw', total_power * 0.03)
        total_power_kw = flow_results.get('total_power_kw', 0)
        voltage_400kv = flow_results.get('voltage_400kv', 0)
        voltage_220kv = flow_results.get('voltage_220kv', 0)
        max_voltage_pu = flow_results.get('max_voltage_pu', 1.0)
        min_voltage_pu = flow_results.get('min_voltage_pu', 1.0)
        if total_power_kw != 0:
            # Use absolute value (negative means source power in OpenDSS)
            total_power = abs(total_power_kw) / 1000  # Convert kW to MW
    else:
        power_factor = 0.95
        losses_mw = total_power * 0.03

    # Calculate efficiency from real losses
    efficiency = ((total_power - losses_mw) / total_power * 100) if total_power > 0 else 96

    # Calculate power flow values
    active_power = total_power
    reactive_power = active_power * np.tan(np.arccos(power_factor))
    apparent_power = active_power / power_factor

    # Calculate voltage stability from actual bus voltages
    # Voltage stability based on how close all buses are to 1.0 pu (nominal)
    # Maximum deviation from 1.0 pu determines stability
    max_deviation = max(abs(max_voltage_pu - 1.0), abs(min_voltage_pu - 1.0))
    voltage_stability = 100 - (max_deviation * 100)  # Higher stability = lower deviation

    # Get frequency from OpenDSS results (with fallback)
    frequency = flow_results.get('frequency', 50.0) if flow_results else 50.0
    # If OpenDSS didn't provide frequency or it's anomaly-affected, add small natural variation
    if frequency == 50.0:
        frequency = 50.0 + np.random.uniform(-0.03, 0.03)

    metrics = {
        "timestamp": timestamp.isoformat(),
        "system_health": round(system_health, 4),  # From actual asset health
        "total_load": round(total_power, 4),
        "total_power": round(total_power, 4),
        "efficiency": round(efficiency, 4),  # From actual losses
        "power_factor": round(power_factor, 4),
        "voltage_stability": round(voltage_stability, 4),
        "frequency": round(frequency, 4),
        "generation": round(total_power + losses_mw, 4),  # Load + losses
        "losses": round(losses_mw, 4),  # Real losses
        "active_power": round(active_power, 4),
        "reactive_power": round(reactive_power, 4),
        "apparent_power": round(apparent_power, 4),
        "voltage_400kv": round(voltage_400kv, 4),  # From OpenDSS
        "voltage_220kv": round(voltage_220kv, 4),  # From OpenDSS
        "alerts": [],
        "predictions": {}
    }

    # Store in real-time cache for immediate display
    await data_manager.store_realtime_data("current_metrics", metrics)

    # Buffer metrics for periodic database storage (hourly)
    await data_manager.buffer_metrics(metrics)

    # Store power flow data to timeseries database every minute
    try:
        from timeseries_db import timeseries_db
        # Store only once per minute to avoid excessive database writes
        if not hasattr(get_current_metrics, '_last_power_flow_store'):
            get_current_metrics._last_power_flow_store = 0

        current_time = time.time()
        if current_time - get_current_metrics._last_power_flow_store >= 60:  # 60 seconds
            # Get actual bus voltages from load flow or assets
            voltage_400kv = 400.0
            voltage_220kv = 220.0

            if load_flow and load_flow.circuit:
                try:
                    flow_results = load_flow.solve()
                    voltage_400kv = flow_results.get('voltage_400kv', 400.0)
                    voltage_220kv = flow_results.get('voltage_220kv', 220.0)
                except:
                    pass

            # Fallback to asset real-time data if available
            if asset_manager and asset_manager.assets:
                for asset_id, asset in asset_manager.assets.items():
                    rt_data = asset.real_time_data
                    if 'voltage_kv' in rt_data:
                        v = rt_data['voltage_kv']
                        # Categorize by voltage level
                        if v > 300:  # 400kV bus
                            voltage_400kv = v
                        elif v > 100:  # 220kV bus
                            voltage_220kv = v

            timeseries_db.insert_power_flow({
                'active_power': active_power,
                'reactive_power': reactive_power,
                'apparent_power': apparent_power,
                'power_factor': power_factor,
                'frequency': metrics['frequency'],
                'voltage_400kv': voltage_400kv,
                'voltage_220kv': voltage_220kv
            }, timestamp)
            get_current_metrics._last_power_flow_store = current_time
            logger.debug("Stored power flow data to timeseries database")
    except Exception as e:
        logger.error(f"Failed to store power flow data: {e}")

    # Add AI predictions if available
    if ai_manager:
        try:
            # Get real asset data for health degradation prediction
            current_data = {}

            if asset_manager and asset_manager.assets:
                for asset_id, asset in asset_manager.assets.items():
                    if 'TR' in asset_id or 'T' in asset_id:  # Transformers
                        rt_data = asset.real_time_data
                        current_data[asset_id] = {
                            "voltage": rt_data.get('voltage_kv', asset.electrical.voltage_rating_kv),
                            "current": rt_data.get('current_a', asset.electrical.current_rating_a * 0.7),
                            "power": rt_data.get('power_mw', 0),
                            "temperature": rt_data.get('temperature_c', asset.thermal.operating_temperature_c),
                            "health_score": asset.health.overall_health
                        }

            # Fallback if no assets available
            if not current_data:
                current_data = {
                    "PowerTransformer_T1": {
                        "voltage": 400.0,
                        "current": 200.0,
                        "power": total_power * 0.6,
                        "temperature": 65.0,
                        "health_score": 85.0
                    }
                }

            # Use actual AI manager method via predictive_model
            predictions = ai_manager.predictive_model.predict_health_degradation(current_data)
            if predictions:
                metrics["predictions"]["health_predictions"] = predictions[:2]  # Just show first 2
                metrics["predictions"]["anomaly_detected"] = any(p.get("predicted_health", 100) < 70 for p in predictions)
                metrics["predictions"]["failure_probability"] = max((100 - p.get("predicted_health", 100)) / 100 for p in predictions)
        except Exception as e:
            logger.error(f"Error getting AI predictions: {e}")

    # Apply active anomaly modifications to metrics
    try:
        from src.api.anomaly_endpoints import apply_anomaly_to_metrics
        metrics = apply_anomaly_to_metrics(metrics)
    except Exception as e:
        logger.error(f"Error applying anomaly to metrics: {e}")

    return metrics

# API Routes

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Indian EHV Substation Digital Twin",
        "status": "operational",
        "version": "1.0.0",
        "endpoints": {
            "api_docs": "/docs",
            "assets": "/api/assets",
            "metrics": "/api/metrics",
            "scada": "/api/scada/data",
            "simulation": "/api/simulation",
            "ai_analysis": "/api/ai/analysis"
        }
    }

def calculate_health_score(asset_type: str, temperature: float, load_percent: float, age_years: float, operations: int = 0) -> float:
    """Calculate dynamic health score based on operating conditions"""
    base_health = 100.0

    # Temperature impact (optimal: 55-65°C for transformers)
    if asset_type in ["Power Transformer", "Distribution Transformer"]:
        if temperature < 55:
            temp_penalty = 0
        elif temperature <= 65:
            temp_penalty = 0
        elif temperature <= 75:
            temp_penalty = (temperature - 65) * 1.5  # 1.5% per degree over 65°C
        else:
            temp_penalty = 15 + (temperature - 75) * 2  # 2% per degree over 75°C
    else:
        temp_penalty = 0

    # Load impact (optimal: below 80%)
    if load_percent <= 80:
        load_penalty = 0
    elif load_percent <= 90:
        load_penalty = (load_percent - 80) * 0.5  # 0.5% per percent over 80%
    elif load_percent <= 100:
        load_penalty = 5 + (load_percent - 90) * 1  # 1% per percent over 90%
    else:
        load_penalty = 15 + (load_percent - 100) * 2  # 2% per percent over 100%

    # Age impact
    if asset_type == "Circuit Breaker":
        expected_life = 30  # years
        operations_limit = 10000  # mechanical operations
        age_penalty = min(20, (age_years / expected_life) * 20)
        ops_penalty = min(10, (operations / operations_limit) * 10)
    else:
        expected_life = 25  # years for transformers
        age_penalty = min(25, (age_years / expected_life) * 25)
        ops_penalty = 0

    # Calculate final health score (deterministic based on actual conditions)
    health = base_health - temp_penalty - load_penalty - age_penalty - ops_penalty

    return max(0, min(100, round(health, 2)))

# DEPRECATED - Using asset_endpoints.py instead
# The old get_assets function has been replaced with asset_endpoints.py
# which uses the proper SubstationAssetManager
"""
@app.get("/api/assets")
async def get_assets_old():
    # Get all substation assets with dynamic health scores from database

    # Get latest metrics from database (last 24 hours)
    recent_metrics = await data_manager.get_historical_metrics(hours=24)

    # If we have stored data, calculate averages from it
    if recent_metrics:
        # Calculate average values from historical data
        total_power_avg = np.mean([m.get('total_power', 350) for m in recent_metrics])
        efficiency_avg = np.mean([m.get('efficiency', 92) for m in recent_metrics])

        # Use database values to derive asset conditions
        t1_load = min(100, (total_power_avg * 0.6 / 315) * 100)  # Load as percentage of 315 MVA rating
        t2_load = min(100, (total_power_avg * 0.4 / 315) * 100)

        # Temperature based on load and efficiency
        t1_temp = 55 + (t1_load / 100) * 20 + np.random.normal(0, 2)
        t2_temp = 55 + (t2_load / 100) * 18 + np.random.normal(0, 2)
    else:
        # Fallback to realistic operating values if no database data
        t1_temp = 68 + np.random.normal(0, 2)
        t1_load = 85 + np.random.normal(0, 3)
        t2_temp = 72 + np.random.normal(0, 2)
        t2_load = 78 + np.random.normal(0, 3)

    # Fixed asset ages (would be from asset database in real system)
    t1_age = 8  # 8 years old
    t2_age = 12  # 12 years old
    cb1_age = 5  # 5 years old
    cb1_ops = 2850  # Number of operations

    # Circuit breaker values
    cb1_temp = 45 + np.random.normal(0, 2)
    cb1_load = 75 + np.random.normal(0, 5)

    # Create comprehensive asset list for EHV substation
    assets = []

    # 1. POWER TRANSFORMERS (2 units)
    assets.extend([
        AssetData(
            id="T1",
            name="Transformer 1",
            type="Power Transformer",
            status="operational",
            health=calculate_health_score("Power Transformer", t1_temp, t1_load, t1_age),
            parameters={
                "rating": "315 MVA",
                "voltage": "400/220 kV",
                "temperature": f"{t1_temp:.1f}°C",
                "load": f"{t1_load:.1f}%",
                "oil_level": "Normal",
                "tap_position": "7",
                "age": f"{t1_age} years"
            }
        ),
        AssetData(
            id="T2",
            name="Transformer 2",
            type="Power Transformer",
            status="operational",
            health=calculate_health_score("Power Transformer", t2_temp, t2_load, t2_age),
            parameters={
                "rating": "315 MVA",
                "voltage": "400/220 kV",
                "temperature": f"{t2_temp:.1f}°C",
                "load": f"{t2_load:.1f}%",
                "oil_level": "Normal",
                "tap_position": "8",
                "age": f"{t2_age} years"
            }
        )
    ])

    # 2. CIRCUIT BREAKERS (Multiple for different bays)
    for i in range(1, 7):  # 6 Circuit Breakers
        cb_status = "closed" if i <= 4 else "open"
        cb_ops = 2850 + i * 150
        cb_health = calculate_health_score("Circuit Breaker", 45 + np.random.normal(0, 2),
                                          75 + np.random.normal(0, 5), 5 + i, cb_ops)
        assets.append(AssetData(
            id=f"CB{i}",
            name=f"Circuit Breaker {i}",
            type="Circuit Breaker",
            status=cb_status,
            health=cb_health,
            parameters={
                "rating": "400 kV" if i <= 3 else "220 kV",
                "breaking_capacity": "50 kA" if i <= 3 else "40 kA",
                "SF6_pressure": f"{6.2 + np.random.uniform(-0.1, 0.1):.1f} bar",
                "operations": str(cb_ops),
                "age": f"{5 + i} years"
            }
        ))

    # 3. CURRENT TRANSFORMERS (CTs)
    for i in range(1, 9):  # 8 CTs
        ct_health = 92 + np.random.uniform(-3, 5)
        assets.append(AssetData(
            id=f"CT{i}",
            name=f"Current Transformer {i}",
            type="Current Transformer",
            status="operational",
            health=ct_health,
            parameters={
                "ratio": "2000/1 A" if i <= 4 else "1600/1 A",
                "voltage": "400 kV" if i <= 4 else "220 kV",
                "accuracy": "0.2S",
                "burden": "30 VA",
                "insulation": "Oil-filled"
            }
        ))

    # 4. CAPACITOR VOLTAGE TRANSFORMERS (CVTs)
    for i in range(1, 7):  # 6 CVTs
        cvt_health = 94 + np.random.uniform(-2, 3)
        assets.append(AssetData(
            id=f"CVT{i}",
            name=f"Voltage Transformer {i}",
            type="Capacitor Voltage Transformer",
            status="operational",
            health=cvt_health,
            parameters={
                "ratio": "400kV/110V" if i <= 3 else "220kV/110V",
                "accuracy": "0.2",
                "burden": "100 VA",
                "capacitance": f"{4400 + i*100} pF"
            }
        ))

    # 5. ISOLATORS/DISCONNECTORS
    for i in range(1, 13):  # 12 Isolators
        iso_status = "closed" if i <= 8 else "open"
        iso_health = 96 + np.random.uniform(-3, 2)
        assets.append(AssetData(
            id=f"ISO{i}",
            name=f"Isolator {i}",
            type="Isolator",
            status=iso_status,
            health=iso_health,
            parameters={
                "rating": "400 kV" if i <= 6 else "220 kV",
                "current": "2000 A" if i <= 6 else "1600 A",
                "type": "Double Break",
                "drive": "Motorized"
            }
        ))

    # 6. LIGHTNING ARRESTERS
    for i in range(1, 7):  # 6 Lightning Arresters
        la_health = 93 + np.random.uniform(-2, 4)
        assets.append(AssetData(
            id=f"LA{i}",
            name=f"Lightning Arrester {i}",
            type="Lightning Arrester",
            status="operational",
            health=la_health,
            parameters={
                "rating": "360 kV" if i <= 3 else "198 kV",
                "MCOV": "318 kV" if i <= 3 else "174 kV",
                "type": "Zinc Oxide Gapless",
                "leakage_current": f"{0.5 + np.random.uniform(-0.1, 0.1):.2f} mA"
            }
        ))

    # 7. BUS BARS
    for i in range(1, 5):  # 4 Bus sections
        bus_health = 97 + np.random.uniform(-1, 2)
        assets.append(AssetData(
            id=f"BUS{i}",
            name=f"Bus Bar Section {i}",
            type="Bus Bar",
            status="energized",
            health=bus_health,
            parameters={
                "voltage": "400 kV" if i <= 2 else "220 kV",
                "current_capacity": "3150 A",
                "material": "ACSR",
                "temperature": f"{45 + np.random.normal(0, 5):.1f}°C"
            }
        ))

    # 8. SHUNT REACTORS
    for i in range(1, 3):  # 2 Shunt Reactors
        reactor_health = 88 + np.random.uniform(-3, 5)
        assets.append(AssetData(
            id=f"SR{i}",
            name=f"Shunt Reactor {i}",
            type="Shunt Reactor",
            status="operational",
            health=reactor_health,
            parameters={
                "rating": "63 MVAR",
                "voltage": "400 kV",
                "cooling": "ONAN",
                "temperature": f"{62 + np.random.normal(0, 3):.1f}°C"
            }
        ))

    # 9. CAPACITOR BANKS
    for i in range(1, 3):  # 2 Capacitor Banks
        cap_health = 90 + np.random.uniform(-2, 4)
        assets.append(AssetData(
            id=f"CAP{i}",
            name=f"Capacitor Bank {i}",
            type="Capacitor Bank",
            status="operational" if i == 1 else "standby",
            health=cap_health,
            parameters={
                "rating": "50 MVAR",
                "voltage": "220 kV",
                "steps": "5",
                "power_factor": f"{0.95 + np.random.uniform(-0.02, 0.02):.3f}"
            }
        ))

    # 10. WAVE TRAPS
    for i in range(1, 5):  # 4 Wave Traps
        wt_health = 95 + np.random.uniform(-2, 3)
        assets.append(AssetData(
            id=f"WT{i}",
            name=f"Wave Trap {i}",
            type="Wave Trap",
            status="operational",
            health=wt_health,
            parameters={
                "inductance": "0.5 mH",
                "frequency_band": "50-500 kHz",
                "rated_current": "1250 A",
                "voltage": "400 kV" if i <= 2 else "220 kV"
            }
        ))

    # 11. AUXILIARY TRANSFORMERS
    assets.extend([
        AssetData(
            id="AUX1",
            name="Station Service Transformer 1",
            type="Auxiliary Transformer",
            status="operational",
            health=94 + np.random.uniform(-2, 3),
            parameters={
                "rating": "1.6 MVA",
                "voltage": "33/0.415 kV",
                "cooling": "ONAN",
                "load": f"{35 + np.random.normal(0, 5):.1f}%"
            }
        ),
        AssetData(
            id="AUX2",
            name="Station Service Transformer 2",
            type="Auxiliary Transformer",
            status="standby",
            health=92 + np.random.uniform(-2, 3),
            parameters={
                "rating": "1.6 MVA",
                "voltage": "33/0.415 kV",
                "cooling": "ONAN",
                "load": "0%"
            }
        )
    ])

    # 12. BATTERY BANK & DC SYSTEM
    assets.extend([
        AssetData(
            id="BAT1",
            name="Battery Bank 220V DC",
            type="Battery System",
            status="operational",
            health=89 + np.random.uniform(-2, 4),
            parameters={
                "voltage": "220 V DC",
                "capacity": "300 Ah",
                "cells": "110",
                "charge_level": f"{98 + np.random.uniform(-2, 1):.1f}%",
                "type": "VRLA"
            }
        ),
        AssetData(
            id="CHG1",
            name="Battery Charger 1",
            type="Battery Charger",
            status="operational",
            health=93 + np.random.uniform(-1, 2),
            parameters={
                "input": "415 V AC",
                "output": "220 V DC",
                "current": "100 A",
                "mode": "Float Charging"
            }
        )
    ])

    # 13. PROTECTION & CONTROL PANELS
    assets.extend([
        AssetData(
            id="PNL1",
            name="Main Protection Panel",
            type="Control Panel",
            status="operational",
            health=96 + np.random.uniform(-1, 2),
            parameters={
                "relays": "Distance, Differential, Overcurrent",
                "communication": "IEC 61850",
                "redundancy": "Dual Channel",
                "last_test": "15 days ago"
            }
        ),
        AssetData(
            id="SCADA1",
            name="SCADA System",
            type="SCADA",
            status="operational",
            health=98 + np.random.uniform(-1, 1),
            parameters={
                "protocol": "IEC 61850/104",
                "points": "2500",
                "update_rate": "1 sec",
                "redundancy": "Hot Standby"
            }
        )
    ])

    # 14. FIRE PROTECTION SYSTEM
    assets.append(AssetData(
        id="FIRE1",
        name="Fire Protection System",
        type="Fire System",
        status="armed",
        health=99 + np.random.uniform(-0.5, 0.5),
        parameters={
            "type": "Water Spray & FM200",
            "zones": "8",
            "detectors": "Heat & Smoke",
            "last_test": "7 days ago"
        }
    ))

    # 15. EARTHING SYSTEM
    assets.append(AssetData(
        id="EARTH1",
        name="Earthing Grid",
        type="Earthing System",
        status="operational",
        health=97 + np.random.uniform(-1, 2),
        parameters={
            "resistance": f"{0.45 + np.random.uniform(-0.05, 0.05):.2f} Ω",
            "grid_type": "Mesh",
            "rods": "85",
            "last_measurement": "30 days ago"
        }
    ))

    # 16. DIESEL GENERATOR
    assets.append(AssetData(
        id="DG1",
        name="Emergency Diesel Generator",
        type="Diesel Generator",
        status="standby",
        health=91 + np.random.uniform(-2, 3),
        parameters={
            "rating": "500 kVA",
            "voltage": "415 V",
            "fuel_level": "85%",
            "runtime_hours": "245",
            "auto_start": "Enabled"
        }
    ))

    return assets
"""

@app.get("/api/metrics")
async def get_metrics():
    """Get current system metrics with real trend calculations"""
    # Get current metrics
    metrics = await get_current_metrics()

    # Calculate real trends from historical data
    try:
        from src.services.trend_calculator import get_trend_calculator

        # Get historical data for trend calculation (last 24 hours)
        historical_data = await data_manager.get_historical_metrics(hours=24)

        if historical_data and len(historical_data) > 1:
            trend_calc = get_trend_calculator(significance_threshold=0.1)

            # Calculate trends for key metrics (1 hour comparison)
            metric_names = ['total_power', 'efficiency', 'voltage_stability', 'frequency']
            trends = {}

            for metric_name in metric_names:
                if metric_name in metrics:
                    trend = trend_calc.calculate_trend(
                        current_value=metrics[metric_name],
                        historical_data=historical_data,
                        metric_key=metric_name,
                        period='1h'  # Compare with 1 hour ago
                    )

                    # Add trend information to metrics
                    trends[metric_name] = {
                        'value': trend_calc.format_trend_display(trend),
                        'percentage': round(trend.percentage_change, 6),  # Keep 6 decimals
                        'direction': trend.trend_direction,
                        'is_significant': trend.is_significant,
                        'previous_value': trend.previous_value,
                        'absolute_change': round(trend.absolute_change, 6)  # Keep 6 decimals
                    }

            metrics['trends'] = trends
        else:
            # Not enough historical data - return neutral trends
            metrics['trends'] = {
                'total_power': {'value': '±0.0%', 'percentage': 0, 'direction': 'stable', 'is_significant': False},
                'efficiency': {'value': '±0.0%', 'percentage': 0, 'direction': 'stable', 'is_significant': False},
                'voltage_stability': {'value': '±0.0%', 'percentage': 0, 'direction': 'stable', 'is_significant': False},
                'frequency': {'value': '±0.0%', 'percentage': 0, 'direction': 'stable', 'is_significant': False}
            }

    except Exception as e:
        logger.error(f"Error calculating trends: {e}")
        # Fallback to no trends if error occurs
        metrics['trends'] = {}

    return metrics

@app.get("/api/scada/data")
async def get_scada_data():
    """Get latest SCADA data"""
    if not scada:
        raise HTTPException(status_code=503, detail="SCADA system not available")

    try:
        # Get integrated SCADA and IoT data
        recent_data = scada.get_integrated_data()
        return {
            "status": "connected",
            "timestamp": datetime.now(IST).isoformat(),
            "data": recent_data,
            "points_count": len(recent_data) if isinstance(recent_data, list) else 0
        }
    except Exception as e:
        logger.error(f"Error getting SCADA data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_llm_insights(anomalies, predictions, optimization, metrics, current_data):
    """Generate intelligent, data-driven insights based on AI/ML analysis results with circuit topology awareness"""
    insights = {
        "summary": "",
        "critical_findings": [],
        "recommendations": [],
        "health_assessment": "",
        "operational_status": "",
        "circuit_analysis": "",
        "analysis_depth": "comprehensive"
    }

    # Circuit topology understanding (Indian EHV 400/220 kV Substation)
    circuit_context = {
        "topology": "Double busbar with bus coupler configuration",
        "primary_voltage": "400 kV (grid connection)",
        "secondary_voltage": "220 kV (distribution)",
        "transformers": ["TX1_400_220 (315 MVA)", "TX2_400_220 (315 MVA) - Redundant"],
        "feeders": ["220 kV Feeder 1 (5 km)", "220 kV Feeder 2 (4.5 km)"],
        "protection": "Differential, Distance, Busbar, and Breaker Failure protection schemes"
    }

    # Analyze anomalies by severity
    high_severity_anomalies = [a for a in anomalies if a.get('severity') == 'high']
    medium_severity_anomalies = [a for a in anomalies if a.get('severity') == 'medium']

    # Analyze predictions by urgency
    critical_predictions = [p for p in predictions if p.get('urgency') in ['critical', 'high']]
    medium_predictions = [p for p in predictions if p.get('urgency') == 'medium']

    # Calculate key metrics
    avg_health = sum(d.get('health_score', 100) for d in current_data.values()) / len(current_data) if current_data else 100
    total_power = metrics.get('total_power', 0)
    voltage_stability = metrics.get('voltage_stability', 0)
    power_factor = metrics.get('power_factor', 0.95)

    # Count asset types with issues
    transformer_issues = [a for a in anomalies if 'TR' in a.get('asset_id', '')]
    breaker_issues = [a for a in anomalies if 'CB' in a.get('asset_id', '')]

    # Generate dynamic summary based on actual conditions
    if high_severity_anomalies:
        affected_assets = ', '.join([a.get('asset_id', 'Unknown') for a in high_severity_anomalies[:3]])
        insights["summary"] = f"⚠️ CRITICAL ALERT: Detected {len(high_severity_anomalies)} high-severity anomalies requiring immediate investigation. Affected equipment: {affected_assets}. Substation operating at {avg_health:.1f}% fleet health with {total_power:.1f} MW load."
    elif medium_severity_anomalies or critical_predictions:
        insights["summary"] = f"📊 MONITORING REQUIRED: System shows {len(medium_severity_anomalies)} medium-severity anomalies and {len(critical_predictions)} assets flagged for preventive maintenance. Current load: {total_power:.1f} MW at {voltage_stability:.1f}% voltage stability. Fleet health: {avg_health:.1f}%."
    else:
        insights["summary"] = f"✅ OPTIMAL OPERATION: All {len(current_data)} assets operating within normal parameters. Load balanced at {total_power:.1f} MW with {voltage_stability:.1f}% voltage stability and {power_factor:.2f} power factor. Fleet health: {avg_health:.1f}%."

    # Generate data-driven critical findings
    if high_severity_anomalies:
        for anomaly in high_severity_anomalies[:3]:
            asset_id = anomaly.get('asset_id', 'Unknown')
            score = anomaly.get('anomaly_score', 0)
            asset_data = current_data.get(asset_id, {})

            # Analyze what's abnormal
            temp = asset_data.get('temperature', 0)
            voltage = asset_data.get('voltage', 0)
            current = asset_data.get('current', 0)

            if 'TR' in asset_id:
                insights["critical_findings"].append(
                    f"{asset_id}: Anomaly score {score:.2f} detected. Operating at {temp:.1f}°C, {voltage:.1f} kV, {current:.1f} A. Pattern suggests thermal runaway or winding degradation - schedule immediate oil analysis and dissolved gas testing."
                )
            elif 'CB' in asset_id:
                insights["critical_findings"].append(
                    f"{asset_id}: Anomaly score {score:.2f}. Contact resistance or mechanism wear detected. Current operating conditions: {voltage:.1f} kV, {current:.1f} A. Recommend timing test and contact inspection."
                )
            else:
                insights["critical_findings"].append(
                    f"{asset_id}: Anomaly detected (score {score:.2f}). Abnormal operational signature at {voltage:.1f} kV, {current:.1f} A. Requires diagnostic evaluation."
                )

    if critical_predictions:
        for pred in critical_predictions[:2]:
            asset_id = pred.get('asset_id', 'Unknown')
            current_health = pred.get('current_health', 100)
            predicted_health = pred.get('predicted_health', 100)
            health_drop = current_health - predicted_health

            insights["critical_findings"].append(
                f"Predictive Analytics - {asset_id}: ML model forecasts {health_drop:.1f}% health degradation (from {current_health:.1f}% to {predicted_health:.1f}%). Recommend scheduling maintenance before reaching {predicted_health:.1f}% threshold."
            )

    # Generate intelligent recommendations based on data
    if transformer_issues:
        insights["recommendations"].append(
            f"Transformer Maintenance: {len(transformer_issues)} transformer(s) showing abnormal patterns. Schedule oil testing, thermography scan, and dissolved gas analysis within 48 hours."
        )

    if breaker_issues:
        insights["recommendations"].append(
            f"Circuit Breaker Assessment: {len(breaker_issues)} breaker(s) require inspection. Perform contact resistance measurement and timing tests during next maintenance window."
        )

    if power_factor < 0.92:
        insights["recommendations"].append(
            f"Power Quality: Power factor at {power_factor:.2f} is below optimal. Review capacitor bank status and consider reactive power compensation to improve efficiency."
        )

    if voltage_stability < 95:
        insights["recommendations"].append(
            f"Voltage Regulation: Stability at {voltage_stability:.1f}% requires attention. Check tap changer positions on transformers and review voltage control strategy."
        )

    if total_power > 250:  # Assuming high load threshold
        insights["recommendations"].append(
            f"Load Management: Current load at {total_power:.1f} MW approaching capacity. Consider load redistribution across 220 kV feeders to optimize transformer loading."
        )

    # Default recommendations if none triggered
    if not insights["recommendations"]:
        insights["recommendations"] = [
            f"Routine Monitoring: Maintain current surveillance protocols for all {len(current_data)} assets.",
            f"Predictive Maintenance: Continue trend analysis on {len(predictions)} assets with scheduled health assessments.",
            f"Load Optimization: Current {total_power:.1f} MW load is well-distributed. Monitor for seasonal demand changes."
        ]

    # Dynamic health assessment
    if avg_health >= 98:
        insights["health_assessment"] = f"EXCELLENT: Fleet health at {avg_health:.1f}% - all {len(current_data)} assets operating within design specifications. Zero critical degradation indicators detected."
    elif avg_health >= 95:
        insights["health_assessment"] = f"VERY GOOD: Fleet health at {avg_health:.1f}% - minor wear patterns observed in {len(medium_predictions)} assets. Continue scheduled maintenance program."
    elif avg_health >= 90:
        insights["health_assessment"] = f"GOOD: Fleet health at {avg_health:.1f}% - {len(critical_predictions)} assets showing early degradation signs. Proactive intervention recommended."
    elif avg_health >= 85:
        insights["health_assessment"] = f"FAIR: Fleet health at {avg_health:.1f}% - multiple assets require attention. Prioritize maintenance on critical equipment."
    else:
        insights["health_assessment"] = f"⚠️ ATTENTION REQUIRED: Fleet health at {avg_health:.1f}% - significant degradation detected. Immediate assessment and intervention plan needed."

    # Detailed operational status
    freq = metrics.get('frequency', 50.0)
    freq_status = "stable" if 49.9 <= freq <= 50.1 else "⚠️ deviation"

    insights["operational_status"] = (
        f"Load: {total_power:.1f} MW | Voltage Stability: {voltage_stability:.1f}% | "
        f"Frequency: {freq:.2f} Hz ({freq_status}) | Power Factor: {power_factor:.2f} | "
        f"Assets Online: {len(current_data)}"
    )

    # Circuit topology-aware analysis
    tx1_data = current_data.get('TR1', {})
    tx2_data = current_data.get('TR2', {})

    if high_severity_anomalies:
        affected_tx = [a for a in anomalies if 'TR' in a.get('asset_id', '')]
        if affected_tx:
            insights["circuit_analysis"] = (
                f"CIRCUIT IMPACT ASSESSMENT: {len(affected_tx)} transformer(s) in the 400/220 kV double-busbar configuration showing anomalies. "
                f"With total installed capacity of 630 MVA (2×315 MVA), current load at {total_power:.1f} MW represents "
                f"{(total_power/630)*100:.1f}% utilization. "
            )
            if len(affected_tx) == 2:
                insights["circuit_analysis"] += (
                    "⚠️ CRITICAL: Both TX1 and TX2 affected - zero redundancy available. "
                    "N-1 contingency violated. Immediate load shedding or grid support may be required."
                )
            elif 'TR1' in str(affected_tx):
                tx2_health = tx2_data.get('health_score', 100)
                insights["circuit_analysis"] += (
                    f"TX2 (backup) available at {tx2_health:.1f}% health. "
                    f"Can handle {315*(tx2_health/100):.0f} MVA. Bus coupler must remain closed for N-1 security."
                )
            else:
                tx1_health = tx1_data.get('health_score', 100)
                insights["circuit_analysis"] += (
                    f"TX1 (primary) available at {tx1_health:.1f}% health. "
                    f"Can handle {315*(tx1_health/100):.0f} MVA. N-1 criterion maintained."
                )

        affected_cb = [a for a in anomalies if 'CB' in a.get('asset_id', '')]
        if affected_cb:
            if insights["circuit_analysis"]:
                insights["circuit_analysis"] += " | "
            insights["circuit_analysis"] += (
                f"PROTECTION SCHEME ALERT: {len(affected_cb)} circuit breaker(s) showing abnormal operation. "
                "This may compromise busbar protection and breaker failure schemes. "
                "Verify backup protection is functional."
            )
    else:
        # Normal operation analysis
        tx1_load = tx1_data.get('power', 0)
        tx2_load = tx2_data.get('power', 0)
        load_balance = abs(tx1_load - tx2_load) / max(tx1_load + tx2_load, 1) * 100 if (tx1_load + tx2_load) > 0 else 0

        insights["circuit_analysis"] = (
            f"CIRCUIT STATUS: Double busbar configuration operating normally. "
            f"TX1 loading: {tx1_load:.1f} MW, TX2 loading: {tx2_load:.1f} MW. "
            f"Load imbalance: {load_balance:.1f}%. "
        )

        if load_balance > 20:
            insights["circuit_analysis"] += (
                "⚠️ High load imbalance detected - consider redistributing load via 220 kV feeders or adjusting bus coupler."
            )
        else:
            insights["circuit_analysis"] += (
                "Load well-balanced across transformers. N-1 contingency fully supported. "
                f"Available reserve capacity: {630 - total_power:.0f} MW ({((630-total_power)/630)*100:.1f}%)."
            )

    return insights

@app.post("/api/simulation")
async def run_simulation(request: SimulationRequest):
    """Run a simulation scenario"""
    if not load_flow:
        raise HTTPException(status_code=503, detail="Simulation engine not available")

    try:
        # Run load flow analysis
        results = load_flow.solve()

        # Analyze based on scenario
        if request.scenario == "contingency":
            # Simulate N-1 contingency
            contingency_results = load_flow.run_contingency_analysis()
            results["contingency"] = contingency_results
        elif request.scenario == "fault":
            # Simulate fault condition
            fault_results = load_flow.analyze_fault_current()
            results["fault"] = fault_results

        return {
            "scenario": request.scenario,
            "timestamp": datetime.now(IST).isoformat(),
            "results": results,
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/analysis")
async def get_ai_analysis():
    """Get AI/ML analysis results"""
    if not ai_manager or not asset_manager:
        raise HTTPException(status_code=503, detail="AI system not available")

    try:
        # Prepare current asset data for analysis
        current_data = {}
        assets_dict = {}
        for asset_id, asset in asset_manager.assets.items():
            rt_data = asset.real_time_data
            voltage = rt_data.get('voltage_kv', asset.electrical.voltage_rating_kv)
            current = rt_data.get('current_a', asset.electrical.current_rating_a * 0.7)

            current_data[asset_id] = {
                'asset_type': asset.asset_type.value,
                'voltage': voltage,
                'current': current,
                'power': voltage * current / 1000,
                'temperature': asset.thermal.temperature_celsius,
                'health_score': asset.health.overall_health,
                'age_days': (datetime.now(IST).replace(tzinfo=None) - asset.commissioned_date).days
            }

            assets_dict[asset_id] = {
                'name': asset.name,
                'status': asset.status.value,
                'health': asset.health.overall_health,
                'parameters': {
                    'voltage': voltage,
                    'current': current,
                    'temperature': asset.thermal.temperature_celsius,
                    'power': voltage * current / 1000
                }
            }

        # Get metrics
        metrics = {
            'total_power': sum(d['power'] for d in current_data.values()),
            'frequency': 50.0,
            'voltage_stability': 98.5,
            'efficiency': 96.8,
            'power_factor': 0.95
        }

        # Use the analyze_current_state method which combines all AI features
        analysis_result = ai_manager.analyze_current_state(assets_dict, metrics)

        # Get anomaly detection results (backup if analyze_current_state doesn't return anomalies)
        anomalies = analysis_result.get('anomalies', [])
        if not anomalies:
            try:
                anomalies = ai_manager.anomaly_detector.detect_anomalies(current_data)
            except Exception as e:
                logger.warning(f"Anomaly detection error: {e}")
                anomalies = []

        # Get predictive maintenance results (backup if not in analysis_result)
        predictions = analysis_result.get('predictions', [])
        if not predictions:
            try:
                predictions = ai_manager.predictive_model.predict_health_degradation(current_data)
            except Exception as e:
                logger.warning(f"Prediction error: {e}")
                predictions = []

        # Get optimization recommendations (backup if not in analysis_result)
        optimization = analysis_result.get('optimization', {})
        if not optimization:
            try:
                optimization = ai_manager.optimizer.optimize_power_flow(metrics)
            except Exception as e:
                logger.warning(f"Optimization error: {e}")
                optimization = {}

        # Generate LLM-based insights
        llm_insights = generate_llm_insights(anomalies, predictions, optimization, metrics, current_data)

        return {
            "timestamp": datetime.now(IST).isoformat(),
            "anomalies": anomalies,
            "predictions": predictions,
            "optimization": optimization,
            "llm_insights": llm_insights,
            "model_confidence": analysis_result.get('model_confidence', 0.92)
        }
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/iot/devices")
async def get_iot_devices():
    """Get IoT devices and sensors"""
    try:
        # Generate IoT device data from assets
        devices = []
        if asset_manager:
            for asset_id, asset in asset_manager.assets.items():
                devices.append({
                    "id": asset_id,
                    "name": asset.name,
                    "type": asset.asset_type.value,
                    "status": "online" if asset.status.value == "operational" else "offline",
                    "location": asset.location,
                    "last_update": datetime.now(IST).isoformat(),
                    "metrics": {
                        "temperature": asset.thermal.temperature_celsius,
                        "health_score": asset.health.overall_health,
                        "voltage": asset.electrical.voltage_rating_kv
                    }
                })

        return {
            "devices": devices,
            "total_count": len(devices),
            "online_count": len([d for d in devices if d["status"] == "online"]),
            "timestamp": datetime.now(IST).isoformat()
        }
    except Exception as e:
        logger.error(f"IoT devices error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/control")
async def send_control_command(command: ControlCommand):
    """Send control command to asset"""
    try:
        # Log the command
        logger.info(f"Control command: {command.asset_id} - {command.command} = {command.value}")

        # In a real system, this would interface with actual equipment
        # For now, we'll simulate the response
        return {
            "status": "executed",
            "asset_id": command.asset_id,
            "command": command.command,
            "value": command.value,
            "timestamp": datetime.now(IST).isoformat(),
            "confirmation": f"Command {command.command} sent to {command.asset_id}"
        }
    except Exception as e:
        logger.error(f"Control command error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()

            # Process commands from client
            try:
                command = json.loads(data)
                if command.get("type") == "subscribe":
                    # Handle subscription requests
                    await websocket.send_json({
                        "type": "subscription_confirmed",
                        "channels": command.get("channels", [])
                    })
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache and storage statistics"""
    return data_manager.get_cache_stats()

@app.get("/api/metrics/historical")
async def get_historical_metrics(hours: int = 24):
    """Get historical metrics for analysis"""
    metrics = await data_manager.get_historical_metrics(hours=hours)
    return {
        "hours": hours,
        "count": len(metrics),
        "data": metrics
    }

@app.get("/api/realtime/summary")
async def get_realtime_summary():
    """Get summary of all real-time data"""
    return await data_manager.get_realtime_summary()

@app.post("/api/data/cleanup")
async def cleanup_old_data():
    """Trigger cleanup of old data"""
    await data_manager.cleanup_old_data()
    return {"status": "cleanup_completed", "timestamp": datetime.now(IST).isoformat()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    cache_stats = data_manager.get_cache_stats()
    return {
        "status": "healthy",
        "timestamp": datetime.now(IST).isoformat(),
        "components": {
            "scada": scada is not None,
            "load_flow": load_flow is not None,
            "ai_manager": ai_manager is not None,
            "monitor": monitor is not None,
            "websocket_connections": len(manager.active_connections),
            "redis_connected": cache_stats.get("redis_connected", False),
            "cache_size": cache_stats.get("memory_cache_size", 0)
        },
        "storage_strategy": {
            "realtime_cache_ttl": Config.REALTIME_CACHE_TTL,
            "metrics_storage_interval": Config.METRICS_STORAGE_INTERVAL,
            "last_storage": cache_stats.get("last_storage")
        }
    }

if __name__ == "__main__":
    import uvicorn
    # Use configuration from environment
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT, reload=False)