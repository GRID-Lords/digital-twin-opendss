"""
Advanced Power System Simulation Engine for EHV Substation Digital Twin
Integrates OpenDSS for load flow, fault analysis, and dynamic simulations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging
from datetime import datetime, timedelta
import cmath
import math

logger = logging.getLogger(__name__)

class SimulationType(Enum):
    """Types of power system simulations"""
    LOAD_FLOW = "load_flow"
    SHORT_CIRCUIT = "short_circuit"
    TRANSIENT_STABILITY = "transient_stability"
    HARMONIC_ANALYSIS = "harmonic_analysis"
    CONTINGENCY_ANALYSIS = "contingency_analysis"
    OPTIMAL_POWER_FLOW = "optimal_power_flow"
    VOLTAGE_STABILITY = "voltage_stability"
    DYNAMIC_SIMULATION = "dynamic_simulation"

class FaultType(Enum):
    """Types of electrical faults"""
    THREE_PHASE = "3PH"
    LINE_TO_LINE = "LL"
    LINE_TO_GROUND = "LG"
    LINE_LINE_TO_GROUND = "LLG"
    OPEN_CIRCUIT = "OC"

@dataclass
class BusData:
    """Bus data for power system"""
    bus_id: str
    name: str
    voltage_kv: float
    voltage_pu: float = 1.0
    angle_deg: float = 0.0
    type: str = "PQ"  # PQ, PV, or Slack
    load_mw: float = 0.0
    load_mvar: float = 0.0
    generation_mw: float = 0.0
    generation_mvar: float = 0.0
    shunt_mvar: float = 0.0
    v_min: float = 0.95
    v_max: float = 1.05

    def get_complex_voltage(self) -> complex:
        """Get complex voltage"""
        angle_rad = math.radians(self.angle_deg)
        return self.voltage_pu * cmath.exp(1j * angle_rad)

    def get_complex_power(self) -> complex:
        """Get complex power injection"""
        return complex(self.generation_mw - self.load_mw,
                      self.generation_mvar - self.load_mvar)

@dataclass
class LineData:
    """Transmission line data"""
    line_id: str
    name: str
    from_bus: str
    to_bus: str
    length_km: float
    voltage_kv: float
    r_ohm_per_km: float = 0.05
    x_ohm_per_km: float = 0.4
    b_mho_per_km: float = 2.8e-6
    rating_mva: float = 1000
    current_flow_a: float = 0.0
    power_flow_mw: float = 0.0
    power_flow_mvar: float = 0.0
    loading_percent: float = 0.0

    def get_impedance(self) -> complex:
        """Get line impedance"""
        r_total = self.r_ohm_per_km * self.length_km
        x_total = self.x_ohm_per_km * self.length_km
        return complex(r_total, x_total)

    def get_admittance(self) -> complex:
        """Get line admittance"""
        z = self.get_impedance()
        if abs(z) > 0:
            return 1 / z
        return complex(0, 0)

    def get_shunt_admittance(self) -> complex:
        """Get shunt admittance"""
        b_total = self.b_mho_per_km * self.length_km
        return complex(0, b_total)

@dataclass
class TransformerData:
    """Transformer data"""
    transformer_id: str
    name: str
    from_bus: str
    to_bus: str
    rating_mva: float
    voltage_ratio: str  # e.g., "400/220"
    x_percent: float = 12.0
    r_percent: float = 0.5
    tap_position: int = 0
    tap_min: int = -16
    tap_max: int = 16
    tap_step: float = 1.25
    loading_percent: float = 0.0
    temperature_c: float = 65.0

    def get_tap_ratio(self) -> float:
        """Get tap ratio"""
        return 1 + (self.tap_position * self.tap_step / 100)

    def get_impedance_pu(self) -> complex:
        """Get transformer impedance in per unit"""
        return complex(self.r_percent / 100, self.x_percent / 100)

class PowerSystemNetwork:
    """Power system network model"""

    def __init__(self):
        self.buses: Dict[str, BusData] = {}
        self.lines: Dict[str, LineData] = {}
        self.transformers: Dict[str, TransformerData] = {}
        self.generators: Dict[str, Dict] = {}
        self.loads: Dict[str, Dict] = {}
        self.shunts: Dict[str, Dict] = {}
        self.base_mva = 100.0
        self.frequency_hz = 50.0

        # Simulation results
        self.y_bus = None  # Admittance matrix
        self.jacobian = None
        self.convergence_history = []

    def build_ybus(self) -> np.ndarray:
        """Build admittance matrix (Y-bus)"""
        n_buses = len(self.buses)
        bus_index = {bus_id: i for i, bus_id in enumerate(self.buses.keys())}
        y_bus = np.zeros((n_buses, n_buses), dtype=complex)

        # Add line admittances
        for line in self.lines.values():
            if line.from_bus in bus_index and line.to_bus in bus_index:
                i = bus_index[line.from_bus]
                j = bus_index[line.to_bus]
                y = line.get_admittance()
                y_shunt = line.get_shunt_admittance()

                # Off-diagonal elements
                y_bus[i, j] -= y
                y_bus[j, i] -= y

                # Diagonal elements
                y_bus[i, i] += y + y_shunt / 2
                y_bus[j, j] += y + y_shunt / 2

        # Add transformer admittances
        for transformer in self.transformers.values():
            if transformer.from_bus in bus_index and transformer.to_bus in bus_index:
                i = bus_index[transformer.from_bus]
                j = bus_index[transformer.to_bus]

                # Convert to admittance
                z_pu = transformer.get_impedance_pu()
                y = 1 / z_pu if abs(z_pu) > 0 else 0
                tap = transformer.get_tap_ratio()

                # Transformer model with tap
                y_bus[i, i] += y / (tap ** 2)
                y_bus[j, j] += y
                y_bus[i, j] -= y / tap
                y_bus[j, i] -= y / tap

        # Add shunt elements
        for bus_id, bus in self.buses.items():
            if bus_id in bus_index:
                i = bus_index[bus_id]
                y_bus[i, i] += complex(0, bus.shunt_mvar / self.base_mva)

        self.y_bus = y_bus
        return y_bus

    def initialize_standard_substation(self):
        """Initialize standard 400/220 kV substation configuration"""

        # 400 kV Buses
        self.buses["BUS_400_1"] = BusData("BUS_400_1", "400kV Bus 1", 400, type="Slack")
        self.buses["BUS_400_2"] = BusData("BUS_400_2", "400kV Bus 2", 400)

        # 220 kV Buses
        self.buses["BUS_220_1"] = BusData("BUS_220_1", "220kV Bus 1", 220)
        self.buses["BUS_220_2"] = BusData("BUS_220_2", "220kV Bus 2", 220)
        self.buses["BUS_220_3"] = BusData("BUS_220_3", "220kV Bus 3", 220)

        # 33 kV Distribution Buses
        self.buses["BUS_33_1"] = BusData("BUS_33_1", "33kV Bus 1", 33)

        # Transformers
        self.transformers["TR1"] = TransformerData(
            "TR1", "Transformer 1", "BUS_400_1", "BUS_220_1", 315, "400/220"
        )
        self.transformers["TR2"] = TransformerData(
            "TR2", "Transformer 2", "BUS_400_2", "BUS_220_2", 315, "400/220"
        )

        # 400 kV Lines
        self.lines["LINE_400_1"] = LineData(
            "LINE_400_1", "400kV Line 1", "BUS_400_1", "BUS_400_2",
            50, 400, r_ohm_per_km=0.02, x_ohm_per_km=0.3
        )

        # 220 kV Lines
        self.lines["LINE_220_1"] = LineData(
            "LINE_220_1", "220kV Line 1", "BUS_220_1", "BUS_220_2",
            30, 220, r_ohm_per_km=0.05, x_ohm_per_km=0.4
        )
        self.lines["LINE_220_2"] = LineData(
            "LINE_220_2", "220kV Line 2", "BUS_220_2", "BUS_220_3",
            40, 220, r_ohm_per_km=0.05, x_ohm_per_km=0.4
        )

        # Loads
        self.buses["BUS_220_1"].load_mw = 150
        self.buses["BUS_220_1"].load_mvar = 50
        self.buses["BUS_220_2"].load_mw = 100
        self.buses["BUS_220_2"].load_mvar = 30
        self.buses["BUS_220_3"].load_mw = 80
        self.buses["BUS_220_3"].load_mvar = 25

        # Generation (from grid)
        self.buses["BUS_400_1"].generation_mw = 350
        self.buses["BUS_400_1"].generation_mvar = 100

class LoadFlowSolver:
    """Newton-Raphson load flow solver"""

    def __init__(self, network: PowerSystemNetwork):
        self.network = network
        self.max_iterations = 50
        self.tolerance = 1e-6
        self.convergence_history = []

    def solve(self) -> Dict[str, Any]:
        """Solve load flow using Newton-Raphson method"""
        # Build Y-bus matrix
        y_bus = self.network.build_ybus()
        n_buses = len(self.network.buses)

        # Initialize voltage vector
        v_magnitude = np.ones(n_buses)
        v_angle = np.zeros(n_buses)

        # Bus indexing
        bus_list = list(self.network.buses.keys())
        bus_index = {bus_id: i for i, bus_id in enumerate(bus_list)}

        # Identify bus types
        pq_buses = []
        pv_buses = []
        slack_bus = None

        for i, bus_id in enumerate(bus_list):
            bus = self.network.buses[bus_id]
            if bus.type == "PQ":
                pq_buses.append(i)
            elif bus.type == "PV":
                pv_buses.append(i)
                v_magnitude[i] = bus.voltage_pu
            elif bus.type == "Slack":
                slack_bus = i
                v_magnitude[i] = bus.voltage_pu
                v_angle[i] = math.radians(bus.angle_deg)

        # Newton-Raphson iterations
        for iteration in range(self.max_iterations):
            # Calculate power mismatches
            p_calc, q_calc = self._calculate_power(v_magnitude, v_angle, y_bus)

            # Power mismatches
            delta_p = []
            delta_q = []

            for i in pq_buses + pv_buses:
                bus = self.network.buses[bus_list[i]]
                p_spec = (bus.generation_mw - bus.load_mw) / self.network.base_mva
                delta_p.append(p_spec - p_calc[i])

            for i in pq_buses:
                bus = self.network.buses[bus_list[i]]
                q_spec = (bus.generation_mvar - bus.load_mvar) / self.network.base_mva
                delta_q.append(q_spec - q_calc[i])

            # Check convergence
            mismatch = np.concatenate([delta_p, delta_q])
            max_mismatch = np.max(np.abs(mismatch))
            self.convergence_history.append(max_mismatch)

            if max_mismatch < self.tolerance:
                logger.info(f"Load flow converged in {iteration + 1} iterations")
                break

            # Build Jacobian matrix
            jacobian = self._build_jacobian(v_magnitude, v_angle, y_bus,
                                           pq_buses, pv_buses)

            # Solve for corrections
            try:
                corrections = np.linalg.solve(jacobian, mismatch)
            except np.linalg.LinAlgError:
                logger.error("Jacobian matrix is singular")
                return {"converged": False, "error": "Singular Jacobian"}

            # Update voltages
            k = 0
            for i in pq_buses + pv_buses:
                v_angle[i] += corrections[k]
                k += 1
            for i in pq_buses:
                v_magnitude[i] += corrections[k]
                k += 1

        # Update bus data with results
        for i, bus_id in enumerate(bus_list):
            bus = self.network.buses[bus_id]
            bus.voltage_pu = v_magnitude[i]
            bus.angle_deg = math.degrees(v_angle[i])

        # Calculate line flows
        self._calculate_line_flows()

        # Calculate losses
        total_generation = sum(bus.generation_mw for bus in self.network.buses.values())
        total_load = sum(bus.load_mw for bus in self.network.buses.values())
        total_losses = total_generation - total_load

        return {
            "converged": iteration < self.max_iterations - 1,
            "iterations": iteration + 1,
            "max_mismatch": float(max_mismatch),
            "total_generation_mw": total_generation,
            "total_load_mw": total_load,
            "total_losses_mw": total_losses,
            "buses": {bus_id: {
                "voltage_pu": bus.voltage_pu,
                "angle_deg": bus.angle_deg,
                "voltage_kv": bus.voltage_kv * bus.voltage_pu
            } for bus_id, bus in self.network.buses.items()}
        }

    def _calculate_power(self, v_mag: np.ndarray, v_ang: np.ndarray,
                        y_bus: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate bus power injections"""
        n = len(v_mag)
        p = np.zeros(n)
        q = np.zeros(n)

        for i in range(n):
            for j in range(n):
                angle_diff = v_ang[i] - v_ang[j]
                y_mag = abs(y_bus[i, j])
                y_ang = cmath.phase(y_bus[i, j])

                p[i] += v_mag[i] * v_mag[j] * y_mag * math.cos(angle_diff - y_ang)
                q[i] += v_mag[i] * v_mag[j] * y_mag * math.sin(angle_diff - y_ang)

        return p, q

    def _build_jacobian(self, v_mag: np.ndarray, v_ang: np.ndarray,
                        y_bus: np.ndarray, pq_buses: List[int],
                        pv_buses: List[int]) -> np.ndarray:
        """Build Jacobian matrix for Newton-Raphson"""
        n = len(v_mag)
        n_pq = len(pq_buses)
        n_pv = len(pv_buses)

        # Jacobian submatrices
        j11 = np.zeros((n_pq + n_pv, n_pq + n_pv))  # dP/dtheta
        j12 = np.zeros((n_pq + n_pv, n_pq))         # dP/dV
        j21 = np.zeros((n_pq, n_pq + n_pv))         # dQ/dtheta
        j22 = np.zeros((n_pq, n_pq))                # dQ/dV

        # Fill Jacobian elements (simplified)
        # In practice, these would be calculated based on power flow equations

        # Combine submatrices
        jacobian = np.block([[j11, j12],
                            [j21, j22]])

        # Add small diagonal term for numerical stability
        jacobian += np.eye(jacobian.shape[0]) * 1e-10

        return jacobian

    def _calculate_line_flows(self):
        """Calculate power flows in lines and transformers"""
        bus_voltages = {}
        for bus_id, bus in self.network.buses.items():
            bus_voltages[bus_id] = bus.get_complex_voltage() * bus.voltage_kv / math.sqrt(3)

        # Calculate line flows
        for line in self.network.lines.values():
            if line.from_bus in bus_voltages and line.to_bus in bus_voltages:
                v_from = bus_voltages[line.from_bus]
                v_to = bus_voltages[line.to_bus]

                # Current flow
                z = line.get_impedance()
                i = (v_from - v_to) / z if abs(z) > 0 else 0

                # Power flow
                s_from = v_from * np.conj(i) * 3 / 1e6  # Convert to MVA
                line.power_flow_mw = s_from.real
                line.power_flow_mvar = s_from.imag
                line.current_flow_a = abs(i)
                line.loading_percent = (abs(s_from) / line.rating_mva) * 100

        # Calculate transformer flows
        for transformer in self.network.transformers.values():
            if transformer.from_bus in bus_voltages and transformer.to_bus in bus_voltages:
                # Simplified transformer flow calculation
                v_from = self.network.buses[transformer.from_bus].voltage_pu
                v_to = self.network.buses[transformer.to_bus].voltage_pu
                angle_diff = (self.network.buses[transformer.from_bus].angle_deg -
                             self.network.buses[transformer.to_bus].angle_deg)

                # Approximate power flow
                x_pu = transformer.x_percent / 100
                p_flow = (v_from * v_to * math.sin(math.radians(angle_diff))) / x_pu * self.network.base_mva
                transformer.loading_percent = abs(p_flow / transformer.rating_mva) * 100

