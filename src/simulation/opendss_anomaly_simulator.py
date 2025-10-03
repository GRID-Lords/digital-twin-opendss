"""
OpenDSS Anomaly Simulation Module for EHV Substation Digital Twin
Simulates various electrical anomalies and disturbances for AI/ML training and testing
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging
from datetime import datetime, timedelta
import opendssdirect as dss
import random
import os

logger = logging.getLogger(__name__)

class AnomalyType(Enum):
    """Types of anomalies that can be simulated"""
    # Voltage Anomalies
    VOLTAGE_SAG = "voltage_sag"
    VOLTAGE_SWELL = "voltage_swell"
    VOLTAGE_INTERRUPTION = "voltage_interruption"
    VOLTAGE_IMBALANCE = "voltage_imbalance"
    VOLTAGE_FLICKER = "voltage_flicker"

    # Current Anomalies
    OVERCURRENT = "overcurrent"
    CURRENT_IMBALANCE = "current_imbalance"
    GROUND_FAULT = "ground_fault"

    # Harmonic Anomalies
    HARMONIC_DISTORTION = "harmonic_distortion"
    THD_VIOLATION = "thd_violation"
    RESONANCE = "resonance"

    # Transformer Anomalies
    TRANSFORMER_OVERLOAD = "transformer_overload"
    TRANSFORMER_OVERHEATING = "transformer_overheating"
    TAP_CHANGER_FAILURE = "tap_changer_failure"
    WINDING_FAULT = "winding_fault"

    # Breaker Anomalies
    BREAKER_FAILURE = "breaker_failure"
    SWITCHING_TRANSIENT = "switching_transient"
    ARC_FAULT = "arc_fault"

    # System Anomalies
    FREQUENCY_DEVIATION = "frequency_deviation"
    POWER_OSCILLATION = "power_oscillation"
    ISLANDING = "islanding"
    CASCADING_FAILURE = "cascading_failure"

    # Capacitor Bank Anomalies
    CAPACITOR_FAILURE = "capacitor_failure"
    CAPACITOR_SWITCHING = "capacitor_switching"

    # Protection System Anomalies
    RELAY_MISOPERATION = "relay_misoperation"
    CT_SATURATION = "ct_saturation"
    CVT_FERRORESONANCE = "cvt_ferroresonance"

@dataclass
class AnomalyProfile:
    """Profile for an anomaly simulation"""
    anomaly_type: AnomalyType
    location: str  # Bus or component name
    severity: float  # 0.0 to 1.0
    duration_cycles: int  # Duration in power cycles
    start_time: float  # Start time in seconds
    affected_phases: List[str]  # ['A', 'B', 'C']
    parameters: Dict[str, Any]  # Additional parameters

class OpenDSSAnomalySimulator:
    """Main class for simulating anomalies in OpenDSS"""

    def __init__(self, dss_file: str):
        """Initialize the anomaly simulator with a DSS circuit file"""
        self.dss_file = dss_file
        self.dss = None
        self._initialize_dss()

        # Store baseline values
        self.baseline_voltages = {}
        self.baseline_currents = {}
        self.baseline_powers = {}

        # Anomaly injection points
        self.injection_points = []

        # Results storage
        self.simulation_results = []

    def _initialize_dss(self):
        """Initialize OpenDSS with the circuit file"""
        try:
            # opendssdirect doesn't need object creation, use module directly
            self.dss = dss

            # Create a default circuit if file doesn't exist
            if not os.path.exists(self.dss_file):
                logger.warning(f"DSS file not found: {self.dss_file}, creating default circuit")
                self._create_default_ehv_circuit()
            else:
                logger.info(f"Compiling DSS file: {self.dss_file}")
                dss.run_command(f"compile [{self.dss_file}]")
                if not dss.Solution.Converged():
                    logger.error("DSS compilation/solve failed")
                    raise RuntimeError("DSS compilation/solve failed")

            # Solve baseline
            dss.run_command("solve")
            if not dss.Solution.Converged():
                logger.warning("DSS baseline solve did not converge")

            self._store_baseline()
            logger.info(f"OpenDSS initialized successfully with circuit: {self.dss_file}")

        except Exception as e:
            logger.error(f"Failed to initialize OpenDSS: {e}")
            # Fallback to creating circuit programmatically
            self._create_default_ehv_circuit()

    def _create_default_ehv_circuit(self):
        """Create a default 400/220 kV substation circuit in OpenDSS"""
        logger.info("Creating default EHV substation circuit")

        # Clear any existing circuit
        dss.run_command("clear")

        # Create new circuit - 400 kV source
        dss.run_command("new circuit.EHV_Substation basekv=400 pu=1.0 phases=3 bus1=SourceBus")
        dss.run_command("set frequency=50")
        dss.run_command("set mode=snapshot")
        dss.run_command("set controlmode=static")

        # 400 kV buses
        dss.run_command("new bus.Bus400_1 basekv=400")
        dss.run_command("new bus.Bus400_2 basekv=400")

        # 220 kV buses
        dss.run_command("new bus.Bus220_1 basekv=220")
        dss.run_command("new bus.Bus220_2 basekv=220")
        dss.run_command("new bus.Bus220_3 basekv=220")

        # 33 kV distribution bus
        dss.run_command("new bus.Bus33_1 basekv=33")

        # 400 kV transmission lines
        dss.run_command("""
            new line.Line400_1 bus1=SourceBus bus2=Bus400_1
            ~ length=50 units=km
            ~ r1=0.02 x1=0.3 r0=0.1 x0=0.9 c1=11.0 c0=3.7
        """)

        dss.run_command("""
            new line.Line400_2 bus1=Bus400_1 bus2=Bus400_2
            ~ length=30 units=km
            ~ r1=0.02 x1=0.3 r0=0.1 x0=0.9 c1=11.0 c0=3.7
        """)

        # 400/220 kV transformers
        dss.run_command("""
            new transformer.TR1 phases=3 windings=2
            ~ wdg=1 bus=Bus400_1 kv=400 kva=315000 %r=0.5
            ~ wdg=2 bus=Bus220_1 kv=220 kva=315000 %r=0.5
            ~ xhl=12 %loadloss=0.5 %noloadloss=0.1
        """)

        dss.run_command("""
            new transformer.TR2 phases=3 windings=2
            ~ wdg=1 bus=Bus400_2 kv=400 kva=315000 %r=0.5
            ~ wdg=2 bus=Bus220_2 kv=220 kva=315000 %r=0.5
            ~ xhl=12 %loadloss=0.5 %noloadloss=0.1
        """)

        # 220 kV lines
        dss.run_command("""
            new line.Line220_1 bus1=Bus220_1 bus2=Bus220_2
            ~ length=40 units=km
            ~ r1=0.05 x1=0.4 r0=0.15 x0=1.2 c1=9.0 c0=3.0
        """)

        dss.run_command("""
            new line.Line220_2 bus1=Bus220_2 bus2=Bus220_3
            ~ length=35 units=km
            ~ r1=0.05 x1=0.4 r0=0.15 x0=1.2 c1=9.0 c0=3.0
        """)

        # 220/33 kV transformer
        dss.run_command("""
            new transformer.TR3 phases=3 windings=2
            ~ wdg=1 bus=Bus220_3 kv=220 kva=100000 %r=0.6
            ~ wdg=2 bus=Bus33_1 kv=33 kva=100000 %r=0.6
            ~ xhl=10 %loadloss=0.6 %noloadloss=0.15
        """)

        # Loads at 220 kV
        dss.run_command("new load.Load220_1 bus1=Bus220_1 phases=3 kv=220 kw=150000 kvar=50000 model=1")
        dss.run_command("new load.Load220_2 bus1=Bus220_2 phases=3 kv=220 kw=100000 kvar=30000 model=1")
        dss.run_command("new load.Load220_3 bus1=Bus220_3 phases=3 kv=220 kw=80000 kvar=25000 model=1")

        # Load at 33 kV
        dss.run_command("new load.Load33_1 bus1=Bus33_1 phases=3 kv=33 kw=50000 kvar=15000 model=1")

        # Capacitor banks for reactive power compensation
        dss.run_command("new capacitor.Cap220_1 bus1=Bus220_1 phases=3 kv=220 kvar=30000")
        dss.run_command("new capacitor.Cap220_2 bus1=Bus220_2 phases=3 kv=220 kvar=20000")

        # Monitors for data collection
        dss.run_command("new monitor.Mon_400_1 element=line.Line400_1 terminal=1 mode=0")
        dss.run_command("new monitor.Mon_TR1 element=transformer.TR1 terminal=1 mode=0")
        dss.run_command("new monitor.Mon_220_1 element=line.Line220_1 terminal=1 mode=0")

        # Solve the circuit
        dss.run_command("solve")

        logger.info("Default EHV circuit created successfully")

    def _store_baseline(self):
        """Store baseline values for comparison"""
        # Get all buses
        bus_names = dss.Circuit.AllBusNames()

        for bus_name in bus_names:
            dss.Circuit.SetActiveBus(bus_name)

            # Store voltage
            voltages = dss.Bus.puVmagAngle()
            self.baseline_voltages[bus_name] = voltages

        # Store baseline for circuit-level metrics
        # Note: Element-level baselines can be added if needed using specific element types

    def inject_voltage_sag(self, bus: str, magnitude: float = 0.7,
                          duration_cycles: int = 30, phases: List[str] = ['A', 'B', 'C']):
        """Inject voltage sag anomaly"""
        if not self.dss:
            raise RuntimeError("OpenDSS not initialized. Cannot inject anomaly.")

        logger.info(f"Injecting voltage sag at {bus}: {magnitude} pu for {duration_cycles} cycles")

        # Create fault to simulate voltage sag
        fault_resistance = 0.001 + (1 - magnitude) * 10  # Adjust fault resistance based on sag depth

        if 'A' in phases:
            dss.run_command(f"new fault.sag_A bus1={bus}.1 bus2={bus}.0 r=({fault_resistance})")
        if 'B' in phases:
            dss.run_command(f"new fault.sag_B bus1={bus}.2 bus2={bus}.0 r=({fault_resistance})")
        if 'C' in phases:
            dss.run_command(f"new fault.sag_C bus1={bus}.3 bus2={bus}.0 r=({fault_resistance})")

        # Solve with fault
        dss.run_command("solve")

        # Record anomaly data
        anomaly_data = self._capture_system_state()
        anomaly_data['anomaly_type'] = 'voltage_sag'
        anomaly_data['location'] = bus
        anomaly_data['severity'] = 1 - magnitude

        # Clear faults
        if 'A' in phases:
            dss.run_command("disable fault.sag_A")
        if 'B' in phases:
            dss.run_command("disable fault.sag_B")
        if 'C' in phases:
            dss.run_command("disable fault.sag_C")

        dss.run_command("solve")

        return anomaly_data

    def inject_harmonic_distortion(self, bus: str, harmonics: Dict[int, float]):
        """Inject harmonic distortion at a bus"""
        logger.info(f"Injecting harmonic distortion at {bus}")

        # Create harmonic current source
        for h_order, h_magnitude in harmonics.items():
            dss.run_command(f"""
                new isource.harm_{h_order} bus1={bus}
                ~ amps={h_magnitude}
                ~ angle=0
                ~ frequency={50 * h_order}
            """)

        # Enable harmonics mode and solve
        dss.run_command("set mode=harmonics")
        dss.run_command("solve")

        # Capture harmonic data
        anomaly_data = self._capture_harmonic_state()
        anomaly_data['anomaly_type'] = 'harmonic_distortion'
        anomaly_data['location'] = bus
        anomaly_data['harmonics'] = harmonics

        # Clean up harmonic sources
        for h_order in harmonics.keys():
            dss.run_command(f"disable isource.harm_{h_order}")

        # Reset to normal mode
        dss.run_command("set mode=snapshot")
        dss.run_command("solve")

        return anomaly_data

    def inject_transformer_overload(self, transformer: str, overload_factor: float = 1.5):
        """Simulate transformer overload condition"""
        logger.info(f"Injecting transformer overload: {transformer} at {overload_factor}x")

        # Get transformer rated power
        dss.Circuit.set_active_element(f"transformer.{transformer}")
        kva_rating = dss.Transformers.kva()

        # Add additional load to cause overload
        overload_kw = kva_rating * overload_factor * 0.9  # Assuming 0.9 power factor
        overload_kvar = kva_rating * overload_factor * 0.436  # For 0.9 power factor

        # Get transformer secondary bus
        dss.Circuit.set_active_element(f"transformer.{transformer}")
        bus2 = dss.CktElement.bus_names[1]

        # Add temporary overload
        dss.run_command(f"""
            new load.overload_{transformer} bus1={bus2}
            ~ phases=3 kv=220
            ~ kw={overload_kw} kvar={overload_kvar}
            ~ model=1
        """)

        dss.run_command("solve")

        # Capture overload condition
        anomaly_data = self._capture_system_state()
        anomaly_data['anomaly_type'] = 'transformer_overload'
        anomaly_data['location'] = transformer
        anomaly_data['overload_factor'] = overload_factor

        # Calculate transformer loading
        dss.Circuit.set_active_element(f"transformer.{transformer}")
        currents = dss.CktElement.currents_mag_ang

        # Remove temporary load
        dss.run_command(f"disable load.overload_{transformer}")
        dss.run_command("solve")

        return anomaly_data

    def inject_capacitor_switching(self, capacitor: str):
        """Simulate capacitor bank switching transient"""
        logger.info(f"Simulating capacitor switching: {capacitor}")

        # Disable capacitor (opening)
        dss.run_command(f"disable capacitor.{capacitor}")
        dss.run_command("solve")

        opening_data = self._capture_system_state()
        opening_data['event'] = 'capacitor_open'

        # Re-enable capacitor (closing) - this creates switching transient
        dss.run_command(f"enable capacitor.{capacitor}")
        dss.run_command("solve")

        closing_data = self._capture_system_state()
        closing_data['event'] = 'capacitor_close'

        anomaly_data = {
            'anomaly_type': 'capacitor_switching',
            'location': capacitor,
            'opening': opening_data,
            'closing': closing_data
        }

        return anomaly_data

    def inject_ground_fault(self, bus: str, fault_resistance: float = 0.01, phase: str = 'A'):
        """Inject single line to ground fault"""
        logger.info(f"Injecting ground fault at {bus} phase {phase}")

        phase_num = {'A': 1, 'B': 2, 'C': 3}[phase]

        # Create ground fault
        dss.run_command(f"""
            new fault.gnd_fault bus1={bus}.{phase_num} bus2={bus}.0
            ~ r={fault_resistance}
            ~ ontime=0.0
            ~ temporary=yes
        """)

        dss.run_command("solve")

        # Capture fault data
        anomaly_data = self._capture_system_state()
        anomaly_data['anomaly_type'] = 'ground_fault'
        anomaly_data['location'] = bus
        anomaly_data['phase'] = phase
        anomaly_data['fault_resistance'] = fault_resistance

        # Calculate fault current
        dss.Circuit.set_active_element(f"fault.gnd_fault")
        fault_current = max(dss.CktElement.currents_mag_ang[::2])  # Get magnitudes
        anomaly_data['fault_current_a'] = fault_current

        # Clear fault
        dss.run_command("disable fault.gnd_fault")
        dss.run_command("solve")

        return anomaly_data

    def inject_frequency_deviation(self, deviation_hz: float = 0.5):
        """Simulate frequency deviation"""
        logger.info(f"Injecting frequency deviation: {deviation_hz} Hz")

        # Change system frequency
        original_freq = 50.0
        new_freq = original_freq + deviation_hz

        dss.run_command(f"set frequency={new_freq}")
        dss.run_command("solve")

        # Capture system response
        anomaly_data = self._capture_system_state()
        anomaly_data['anomaly_type'] = 'frequency_deviation'
        anomaly_data['frequency_hz'] = new_freq
        anomaly_data['deviation_hz'] = deviation_hz

        # Restore original frequency
        dss.run_command(f"set frequency={original_freq}")
        dss.run_command("solve")

        return anomaly_data

    def inject_ct_saturation(self, ct_location: str, saturation_level: float = 0.8):
        """Simulate CT saturation during fault"""
        logger.info(f"Simulating CT saturation at {ct_location}")

        # Create a high current fault to cause CT saturation
        dss.run_command(f"""
            new fault.ct_sat_fault bus1={ct_location}.1.2.3
            ~ bus2={ct_location}.0
            ~ r=0.001
        """)

        dss.run_command("solve")

        # Get fault current
        dss.Circuit.set_active_element(f"fault.ct_sat_fault")
        actual_current = max(dss.CktElement.currents_mag_ang[::2])

        # Simulate saturated CT output (clipped waveform)
        saturated_current = min(actual_current, actual_current * saturation_level)

        anomaly_data = {
            'anomaly_type': 'ct_saturation',
            'location': ct_location,
            'actual_current_a': actual_current,
            'measured_current_a': saturated_current,
            'saturation_ratio': saturated_current / actual_current if actual_current > 0 else 0,
            'error_percent': ((actual_current - saturated_current) / actual_current * 100) if actual_current > 0 else 0
        }

        # Clear fault
        dss.run_command("disable fault.ct_sat_fault")
        dss.run_command("solve")

        return anomaly_data

    def _capture_system_state(self) -> Dict[str, Any]:
        """Capture current system state"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'buses': {},
            'elements': {},
            'losses': {},
            'summary': {}
        }

        # Capture bus voltages
        bus_names = dss.Circuit.AllBusNames()
        for bus_name in bus_names:
            dss.Circuit.SetActiveBus(bus_name)
            voltages = dss.Bus.puVmagAngle()

            # Extract magnitude and angle from puVmagAngle
            voltage_mags = [voltages[i] for i in range(0, len(voltages), 2)]
            voltage_angles = [voltages[i] for i in range(1, len(voltages), 2)]

            state['buses'][bus_name] = {
                'voltage_pu_mag': voltage_mags,
                'voltage_angle': voltage_angles,
            }

        # Element data capture simplified for now
        # Can be expanded with specific element types if needed

        # System summary
        total_power = dss.Circuit.TotalPower()
        losses = dss.Circuit.Losses()
        state['summary'] = {
            'total_power_kw': total_power[0],
            'total_reactive_kvar': total_power[1],
            'losses_kw': losses[0] / 1000,
            'losses_kvar': losses[1] / 1000
        }

        return state

    def _capture_harmonic_state(self) -> Dict[str, Any]:
        """Capture harmonic analysis results"""
        state = self._capture_system_state()

        # Add harmonic specific data
        harmonic_data = {
            'harmonic_voltages': {},
            'harmonic_currents': {},
            'thd_voltage': {},
            'thd_current': {}
        }

        # Get voltage harmonics for each bus
        bus_names = dss.Circuit.AllBusNames()
        for bus_name in bus_names:
            dss.Circuit.SetActiveBus(bus_name)

            # Get harmonic voltages (simplified - would need harmonic solution)
            v_harmonics = dss.Bus.puVmagAngle()

            # Calculate THD (simplified) - using pu voltages
            fundamental = v_harmonics[0] if len(v_harmonics) > 0 else 0

            # Simplified THD calculation (would need actual harmonic solution in production)
            thd = 0.0  # Placeholder

            harmonic_data['thd_voltage'][bus_name] = thd

        state['harmonics'] = harmonic_data
        return state

    def generate_anomaly_dataset(self, num_samples: int = 1000) -> pd.DataFrame:
        """Generate dataset with various anomalies for AI/ML training"""
        logger.info(f"Generating anomaly dataset with {num_samples} samples")

        dataset = []
        anomaly_types = list(AnomalyType)

        for i in range(num_samples):
            # Randomly select anomaly type
            if random.random() < 0.7:  # 70% normal operation
                # Normal operation
                dss.run_command("solve")
                state = self._capture_system_state()
                state['label'] = 0  # Normal
                state['anomaly_type'] = 'normal'
            else:
                # Inject random anomaly
                anomaly_type = random.choice(anomaly_types)

                try:
                    if anomaly_type == AnomalyType.VOLTAGE_SAG:
                        bus = random.choice(['Bus220_1', 'Bus220_2', 'Bus400_1'])
                        magnitude = random.uniform(0.5, 0.9)
                        state = self.inject_voltage_sag(bus, magnitude)

                    elif anomaly_type == AnomalyType.HARMONIC_DISTORTION:
                        bus = random.choice(['Bus220_1', 'Bus220_2'])
                        harmonics = {
                            3: random.uniform(0.01, 0.05),
                            5: random.uniform(0.02, 0.08),
                            7: random.uniform(0.01, 0.04)
                        }
                        state = self.inject_harmonic_distortion(bus, harmonics)

                    elif anomaly_type == AnomalyType.TRANSFORMER_OVERLOAD:
                        transformer = random.choice(['TR1', 'TR2'])
                        overload = random.uniform(1.1, 1.5)
                        state = self.inject_transformer_overload(transformer, overload)

                    elif anomaly_type == AnomalyType.GROUND_FAULT:
                        bus = random.choice(['Bus220_1', 'Bus220_2', 'Bus400_1'])
                        phase = random.choice(['A', 'B', 'C'])
                        state = self.inject_ground_fault(bus, phase=phase)

                    else:
                        # Default to voltage sag for unimplemented types
                        state = self.inject_voltage_sag('Bus220_1', 0.8)

                    state['label'] = 1  # Anomaly

                except Exception as e:
                    logger.error(f"Error injecting {anomaly_type}: {e}")
                    continue

            # Extract features for ML
            features = self._extract_features(state)
            dataset.append(features)

            if (i + 1) % 100 == 0:
                logger.info(f"Generated {i + 1}/{num_samples} samples")

        return pd.DataFrame(dataset)

    def _extract_features(self, state: Dict) -> Dict:
        """Extract relevant features from system state for ML"""
        features = {
            'timestamp': state.get('timestamp', datetime.now().isoformat()),
            'label': state.get('label', 0),
            'anomaly_type': state.get('anomaly_type', 'normal')
        }

        # Extract voltage features
        voltage_mags = []
        voltage_imbalances = []

        for bus_name, bus_data in state.get('buses', {}).items():
            if 'voltage_mag' in bus_data:
                v_mag = bus_data['voltage_mag']
                if len(v_mag) >= 3:
                    voltage_mags.extend(v_mag[:3])
                    # Calculate voltage imbalance
                    v_avg = np.mean(v_mag[:3])
                    v_imbalance = max(abs(v - v_avg) for v in v_mag[:3]) / v_avg if v_avg > 0 else 0
                    voltage_imbalances.append(v_imbalance)

        features['voltage_mag_mean'] = np.mean(voltage_mags) if voltage_mags else 0
        features['voltage_mag_std'] = np.std(voltage_mags) if voltage_mags else 0
        features['voltage_mag_min'] = min(voltage_mags) if voltage_mags else 0
        features['voltage_mag_max'] = max(voltage_mags) if voltage_mags else 0
        features['voltage_imbalance_max'] = max(voltage_imbalances) if voltage_imbalances else 0

        # Extract current features
        current_mags = []
        for element_name, element_data in state.get('elements', {}).items():
            if 'current_mag' in element_data:
                current_mags.extend(element_data['current_mag'])

        features['current_mag_mean'] = np.mean(current_mags) if current_mags else 0
        features['current_mag_std'] = np.std(current_mags) if current_mags else 0
        features['current_mag_max'] = max(current_mags) if current_mags else 0

        # System level features
        summary = state.get('summary', {})
        features['total_power_kw'] = summary.get('total_power_kw', 0)
        features['total_reactive_kvar'] = summary.get('total_reactive_kvar', 0)
        features['losses_kw'] = summary.get('losses_kw', 0)
        features['losses_kvar'] = summary.get('losses_kvar', 0)

        # Power factor
        if features['total_power_kw'] != 0:
            apparent_power = np.sqrt(features['total_power_kw']**2 + features['total_reactive_kvar']**2)
            features['power_factor'] = features['total_power_kw'] / apparent_power if apparent_power > 0 else 0
        else:
            features['power_factor'] = 0

        # Harmonic features (if available)
        if 'harmonics' in state:
            thd_voltages = list(state['harmonics'].get('thd_voltage', {}).values())
            features['thd_voltage_mean'] = np.mean(thd_voltages) if thd_voltages else 0
            features['thd_voltage_max'] = max(thd_voltages) if thd_voltages else 0

        return features

    def run_anomaly_scenario(self, scenario: str) -> Dict[str, Any]:
        """Run predefined anomaly scenarios for testing"""
        logger.info(f"Running anomaly scenario: {scenario}")

        scenarios = {
            'voltage_collapse': self._scenario_voltage_collapse,
            'cascading_failure': self._scenario_cascading_failure,
            'transformer_failure': self._scenario_transformer_failure,
            'harmonic_resonance': self._scenario_harmonic_resonance,
            'protection_misoperation': self._scenario_protection_misoperation
        }

        if scenario in scenarios:
            return scenarios[scenario]()
        else:
            logger.error(f"Unknown scenario: {scenario}")
            return {}

    def _scenario_voltage_collapse(self) -> Dict[str, Any]:
        """Simulate voltage collapse scenario"""
        results = {
            'scenario': 'voltage_collapse',
            'stages': []
        }

        # Stage 1: Heavy loading
        dss.run_command("new load.heavy_load bus1=Bus220_1 phases=3 kv=220 kw=200000 kvar=100000")
        dss.run_command("solve")
        results['stages'].append(self._capture_system_state())

        # Stage 2: Loss of reactive support
        dss.run_command("disable capacitor.Cap220_1")
        dss.run_command("solve")
        results['stages'].append(self._capture_system_state())

        # Stage 3: Line outage
        dss.run_command("disable line.Line220_1")
        dss.run_command("solve")
        results['stages'].append(self._capture_system_state())

        # Restore
        dss.run_command("disable load.heavy_load")
        dss.run_command("enable capacitor.Cap220_1")
        dss.run_command("enable line.Line220_1")
        dss.run_command("solve")

        return results

    def _scenario_cascading_failure(self) -> Dict[str, Any]:
        """Simulate cascading failure scenario"""
        results = {
            'scenario': 'cascading_failure',
            'cascade_sequence': []
        }

        # Initial fault
        dss.run_command("new fault.initial bus1=Bus400_1.1.2.3 bus2=Bus400_1.0 r=0.001")
        dss.run_command("solve")
        results['cascade_sequence'].append({
            'event': 'initial_fault',
            'state': self._capture_system_state()
        })

        # Breaker trips (simulated by disabling line)
        dss.run_command("disable fault.initial")
        dss.run_command("disable line.Line400_1")
        dss.run_command("solve")
        results['cascade_sequence'].append({
            'event': 'line_trip',
            'state': self._capture_system_state()
        })

        # Overload on remaining path
        dss.run_command("disable transformer.TR1")
        dss.run_command("solve")
        results['cascade_sequence'].append({
            'event': 'transformer_trip',
            'state': self._capture_system_state()
        })

        # Restore
        dss.run_command("enable line.Line400_1")
        dss.run_command("enable transformer.TR1")
        dss.run_command("solve")

        return results

    def _scenario_transformer_failure(self) -> Dict[str, Any]:
        """Simulate transformer failure with various fault types"""
        results = {
            'scenario': 'transformer_failure',
            'fault_types': []
        }

        # Winding short circuit
        dss.run_command("new fault.winding bus1=Bus400_1.1 bus2=Bus220_1.1 r=0.1")
        dss.run_command("solve")
        results['fault_types'].append({
            'type': 'winding_short',
            'state': self._capture_system_state()
        })
        dss.run_command("disable fault.winding")

        # Core saturation (simulated by harmonic injection)
        harmonics = {3: 0.15, 5: 0.10, 7: 0.05}
        results['fault_types'].append({
            'type': 'core_saturation',
            'state': self.inject_harmonic_distortion('Bus400_1', harmonics)
        })

        return results

    def _scenario_harmonic_resonance(self) -> Dict[str, Any]:
        """Simulate harmonic resonance condition"""
        results = {
            'scenario': 'harmonic_resonance',
            'frequency_scan': []
        }

        # Scan different harmonic frequencies
        for h_order in [3, 5, 7, 9, 11]:
            dss.run_command(f"set frequency={50 * h_order}")
            dss.run_command("solve")

            state = self._capture_system_state()
            state['harmonic_order'] = h_order
            results['frequency_scan'].append(state)

        # Restore fundamental frequency
        dss.run_command("set frequency=50")
        dss.run_command("solve")

        return results

    def _scenario_protection_misoperation(self) -> Dict[str, Any]:
        """Simulate protection system misoperation"""
        results = {
            'scenario': 'protection_misoperation',
            'events': []
        }

        # Sympathetic trip (healthy line trips due to fault on adjacent line)
        # Fault on Line220_1
        dss.run_command("new fault.test bus1=Bus220_1.1.2.3 bus2=Bus220_1.0 r=0.01")
        dss.run_command("solve")

        fault_state = self._capture_system_state()
        results['events'].append({
            'type': 'fault_applied',
            'state': fault_state
        })

        # Misoperation: Line220_2 also trips (simulated)
        dss.run_command("disable fault.test")
        dss.run_command("disable line.Line220_1")  # Correct trip
        dss.run_command("disable line.Line220_2")  # Misoperation
        dss.run_command("solve")

        results['events'].append({
            'type': 'protection_misoperation',
            'state': self._capture_system_state(),
            'description': 'Healthy line tripped due to sympathetic operation'
        })

        # Restore
        dss.run_command("enable line.Line220_1")
        dss.run_command("enable line.Line220_2")
        dss.run_command("solve")

        return results

