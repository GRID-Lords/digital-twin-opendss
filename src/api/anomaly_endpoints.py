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
import pytz

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
_load_flow_engine = None  # Reference to the main load flow engine

def set_load_flow_engine(engine):
    """Set reference to the main load flow engine"""
    global _load_flow_engine
    _load_flow_engine = engine
    logger.info("Load flow engine reference set for anomaly simulation")

def get_active_anomaly():
    """Get the currently active anomaly"""
    return active_anomaly

def apply_anomaly_to_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Apply active anomaly modifications to metrics"""
    global active_anomaly
    logger.info(f"🔍 apply_anomaly_to_metrics called, active_anomaly: {active_anomaly}")

    if not active_anomaly:
        logger.info("No active anomaly, returning metrics unchanged")
        return metrics

    try:
        anomaly_type = active_anomaly.get('type')
        params = active_anomaly.get('parameters', {})
        logger.info(f"Applying anomaly type: {anomaly_type}, params: {params}")

        # Apply frequency deviation
        if anomaly_type == 'frequency_deviation':
            deviation = params.get('deviation', 0.3)
            freq_type = params.get('type', 'under')
            # Get current frequency (which has normal variations) and apply deviation
            current_freq = metrics.get('frequency', 50.0)
            if freq_type == 'under':
                metrics['frequency'] = current_freq - deviation
            else:
                metrics['frequency'] = current_freq + deviation

        # Apply voltage sag
        elif anomaly_type == 'voltage_sag':
            severity = active_anomaly.get('severity', 0.85)
            metrics['voltage_400kv'] = metrics.get('voltage_400kv', 400) * severity
            metrics['voltage_220kv'] = metrics.get('voltage_220kv', 220) * severity

        # Apply voltage surge
        elif anomaly_type == 'voltage_surge':
            severity = active_anomaly.get('severity', 1.12)
            metrics['voltage_400kv'] = metrics.get('voltage_400kv', 400) * severity
            metrics['voltage_220kv'] = metrics.get('voltage_220kv', 220) * severity

        # Apply transformer overload
        elif anomaly_type == 'overload' or anomaly_type == 'transformer_overload':
            load_factor = params.get('load_factor', 1.2)
            metrics['total_load'] = metrics.get('total_load', 0) * load_factor
            metrics['total_power'] = metrics.get('total_power', 0) * load_factor
            metrics['efficiency'] = max(0, metrics.get('efficiency', 0) - 25)  # Reduce efficiency

        logger.debug(f"Applied {anomaly_type} anomaly to metrics")
    except Exception as e:
        logger.error(f"Error applying anomaly to metrics: {e}")

    return metrics

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
    type: str  # Anomaly type (voltage_sag, voltage_surge, transformer_overload, etc.)
    severity: Optional[float] = None  # Severity in p.u. or load factor
    location: Optional[str] = "Bus220_1"  # Bus or component
    parameters: Optional[Dict[str, Any]] = {}  # Additional parameters like transformer, harmonic_order, etc.

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
    severity: float
    start_time: str
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

        # Use severity value (defaults to 0.7 for moderate severity)
        severity_value = request.severity if request.severity is not None else 0.7

        # Generate anomaly ID
        anomaly_id = f"ANM_{datetime.now().strftime('%Y%m%d%H%M%S')}_{request.type}"

        # === GENERATE INSIGHTS & STORE ALERT FIRST (before simulation) ===
        # Get predefined insights for this anomaly type
        insights = get_anomaly_insights(
            request.type,
            request.location,
            request.severity or 0.85,
            request.parameters
        )

        # Store alert with insights in database (ALWAYS store, even if simulation fails)
        try:
            from src.database import db
            from src.monitoring.alert_service import alert_service

            # Capture current system state
            system_state = {}
            try:
                # Import the global services to get current metrics
                import src.backend_server as backend
                logger.info(f"Capturing system state: backend module loaded, hasattr load_flow: {hasattr(backend, 'load_flow')}")
                if hasattr(backend, 'load_flow') and backend.load_flow:
                    logger.info("load_flow found, calling get_metrics()")
                    metrics = backend.load_flow.get_metrics()
                    logger.info(f"Metrics retrieved: {list(metrics.keys())}")
                    system_state = {
                        'total_power_mw': round(metrics.get('total_power', 0), 2),
                        'voltage_400kv': round(metrics.get('voltage_400kv', 0), 2),
                        'voltage_220kv': round(metrics.get('voltage_220kv', 0), 2),
                        'frequency_hz': round(metrics.get('frequency', 50.0), 2),
                        'power_factor': round(metrics.get('power_factor', 0), 3),
                        'efficiency': round(metrics.get('efficiency', 0), 2),
                        'losses_mw': round(metrics.get('losses', 0), 2),
                        'generation_mw': round(metrics.get('generation', 0), 2),
                        'total_load_mw': round(metrics.get('total_load', 0), 2)
                    }
                    logger.info(f"System state captured: {system_state}")
                else:
                    logger.warning("load_flow not found or is None")
            except Exception as state_error:
                logger.error(f"Failed to capture system state: {state_error}", exc_info=True)

            # Create comprehensive alert description
            alert_description = (
                f"{request.type.replace('_', ' ').title()} at {request.location}\n\n"
                f"**Root Cause:**\n{insights['cause']}\n\n"
                f"**Impact:**\n{insights['impact']}\n\n"
                f"**Recommended Actions:**\n{insights['recommendation']}"
            )

            # Store in database
            alert_id = db.store_alert(
                alert_type='anomaly_simulation',
                severity='high',  # All anomaly simulations are high severity
                asset_id=request.location,
                message=alert_description,
                data={
                    'anomaly_id': anomaly_id,
                    'anomaly_type': request.type,
                    'severity_value': severity_value,
                    'parameters': request.parameters,
                    'insights': insights,
                    'system_state': system_state  # Add system state at time of anomaly
                }
            )

            logger.info(f"Alert stored for anomaly: {anomaly_id}, DB Alert ID: {alert_id}")

            # Broadcast anomaly alert via WebSocket with critical notification
            try:
                import src.backend_server as backend
                if hasattr(backend, 'manager'):
                    notification_message = {
                        'type': 'alert_notification',
                        'notification_type': 'critical',  # Anomalies are always critical
                        'alert': {
                            'id': alert_id,
                            'message': f"{request.type.replace('_', ' ').title()} at {request.location}",
                            'severity': 'critical',
                            'alert_type': 'anomaly_simulation',
                            'asset_id': request.location,
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    await backend.manager.broadcast(notification_message)
                    logger.info(f"Broadcasted critical anomaly notification via WebSocket")
            except Exception as ws_error:
                logger.warning(f"Failed to broadcast anomaly via WebSocket: {ws_error}")

        except Exception as db_error:
            logger.warning(f"Failed to store alert in database: {db_error}")
            # Continue even if database storage fails

        # === NOW ATTEMPT SIMULATION (optional - will continue if fails) ===
        result = None
        impact = {}
        viz_data = {}

        try:
            simulator = get_simulator()

            # Map frontend anomaly types to simulator methods
            anomaly_map = {
                'voltage_sag': lambda: simulator.inject_voltage_sag(
                    request.location,
                    magnitude=severity_value,  # Use provided severity directly (0.7 = 70% voltage)
                    duration_cycles=30,
                    phases=['A', 'B', 'C']
                ),
                'voltage_swell': lambda: simulator.inject_voltage_sag(
                    request.location,
                    magnitude=1.0 + (1.0 - severity_value),  # Invert for swell (0.7 becomes 1.3)
                    duration_cycles=20,
                    phases=['A', 'B', 'C']
                ),
                'ground_fault': lambda: simulator.inject_ground_fault(
                    request.location,
                    fault_resistance=0.01 * (1.0 - severity_value),  # Lower resistance = higher severity
                    phase='A'
                ),
                'harmonic_distortion': lambda: simulator.inject_harmonic_distortion(
                    request.location,
                    harmonics={
                        3: 0.05 * (1.0 - severity_value),
                        5: 0.08 * (1.0 - severity_value),
                        7: 0.03 * (1.0 - severity_value)
                    }
                ),
                'transformer_overload': lambda: simulator.inject_transformer_overload(
                    request.parameters.get('transformer', 'TR1'),
                    overload_factor=1.0 + (1.0 - severity_value)  # 0.7 becomes 1.3x overload
                ),
                'capacitor_switching': lambda: simulator.inject_capacitor_switching(
                    request.parameters.get('capacitor', 'Cap1')
                ),
                'ct_saturation': lambda: simulator.inject_ct_saturation(
                    request.location,
                    saturation_level=severity_value
                ),
                'frequency_deviation': lambda: simulator.inject_frequency_deviation(
                    deviation_hz=0.5 * (1.0 - severity_value)
                )
            }

            # Execute anomaly injection
            if request.type in anomaly_map:
                result = anomaly_map[request.type]()
            else:
                raise ValueError(f"Unknown anomaly type: {request.type}")

            # Calculate impact metrics
            impact = calculate_anomaly_impact(result, request.type)

            # Generate visualization data for frontend
            viz_data = generate_visualization_data(result, request.type)

        except Exception as sim_error:
            logger.warning(f"Simulation failed (continuing with alert record): {sim_error}")
            # Use default impact values
            impact = {
                'severity_score': severity_value,
                'affected_components': [],
                'voltage_deviation': 0,
                'current_deviation': 0,
                'power_loss': 0.0,
                'insights': insights
            }

        # Store active anomaly info for persistence (use global variable from function start)
        active_anomaly = {
            'id': anomaly_id,
            'type': request.type,
            'location': request.location,
            'severity': severity_value,
            'parameters': request.parameters,  # Store parameters for applying anomaly
            'start_time': datetime.now().isoformat()
        }
        logger.info(f"🔥 Active anomaly SET: {active_anomaly}")

        # *** INJECT ANOMALY INTO OPENDSS CIRCUIT ***
        try:
            import src.backend_server as backend
            if hasattr(backend, 'load_flow') and backend.load_flow:
                # Set anomaly in load_flow - it will be injected before next solve()
                backend.load_flow.set_anomaly(request.type, request.parameters)
                logger.info(f"✅ Anomaly injected into OpenDSS load_flow: {request.type}")
            else:
                logger.warning("load_flow not available - anomaly will only modify metrics, not OpenDSS circuit")
        except Exception as inject_error:
            logger.error(f"Failed to inject anomaly into OpenDSS circuit: {inject_error}")

        # NOTE: Auto-clear disabled - user must manually clear via /clear endpoint
        # asyncio.create_task(clear_anomaly_after_delay(
        #     anomaly_id,
        #     request.duration / 1000  # Convert to seconds
        # ))

        response = AnomalyResponse(
            success=True,
            anomaly_id=anomaly_id,
            type=request.type,
            location=request.location,
            severity=severity_value,
            start_time=datetime.now().isoformat(),
            impact={**impact, 'insights': insights},  # Include insights in impact
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
            "stages": processed_result
        }

    except Exception as e:
        logger.error(f"Error running scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=SimulationStatusResponse)
async def get_simulation_status():
    """Get current simulation status and active anomalies"""
    global active_anomaly
    try:
        simulator = get_simulator()

        # Get current system state
        system_state = simulator._capture_system_state()

        # Get list of active anomalies from global variable
        active_anomalies = [active_anomaly] if active_anomaly else []
        logger.info(f"🔍 Status endpoint: active_anomaly = {active_anomaly}")

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
    global active_anomaly, active_anomaly_task

    try:
        simulator = get_simulator()

        # Re-initialize to clear all anomalies
        simulator._initialize_dss()

        # Clear the active anomaly tracking
        active_anomaly = None
        active_anomaly_task = None

        # *** CLEAR ANOMALY FROM OPENDSS CIRCUIT ***
        try:
            import src.backend_server as backend
            if hasattr(backend, 'load_flow') and backend.load_flow:
                backend.load_flow.clear_anomaly()
                logger.info("✅ Anomaly cleared from OpenDSS load_flow")
            else:
                logger.warning("load_flow not available")
        except Exception as clear_error:
            logger.error(f"Failed to clear anomaly from OpenDSS circuit: {clear_error}")

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

def get_anomaly_insights(anomaly_type: str, location: str, severity: float, parameters: Dict) -> Dict[str, Any]:
    """Generate predefined insights and recommendations for each anomaly type"""

    # Use timestamp hash to select variation (0-9)
    import time
    variation_index = int(time.time() * 1000) % 10

    # Define 10 variations for each anomaly type
    voltage_sag_variations = [
        {  # Variation 0: Motor starting
            'cause': f"Voltage sag detected at {location}. Analysis indicates:\n"
                    "• Large induction motor starting on adjacent feeder (800 HP motor)\n"
                    "• High inrush current (6-8× rated) drawing excessive reactive power\n"
                    "• Weak source impedance amplifying voltage drop\n"
                    f"• Severity: {severity} p.u. ({'Critical - Equipment may trip' if severity < 0.8 else 'Moderate - Monitor closely' if severity < 0.9 else 'Minor - Within acceptable limits'})",
            'impact': f"• Voltage dropped to {severity*100:.1f}% of nominal (expected: >90%)\n"
                     "• VFDs and PLCs may reset or fault\n"
                     "• Contactors may drop out causing production loss\n"
                     "• Incandescent lighting dimming observed\n"
                     "• Estimated production loss: $2,500/minute if equipment trips",
            'recommendation': "Immediate Actions:\n"
                            "1. Install soft-starter or VFD on large motors (ROI: 6-12 months)\n"
                            "2. Stagger motor starting sequence - delay by 30 seconds minimum\n"
                            "3. Check if motor sizing is appropriate (may be oversized)\n"
                            "4. Verify transformer tap position - may need adjustment\n"
                            "5. Consider reactor installation to limit inrush current\n\n"
                            "Long-term Solutions:\n"
                            "• Upgrade feeder to higher conductor size (reduce impedance)\n"
                            "• Install 5 MVAR Static VAR Compensator (SVC) - Cost: ₹2.5 Cr\n"
                            "• Implement voltage sag monitoring with SCADA alerts\n"
                            "• Consider on-site generator for critical loads",
        },
        {  # Variation 1: Fault on adjacent feeder
            'cause': f"Voltage sag at {location} caused by fault event:\n"
                    "• Single Line-to-Ground fault on 33kV feeder F-203\n"
                    "• Fault current: 12.5 kA (cleared in 150ms by OCR relay)\n"
                    "• Fault location: 8.2 km from substation (fault locator data)\n"
                    f"• Severity: {severity} p.u. - Auto-reclosure successful after 1 second",
            'impact': f"• Momentary voltage dip to {severity*100:.1f}% for 150 milliseconds\n"
                     "• 15 industrial customers reported UPS battery discharge\n"
                     "• 3 CNC machines halted mid-cycle (require manual restart)\n"
                     "• SCADA recorded 18 undervoltage alarms\n"
                     "• No transformer damage detected (Buchholz relay stable)",
            'recommendation': "Immediate Actions:\n"
                            "1. Dispatch field crew to inspect fault location (tree contact suspected)\n"
                            "2. Review relay settings - 150ms may be too slow for sensitive loads\n"
                            "3. Check auto-recloser operation (1 attempt successful)\n"
                            "4. Thermal scan of fault point using drone/IR camera\n"
                            "5. Notify affected customers and provide estimated restoration time\n\n"
                            "Preventive Measures:\n"
                            "• Accelerate tree trimming program in identified corridor\n"
                            "• Install fault current limiters (FCL) on critical feeders\n"
                            "• Upgrade to adaptive protection with faster clearing time\n"
                            "• Consider underground cable for fault-prone sections",
        },
        {  # Variation 2: Transformer energization
            'cause': f"Voltage sag during transformer energization at {location}:\n"
                    "• 100 MVA, 220/33kV power transformer being switched in\n"
                    "• Magnetizing inrush current reached 8× rated (peak: 2400 A)\n"
                    "• Inrush decay time: 3-5 seconds (typical for cold transformer)\n"
                    f"• Residual flux from previous operation amplified inrush\n"
                    f"• Measured voltage dip: {severity} p.u.",
            'impact': f"• Voltage temporarily dropped to {severity*100:.1f}% during inrush\n"
                     "• Harmonic content: 2nd harmonic = 65%, 3rd harmonic = 25%\n"
                     "• Adjacent transformer differential relay showed 40% pickup (no trip)\n"
                     "• Capacitor bank controller detected voltage imbalance\n"
                     "• Auto-transfer switches (ATS) on standby mode activated",
            'recommendation': "Immediate Actions:\n"
                            "1. Implement controlled switching with synchronized breaker\n"
                            "2. Use residual flux measurement before energization\n"
                            "3. Install pre-insertion resistors (PIR) in breaker mechanism\n"
                            "4. Coordinate protection settings to avoid nuisance trips\n"
                            "5. Monitor transformer temperature for next 24 hours\n\n"
                            "Best Practices:\n"
                            "• Energize at voltage zero-crossing (minimize inrush by 60%)\n"
                            "• Use controlled switching device (CSD) - Cost: ₹15 lakhs\n"
                            "• Implement harmonic blocking in differential protection\n"
                            "• Train operators on transformer energization procedure",
        },
        {  # Variation 3: Capacitor bank switching
            'cause': f"Voltage sag triggered by capacitor bank switching at {location}:\n"
                    "• 25 MVAR capacitor bank de-energization\n"
                    "• Reactive power sudden loss causing voltage collapse\n"
                    "• Controller malfunction: Both banks tripped simultaneously\n"
                    f"• Power factor dropped from 0.98 to 0.82 lagging\n"
                    f"• Voltage sag magnitude: {severity} p.u.",
            'impact': f"• System voltage fell to {severity*100:.1f}% within 2 cycles\n"
                     "• Reactive power deficit: 50 MVAR (both banks offline)\n"
                     "• Generator AVR went to ceiling trying to boost voltage\n"
                     "• 220kV bus voltage also affected (cascading effect)\n"
                     "• Penalty charges for low power factor: ₹3.5 lakhs/month",
            'recommendation': "Immediate Actions:\n"
                            "1. Manually energize backup capacitor bank (Bank-C)\n"
                            "2. Investigate capacitor bank controller fault (replace if needed)\n"
                            "3. Check capacitor units for blown fuses (IR scan recommended)\n"
                            "4. Review voltage control logic - too aggressive switching\n"
                            "5. Coordinate with generator AVR to prevent overshoot\n\n"
                            "System Upgrades:\n"
                            "• Install SVC or STATCOM for smooth reactive compensation\n"
                            "• Implement redundant voltage control scheme (N-1 contingency)\n"
                            "• Add voltage regulators on critical feeders\n"
                            "• Replace aging capacitor controller with modern PLC-based system",
        },
        {  # Variation 4: Load rejection
            'cause': f"Voltage sag caused by large load shedding event at {location}:\n"
                    "• Major industrial customer (120 MW cement plant) tripped offline\n"
                    "• Circuit breaker operated due to internal fault at customer end\n"
                    "• Sudden reactive power imbalance in network\n"
                    f"• Generator automatic runback initiated\n"
                    f"• Transient voltage dip: {severity} p.u. before stabilization",
            'impact': f"• Voltage dipped to {severity*100:.1f}% during transient (recovered in 3 seconds)\n"
                     "• Frequency rose from 50.00 to 50.15 Hz (excess generation)\n"
                     "• Other customers on same feeder saw voltage fluctuation\n"
                     "• SCADA recorded 25 event logs\n"
                     "• Loss of supply to 1,200 households (indirect effect)",
            'recommendation': "Immediate Actions:\n"
                            "1. Contact cement plant maintenance team to identify fault cause\n"
                            "2. Inspect feeder breaker that operated - verify proper function\n"
                            "3. Review generator runback settings (may be too sensitive)\n"
                            "4. Check if other customers affected - perform courtesy calls\n"
                            "5. Prepare for load restoration - gradual ramp-up recommended\n\n"
                            "Network Improvements:\n"
                            "• Install inter-bus tie to provide alternate feed path\n"
                            "• Implement load balancing across multiple feeders\n"
                            "• Add synchrophasor (PMU) for real-time stability monitoring\n"
                            "• Consider contractual load shedding agreements with large customers",
        },
        {  # Variation 5: Weak grid condition
            'cause': f"Voltage sag at {location} due to weak grid conditions:\n"
                    "• Source impedance high (0.85 Ω) due to long transmission line\n"
                    "• System X/R ratio: 12 (typical: 5-8 for stable systems)\n"
                    "• No voltage support devices in vicinity (nearest SVC 85 km away)\n"
                    f"• Load increase from 320 MW to 385 MW in last hour\n"
                    f"• Voltage regulation poor: {severity} p.u.",
            'impact': f"• Operating voltage: {severity*100:.1f}% (below statutory limit of 95%)\n"
                     "• Equipment efficiency loss: ~3% due to undervoltage\n"
                     "• Motor current increased by 8% (thermal stress)\n"
                     "• Lighting output reduced (complaints from customers)\n"
                     "• Risk of voltage collapse if load continues rising",
            'recommendation': "Immediate Actions:\n"
                            "1. Request grid operator to adjust transformer taps at 220kV side\n"
                            "2. Energize all available capacitor banks for voltage boost\n"
                            "3. Implement voltage-based load shedding if voltage drops below 0.92 p.u.\n"
                            "4. Monitor power factor - maintain above 0.95 to reduce reactive draw\n"
                            "5. Coordinate with neighboring substations for load transfer\n\n"
                            "Infrastructure Development:\n"
                            "• Install 100 MVAR STATCOM for dynamic voltage support - ₹45 Cr\n"
                            "• Add 220kV transmission line to reduce source impedance\n"
                            "• Implement on-load tap changer (OLTC) automation\n"
                            "• Build new 400/220kV substation to strengthen network",
        },
        {  # Variation 6: Harmonic resonance
            'cause': f"Voltage sag coupled with harmonic resonance at {location}:\n"
                    "• Capacitor bank creating series resonance at 5th harmonic (250 Hz)\n"
                    "• VFD loads injecting 5th and 7th harmonic currents\n"
                    "• Resonance amplifying harmonic voltages by factor of 4.5\n"
                    f"• Combined effect causing voltage distortion and magnitude drop\n"
                    f"• Fundamental voltage: {severity} p.u., THDv: 8.5%",
            'impact': f"• Voltage waveform distorted - fundamental at {severity*100:.1f}%\n"
                     "• Capacitor bank overheating (temperature: 78°C, limit: 65°C)\n"
                     "• Transformer audible noise increased (harmonic core losses)\n"
                     "• Electronic equipment malfunctioning (PLCs, drives)\n"
                     "• Protection relays showing erratic behavior (harmonic interference)",
            'recommendation': "Immediate Actions:\n"
                            "1. De-energize capacitor bank to break resonance condition\n"
                            "2. Install harmonic power quality analyzer on main bus\n"
                            "3. Measure THD at multiple points - identify harmonic sources\n"
                            "4. Check VFD configurations - enable DC bus inductors if available\n"
                            "5. Emergency: Consider load shedding of VFD loads if overheating persists\n\n"
                            "Harmonic Mitigation:\n"
                            "• Install 5th harmonic tuned filter (25 MVAR) - ₹1.2 Cr\n"
                            "• Replace standard capacitors with detuned reactor design\n"
                            "• Implement active harmonic filter (AHF) for dynamic compensation\n"
                            "• Use 12-pulse VFDs for large drives (reduce harmonics by 40%)",
        },
        {  # Variation 7: Geomagnetic disturbance
            'cause': f"Voltage sag influenced by geomagnetic disturbance (GMD) at {location}:\n"
                    "• Solar flare activity detected (NOAA Space Weather Alert Level G3)\n"
                    "• Geomagnetically induced currents (GIC) in transformer neutrals\n"
                    "• Transformer magnetizing current increased due to DC bias\n"
                    f"• Half-cycle saturation causing reactive power absorption\n"
                    f"• System voltage depressed to {severity} p.u.",
            'impact': f"• Voltage reduced to {severity*100:.1f}% across multiple substations\n"
                     "• Transformer neutral current: 65 A DC (normal: <5 A)\n"
                     "• Harmonic distortion: 2nd harmonic dominant (transformer saturation)\n"
                     "• Regional grid instability - 3 neighboring substations affected\n"
                     "• SCADA alerts from 150+ locations simultaneously",
            'recommendation': "Immediate Actions:\n"
                            "1. Monitor space weather forecasts (NOAA, ISRO alerts)\n"
                            "2. Increase reactive power reserves - energize all capacitors\n"
                            "3. Reduce transformer loading to prevent thermal runaway\n"
                            "4. Coordinate with grid operator for regional voltage support\n"
                            "5. Prepare for possible transformer protection trips\n\n"
                            "GIC Mitigation Strategies:\n"
                            "• Install neutral blocking devices on critical transformers\n"
                            "• Implement geomagnetic monitoring at substation (magnetometers)\n"
                            "• Develop GMD emergency response procedures\n"
                            "• Consider DC-blocking capacitors in neutral (research stage)\n"
                            "• Participate in grid-wide GMD preparedness drills",
        },
        {  # Variation 8: Cable fault
            'cause': f"Voltage sag due to incipient cable fault at {location}:\n"
                    "• 220kV underground cable showing partial discharge activity\n"
                    "• Insulation degradation detected at cable joint (15-year old installation)\n"
                    "• Intermittent arcing causing voltage fluctuations\n"
                    f"• Not yet a solid fault, but impedance increasing\n"
                    f"• Voltage sag severity: {severity} p.u. during discharge events",
            'impact': f"• Voltage drops to {severity*100:.1f}% every 5-10 minutes (intermittent)\n"
                     "• Partial discharge magnitude: 3500 pC (alarm threshold: 1000 pC)\n"
                     "• Cable sheath voltage rising (insulation stress indicator)\n"
                     "• Risk of catastrophic failure within 48-72 hours\n"
                     "• Critical customers at risk if cable fails completely",
            'recommendation': "Immediate Actions:\n"
                            "1. URGENT: Schedule cable replacement within 48 hours\n"
                            "2. Perform online partial discharge (PD) monitoring - locate exact fault\n"
                            "3. Prepare backup feed path - test transfer switches\n"
                            "4. Notify critical customers of potential outage\n"
                            "5. Arrange emergency response crew on standby\n\n"
                            "Cable Health Management:\n"
                            "• Implement continuous PD monitoring system - ₹25 lakhs\n"
                            "• Perform VLF tan-delta testing on all aging cables (>10 years)\n"
                            "• Upgrade cable joints to composite silicone design\n"
                            "• Replace XLPE cables in high-moisture areas\n"
                            "• Maintain cable asset database with health scores",
        },
        {  # Variation 9: Lightning strike
            'cause': f"Voltage sag caused by nearby lightning strike at {location}:\n"
                    "• Direct lightning strike to 400kV transmission tower (Tower #127)\n"
                    "• Strike current estimated: 85 kA (peak), negative polarity\n"
                    "• Surge arrester operated successfully (discharge counter: +1)\n"
                    f"• Overvoltage wave reflected causing temporary voltage collapse\n"
                    f"• Voltage dip: {severity} p.u. for 200 milliseconds",
            'impact': f"• Momentary voltage sag to {severity*100:.1f}% (recovered automatically)\n"
                     "• Surge arrester energy absorption: 2.5 MJ\n"
                     "• Insulator flashover on one phase (auto-reclose successful)\n"
                     "• UPS systems switched to battery mode (12 facilities)\n"
                     "• No equipment damage reported (protection worked correctly)",
            'recommendation': "Immediate Actions:\n"
                            "1. Inspect Tower #127 - check for structural damage or burnt components\n"
                            "2. Test surge arrester with leakage current measurement\n"
                            "3. Verify insulator condition - IR scan for tracking/damage\n"
                            "4. Review lightning detection system records (time/location correlation)\n"
                            "5. Check tower grounding resistance - should be <5 Ω\n\n"
                            "Lightning Protection Enhancement:\n"
                            "• Install additional surge arresters at critical equipment\n"
                            "• Upgrade tower grounding with deep-driven rods\n"
                            "• Add overhead ground wire (OHGW) to transmission line\n"
                            "• Implement early streamer emission (ESE) air terminals\n"
                            "• Join lightning detection network for predictive alerts",
        }
    ]

    # Similar variations for other anomaly types (abbreviated for space)
    insights = {
        'voltage_sag': voltage_sag_variations[variation_index],

        'voltage_surge': {
            'cause': f"Voltage sag detected at {location}. Common causes include:\n"
                    "• Large motor starting currents drawing excessive reactive power\n"
                    "• Fault on adjacent feeders causing temporary voltage drop\n"
                    "• Transformer inrush current during energization\n"
                    f"• Severity: {severity} p.u. ({'Critical' if severity < 0.8 else 'Moderate' if severity < 0.9 else 'Minor'})",
            'impact': f"• Voltage dropped to {severity*100:.1f}% of nominal\n"
                     "• Sensitive electronic equipment may malfunction\n"
                     "• Motors may stall or draw excessive current\n"
                     "• Protection relays may operate if voltage is too low",
            'recommendation': "Immediate Actions:\n"
                            "1. Check for faults on feeders - inspect circuit breaker status\n"
                            "2. Verify motor starting sequence - consider soft-starters\n"
                            "3. Install Static VAR Compensator (SVC) or STATCOM for voltage support\n"
                            "4. Review transformer tap settings for voltage regulation\n"
                            "5. Consider series compensation or line reinforcement\n\n"
                            "Long-term Solutions:\n"
                            "• Install Dynamic Voltage Restorer (DVR) for critical loads\n"
                            "• Upgrade transformer capacity if overloaded\n"
                            "• Implement voltage monitoring and predictive maintenance",
            'severity_level': 'high' if severity < 0.85 else 'medium'
        },

        'voltage_surge': {
            'cause': f"Voltage surge detected at {location}. Common causes include:\n"
                    "• Capacitor bank switching causing resonance\n"
                    "• Sudden load rejection (large load disconnection)\n"
                    "• Lightning strikes on transmission lines\n"
                    f"• Ferroresonance in lightly loaded transformers\n"
                    f"• Severity: {severity} p.u. ({'Critical' if severity > 1.15 else 'Moderate' if severity > 1.1 else 'Minor'})",
            'impact': f"• Voltage rose to {severity*100:.1f}% of nominal\n"
                     "• Risk of insulation breakdown in equipment\n"
                     "• MOV/surge arresters may conduct\n"
                     "• Electronic equipment damage possible\n"
                     "• Overvoltage protection may trip",
            'recommendation': "Immediate Actions:\n"
                            "1. Verify capacitor bank switching sequence - check control logic\n"
                            "2. Inspect surge arresters for proper operation\n"
                            "3. Check voltage regulator and AVR settings\n"
                            "4. Review recent load changes and switching operations\n"
                            "5. Ensure proper grounding of neutral points\n\n"
                            "Long-term Solutions:\n"
                            "• Install pre-insertion resistors for capacitor switching\n"
                            "• Implement synchronized switching controllers\n"
                            "• Upgrade surge protection devices (SPDs)\n"
                            "• Add reactors to limit inrush and resonance",
            'severity_level': 'high' if severity > 1.12 else 'medium'
        },

        'transformer_overload': {
            'cause': f"Transformer overload detected. Common causes include:\n"
                    f"• Load factor: {parameters.get('load_factor', severity)}x rated capacity\n"
                    "• Increased demand during peak hours\n"
                    "• Unbalanced phase loading\n"
                    "• Loss of parallel transformer causing redistribution\n"
                    "• Ambient temperature rise reducing cooling efficiency",
            'impact': "• Accelerated aging due to thermal stress\n"
                     "• Hot-spot temperature rise above design limits\n"
                     "• Reduced insulation life (halved for every 6°C rise)\n"
                     "• Risk of winding damage and insulation failure\n"
                     f"• Efficiency drop: {(1 - 1/parameters.get('load_factor', severity))*100:.1f}%",
            'recommendation': "Immediate Actions:\n"
                            "1. Monitor top oil and winding temperatures via SCADA\n"
                            "2. Check cooling system - fans, pumps, radiators\n"
                            "3. Redistribute load to parallel transformers if available\n"
                            "4. Implement load shedding for non-critical loads\n"
                            "5. Inspect for hot spots using thermal imaging\n\n"
                            "Long-term Solutions:\n"
                            "• Add parallel transformer to share load\n"
                            "• Upgrade to higher capacity transformer\n"
                            "• Implement Dissolved Gas Analysis (DGA) monitoring\n"
                            "• Install advanced cooling systems (forced air/oil)\n"
                            "• Review load forecasting and demand management",
            'severity_level': 'critical' if parameters.get('load_factor', severity) > 1.3 else 'high'
        },

        'ground_fault': {
            'cause': f"Ground fault detected at {location}. Common causes include:\n"
                    f"• Fault resistance: {parameters.get('fault_resistance', 5)}Ω\n"
                    "• Insulation failure in cable or equipment\n"
                    "• Tree/bird contact with overhead lines\n"
                    "• Equipment degradation or moisture ingress\n"
                    "• Installation/maintenance errors",
            'impact': "• Zero sequence current flow through ground\n"
                     "• Risk of arc flash and equipment damage\n"
                     "• Ground Potential Rise (GPR) - shock hazard\n"
                     "• Protection relays will trip (87G, 51N)\n"
                     "• Service interruption until fault cleared",
            'recommendation': "Immediate Actions:\n"
                            "1. Isolate faulted section using circuit breakers\n"
                            "2. Verify ground relay operation (87G, 51N, 67N)\n"
                            "3. Use fault locator/TDR to identify exact location\n"
                            "4. Check for visible damage, smoke, or arc marks\n"
                            "5. Perform insulation resistance (IR) tests\n\n"
                            "Long-term Solutions:\n"
                            "• Implement sensitive earth fault protection\n"
                            "• Install cable sheath voltage limiters\n"
                            "• Upgrade cable insulation or replace aging cables\n"
                            "• Implement online partial discharge monitoring\n"
                            "• Regular preventive maintenance and IR testing",
            'severity_level': 'critical'
        },

        'harmonic_distortion': {
            'cause': f"Harmonic distortion detected. Common causes include:\n"
                    f"• THD: {parameters.get('thd', 5)}%\n"
                    f"• Dominant harmonic order: {parameters.get('harmonic_order', 5)}\n"
                    "• Non-linear loads (VFDs, UPS, rectifiers)\n"
                    "• Capacitor-reactor resonance at harmonic frequency\n"
                    "• Saturated transformers generating harmonics",
            'impact': "• Increased transformer losses and heating\n"
                     "• Capacitor bank failure due to harmonic currents\n"
                     "• Interference with communication systems\n"
                     "• Neutral conductor overloading (triplen harmonics)\n"
                     "• Protection relay maloperation",
            'recommendation': "Immediate Actions:\n"
                            "1. Measure harmonic spectrum using power quality analyzer\n"
                            "2. Identify major harmonic sources (VFDs, UPS units)\n"
                            "3. Check capacitor banks for overheating\n"
                            "4. Verify harmonic limits per IEEE 519 standard\n"
                            "5. Monitor neutral current for triplen harmonics\n\n"
                            "Long-term Solutions:\n"
                            "• Install harmonic filters (passive or active)\n"
                            "• Use 12-pulse or 18-pulse rectifier configurations\n"
                            "• Implement Active Power Filters (APF)\n"
                            "• Derate transformers serving non-linear loads\n"
                            "• K-rated transformers for harmonic environments",
            'severity_level': 'high' if parameters.get('thd', 5) > 8 else 'medium'
        },

        'frequency_deviation': {
            'cause': f"Frequency deviation detected. Common causes include:\n"
                    f"• Frequency deviation: {parameters.get('deviation', 0.3)} Hz {'under' if parameters.get('type') == 'under' else 'over'}\n"
                    "• Generation-load imbalance in grid\n"
                    "• Major generator tripping\n"
                    "• Large load changes or load shedding\n"
                    "• Islanding condition in distributed generation",
            'impact': "• Generator governor instability\n"
                     "• Turbine blade stress and vibration\n"
                     "• Motor speed changes affecting processes\n"
                     "• Under-frequency load shedding (UFLS) may activate\n"
                     "• Risk of grid collapse if not corrected",
            'recommendation': "Immediate Actions:\n"
                            "1. Check grid connection and synchronization\n"
                            "2. Verify generator governor response\n"
                            "3. Monitor frequency trend - rising or falling\n"
                            "4. Prepare for UFLS activation if frequency drops\n"
                            "5. Coordinate with system operator/load dispatch\n\n"
                            "Long-term Solutions:\n"
                            "• Implement fast frequency response (FFR) systems\n"
                            "• Add inertia support from synchronous condensers\n"
                            "• Install battery energy storage systems (BESS)\n"
                            "• Upgrade load shedding schemes (UFLS/OFLS)\n"
                            "• Participate in frequency regulation services",
            'severity_level': 'critical' if abs(parameters.get('deviation', 0.3)) > 0.5 else 'high'
        }
    }

    # Return insights for the specific anomaly type
    return insights.get(anomaly_type, {
        'cause': f"Anomaly of type '{anomaly_type}' detected",
        'impact': "Impact being assessed",
        'recommendation': "Standard troubleshooting procedures apply",
        'severity_level': 'medium'
    })

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