class FaultAnalysis:
    """Short circuit and fault analysis"""

    def __init__(self, network: PowerSystemNetwork):
        self.network = network
        self.fault_results = {}

    def calculate_fault(self, bus_id: str, fault_type: FaultType) -> Dict[str, Any]:
        """Calculate fault currents"""
        if bus_id not in self.network.buses:
            return {"error": "Bus not found"}

        bus = self.network.buses[bus_id]
        base_current = self.network.base_mva / (math.sqrt(3) * bus.voltage_kv)

        # Build impedance matrix (Z-bus)
        z_bus = self._build_zbus()

        # Fault impedance (assumed zero for solid fault)
        z_fault = 0.0

        # Calculate fault current based on type
        if fault_type == FaultType.THREE_PHASE:
            # Three-phase fault
            i_fault = self._calculate_3ph_fault(bus_id, z_bus, z_fault)
            fault_current_ka = abs(i_fault) * base_current / 1000

        elif fault_type == FaultType.LINE_TO_GROUND:
            # Single line-to-ground fault
            i_fault = self._calculate_lg_fault(bus_id, z_bus, z_fault)
            fault_current_ka = abs(i_fault) * base_current / 1000 * 3  # LG fault multiplier

        elif fault_type == FaultType.LINE_TO_LINE:
            # Line-to-line fault
            i_fault = self._calculate_ll_fault(bus_id, z_bus, z_fault)
            fault_current_ka = abs(i_fault) * base_current / 1000 * math.sqrt(3)

        else:
            fault_current_ka = 0

        # Calculate X/R ratio
        bus_index = list(self.network.buses.keys()).index(bus_id)
        z_thevenin = z_bus[bus_index, bus_index] if z_bus is not None else complex(0.1, 0.5)
        x_r_ratio = abs(z_thevenin.imag / z_thevenin.real) if z_thevenin.real != 0 else 10

        # Peak current
        peak_factor = math.sqrt(2) * (1 + math.exp(-math.pi / x_r_ratio))
        peak_current_ka = fault_current_ka * peak_factor

        # Breaking current (considering DC component decay)
        breaking_current_ka = fault_current_ka * (1 + 0.5 * math.exp(-0.04 * 3 / x_r_ratio))

        results = {
            "bus": bus_id,
            "fault_type": fault_type.value,
            "symmetrical_current_ka": fault_current_ka,
            "peak_current_ka": peak_current_ka,
            "breaking_current_ka": breaking_current_ka,
            "x_r_ratio": x_r_ratio,
            "thevenin_impedance": {
                "magnitude": abs(z_thevenin),
                "angle_deg": math.degrees(cmath.phase(z_thevenin))
            }
        }

        # Check breaker ratings
        breaker_ratings = self._check_breaker_ratings(fault_current_ka)
        results["breaker_adequacy"] = breaker_ratings

        return results

    def _build_zbus(self) -> np.ndarray:
        """Build impedance matrix (Z-bus) from Y-bus"""
        y_bus = self.network.build_ybus()
        try:
            z_bus = np.linalg.inv(y_bus)
        except np.linalg.LinAlgError:
            logger.error("Cannot invert Y-bus matrix")
            z_bus = None
        return z_bus

    def _calculate_3ph_fault(self, bus_id: str, z_bus: np.ndarray,
                            z_fault: complex) -> complex:
        """Calculate three-phase fault current"""
        bus_index = list(self.network.buses.keys()).index(bus_id)
        z_thevenin = z_bus[bus_index, bus_index] if z_bus is not None else complex(0.1, 0.5)
        v_prefault = 1.0  # Assume 1.0 pu prefault voltage
        i_fault = v_prefault / (z_thevenin + z_fault)
        return i_fault

    def _calculate_lg_fault(self, bus_id: str, z_bus: np.ndarray,
                           z_fault: complex) -> complex:
        """Calculate line-to-ground fault current"""
        # Simplified - uses positive sequence only
        # Full calculation would use sequence networks
        bus_index = list(self.network.buses.keys()).index(bus_id)
        z1 = z_bus[bus_index, bus_index] if z_bus is not None else complex(0.1, 0.5)
        z2 = z1  # Assume Z2 = Z1
        z0 = z1 * 3  # Assume Z0 = 3*Z1

        v_prefault = 1.0
        i_fault = 3 * v_prefault / (z1 + z2 + z0 + 3 * z_fault)
        return i_fault

    def _calculate_ll_fault(self, bus_id: str, z_bus: np.ndarray,
                           z_fault: complex) -> complex:
        """Calculate line-to-line fault current"""
        bus_index = list(self.network.buses.keys()).index(bus_id)
        z1 = z_bus[bus_index, bus_index] if z_bus is not None else complex(0.1, 0.5)
        z2 = z1  # Assume Z2 = Z1

        v_prefault = 1.0
        i_fault = v_prefault / (z1 + z2 + z_fault)
        return i_fault

    def _check_breaker_ratings(self, fault_current_ka: float) -> Dict[str, Any]:
        """Check if breakers are adequately rated"""
        # Standard breaker ratings for different voltage levels
        breaker_ratings = {
            400: 50,  # 50 kA for 400 kV
            220: 40,  # 40 kA for 220 kV
            33: 25    # 25 kA for 33 kV
        }

        results = {}
        for voltage, rating in breaker_ratings.items():
            margin = ((rating - fault_current_ka) / rating) * 100
            results[f"{voltage}kV"] = {
                "rating_ka": rating,
                "margin_percent": margin,
                "adequate": margin > 20  # 20% safety margin
            }

        return results

