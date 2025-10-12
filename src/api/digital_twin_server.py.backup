#!/usr/bin/env python3
"""
Digital Twin Server for Indian EHV 400/220 kV Substation
Real-time simulation, monitoring, and control via REST API and WebSocket
"""

import asyncio
import json
import logging
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
import websockets
from websockets.server import WebSocketServerProtocol
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel
import opendssdirect as dss
from visualization.circuit_visualizer import OpenDSSVisualizer
from models.ai_ml_models import SubstationAIManager
from integration.scada_integration import SCADAIntegrationManager
from simulation.load_flow import LoadFlowAnalysis
from database import db
from utils.dss_validator import validate_dss_file_changes, DSSValidator
import matplotlib
matplotlib.use('Agg', force=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS FOR DIGITAL TWIN
# ============================================================================

@dataclass
class AssetStatus:
    """Asset status for digital twin"""
    asset_id: str
    asset_type: str
    status: str  # 'healthy', 'warning', 'fault', 'maintenance'
    voltage: float
    current: float
    power: float
    temperature: float
    timestamp: str
    health_score: float  # 0-100

@dataclass
class SubstationMetrics:
    """Overall substation metrics"""
    total_power: float
    total_load: float
    efficiency: float
    voltage_stability: float
    frequency: float
    timestamp: str
    grid_connection: bool
    fault_count: int

@dataclass
class FaultAnalysis:
    """Fault analysis results"""
    fault_type: str
    fault_location: str
    fault_impedance: float
    fault_current: float
    protection_operation: bool
    clearance_time: float
    timestamp: str

class DigitalTwinRequest(BaseModel):
    """Request model for digital twin operations"""
    operation: str
    parameters: Dict[str, Any] = {}

class AssetControlRequest(BaseModel):
    """Request model for asset control"""
    asset_id: str
    action: str  # 'open', 'close', 'trip', 'reset'
    parameters: Dict[str, Any] = {}

# ============================================================================
# DIGITAL TWIN CORE CLASS
# ============================================================================

class IndianEHVSubstationDigitalTwin:
    """Digital Twin for Indian EHV 400/220 kV Substation"""
    
    def __init__(self, dss_file: str = "src/models/IndianEHVSubstation.dss"):
        self.dss_file = Path(dss_file)
        self.visualizer = OpenDSSVisualizer(str(self.dss_file))
        self.is_running = False
        self.simulation_thread = None
        self.websocket_clients: List[WebSocketServerProtocol] = []

        # Digital twin state
        self.assets: Dict[str, AssetStatus] = {}
        self.metrics = SubstationMetrics(
            total_power=0.0, total_load=0.0, efficiency=0.0,
            voltage_stability=0.0, frequency=50.0, timestamp="",
            grid_connection=True, fault_count=0
        )
        self.faults: List[FaultAnalysis] = []

        # OpenDSS Load Flow Analysis
        self.load_flow = LoadFlowAnalysis()
        self.opendss_results = {}

        # AI/ML integration
        self.ai_manager = SubstationAIManager()

        # SCADA integration
        scada_config = {
            'collection_interval': 1.0,
            'modbus_host': 'localhost',
            'modbus_port': 502
        }
        self.scada_manager = SCADAIntegrationManager(scada_config)

        # Initialize the substation
        self._initialize_substation()
    
    def _initialize_substation(self):
        """Initialize the substation model"""
        try:
            logger.info("Initializing Indian EHV Substation Digital Twin...")
            self.visualizer.load_and_solve()

            # Load OpenDSS circuit for real-time analysis
            self.load_flow.load_circuit(str(self.dss_file))

            # Run initial solve to get baseline data
            self.opendss_results = self.load_flow.solve()
            logger.info(f"Initial OpenDSS solve: {self.opendss_results}")

            self._setup_assets()

            # Initialize AI/ML models
            self.ai_manager.initialize_with_synthetic_data()

            # Start SCADA integration
            self.scada_manager.start_integration()

            # Initialize DSS file versioning in database
            self._initialize_dss_versioning()

            logger.info("Digital Twin initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize digital twin: {e}")
            raise

    def _initialize_dss_versioning(self):
        """Initialize DSS file versioning - create first version if none exists"""
        try:
            # Check if any versions exist
            active_version = db.get_active_dss_version()
            if not active_version:
                # No versions exist, create the first one from the original file
                if self.dss_file.exists():
                    logger.info("No DSS versions found, creating initial version from file...")
                    original_content = self.dss_file.read_text()
                    version_id = db.create_dss_version(
                        content=original_content,
                        created_by='system',
                        description='Initial version from original DSS file'
                    )
                    logger.info(f"Created initial DSS version with ID {version_id}")
                else:
                    logger.warning(f"DSS file not found at {self.dss_file}")
            else:
                logger.info(f"Active DSS version found: v{active_version['version_number']}")
        except Exception as e:
            logger.error(f"Error initializing DSS versioning: {e}")
            # Non-fatal error, continue with initialization

    def _setup_assets(self):
        """Setup asset monitoring for all substation components with real OpenDSS data"""
        # Get initial values from OpenDSS results
        voltage_400kv = self.opendss_results.get('voltage_400kv', 400.0)
        voltage_220kv = self.opendss_results.get('voltage_220kv', 220.0)
        total_power_kw = abs(self.opendss_results.get('total_power_kw', 0))
        converged = self.opendss_results.get('converged', True)

        logger.info(f"Initializing assets with OpenDSS data: V400={voltage_400kv:.2f} kV, V220={voltage_220kv:.2f} kV, Power={total_power_kw:.2f} kW")

        # Grid connection
        self.assets["Grid400kV"] = AssetStatus(
            asset_id="Grid400kV", asset_type="GridConnection",
            status="healthy" if converged else "warning",
            voltage=voltage_400kv,
            current=total_power_kw / (voltage_400kv * 1.732) if voltage_400kv > 0 else 0,
            power=total_power_kw / 1000.0,  # Convert to MW
            temperature=25.0, timestamp=datetime.now().isoformat(),
            health_score=100.0
        )
        
        # Main transformers - Initialize with OpenDSS data
        tx_power_kw = total_power_kw / 2.0  # Split between two transformers
        tx_current = tx_power_kw / (voltage_400kv * 1.732) if voltage_400kv > 0 else 0
        load_factor = tx_power_kw / 315000.0  # 315 MVA rated
        tx_temp = 45.0 + (load_factor * 25.0)  # Temperature based on loading

        self.assets["TX1_400_220"] = AssetStatus(
            asset_id="TX1_400_220", asset_type="PowerTransformer",
            status="healthy" if converged else "warning",
            voltage=voltage_400kv,
            current=tx_current,
            power=tx_power_kw,
            temperature=tx_temp,
            timestamp=datetime.now().isoformat(),
            health_score=95.0
        )

        self.assets["TX2_400_220"] = AssetStatus(
            asset_id="TX2_400_220", asset_type="PowerTransformer",
            status="healthy" if converged else "warning",
            voltage=voltage_400kv,
            current=tx_current,
            power=tx_power_kw,
            temperature=tx_temp,
            timestamp=datetime.now().isoformat(),
            health_score=95.0
        )

        # Distribution transformers - Initialize with OpenDSS data
        dtx_power_kw = total_power_kw / 4.0  # Distribute among distribution transformers
        dtx_current = dtx_power_kw / (voltage_220kv * 1.732) if voltage_220kv > 0 else 0
        dtx_load_factor = dtx_power_kw / 50000.0  # 50 MVA rated
        dtx_temp = 50.0 + (dtx_load_factor * 20.0)

        self.assets["DTX1_220_33"] = AssetStatus(
            asset_id="DTX1_220_33", asset_type="DistributionTransformer",
            status="healthy" if converged else "warning",
            voltage=voltage_220kv,
            current=dtx_current,
            power=dtx_power_kw,
            temperature=dtx_temp,
            timestamp=datetime.now().isoformat(),
            health_score=90.0
        )

        self.assets["DTX2_220_33"] = AssetStatus(
            asset_id="DTX2_220_33", asset_type="DistributionTransformer",
            status="healthy" if converged else "warning",
            voltage=voltage_220kv,
            current=dtx_current,
            power=dtx_power_kw,
            temperature=dtx_temp,
            timestamp=datetime.now().isoformat(),
            health_score=90.0
        )
        
        # Circuit breakers
        for i in range(1, 6):
            self.assets[f"CB_{i}"] = AssetStatus(
                asset_id=f"CB_{i}", asset_type="CircuitBreaker",
                status="healthy", voltage=0.0, current=0.0, power=0.0,
                temperature=30.0, timestamp=datetime.now().isoformat(),
                health_score=98.0
            )
        
        # Loads - Initialize with real DSS file values (15 MW and 12 MW as defined in DSS)
        load1_power_kw = 15000.0  # From DSS file
        load2_power_kw = 12000.0  # From DSS file
        load_voltage_kv = 33.0    # From DSS file

        self.assets["IndustrialLoad1"] = AssetStatus(
            asset_id="IndustrialLoad1", asset_type="IndustrialLoad",
            status="healthy",
            voltage=load_voltage_kv,
            current=load1_power_kw / (load_voltage_kv * 1.732),
            power=load1_power_kw,
            temperature=35.0 + (load1_power_kw / 20000.0 * 10.0),  # Temperature based on power
            timestamp=datetime.now().isoformat(),
            health_score=85.0
        )

        self.assets["IndustrialLoad2"] = AssetStatus(
            asset_id="IndustrialLoad2", asset_type="IndustrialLoad",
            status="healthy",
            voltage=load_voltage_kv,
            current=load2_power_kw / (load_voltage_kv * 1.732),
            power=load2_power_kw,
            temperature=35.0 + (load2_power_kw / 20000.0 * 10.0),  # Temperature based on power
            timestamp=datetime.now().isoformat(),
            health_score=85.0
        )
    
    def start_simulation(self):
        """Start the digital twin simulation"""
        if not self.is_running:
            self.is_running = True
            self.simulation_thread = threading.Thread(target=self._simulation_loop)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            logger.info("Digital Twin simulation started")
    
    def stop_simulation(self):
        """Stop the digital twin simulation"""
        self.is_running = False
        if self.simulation_thread:
            self.simulation_thread.join()
        logger.info("Digital Twin simulation stopped")
    
    def _simulation_loop(self):
        """Main simulation loop for real-time updates"""
        while self.is_running:
            try:
                # Run OpenDSS solve to get real power flow data
                self.opendss_results = self.load_flow.solve()
                logger.debug(f"OpenDSS solve: converged={self.opendss_results.get('converged', False)}, total_power={self.opendss_results.get('total_power_kw', 0):.2f} kW")

                # Update asset statuses with real OpenDSS data
                self._update_asset_statuses()

                # Update substation metrics with real OpenDSS data
                self._update_substation_metrics()

                # Run AI/ML analysis
                self._run_ai_analysis()

                # Broadcast updates to WebSocket clients
                self._broadcast_updates()

                # Sleep for 1 second (1 Hz update rate)
                time.sleep(1.0)

            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                time.sleep(1.0)
    
    def _update_asset_statuses(self):
        """Update asset statuses with real OpenDSS data"""
        current_time = datetime.now().isoformat()

        # Get OpenDSS data
        dss_engine = self.load_flow.dss
        if not dss_engine:
            logger.warning("OpenDSS not available, skipping asset update")
            return

        try:
            # Update Grid Connection from OpenDSS source
            if "Grid400kV" in self.assets:
                asset = self.assets["Grid400kV"]
                asset.voltage = self.opendss_results.get('voltage_400kv', 400.0)
                asset.power = abs(self.opendss_results.get('total_power_kw', 0)) / 1000.0  # Convert to MW
                asset.current = asset.power * 1000 / (asset.voltage * 1.732) if asset.voltage > 0 else 0
                asset.temperature = 25.0
                asset.status = "healthy" if self.opendss_results.get('converged', False) else "warning"
                asset.timestamp = current_time

            # Update Power Transformers (400/220 kV)
            for transformer_id in ["TX1_400_220", "TX2_400_220"]:
                if transformer_id in self.assets:
                    asset = self.assets[transformer_id]

                    # Get transformer data from OpenDSS
                    try:
                        dss_engine.Circuit.SetActiveElement(f"Transformer.{transformer_id}")
                        powers = dss_engine.CktElement.Powers()  # Returns [kW, kvar] for each terminal
                        if powers and len(powers) >= 2:
                            # Power in kW (primary side)
                            asset.power = abs(powers[0])  # kW
                            # Voltage from OpenDSS results
                            asset.voltage = self.opendss_results.get('voltage_400kv', 400.0)
                            # Calculate current (3-phase)
                            asset.current = asset.power / (asset.voltage * 1.732) if asset.voltage > 0 else 0
                        else:
                            asset.power = abs(self.opendss_results.get('total_power_kw', 0)) / 2000.0  # Estimate
                            asset.voltage = self.opendss_results.get('voltage_400kv', 400.0)
                            asset.current = asset.power / (asset.voltage * 1.732) if asset.voltage > 0 else 0
                    except Exception as e:
                        logger.debug(f"Could not get transformer data for {transformer_id}: {e}")
                        asset.power = abs(self.opendss_results.get('total_power_kw', 0)) / 2000.0  # Estimate
                        asset.voltage = self.opendss_results.get('voltage_400kv', 400.0)
                        asset.current = asset.power / (asset.voltage * 1.732) if asset.voltage > 0 else 0

                    # Temperature based on real load
                    base_temp = 45.0
                    load_mva = asset.power / 1000.0  # Convert kW to approx MVA
                    load_factor = min(load_mva / 315.0, 1.0)  # 315 MVA rated
                    asset.temperature = base_temp + (load_factor * 35.0) + np.random.normal(0, 1)

                    # Health score based on temperature
                    if asset.temperature > 85:
                        asset.health_score = max(0, asset.health_score - 0.5)
                        asset.status = "fault"
                    elif asset.temperature > 70:
                        asset.health_score = max(60, asset.health_score - 0.1)
                        asset.status = "warning"
                    else:
                        asset.health_score = min(100, asset.health_score + 0.05)
                        asset.status = "healthy"

                    asset.timestamp = current_time

            # Update Distribution Transformers (220/33 kV)
            for transformer_id in ["DTX1_220_33", "DTX2_220_33"]:
                if transformer_id in self.assets:
                    asset = self.assets[transformer_id]

                    # Get transformer data from OpenDSS
                    try:
                        dss_engine.Circuit.SetActiveElement(f"Transformer.{transformer_id}")
                        powers = dss_engine.CktElement.Powers()
                        if powers and len(powers) >= 2:
                            asset.power = abs(powers[0])  # kW
                            asset.voltage = self.opendss_results.get('voltage_220kv', 220.0)
                            asset.current = asset.power / (asset.voltage * 1.732) if asset.voltage > 0 else 0
                        else:
                            asset.power = abs(self.opendss_results.get('total_power_kw', 0)) / 4000.0
                            asset.voltage = self.opendss_results.get('voltage_220kv', 220.0)
                            asset.current = asset.power / (asset.voltage * 1.732) if asset.voltage > 0 else 0
                    except Exception as e:
                        logger.debug(f"Could not get transformer data for {transformer_id}: {e}")
                        asset.power = abs(self.opendss_results.get('total_power_kw', 0)) / 4000.0
                        asset.voltage = self.opendss_results.get('voltage_220kv', 220.0)
                        asset.current = asset.power / (asset.voltage * 1.732) if asset.voltage > 0 else 0

                    # Temperature based on real load
                    base_temp = 50.0
                    load_mva = asset.power / 1000.0
                    load_factor = min(load_mva / 50.0, 1.0)  # 50 MVA rated
                    asset.temperature = base_temp + (load_factor * 30.0) + np.random.normal(0, 1)

                    # Health score based on temperature
                    if asset.temperature > 90:
                        asset.health_score = max(0, asset.health_score - 0.5)
                        asset.status = "fault"
                    elif asset.temperature > 75:
                        asset.health_score = max(60, asset.health_score - 0.1)
                        asset.status = "warning"
                    else:
                        asset.health_score = min(100, asset.health_score + 0.05)
                        asset.status = "healthy"

                    asset.timestamp = current_time

            # Update Circuit Breakers
            for cb_id in [f"CB_{i}" for i in range(1, 6)]:
                if cb_id in self.assets:
                    asset = self.assets[cb_id]
                    asset.temperature = 30.0 + np.random.normal(0, 2)
                    if asset.status == "fault":
                        asset.health_score = max(0, asset.health_score - 1)
                    else:
                        asset.health_score = min(100, asset.health_score + 0.05)
                        asset.status = "healthy"
                    asset.timestamp = current_time

            # Update Industrial Loads with real OpenDSS data
            for load_id in ["IndustrialLoad1", "IndustrialLoad2"]:
                if load_id in self.assets:
                    asset = self.assets[load_id]

                    # Get load data from OpenDSS
                    try:
                        dss_engine.Circuit.SetActiveElement(f"Load.{load_id}")
                        powers = dss_engine.CktElement.Powers()
                        voltages = dss_engine.CktElement.VoltagesMagAng()

                        if powers and len(powers) >= 2:
                            asset.power = abs(powers[0])  # kW
                            asset.current = abs(powers[0]) / (33.0 * 1.732) if powers[0] != 0 else 0
                        else:
                            # Fallback: use base values from DSS file
                            base_power = 15000.0 if "1" in load_id else 12000.0
                            asset.power = base_power
                            asset.current = base_power / (33.0 * 1.732)

                        # Get voltage from bus
                        if voltages and len(voltages) >= 1:
                            asset.voltage = voltages[0] / 1000.0  # Convert V to kV
                        else:
                            asset.voltage = 33.0
                    except Exception as e:
                        logger.debug(f"Could not get load data for {load_id}: {e}")
                        # Fallback values
                        base_power = 15000.0 if "1" in load_id else 12000.0
                        asset.power = base_power
                        asset.voltage = 33.0
                        asset.current = base_power / (33.0 * 1.732)

                    # Temperature based on real power
                    base_temp = 35.0
                    power_factor = asset.power / 20000.0  # Normalize
                    asset.temperature = base_temp + (power_factor * 15.0) + np.random.normal(0, 1)

                    # Health status
                    if asset.power > 18000:
                        asset.status = "warning"
                        asset.health_score = max(70, asset.health_score - 0.1)
                    else:
                        asset.status = "healthy"
                        asset.health_score = min(100, asset.health_score + 0.05)

                    asset.timestamp = current_time

        except Exception as e:
            logger.error(f"Error updating asset statuses from OpenDSS: {e}")
            # Continue with existing values
    
    def _update_substation_metrics(self):
        """Update overall substation metrics with real OpenDSS data"""
        current_time = datetime.now().isoformat()

        # Use real OpenDSS results
        total_power_kw = abs(self.opendss_results.get('total_power_kw', 0))
        total_power_kvar = abs(self.opendss_results.get('total_power_kvar', 0))
        total_losses_mw = self.opendss_results.get('total_losses_mw', 0)

        # Calculate total power in MW
        total_power_mw = total_power_kw / 1000.0

        # Calculate efficiency from real losses
        input_power_mw = total_power_mw + total_losses_mw
        self.metrics.efficiency = (total_power_mw / input_power_mw * 100) if input_power_mw > 0 else 0

        # Voltage stability from OpenDSS voltage profile
        max_voltage_pu = self.opendss_results.get('max_voltage_pu', 1.0)
        min_voltage_pu = self.opendss_results.get('min_voltage_pu', 1.0)
        voltage_deviation = (max_voltage_pu - min_voltage_pu) * 100
        self.metrics.voltage_stability = max(0, 100 - voltage_deviation)

        # Update metrics with real data
        self.metrics.total_power = total_power_mw
        self.metrics.total_load = total_power_mw
        self.metrics.timestamp = current_time
        self.metrics.frequency = 50.0 + np.random.normal(0, 0.05)  # Grid frequency variation
        self.metrics.grid_connection = (
            self.opendss_results.get('converged', False) and
            all(asset.status != "fault" for asset in self.assets.values() if asset.asset_type == "GridConnection")
        )
    
    def _run_ai_analysis(self):
        """Run AI/ML analysis for predictive maintenance"""
        try:
            # Get integrated data from SCADA
            integrated_data = self.scada_manager.get_integrated_data()
            
            # Run AI analysis
            ai_analysis = self.ai_manager.analyze_current_state(self.assets, self.metrics)
            
            # Process AI results
            if ai_analysis:
                # Handle anomalies
                for anomaly in ai_analysis.get('anomalies', []):
                    logger.warning(f"AI Detected Anomaly: {anomaly}")
                
                # Handle predictions
                for prediction in ai_analysis.get('predictions', []):
                    if prediction['urgency'] == 'critical':
                        logger.error(f"Critical Asset: {prediction}")
                    elif prediction['urgency'] == 'high':
                        logger.warning(f"High Priority Asset: {prediction}")
                
                # Handle optimization
                optimization = ai_analysis.get('optimization', {})
                if optimization:
                    logger.info(f"Optimization Score: {optimization.get('optimization_score', 0):.1f}")
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
    
    def _generate_anomaly_alert(self, asset_id: str, asset: AssetStatus):
        """Generate anomaly alert"""
        alert = {
            "type": "anomaly",
            "asset_id": asset_id,
            "severity": "high" if asset.health_score < 50 else "medium",
            "message": f"Anomaly detected in {asset_id}: Temperature={asset.temperature:.1f}°C, Health={asset.health_score:.1f}%",
            "timestamp": datetime.now().isoformat()
        }
        logger.warning(f"Anomaly Alert: {alert['message']}")
    
    def _schedule_maintenance(self, asset_id: str, asset: AssetStatus):
        """Schedule predictive maintenance"""
        maintenance = {
            "type": "maintenance",
            "asset_id": asset_id,
            "priority": "high" if asset.health_score < 60 else "medium",
            "message": f"Maintenance recommended for {asset_id}: Health={asset.health_score:.1f}%",
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Maintenance Alert: {maintenance['message']}")
    
    def _broadcast_updates(self):
        """Broadcast updates to all WebSocket clients"""
        if self.websocket_clients:
            update_data = {
                "type": "update",
                "assets": {aid: asdict(asset) for aid, asset in self.assets.items()},
                "metrics": asdict(self.metrics),
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to all connected clients
            disconnected = []
            for client in self.websocket_clients:
                try:
                    asyncio.create_task(client.send(json.dumps(update_data)))
                except:
                    disconnected.append(client)
            
            # Remove disconnected clients
            for client in disconnected:
                self.websocket_clients.remove(client)
    
    def control_asset(self, asset_id: str, action: str, parameters: Dict[str, Any] = None):
        """Control an asset (circuit breaker, transformer tap, etc.)"""
        if asset_id not in self.assets:
            raise ValueError(f"Asset {asset_id} not found")
        
        asset = self.assets[asset_id]
        
        if action == "open" and asset.asset_type == "CircuitBreaker":
            asset.status = "open"
            logger.info(f"Circuit breaker {asset_id} opened")
        elif action == "close" and asset.asset_type == "CircuitBreaker":
            asset.status = "closed"
            logger.info(f"Circuit breaker {asset_id} closed")
        elif action == "trip":
            asset.status = "fault"
            asset.health_score = max(0, asset.health_score - 10)
            logger.warning(f"Asset {asset_id} tripped")
        elif action == "reset":
            asset.status = "healthy"
            asset.health_score = min(100, asset.health_score + 20)
            logger.info(f"Asset {asset_id} reset")
        else:
            raise ValueError(f"Invalid action {action} for asset type {asset.asset_type}")
        
        return {"status": "success", "message": f"Asset {asset_id} {action} completed"}
    
    def run_fault_analysis(self, fault_type: str, fault_location: str):
        """Run fault analysis simulation"""
        # Simulate fault
        fault = FaultAnalysis(
            fault_type=fault_type,
            fault_location=fault_location,
            fault_impedance=np.random.uniform(0.1, 1.0),
            fault_current=np.random.uniform(1000, 10000),
            protection_operation=True,
            clearance_time=np.random.uniform(0.1, 0.5),
            timestamp=datetime.now().isoformat()
        )
        
        self.faults.append(fault)
        self.metrics.fault_count += 1
        
        logger.warning(f"Fault analysis: {fault_type} at {fault_location}")
        return asdict(fault)
    
    def get_asset_status(self, asset_id: str) -> Dict[str, Any]:
        """Get status of a specific asset"""
        if asset_id not in self.assets:
            raise ValueError(f"Asset {asset_id} not found")
        
        return asdict(self.assets[asset_id])
    
    def get_all_assets(self) -> Dict[str, Any]:
        """Get status of all assets"""
        return {aid: asdict(asset) for aid, asset in self.assets.items()}
    
    def get_substation_metrics(self) -> Dict[str, Any]:
        """Get overall substation metrics"""
        return asdict(self.metrics)
    
    def get_fault_history(self) -> List[Dict[str, Any]]:
        """Get fault analysis history"""
        return [asdict(fault) for fault in self.faults]

    def reload_dss_file(self, new_content: str = None):
        """Reload DSS file from content or active version in database"""
        try:
            if new_content:
                # Write content to temporary file and reload
                temp_dss_path = self.dss_file.parent / "temp_circuit.dss"
                temp_dss_path.write_text(new_content)
                self.load_flow.load_circuit(str(temp_dss_path))
                logger.info("Reloaded DSS file from provided content")
            else:
                # Reload from the active version in database
                active_version = db.get_active_dss_version()
                if active_version:
                    temp_dss_path = self.dss_file.parent / "active_circuit.dss"
                    temp_dss_path.write_text(active_version['content'])
                    self.load_flow.load_circuit(str(temp_dss_path))
                    logger.info(f"Reloaded DSS file from version {active_version['version_number']}")
                else:
                    # Fallback to original file
                    self.load_flow.load_circuit(str(self.dss_file))
                    logger.info("Reloaded DSS file from original file")

            # Re-run solve to update state
            self.opendss_results = self.load_flow.solve()
            return True
        except Exception as e:
            logger.error(f"Failed to reload DSS file: {e}")
            return False

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Initialize FastAPI app
app = FastAPI(
    title="Indian EHV Substation Digital Twin API",
    description="Real-time monitoring and control of 400/220 kV substation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
try:
    app.mount("/static", StaticFiles(directory="../../frontend/build/static"), name="static")
except:
    pass  # Frontend not built yet

# Initialize Digital Twin
digital_twin = IndianEHVSubstationDigitalTwin()

# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Indian EHV Substation Digital Twin API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "assets": "/api/assets",
            "metrics": "/api/metrics",
            "control": "/api/control",
            "faults": "/api/faults",
            "websocket": "/ws"
        }
    }

@app.get("/api/assets")
async def get_all_assets():
    """Get status of all assets"""
    return digital_twin.get_all_assets()

@app.get("/api/assets/{asset_id}")
async def get_asset(asset_id: str):
    """Get status of a specific asset"""
    try:
        return digital_twin.get_asset_status(asset_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/metrics")
async def get_metrics():
    """Get substation metrics"""
    return digital_twin.get_substation_metrics()

@app.post("/api/control")
async def control_asset(request: AssetControlRequest):
    """Control an asset (open/close circuit breaker, etc.)"""
    try:
        result = digital_twin.control_asset(
            request.asset_id, 
            request.action, 
            request.parameters
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/faults/analyze")
async def analyze_fault(fault_type: str, fault_location: str):
    """Run fault analysis"""
    try:
        result = digital_twin.run_fault_analysis(fault_type, fault_location)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/faults")
async def get_fault_history():
    """Get fault analysis history"""
    return digital_twin.get_fault_history()

@app.post("/api/simulation/start")
async def start_simulation():
    """Start digital twin simulation"""
    digital_twin.start_simulation()
    return {"status": "success", "message": "Simulation started"}

@app.post("/api/simulation/stop")
async def stop_simulation():
    """Stop digital twin simulation"""
    digital_twin.stop_simulation()
    return {"status": "success", "message": "Simulation stopped"}

@app.get("/api/visualization/network")
async def get_network_diagram():
    """Generate and return network diagram"""
    try:
        fig = digital_twin.visualizer.create_network_diagram(save=False, show=False)
        # Return base64 encoded image or file path
        return {"status": "success", "message": "Network diagram generated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scada/data")
async def get_scada_data():
    """Get current SCADA data"""
    try:
        data = digital_twin.scada_manager.get_integrated_data()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scada/alarms")
async def get_scada_alarms():
    """Get SCADA alarms"""
    try:
        alarms = digital_twin.scada_manager.get_alarms()
        return alarms
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scada/alarms/{alarm_id}/acknowledge")
async def acknowledge_alarm(alarm_id: int):
    """Acknowledge a SCADA alarm"""
    try:
        digital_twin.scada_manager.acknowledge_alarm(alarm_id)
        return {"status": "success", "message": f"Alarm {alarm_id} acknowledged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/analysis")
async def get_ai_analysis():
    """Get AI/ML analysis results"""
    try:
        analysis = digital_twin.ai_manager.analyze_current_state(
            digital_twin.get_all_assets(), 
            digital_twin.get_substation_metrics()
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/anomalies")
async def get_anomalies():
    """Get detected anomalies"""
    try:
        analysis = digital_twin.ai_manager.analyze_current_state(
            digital_twin.get_all_assets(), 
            digital_twin.get_substation_metrics()
        )
        return analysis.get('anomalies', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/predictions")
async def get_predictions():
    """Get predictive maintenance predictions"""
    try:
        analysis = digital_twin.ai_manager.analyze_current_state(
            digital_twin.get_all_assets(), 
            digital_twin.get_substation_metrics()
        )
        return analysis.get('predictions', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/optimization")
async def get_optimization():
    """Get optimization recommendations"""
    try:
        analysis = digital_twin.ai_manager.analyze_current_state(
            digital_twin.get_all_assets(), 
            digital_twin.get_substation_metrics()
        )
        return analysis.get('optimization', {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/iot/devices")
async def get_iot_devices():
    """Get IoT device status"""
    try:
        devices = digital_twin.scada_manager.iot_manager.get_all_devices()
        return {device_id: {
            'device_id': device.device_id,
            'device_type': device.device_type,
            'location': device.location,
            'status': device.status,
            'last_seen': device.last_seen
        } for device_id, device in devices.items()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/iot/devices/{device_id}/data")
async def get_iot_device_data(device_id: str):
    """Get data from specific IoT device"""
    try:
        data = digital_twin.scada_manager.iot_manager.get_device_data(device_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DSS FILE MANAGEMENT ENDPOINTS
# ============================================================================

class DSSFileRequest(BaseModel):
    """Request model for DSS file operations"""
    content: str
    description: Optional[str] = ""
    created_by: Optional[str] = "user"

class DSSValidateRequest(BaseModel):
    """Request model for DSS file validation"""
    content: str

@app.get("/api/dss/current")
async def get_current_dss():
    """Get currently active DSS file content"""
    try:
        # Try to get from database first
        active_version = db.get_active_dss_version()
        if active_version:
            return {
                "content": active_version['content'],
                "version_id": active_version['id'],
                "version_number": active_version['version_number'],
                "created_at": active_version['created_at'],
                "description": active_version.get('description', ''),
                "is_active": True
            }

        # Fallback to reading from file
        dss_file_path = digital_twin.dss_file
        if dss_file_path.exists():
            content = dss_file_path.read_text()
            return {
                "content": content,
                "version_id": None,
                "version_number": 0,
                "created_at": None,
                "description": "Original file",
                "is_active": True
            }
        else:
            raise HTTPException(status_code=404, detail="DSS file not found")
    except Exception as e:
        logger.error(f"Error getting current DSS file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dss/validate")
async def validate_dss(request: DSSValidateRequest):
    """Validate DSS file changes without saving"""
    try:
        # Get current/original content
        active_version = db.get_active_dss_version()
        if active_version:
            original_content = active_version['content']
        else:
            original_content = digital_twin.dss_file.read_text()

        # Validate changes
        validation_result = validate_dss_file_changes(original_content, request.content)

        return {
            "valid": validation_result['valid'],
            "errors": validation_result['errors'],
            "warnings": validation_result['warnings'],
            "message": validation_result['message']
        }
    except Exception as e:
        logger.error(f"Error validating DSS file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dss/save")
async def save_dss_version(request: DSSFileRequest):
    """Save a new version of the DSS file after validation"""
    try:
        # Get current/original content for validation
        active_version = db.get_active_dss_version()
        if active_version:
            original_content = active_version['content']
        else:
            original_content = digital_twin.dss_file.read_text()

        # Validate changes
        validation_result = validate_dss_file_changes(original_content, request.content)

        if not validation_result['valid']:
            return {
                "success": False,
                "errors": validation_result['errors'],
                "warnings": validation_result['warnings'],
                "message": "Validation failed. Cannot save invalid DSS file."
            }

        # Save new version to database
        version_id = db.create_dss_version(
            content=request.content,
            created_by=request.created_by,
            description=request.description
        )

        # Reload the DSS file in the simulation
        reload_success = digital_twin.reload_dss_file(request.content)

        if not reload_success:
            logger.warning("DSS file saved but failed to reload in simulation")

        return {
            "success": True,
            "version_id": version_id,
            "warnings": validation_result['warnings'],
            "message": "DSS file saved successfully",
            "reload_status": "success" if reload_success else "failed"
        }
    except Exception as e:
        logger.error(f"Error saving DSS file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dss/versions")
async def get_dss_versions(limit: int = 50):
    """Get all DSS file versions"""
    try:
        versions = db.get_all_dss_versions(limit=limit)
        return {
            "versions": versions,
            "total": len(versions)
        }
    except Exception as e:
        logger.error(f"Error getting DSS versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dss/versions/{version_id}")
async def get_dss_version(version_id: int):
    """Get a specific DSS file version by ID"""
    try:
        version = db.get_dss_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail=f"Version {version_id} not found")
        return version
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting DSS version {version_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dss/activate/{version_id}")
async def activate_dss_version(version_id: int):
    """Activate a specific DSS file version"""
    try:
        # Get the version
        version = db.get_dss_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail=f"Version {version_id} not found")

        # Activate in database
        success = db.activate_dss_version(version_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to activate version")

        # Reload the DSS file in the simulation
        reload_success = digital_twin.reload_dss_file(version['content'])

        return {
            "success": True,
            "version_id": version_id,
            "version_number": version['version_number'],
            "message": f"Activated version {version['version_number']}",
            "reload_status": "success" if reload_success else "failed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating DSS version {version_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming"""
    await websocket.accept()
    digital_twin.websocket_clients.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        digital_twin.websocket_clients.remove(websocket)

# ============================================================================
# DASHBOARD HTML
# ============================================================================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Digital Twin Dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Indian EHV Substation Digital Twin</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .status { padding: 5px 10px; border-radius: 4px; color: white; font-weight: bold; }
            .healthy { background: #27ae60; }
            .warning { background: #f39c12; }
            .fault { background: #e74c3c; }
            .metric { display: flex; justify-content: space-between; margin: 10px 0; }
            .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🇮🇳 Indian EHV 400/220 kV Substation Digital Twin</h1>
                <p>Real-time monitoring and control system</p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>Substation Metrics</h3>
                    <div id="metrics"></div>
                </div>
                
                <div class="card">
                    <h3>Asset Status</h3>
                    <div id="assets"></div>
                </div>
                
                <div class="card">
                    <h3>Power Flow Chart</h3>
                    <canvas id="powerChart" width="400" height="200"></canvas>
                </div>
                
                <div class="card">
                    <h3>Voltage Profile</h3>
                    <canvas id="voltageChart" width="400" height="200"></canvas>
                </div>
            </div>
        </div>
        
        <script>
            // WebSocket connection
            const ws = new WebSocket('ws://localhost:8000/ws');
            
            // Charts
            const powerCtx = document.getElementById('powerChart').getContext('2d');
            const voltageCtx = document.getElementById('voltageChart').getContext('2d');
            
            const powerChart = new Chart(powerCtx, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Power (MW)', data: [], borderColor: '#3498db' }] },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });
            
            const voltageChart = new Chart(voltageCtx, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Voltage (kV)', data: [], borderColor: '#e74c3c' }] },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });
            
            // WebSocket message handler
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'update') {
                    updateMetrics(data.metrics);
                    updateAssets(data.assets);
                    updateCharts(data.metrics);
                }
            };
            
            function updateMetrics(metrics) {
                document.getElementById('metrics').innerHTML = `
                    <div class="metric">
                        <span>Total Power:</span>
                        <span class="metric-value">${metrics.total_power.toFixed(1)} MW</span>
                    </div>
                    <div class="metric">
                        <span>Efficiency:</span>
                        <span class="metric-value">${metrics.efficiency.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span>Voltage Stability:</span>
                        <span class="metric-value">${metrics.voltage_stability.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span>Frequency:</span>
                        <span class="metric-value">${metrics.frequency.toFixed(2)} Hz</span>
                    </div>
                `;
            }
            
            function updateAssets(assets) {
                let html = '';
                for (const [id, asset] of Object.entries(assets)) {
                    html += `
                        <div style="margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <strong>${asset.asset_id}</strong>
                            <span class="status ${asset.status}">${asset.status.toUpperCase()}</span>
                            <div>Voltage: ${asset.voltage.toFixed(1)} kV</div>
                            <div>Power: ${asset.power.toFixed(1)} kW</div>
                            <div>Health: ${asset.health_score.toFixed(1)}%</div>
                        </div>
                    `;
                }
                document.getElementById('assets').innerHTML = html;
            }
            
            function updateCharts(metrics) {
                const now = new Date().toLocaleTimeString();
                
                // Update power chart
                powerChart.data.labels.push(now);
                powerChart.data.datasets[0].data.push(metrics.total_power);
                if (powerChart.data.labels.length > 20) {
                    powerChart.data.labels.shift();
                    powerChart.data.datasets[0].data.shift();
                }
                powerChart.update();
                
                // Update voltage chart
                voltageChart.data.labels.push(now);
                voltageChart.data.datasets[0].data.push(metrics.voltage_stability);
                if (voltageChart.data.labels.length > 20) {
                    voltageChart.data.labels.shift();
                    voltageChart.data.datasets[0].data.shift();
                }
                voltageChart.update();
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

if __name__ == "__main__":
    # Start the digital twin simulation
    digital_twin.start_simulation()
    
    # Run the FastAPI server
    uvicorn.run(
        "digital_twin_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )