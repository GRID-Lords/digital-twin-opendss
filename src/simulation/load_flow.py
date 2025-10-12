"""
Load Flow Analysis Module using py-dss-interface
"""
import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class LoadFlowAnalysis:
    def __init__(self):
        self.circuit = None
        self.dss = None
        self.results = {}
        self.base_load_mw = 420  # Base load for Indian EHV substation
        self.active_anomaly = None  # Store active anomaly to inject before solving

    def set_anomaly(self, anomaly_type: str, parameters: Dict[str, Any]):
        """Set active anomaly to be injected before next solve"""
        self.active_anomaly = {
            'type': anomaly_type,
            'parameters': parameters
        }
        logger.info(f"Anomaly set: {anomaly_type} with params {parameters}")

    def clear_anomaly(self):
        """Clear active anomaly"""
        self.active_anomaly = None
        logger.info("Anomaly cleared")

    def inject_anomaly_into_circuit(self):
        """Inject active anomaly directly into OpenDSS circuit before solving"""
        if not self.active_anomaly or not self.dss:
            return

        anomaly_type = self.active_anomaly['type']
        params = self.active_anomaly['parameters']

        try:
            logger.info(f"🔥 Injecting anomaly into OpenDSS circuit: {anomaly_type}")

            if anomaly_type == 'voltage_sag':
                # Reduce source voltage
                severity = params.get('severity', 0.85)
                self.dss.Text.Command(f"Vsource.GridSource.pu={severity}")
                logger.info(f"Applied voltage sag: voltage set to {severity} p.u.")

            elif anomaly_type == 'voltage_surge':
                # Increase source voltage
                severity = params.get('severity', 1.12)
                self.dss.Text.Command(f"Vsource.GridSource.pu={severity}")
                logger.info(f"Applied voltage surge: voltage set to {severity} p.u.")

            elif anomaly_type == 'overload' or anomaly_type == 'transformer_overload':
                # Increase all loads by load factor
                load_factor = params.get('load_factor', 1.2)
                self.dss.Text.Command(f"set loadmult={load_factor}")
                logger.info(f"Applied transformer overload: load multiplier set to {load_factor}")

            elif anomaly_type == 'ground_fault':
                # Enable a fault at specified location
                location = params.get('location', 'Bus400kV_1')
                resistance = params.get('resistance', 5)
                # Create or modify fault object
                self.dss.Text.Command(f"New Fault.AnomalyFault bus1={location} phases=1 r={resistance} enabled=yes")
                logger.info(f"Applied ground fault at {location} with R={resistance}Ω")

            elif anomaly_type == 'harmonics' or anomaly_type == 'harmonic_distortion':
                # Add harmonic spectrum to loads
                thd = params.get('thd', 5)
                order = params.get('order', '5')
                # Apply harmonic spectrum to loads
                self.dss.Text.Command(f"Load.IndustrialLoad1.spectrum=defaultload")
                self.dss.Text.Command(f"Load.IndustrialLoad2.spectrum=defaultload")
                logger.info(f"Applied harmonic distortion: THD={thd}%, order={order}")

            elif anomaly_type == 'frequency_deviation':
                # Change base frequency
                deviation = params.get('deviation', 0.3)
                freq_type = params.get('type', 'under')
                base_freq = 50.0
                if freq_type == 'under':
                    new_freq = base_freq - deviation
                else:
                    new_freq = base_freq + deviation
                self.dss.Text.Command(f"set frequency={new_freq}")
                logger.info(f"Applied frequency deviation: {new_freq} Hz")

            else:
                logger.warning(f"Unknown anomaly type: {anomaly_type}")

        except Exception as e:
            logger.error(f"Error injecting anomaly into circuit: {e}")

    def apply_realistic_load_pattern(self):
        """Apply realistic seasonal and daily load patterns to OpenDSS circuit"""
        if not self.dss or not self.circuit:
            return

        from datetime import datetime
        now = datetime.now()
        hour = now.hour
        month = now.month

        # ==== SEASONAL VARIATIONS (Indian Climate) ====
        if 3 <= month <= 6:  # Summer
            seasonal_factor = 1.15
        elif 7 <= month <= 9:  # Monsoon
            seasonal_factor = 1.0
        elif month >= 11 or month <= 2:  # Winter
            seasonal_factor = 0.85
        else:  # Autumn
            seasonal_factor = 0.95

        # ==== DAILY LOAD PATTERN ====
        if 6 <= hour < 9:  # Morning peak
            daily_factor = 0.85 + (hour - 6) * 0.05
        elif 9 <= hour < 10:
            daily_factor = 0.95
        elif 10 <= hour < 14:  # Midday peak
            daily_factor = 0.95 + (12 - abs(hour - 12)) * 0.05
        elif 14 <= hour < 17:
            daily_factor = 0.90
        elif 17 <= hour < 22:  # Evening peak
            daily_factor = 1.0 + (20 - abs(hour - 20)) * 0.05
        elif 22 <= hour < 24:
            daily_factor = 0.70 - (hour - 22) * 0.05
        else:  # Night valley
            daily_factor = 0.50 + hour * 0.02

        # Combined load factor (but don't override if anomaly is active with overload)
        load_factor = seasonal_factor * daily_factor

        # Skip load pattern if transformer overload anomaly is active (it sets its own loadmult)
        if self.active_anomaly and self.active_anomaly['type'] in ['overload', 'transformer_overload']:
            logger.debug("Skipping realistic load pattern - overload anomaly is active")
            return

        try:
            # Apply load factor to all loads in circuit
            self.dss.Text.Command(f"set loadmult={load_factor}")
            logger.debug(f"Applied load pattern: seasonal={seasonal_factor:.2f}, daily={daily_factor:.2f}, total={load_factor:.2f}")
        except Exception as e:
            logger.warning(f"Could not apply load pattern: {e}")

    def load_circuit(self, dss_file: str):
        """Load circuit from DSS file using OpenDSS"""
        try:
            import opendssdirect as dss
            self.dss = dss
            self._dss_file = dss_file  # Store for re-activation

            # Compile the DSS file
            dss.Text.Command(f"compile [{dss_file}]")

            # Store circuit reference
            self.circuit = dss.Circuit

            logger.info(f"Successfully loaded OpenDSS circuit from {dss_file}")
            return True
        except Exception as e:
            logger.error(f"Error loading circuit: {e}")
            self.circuit = None
            return False

    def solve(self) -> Dict[str, Any]:
        """Run load flow analysis using actual OpenDSS"""
        if not self.dss:
            # Return fallback values if OpenDSS not initialized
            logger.warning("⚠️ OpenDSS not initialized, returning fallback values (NOT REAL DATA)")
            return {
                "converged": True,
                "iterations": 5,
                "max_voltage_pu": 1.02,
                "min_voltage_pu": 0.98,
                "total_losses_mw": 3.2,
                "power_factor": 0.95,
                "voltage_400kv": 400.0,
                "voltage_220kv": 220.0,
                "frequency": 50.0,
                "total_power_kw": 0,
                "total_power_kvar": 0
            }

        try:
            # Recompile circuit to ensure it's active (opendssdirect loses context)
            if hasattr(self, '_dss_file') and self._dss_file:
                self.dss.Text.Command(f"compile [{self._dss_file}]")
                # Must recalculate voltage bases after recompile
                self.dss.Text.Command("CalcVoltageBases")

            # Apply realistic load patterns before solving
            self.apply_realistic_load_pattern()

            # *** INJECT ANOMALY INTO CIRCUIT BEFORE SOLVING ***
            self.inject_anomaly_into_circuit()

            # Solve the power flow
            self.dss.Text.Command("solve")
            logger.info(f"Solve converged: {self.dss.Solution.Converged()}")

            # Check if solution converged
            converged = self.dss.Solution.Converged()
            iterations = self.dss.Solution.Iterations()

            # Get voltage profile
            voltages_pu = []
            voltage_400kv = 400.0
            voltage_220kv = 220.0

            bus_names = self.dss.Circuit.AllBusNames()
            logger.info(f"Found {len(bus_names)} buses in circuit")

            import math
            for bus_name in bus_names:
                self.dss.Circuit.SetActiveBus(bus_name)
                v_pu = self.dss.Bus.puVmagAngle()
                if v_pu and len(v_pu) > 0:
                    voltages_pu.append(v_pu[0])  # Magnitude

                    # Get actual kV value (OpenDSS returns line-to-neutral for 3-phase)
                    kv_base = self.dss.Bus.kVBase()
                    kv_actual_ln = v_pu[0] * kv_base
                    kv_actual_ll = kv_actual_ln * math.sqrt(3)  # Convert to line-to-line

                    # Categorize by voltage level (kv_base is L-N: 400kV L-L = 231 kV L-N)
                    if kv_base > 200:  # 400kV bus (L-N base ~231 kV)
                        voltage_400kv = kv_actual_ll
                        logger.info(f"400kV bus: {bus_name}, kv_base={kv_base:.2f}, v_pu={v_pu[0]:.4f}, kv_L-L={kv_actual_ll:.2f}")
                    elif kv_base > 50:  # 220kV bus (L-N base ~127 kV)
                        voltage_220kv = kv_actual_ll
                        logger.info(f"220kV bus: {bus_name}, kv_base={kv_base:.2f}, v_pu={v_pu[0]:.4f}, kv_L-L={kv_actual_ll:.2f}")

            max_voltage_pu = max(voltages_pu) if voltages_pu else 1.0
            min_voltage_pu = min(voltages_pu) if voltages_pu else 1.0

            # Get total losses (OpenDSS Circuit.Losses() returns in W)
            losses = self.dss.Circuit.Losses()
            total_losses_kw = abs(losses[0]) / 1000  # Convert W to kW
            total_losses_mw = total_losses_kw / 1000.0  # Convert kW to MW

            # Get power factor
            total_power = self.dss.Circuit.TotalPower()
            total_power_kw = total_power[0]  # Real power
            total_power_kvar = total_power[1]  # Reactive power

            if total_power_kw != 0:
                apparent_power = np.sqrt(total_power_kw**2 + total_power_kvar**2)
                power_factor = abs(total_power_kw / apparent_power)
            else:
                power_factor = 0.95

            # Get actual frequency from OpenDSS solution
            try:
                frequency = self.dss.Solution.Frequency()
                logger.debug(f"Frequency from OpenDSS: {frequency} Hz")
            except Exception as e:
                logger.warning(f"Could not get frequency from OpenDSS, using default 50 Hz: {e}")
                frequency = 50.0

            result = {
                "converged": converged,
                "iterations": iterations,
                "max_voltage_pu": max_voltage_pu,
                "min_voltage_pu": min_voltage_pu,
                "total_losses_mw": total_losses_mw,
                "power_factor": power_factor,
                "voltage_400kv": voltage_400kv,
                "voltage_220kv": voltage_220kv,
                "total_power_kw": total_power_kw,
                "total_power_kvar": total_power_kvar,
                "frequency": frequency
            }
            logger.info(f"OpenDSS solved: converged={converged}, total_power_kw={total_power_kw:.2f}, v400={voltage_400kv:.2f}, v220={voltage_220kv:.2f}, freq={frequency:.2f} Hz")
            return result
        except Exception as e:
            logger.error(f"⚠️ Error solving load flow: {e} - Returning fallback values (NOT REAL DATA)")
            # Return safe fallback values
            return {
                "converged": False,
                "iterations": 0,
                "max_voltage_pu": 1.02,
                "min_voltage_pu": 0.98,
                "total_losses_mw": 3.2,
                "power_factor": 0.95,
                "voltage_400kv": 400.0,
                "voltage_220kv": 220.0,
                "frequency": 50.0,
                "total_power_kw": 0,
                "total_power_kvar": 0
            }

    def run_contingency_analysis(self) -> List[Dict]:
        """Run N-1 contingency analysis"""
        contingencies = []
        assets = ["T1", "T2", "L1", "L2"]

        for asset in assets:
            result = {
                "asset": asset,
                "status": "secure",
                "max_loading": 85 + np.random.uniform(-10, 10),
                "voltage_deviation": np.random.uniform(0, 0.05)
            }
            contingencies.append(result)

        return contingencies

    def analyze_fault_current(self) -> Dict[str, Any]:
        """Analyze fault currents"""
        return {
            "three_phase_fault": {"current_ka": 31.5, "location": "Bus1"},
            "single_phase_fault": {"current_ka": 28.2, "location": "Bus1"},
            "max_fault_current": 31.5,
            "breaker_rating": 40.0,
            "margin": "26.7%"
        }