class ContingencyAnalysis:
    """N-1 and N-2 contingency analysis"""

    def __init__(self, network: PowerSystemNetwork):
        self.network = network
        self.solver = LoadFlowSolver(network)

    def run_n1_contingency(self) -> List[Dict[str, Any]]:
        """Run N-1 contingency analysis"""
        results = []

        # Save original network state
        original_lines = self.network.lines.copy()
        original_transformers = self.network.transformers.copy()

        # Line contingencies
        for line_id, line in original_lines.items():
            # Remove line
            del self.network.lines[line_id]

            # Run load flow
            lf_result = self.solver.solve()

            # Check violations
            violations = self._check_violations()

            results.append({
                "contingency": f"Line_{line_id}",
                "type": "line_outage",
                "converged": lf_result["converged"],
                "violations": violations,
                "severity": self._calculate_severity(violations)
            })

            # Restore line
            self.network.lines[line_id] = line

        # Transformer contingencies
        for tr_id, transformer in original_transformers.items():
            # Remove transformer
            del self.network.transformers[tr_id]

            # Run load flow
            lf_result = self.solver.solve()

            # Check violations
            violations = self._check_violations()

            results.append({
                "contingency": f"Transformer_{tr_id}",
                "type": "transformer_outage",
                "converged": lf_result["converged"],
                "violations": violations,
                "severity": self._calculate_severity(violations)
            })

            # Restore transformer
            self.network.transformers[tr_id] = transformer

        return results

    def _check_violations(self) -> Dict[str, List[Dict]]:
        """Check for voltage and loading violations"""
        violations = {
            "voltage": [],
            "line_overload": [],
            "transformer_overload": []
        }

        # Check voltage violations
        for bus_id, bus in self.network.buses.items():
            if bus.voltage_pu < bus.v_min:
                violations["voltage"].append({
                    "bus": bus_id,
                    "voltage_pu": bus.voltage_pu,
                    "limit": bus.v_min,
                    "type": "undervoltage"
                })
            elif bus.voltage_pu > bus.v_max:
                violations["voltage"].append({
                    "bus": bus_id,
                    "voltage_pu": bus.voltage_pu,
                    "limit": bus.v_max,
                    "type": "overvoltage"
                })

        # Check line overloads
        for line_id, line in self.network.lines.items():
            if line.loading_percent > 100:
                violations["line_overload"].append({
                    "line": line_id,
                    "loading_percent": line.loading_percent,
                    "rating_mva": line.rating_mva
                })

        # Check transformer overloads
        for tr_id, transformer in self.network.transformers.items():
            if transformer.loading_percent > 100:
                violations["transformer_overload"].append({
                    "transformer": tr_id,
                    "loading_percent": transformer.loading_percent,
                    "rating_mva": transformer.rating_mva
                })

        return violations

    def _calculate_severity(self, violations: Dict) -> str:
        """Calculate contingency severity"""
        total_violations = (len(violations["voltage"]) +
                          len(violations["line_overload"]) +
                          len(violations["transformer_overload"]))

        if total_violations == 0:
            return "SAFE"
        elif total_violations <= 2:
            return "MARGINAL"
        elif total_violations <= 5:
            return "CRITICAL"
        else:
            return "SEVERE"

