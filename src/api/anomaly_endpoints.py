"""
API Endpoints for Anomaly Simulation and Visualization
Integrates OpenDSS anomaly simulator with frontend controls
"""

from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import json
import logging

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from simulation.opendss_anomaly_simulator import (
    OpenDSSAnomalySimulator,
    AnomalyType,
    AnomalyProfile
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/simulation", tags=["simulation"])

# Global simulator instance and active anomaly tracking
anomaly_simulator = None
active_anomaly = None
active_anomaly_task = None

def get_simulator():
    """Get or create anomaly simulator instance"""
    global anomaly_simulator
    if anomaly_simulator is None:
        # Use the correct DSS file path
        dss_file = Path(__file__).parent.parent / "models" / "IndianEHVSubstation.dss"
        if not dss_file.exists():
            raise FileNotFoundError(f"DSS file not found: {dss_file}")
        anomaly_simulator = OpenDSSAnomalySimulator(str(dss_file))
    return anomaly_simulator

# Request models
class AnomalyRequest(BaseModel):
    type: str  # Anomaly type
    severity: Optional[str] = "medium"  # low, medium, high
    location: Optional[str] = "Bus220_1"  # Bus or component
    duration: Optional[int] = 5000  # Duration in milliseconds
    parameters: Optional[Dict[str, Any]] = {}

class SimulationScenarioRequest(BaseModel):
    scenario: str  # Scenario name
    parameters: Optional[Dict[str, Any]] = {}

class SystemUpdateRequest(BaseModel):
    updates: Dict[str, Any]  # System parameter updates

# Response models
class AnomalyResponse(BaseModel):
    success: bool
    anomaly_id: str
    type: str
    location: str
    severity: str
    start_time: str
    duration_ms: int
    impact: Dict[str, Any]
    visualization_data: Dict[str, Any]

class SimulationStatusResponse(BaseModel):
    active_anomalies: List[Dict[str, Any]]
    system_state: Dict[str, Any]
    timestamp: str

# API Endpoints

@router.post("/anomaly", response_model=AnomalyResponse)
async def trigger_anomaly(request: AnomalyRequest):
    """
    Trigger an anomaly simulation in OpenDSS

    Available anomaly types:
    - voltage_sag, voltage_swell, voltage_interruption
    - overcurrent, ground_fault, current_imbalance
    - harmonic_distortion, thd_violation, resonance
    - transformer_overload, transformer_overheating
    - breaker_failure, switching_transient
    - capacitor_failure, capacitor_switching
    - frequency_deviation, power_oscillation
    """
    global active_anomaly, active_anomaly_task

    try:
        # Check if another anomaly is currently active
        if active_anomaly is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Another anomaly '{active_anomaly['type']}' is currently active. Please wait for it to complete or stop it first."
            )

        simulator = get_simulator()

        # Map frontend anomaly types to simulator methods
        anomaly_map = {
            'voltage_sag': lambda: simulator.inject_voltage_sag(
                request.location,
                magnitude=0.7 if request.severity == 'high' else 0.8,
                duration_cycles=30,
                phases=['A', 'B', 'C']
            ),
            'voltage_swell': lambda: simulator.inject_voltage_sag(
                request.location,
                magnitude=1.2 if request.severity == 'high' else 1.1,
                duration_cycles=20,
                phases=['A', 'B', 'C']
            ),
            'ground_fault': lambda: simulator.inject_ground_fault(
                request.location,
                fault_resistance=0.01 if request.severity == 'high' else 0.1,
                phase='A'
            ),
            'harmonic_distortion': lambda: simulator.inject_harmonic_distortion(
                request.location,
                harmonics={
                    3: 0.05 if request.severity == 'low' else 0.1,
                    5: 0.08 if request.severity == 'low' else 0.15,
                    7: 0.03 if request.severity == 'low' else 0.08
                }
            ),
            'transformer_overload': lambda: simulator.inject_transformer_overload(
                request.parameters.get('transformer', 'TR1'),
                overload_factor=1.3 if request.severity == 'medium' else 1.5
            ),
            'capacitor_switching': lambda: simulator.inject_capacitor_switching(
                request.parameters.get('capacitor', 'Cap1')
            ),
            'ct_saturation': lambda: simulator.inject_ct_saturation(
                request.location,
                saturation_level=0.7 if request.severity == 'high' else 0.85
            ),
            'frequency_deviation': lambda: simulator.inject_frequency_deviation(
                deviation_hz=0.5 if request.severity == 'medium' else 1.0
            )
        }

        # Execute anomaly injection
        if request.type in anomaly_map:
            result = anomaly_map[request.type]()
        else:
            raise ValueError(f"Unknown anomaly type: {request.type}")

        # Generate anomaly ID
        anomaly_id = f"ANM_{datetime.now().strftime('%Y%m%d%H%M%S')}_{request.type}"

        # Calculate impact metrics
        impact = calculate_anomaly_impact(result, request.type)

        # Generate visualization data for frontend
        viz_data = generate_visualization_data(result, request.type)

        # === AI/ML PREDICTION & ALERT INTEGRATION ===
        # Trigger AI/ML analysis and store alert when anomaly occurs
        try:
            # Import alert service and AI insights service
            from src.monitoring.alert_service import alert_service
            from src.monitoring.ai_insights_service import ai_insights_service

            # Create anomaly alert description
            description = f"{request.type.replace('_', ' ').title()} detected at {request.location} with {request.severity} severity"

            # Trigger anomaly alert
            alert = await alert_service.trigger_anomaly_alert(
                anomaly_type=request.type,
                asset_id=request.location,
                description=description,
                severity=request.severity
            )

            # Generate AI insights for this anomaly
            asset_data = {
                'location': request.location,
                'anomaly_type': request.type,
                'severity': request.severity,
                'impact': impact
            }
            metrics = {
                'voltage_deviation': impact.get('voltage_deviation', 0),
                'power_loss': impact.get('power_loss', 0),
                'severity_score': impact.get('severity_score', 0)
            }

            ai_insight = await ai_insights_service.generate_asset_insight(
                request.location,
                asset_data,
                metrics
            )

            logger.info(f"AI/ML analysis completed for anomaly: {anomaly_id}, Alert ID: {alert.get('id') if alert else 'None'}")

        except Exception as ai_error:
            logger.warning(f"AI/ML analysis failed for anomaly {anomaly_id}: {ai_error}")
            # Continue even if AI/ML fails

        # Schedule auto-clear after duration
        asyncio.create_task(clear_anomaly_after_delay(
            anomaly_id,
            request.duration / 1000  # Convert to seconds
        ))

        response = AnomalyResponse(
            success=True,
            anomaly_id=anomaly_id,
            type=request.type,
            location=request.location,
            severity=request.severity,
            start_time=datetime.now().isoformat(),
            duration_ms=request.duration,
            impact=impact,
            visualization_data=viz_data
        )

        logger.info(f"Anomaly triggered: {anomaly_id}")
        return response

    except Exception as e:
        logger.error(f"Error triggering anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scenario")
