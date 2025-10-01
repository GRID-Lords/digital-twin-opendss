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
from src.database import db  # Import database module

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

        # Initialize Asset Manager
        asset_manager = SubstationAssetManager()
        logger.info(f"Asset Manager initialized with {len(asset_manager.assets)} assets")

        # Set asset manager in asset endpoints
        from src.api.asset_endpoints import set_asset_manager
        set_asset_manager(asset_manager)

        # Set managers in historical endpoints
        from src.api.historical_endpoints import set_managers
        set_managers(data_manager, asset_manager)

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
            timestamp = datetime.now()

            # Simulate various metrics
            data = {
                "timestamp": timestamp.isoformat(),
                "transformers": {
                    "T1": {
                        "load": 85 + np.random.normal(0, 5),
                        "temperature": 65 + np.random.normal(0, 3),
                        "oil_level": 95 + np.random.normal(0, 2)
                    },
                    "T2": {
                        "load": 78 + np.random.normal(0, 5),
                        "temperature": 62 + np.random.normal(0, 3),
                        "oil_level": 93 + np.random.normal(0, 2)
                    }
                },
                "breakers": {
                    "CB1": {"status": "closed", "operations": 1250},
                    "CB2": {"status": "closed", "operations": 980},
                    "CB3": {"status": "open", "operations": 1100}
                },
                "bus_voltages": {
                    "400kV": 398.5 + np.random.normal(0, 1),
                    "220kV": 219.2 + np.random.normal(0, 0.5)
                },
                "power_flow": {
                    "active_power": 350 + np.random.normal(0, 10),
                    "reactive_power": 120 + np.random.normal(0, 5),
                    "power_factor": 0.95 + np.random.normal(0, 0.02)
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

                        # Calculate age in days
                        age_delta = datetime.now() - asset.commissioned_date
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

async def get_current_metrics():
    """Get current system metrics with optimized storage"""
    timestamp = datetime.now()

    # Generate real-time metrics
    total_power = 350 + np.random.normal(0, 10)
    efficiency = 92 + np.random.normal(0, 2)

    metrics = {
        "timestamp": timestamp.isoformat(),
        "system_health": efficiency,
        "total_load": total_power,
        "total_power": total_power,
        "efficiency": efficiency,
        "power_factor": 0.95 + np.random.normal(0, 0.02),
        "voltage_stability": 98 + np.random.normal(0, 1),
        "frequency": 50 + np.random.normal(0, 0.1),
        "generation": total_power * 1.05,  # Generation slightly higher than load
        "losses": total_power * 0.05,  # 5% losses
        "alerts": [],
        "predictions": {}
    }

    # Store in real-time cache for immediate display
    await data_manager.store_realtime_data("current_metrics", metrics)

    # Buffer metrics for periodic database storage (hourly)
    await data_manager.buffer_metrics(metrics)

    # Add AI predictions if available
    if ai_manager:
        try:
            # Generate sample current data for health degradation prediction
            current_data = {
                "PowerTransformer_T1": {
                    "voltage": 400 + np.random.normal(0, 5),
                    "current": 200 + np.random.normal(0, 10),
                    "power": total_power * 0.6,
                    "temperature": 65 + np.random.normal(0, 5),
                    "health_score": 85 + np.random.normal(0, 3)
                },
                "DistributionTransformer_T2": {
                    "voltage": 220 + np.random.normal(0, 3),
                    "current": 150 + np.random.normal(0, 8),
                    "power": total_power * 0.4,
                    "temperature": 60 + np.random.normal(0, 5),
                    "health_score": 82 + np.random.normal(0, 3)
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

    # Calculate final health score
    health = base_health - temp_penalty - load_penalty - age_penalty - ops_penalty

    # Add small random variation for realism (±1%)
    health += np.random.uniform(-1, 1)

    return max(0, min(100, health))

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
    """Get current system metrics"""
    return await get_current_metrics()

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
            "timestamp": datetime.now().isoformat(),
            "data": recent_data,
            "points_count": len(recent_data) if isinstance(recent_data, list) else 0
        }
    except Exception as e:
        logger.error(f"Error getting SCADA data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/analysis")
async def get_ai_analysis():
    """Get AI/ML analysis results"""
    if not ai_manager:
        raise HTTPException(status_code=503, detail="AI system not available")

    try:
        # Generate sample data for demonstration
        sample_data = pd.DataFrame(np.random.randn(10, 10))

        # Use actual AI manager methods with proper data format
        current_data = {
            "PowerTransformer_T1": {
                "voltage": 400 + np.random.normal(0, 5),
                "current": 200 + np.random.normal(0, 10),
                "power": 80000 + np.random.normal(0, 1000),
                "temperature": 65 + np.random.normal(0, 5),
                "health_score": 85 + np.random.normal(0, 3)
            }
        }

        # Get health predictions using actual method via predictive_model
        health_predictions = ai_manager.predictive_model.predict_health_degradation(current_data)
        anomalies = [1 if p.get("predicted_health", 100) < 70 else 0 for p in health_predictions]
        failures = [(100 - p.get("predicted_health", 100)) / 100 for p in health_predictions]

        # Calculate statistics
        anomaly_rate = np.mean(anomalies) * 100
        avg_failure_prob = np.mean(failures) * 100

        return {
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "anomaly_detection": {
                    "rate": f"{anomaly_rate:.2f}%",
                    "detected_count": int(np.sum(anomalies)),
                    "total_samples": len(anomalies)
                },
                "failure_prediction": {
                    "average_probability": f"{avg_failure_prob:.2f}%",
                    "high_risk_assets": [],
                    "maintenance_recommendations": []
                },
                "optimization": {
                    "load_balancing": "optimal",
                    "voltage_profile": "within_limits",
                    "losses": "3.2%"
                }
            },
            "model_confidence": 0.92
        }
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
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
            "timestamp": datetime.now().isoformat(),
            "confirmation": f"Command {command.command} sent to {command.asset_id}"
        }
    except Exception as e:
        logger.error(f"Control command error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint
@app.websocket("/ws")
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
    return {"status": "cleanup_completed", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    cache_stats = data_manager.get_cache_stats()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
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