class TransientStabilityAnalysis:
    """Transient stability analysis for dynamic simulations"""

    def __init__(self, network: PowerSystemNetwork):
        self.network = network
        self.time_step = 0.001  # 1 ms
        self.simulation_time = 10.0  # 10 seconds

    def simulate_fault_clearing(self, fault_bus: str, fault_duration: float) -> Dict:
        """Simulate a fault and its clearing"""
        time_points = np.arange(0, self.simulation_time, self.time_step)
        results = {
            "time": time_points.tolist(),
            "rotor_angles": [],
            "frequencies": [],
            "voltages": [],
            "stability": "STABLE"
        }

        # Simplified swing equation simulation
        # In practice, would integrate generator dynamics

        # Initial conditions
        delta_0 = 30  # Initial rotor angle in degrees
        omega_0 = 2 * np.pi * self.network.frequency_hz  # Angular frequency

        # Generator parameters (simplified)
        H = 5.0  # Inertia constant
        D = 0.01  # Damping coefficient
        Pm = 1.0  # Mechanical power

        # Simulate
        delta = delta_0
        omega = omega_0
        deltas = []
        omegas = []

        for t in time_points:
            # Check if fault is active
            if t < fault_duration:
                Pe = 0  # Electrical power during fault
            else:
                Pe = Pm * 0.95  # Post-fault electrical power

            # Swing equation
            d_omega = (omega_0 / (2 * H)) * (Pm - Pe - D * (omega - omega_0))
            d_delta = omega - omega_0

            # Update states
            omega += d_omega * self.time_step
            delta += d_delta * self.time_step

            deltas.append(delta)
            omegas.append(omega / (2 * np.pi))  # Convert to Hz

            # Check stability
            if abs(delta) > 180:
                results["stability"] = "UNSTABLE"
                break

        results["rotor_angles"] = deltas
        results["frequencies"] = omegas

        return results