async def run_scenario(request: SimulationScenarioRequest):
    """
    Run predefined anomaly scenarios

    Available scenarios:
    - voltage_collapse: Progressive voltage collapse
    - cascading_failure: Cascading outage scenario
    - transformer_failure: Various transformer faults
    - harmonic_resonance: Harmonic resonance condition
    - protection_misoperation: Relay misoperation scenario
    """
    try:
        simulator = get_simulator()

        # Run the requested scenario
        result = simulator.run_anomaly_scenario(request.scenario)

        # Process results for frontend
        processed_result = process_scenario_results(result)

        return {
            "success": True,
            "scenario": request.scenario,
            "timestamp": datetime.now().isoformat(),
            "stages": processed_result,
            "duration_ms": len(result.get('stages', [])) * 1000
        }

    except Exception as e:
        logger.error(f"Error running scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=SimulationStatusResponse)
async def get_simulation_status():
    """Get current simulation status and active anomalies"""
    try:
        simulator = get_simulator()

        # Get current system state
        system_state = simulator._capture_system_state()

        # Get list of active anomalies (would need tracking in production)
        active_anomalies = []  # This would be maintained in a real system

        return SimulationStatusResponse(
            active_anomalies=active_anomalies,
            system_state=simplify_system_state(system_state),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Error getting simulation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear")
async def clear_all_anomalies():
    """Clear all active anomalies and restore normal operation"""
    try:
        simulator = get_simulator()

        # Re-initialize to clear all anomalies
        simulator._initialize_dss()

        return {
            "success": True,
            "message": "All anomalies cleared",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error clearing anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-dataset")
async def generate_training_dataset(num_samples: int = 1000):
    """Generate anomaly dataset for AI/ML training"""
    try:
        simulator = get_simulator()

        # Generate dataset
        dataset = simulator.generate_anomaly_dataset(num_samples)

        # Save to CSV
        filename = f"anomaly_dataset_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        dataset.to_csv(filename, index=False)

        # Get statistics
        stats = {
            "total_samples": len(dataset),
            "normal_samples": len(dataset[dataset['label'] == 0]),
            "anomaly_samples": len(dataset[dataset['label'] == 1]),
            "anomaly_types": dataset['anomaly_type'].value_counts().to_dict(),
            "features": dataset.columns.tolist()
        }

        return {
            "success": True,
            "filename": filename,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error generating dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/anomaly")
async def anomaly_websocket(websocket: WebSocket):
    """WebSocket for real-time anomaly updates"""
    await websocket.accept()

    try:
        simulator = get_simulator()

        while True:
            # Send system state every second
            state = simulator._capture_system_state()
            simplified_state = simplify_system_state(state)

            await websocket.send_json({
                "type": "state_update",
                "data": simplified_state,
                "timestamp": datetime.now().isoformat()
            })

            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Helper functions

async def clear_anomaly_after_delay(anomaly_id: str, delay_seconds: float):
    """Clear an anomaly after specified delay"""
    await asyncio.sleep(delay_seconds)
    logger.info(f"Auto-clearing anomaly: {anomaly_id}")
    # In production, would clear specific anomaly

def calculate_anomaly_impact(result: Dict, anomaly_type: str) -> Dict[str, Any]:
    """Calculate the impact of an anomaly"""
    impact = {
        "severity_score": 0,
        "affected_components": [],
        "voltage_deviation": 0,
        "current_deviation": 0,
        "power_loss": 0
    }

    # Calculate impacts based on result data
    if 'buses' in result:
        voltages = []
        for bus_data in result['buses'].values():
            if 'voltage_pu' in bus_data:
                voltages.extend(bus_data['voltage_pu'])

        if voltages:
            impact["voltage_deviation"] = max(abs(1.0 - v) for v in voltages) * 100

    if 'summary' in result:
        impact["power_loss"] = result['summary'].get('losses_kw', 0)

    # Severity scoring
    if anomaly_type in ['ground_fault', 'voltage_collapse']:
        impact["severity_score"] = 0.9
    elif anomaly_type in ['transformer_overload', 'voltage_sag']:
        impact["severity_score"] = 0.7
    else:
        impact["severity_score"] = 0.5

    return impact

def generate_visualization_data(result: Dict, anomaly_type: str) -> Dict[str, Any]:
    """Generate data for frontend visualization"""
    viz_data = {
        "affected_buses": [],
        "affected_lines": [],
        "color_map": {},
        "animation_type": "pulse"
    }

    # Determine affected components and colors
    if anomaly_type == 'voltage_sag':
        viz_data["animation_type"] = "voltage_drop"
        viz_data["color_map"] = {"buses": "#ff4444"}
    elif anomaly_type == 'ground_fault':
        viz_data["animation_type"] = "fault_flash"
        viz_data["color_map"] = {"fault_point": "#ff0000"}
    elif anomaly_type == 'harmonic_distortion':
        viz_data["animation_type"] = "wave_distortion"
        viz_data["color_map"] = {"lines": "#ff8800"}
    elif anomaly_type == 'transformer_overload':
        viz_data["animation_type"] = "heat_pulse"
        viz_data["color_map"] = {"transformer": "#ff6600"}

    # Extract affected components from result
    if 'buses' in result:
        for bus_name, bus_data in result['buses'].items():
            if 'voltage_mag' in bus_data:
                v_mag = bus_data['voltage_mag']
                if any(v < 0.95 or v > 1.05 for v in v_mag):
                    viz_data["affected_buses"].append(bus_name)

    return viz_data

def simplify_system_state(state: Dict) -> Dict:
    """Simplify system state for frontend consumption"""
    simplified = {
        "bus_voltages": {},
        "line_flows": {},
        "transformer_loading": {},
        "total_generation": 0,
        "total_load": 0,
        "losses": 0
    }

    # Extract key metrics
    if 'buses' in state:
        for bus_name, bus_data in state['buses'].items():
            if 'voltage_mag' in bus_data:
                simplified["bus_voltages"][bus_name] = {
                    "voltage_pu": sum(bus_data['voltage_mag']) / len(bus_data['voltage_mag'])
                        if bus_data['voltage_mag'] else 1.0
                }

    if 'summary' in state:
        simplified["total_generation"] = state['summary'].get('total_power_kw', 0)
        simplified["losses"] = state['summary'].get('losses_kw', 0)

    return simplified

def process_scenario_results(result: Dict) -> List[Dict]:
    """Process scenario results for frontend"""
    processed = []

    if 'stages' in result:
        for i, stage in enumerate(result['stages']):
            processed.append({
                "stage": i + 1,
                "description": f"Stage {i + 1}",
                "metrics": simplify_system_state(stage)
            })
    elif 'cascade_sequence' in result:
        for event in result['cascade_sequence']:
            processed.append({
                "event": event.get('event', 'unknown'),
                "metrics": simplify_system_state(event.get('state', {}))
            })

    return processed