def create_anomaly_training_data():
    """Create comprehensive anomaly training dataset"""
    logger.info("Creating anomaly training dataset for AI/ML models")

    # Initialize simulator
    simulator = OpenDSSAnomalySimulator("ehv_substation.dss")

    # Generate dataset with various anomalies
    dataset = simulator.generate_anomaly_dataset(num_samples=2000)

    # Save to CSV
    dataset.to_csv("anomaly_training_data.csv", index=False)
    logger.info(f"Saved training data with {len(dataset)} samples")

    # Generate specific scenario data
    scenarios = ['voltage_collapse', 'cascading_failure', 'transformer_failure',
                'harmonic_resonance', 'protection_misoperation']

    scenario_results = {}
    for scenario in scenarios:
        scenario_results[scenario] = simulator.run_anomaly_scenario(scenario)

    # Save scenario results
    with open("anomaly_scenarios.json", "w") as f:
        json.dump(scenario_results, f, indent=2, default=str)

    logger.info("Anomaly simulation complete")

    return dataset, scenario_results

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create training data
    dataset, scenarios = create_anomaly_training_data()

    print(f"Generated {len(dataset)} training samples")
    print(f"Simulated {len(scenarios)} anomaly scenarios")
    print("\nDataset columns:", dataset.columns.tolist())
    print("\nAnomaly type distribution:")
    print(dataset['anomaly_type'].value_counts())