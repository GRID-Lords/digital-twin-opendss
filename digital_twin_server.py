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
import uvicorn
from pydantic import BaseModel
import opendssdirect as dss
from circuit_visualizer import OpenDSSVisualizer
from ai_ml_models import SubstationAIManager
from scada_integration import SCADAIntegrationManager
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
    
    def __init__(self, dss_file: str = "IndianEHVSubstation.dss"):
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
            self._setup_assets()
            
            # Initialize AI/ML models
            self.ai_manager.initialize_with_synthetic_data()
            
            # Start SCADA integration
            self.scada_manager.start_integration()
            
            logger.info("Digital Twin initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize digital twin: {e}")
            raise
    
    def _setup_assets(self):
        """Setup asset monitoring for all substation components"""
        # Grid connection
        self.assets["Grid400kV"] = AssetStatus(
            asset_id="Grid400kV", asset_type="GridConnection",
            status="healthy", voltage=400.0, current=0.0, power=0.0,
            temperature=25.0, timestamp=datetime.now().isoformat(),
            health_score=100.0
        )
        
        # Main transformers
        self.assets["TX1_400_220"] = AssetStatus(
            asset_id="TX1_400_220", asset_type="PowerTransformer",
            status="healthy", voltage=400.0, current=0.0, power=0.0,
            temperature=45.0, timestamp=datetime.now().isoformat(),
            health_score=95.0
        )
        
        self.assets["TX2_400_220"] = AssetStatus(
            asset_id="TX2_400_220", asset_type="PowerTransformer",
            status="healthy", voltage=400.0, current=0.0, power=0.0,
            temperature=45.0, timestamp=datetime.now().isoformat(),
            health_score=95.0
        )
        
        # Distribution transformers
        self.assets["DTX1_220_33"] = AssetStatus(
            asset_id="DTX1_220_33", asset_type="DistributionTransformer",
            status="healthy", voltage=220.0, current=0.0, power=0.0,
            temperature=50.0, timestamp=datetime.now().isoformat(),
            health_score=90.0
        )
        
        self.assets["DTX2_220_33"] = AssetStatus(
            asset_id="DTX2_220_33", asset_type="DistributionTransformer",
            status="healthy", voltage=220.0, current=0.0, power=0.0,
            temperature=50.0, timestamp=datetime.now().isoformat(),
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
        
        # Loads
        self.assets["IndustrialLoad1"] = AssetStatus(
            asset_id="IndustrialLoad1", asset_type="IndustrialLoad",
            status="healthy", voltage=33.0, current=0.0, power=15000.0,
            temperature=35.0, timestamp=datetime.now().isoformat(),
            health_score=85.0
        )
        
        self.assets["IndustrialLoad2"] = AssetStatus(
            asset_id="IndustrialLoad2", asset_type="IndustrialLoad",
            status="healthy", voltage=33.0, current=0.0, power=12000.0,
            temperature=35.0, timestamp=datetime.now().isoformat(),
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
                # Update asset statuses
                self._update_asset_statuses()
                
                # Update substation metrics
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
        """Update asset statuses based on simulation"""
        current_time = datetime.now().isoformat()
        
        for asset_id, asset in self.assets.items():
            # Simulate realistic variations
            if asset.asset_type == "PowerTransformer":
                # Temperature variation based on load
                base_temp = 45.0
                load_factor = min(asset.power / 100000.0, 1.0)  # Normalize to 100MW
                asset.temperature = base_temp + (load_factor * 20.0) + np.random.normal(0, 2)
                
                # Health score based on temperature and age
                if asset.temperature > 80:
                    asset.health_score = max(0, asset.health_score - 1)
                    asset.status = "warning" if asset.health_score > 70 else "fault"
                elif asset.temperature > 60:
                    asset.status = "warning"
                else:
                    asset.status = "healthy"
                
                # Update voltage and current
                asset.voltage = 400.0 + np.random.normal(0, 5)
                asset.current = (asset.power / (asset.voltage * 1.732)) + np.random.normal(0, 10)
            
            elif asset.asset_type == "CircuitBreaker":
                # Circuit breaker status
                if asset.status == "fault":
                    asset.health_score = max(0, asset.health_score - 2)
                else:
                    asset.health_score = min(100, asset.health_score + 0.1)
            
            elif asset.asset_type == "IndustrialLoad":
                # Load variations
                base_power = 15000.0 if "1" in asset_id else 12000.0
                # Simulate daily load pattern
                hour = datetime.now().hour
                load_factor = 0.6 + 0.4 * np.sin(2 * np.pi * hour / 24)
                asset.power = base_power * load_factor + np.random.normal(0, 500)
                asset.voltage = 33.0 + np.random.normal(0, 1)
                asset.current = asset.power / (asset.voltage * 1.732)
            
            asset.timestamp = current_time
    
    def _update_substation_metrics(self):
        """Update overall substation metrics"""
        current_time = datetime.now().isoformat()
        
        # Calculate total power
        total_power = sum(asset.power for asset in self.assets.values() 
                         if asset.asset_type in ["IndustrialLoad", "CommercialLoad"])
        
        # Calculate efficiency
        input_power = sum(asset.power for asset in self.assets.values() 
                         if asset.asset_type == "PowerTransformer")
        self.metrics.efficiency = (total_power / input_power * 100) if input_power > 0 else 0
        
        # Voltage stability
        voltages = [asset.voltage for asset in self.assets.values() if asset.voltage > 0]
        if voltages:
            voltage_std = np.std(voltages)
            self.metrics.voltage_stability = max(0, 100 - (voltage_std / np.mean(voltages) * 100))
        
        # Update metrics
        self.metrics.total_power = total_power
        self.metrics.total_load = total_power
        self.metrics.timestamp = current_time
        self.metrics.frequency = 50.0 + np.random.normal(0, 0.1)
        self.metrics.grid_connection = all(asset.status != "fault" 
                                         for asset in self.assets.values() 
                                         if asset.asset_type == "GridConnection")
    
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