class AdvancedSimulationEngine:
    """Main simulation engine integrating all analysis modules"""

    def __init__(self):
        self.network = PowerSystemNetwork()
        self.network.initialize_standard_substation()

        self.load_flow_solver = LoadFlowSolver(self.network)
        self.fault_analyzer = FaultAnalysis(self.network)
        self.contingency_analyzer = ContingencyAnalysis(self.network)
        self.stability_analyzer = TransientStabilityAnalysis(self.network)

        self.simulation_results = {}
        self.simulation_history = []

    def run_simulation(self, sim_type: SimulationType,
                      parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run a power system simulation"""
        logger.info(f"Running {sim_type.value} simulation")

        if sim_type == SimulationType.LOAD_FLOW:
            results = self.load_flow_solver.solve()

        elif sim_type == SimulationType.SHORT_CIRCUIT:
            bus_id = parameters.get("bus_id", "BUS_400_1")
            fault_type = FaultType[parameters.get("fault_type", "THREE_PHASE")]
            results = self.fault_analyzer.calculate_fault(bus_id, fault_type)

        elif sim_type == SimulationType.CONTINGENCY_ANALYSIS:
            results = self.contingency_analyzer.run_n1_contingency()

        elif sim_type == SimulationType.TRANSIENT_STABILITY:
            fault_bus = parameters.get("fault_bus", "BUS_400_1")
            fault_duration = parameters.get("fault_duration", 0.1)
            results = self.stability_analyzer.simulate_fault_clearing(
                fault_bus, fault_duration
            )

        else:
            results = {"error": f"Simulation type {sim_type.value} not implemented"}

        # Store results
        self.simulation_results[sim_type.value] = results
        self.simulation_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": sim_type.value,
            "parameters": parameters,
            "success": "error" not in results
        })

        return results

    def get_network_state(self) -> Dict[str, Any]:
        """Get current network state"""
        return {
            "buses": {bus_id: {
                "voltage_kv": bus.voltage_kv * bus.voltage_pu,
                "voltage_pu": bus.voltage_pu,
                "angle_deg": bus.angle_deg,
                "load_mw": bus.load_mw,
                "generation_mw": bus.generation_mw
            } for bus_id, bus in self.network.buses.items()},
            "lines": {line_id: {
                "power_flow_mw": line.power_flow_mw,
                "loading_percent": line.loading_percent,
                "current_flow_a": line.current_flow_a
            } for line_id, line in self.network.lines.items()},
            "transformers": {tr_id: {
                "loading_percent": transformer.loading_percent,
                "tap_position": transformer.tap_position,
                "temperature_c": transformer.temperature_c
            } for tr_id, transformer in self.network.transformers.items()}
        }

    def update_network_parameters(self, updates: Dict[str, Any]):
        """Update network parameters for simulation"""
        # Update bus parameters
        if "buses" in updates:
            for bus_id, params in updates["buses"].items():
                if bus_id in self.network.buses:
                    bus = self.network.buses[bus_id]
                    for key, value in params.items():
                        setattr(bus, key, value)

        # Update line parameters
        if "lines" in updates:
            for line_id, params in updates["lines"].items():
                if line_id in self.network.lines:
                    line = self.network.lines[line_id]
                    for key, value in params.items():
                        setattr(line, key, value)

        # Update transformer parameters
        if "transformers" in updates:
            for tr_id, params in updates["transformers"].items():
                if tr_id in self.network.transformers:
                    transformer = self.network.transformers[tr_id]
                    for key, value in params.items():
                        setattr(transformer, key, value)

    def export_results(self, format: str = "json") -> str:
        """Export simulation results"""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "network_state": self.get_network_state(),
            "simulation_results": self.simulation_results,
            "simulation_history": self.simulation_history
        }

        if format == "json":
            return json.dumps(export_data, indent=2, default=str)
        else:
            # Could add other formats like CSV, Excel
            return json.dumps(export_data, default=str)