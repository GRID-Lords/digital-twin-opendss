"""
Anomaly Simulation Module for OpenDSS Digital Twin
Handles various electrical fault and anomaly scenarios
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class AnomalySimulator:
    """Manages anomaly simulations in OpenDSS circuit"""

    def __init__(self, dss_interface):
        """
        Initialize the anomaly simulator

        Args:
            dss_interface: OpenDSS interface object
        """
        self.dss = dss_interface
        self.active_anomalies = {}
        self.original_states = {}

    async def simulate_voltage_sag(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate voltage sag/dip condition

        Parameters:
            severity: Voltage reduction factor (0.5-0.9 p.u.)
            duration: Duration in seconds
            location: Bus location for the sag
        """
        severity = parameters.get('severity', 0.8)
        duration = parameters.get('duration', 5)
        location = parameters.get('location', 'Bus220_1')

        logger.info(f"Simulating voltage sag at {location}: {severity} p.u. for {duration}s")

        try:
            # Store original voltage
            self.dss.Text.Command(f"select bus={location}")
            original_voltage = self.dss.Bus.kVBase

            # Apply voltage sag by adding a fault impedance
            fault_r = (1 - severity) * 100  # Higher impedance = less severe sag
            self.dss.Text.Command(f"New Fault.VoltSag bus1={location} r={fault_r}")

            # Solve the circuit
            self.dss.Solution.Solve()

            # Get results
            voltages = self.dss.Bus.Voltages
            voltage_mag = np.abs(complex(voltages[0], voltages[1])) / 1000  # Convert to kV

            result = {
                "status": "active",
                "type": "voltage_sag",
                "location": location,
                "severity": severity,
                "actual_voltage": voltage_mag,
                "nominal_voltage": original_voltage,
                "timestamp": datetime.now().isoformat()
            }

            # Schedule cleanup
            asyncio.create_task(self._cleanup_after_delay("VoltSag", duration))

            return result

        except Exception as e:
            logger.error(f"Error simulating voltage sag: {e}")
            return {"status": "error", "message": str(e)}

    async def simulate_voltage_surge(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate voltage surge/swell condition

        Parameters:
            severity: Voltage increase factor (1.1-1.3 p.u.)
            duration: Duration in seconds
            location: Bus location for the surge
        """
        severity = parameters.get('severity', 1.15)
        duration = parameters.get('duration', 3)
        location = parameters.get('location', 'Bus400_1')

        logger.info(f"Simulating voltage surge at {location}: {severity} p.u. for {duration}s")

        try:
            # Apply voltage surge by adding capacitor bank
            cap_kvar = (severity - 1) * 10000  # Reactive power to inject
            self.dss.Text.Command(f"New Capacitor.Surge bus1={location} kvar={cap_kvar} kv=400")

            # Solve the circuit
            self.dss.Solution.Solve()

            # Get results
            self.dss.Text.Command(f"select bus={location}")
            voltages = self.dss.Bus.Voltages
            voltage_mag = np.abs(complex(voltages[0], voltages[1])) / 1000

            result = {
                "status": "active",
                "type": "voltage_surge",
                "location": location,
                "severity": severity,
                "actual_voltage": voltage_mag,
                "timestamp": datetime.now().isoformat()
            }

            # Schedule cleanup
            asyncio.create_task(self._cleanup_after_delay("Surge", duration))

            return result

        except Exception as e:
            logger.error(f"Error simulating voltage surge: {e}")
            return {"status": "error", "message": str(e)}

    async def simulate_transformer_overload(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate transformer overload condition

        Parameters:
            load_factor: Overload factor (1.1-2.0)
            transformer: Transformer ID
            duration: Duration in minutes
        """
        load_factor = parameters.get('load_factor', 1.5)
        transformer = parameters.get('transformer', 'TR1')
        duration = parameters.get('duration', 10)

        logger.info(f"Simulating overload on {transformer}: {load_factor}x for {duration} min")

        try:
            # Get transformer rating
            self.dss.Text.Command(f"select transformer.{transformer}")
            kva_rating = self.dss.Transformers.kVA

            # Add extra load
            extra_load = kva_rating * (load_factor - 1)
            self.dss.Text.Command(
                f"New Load.Overload_{transformer} bus1={transformer}_sec "
                f"kW={extra_load * 0.9} kvar={extra_load * 0.436}"  # PF=0.9
            )

            # Solve the circuit
            self.dss.Solution.Solve()

            # Calculate temperature rise (simplified model)
            base_temp = 65  # Base operating temperature
            temp_rise = (load_factor - 1) * 40  # 40°C rise per 100% overload
            estimated_temp = base_temp + temp_rise

            # Get actual loading
            self.dss.Text.Command(f"select transformer.{transformer}")
            actual_kva = self.dss.CktElement.Powers
            loading_pct = (abs(complex(actual_kva[0], actual_kva[1])) / kva_rating) * 100

            result = {
                "status": "active",
                "type": "transformer_overload",
                "transformer": transformer,
                "load_factor": load_factor,
                "loading_percent": loading_pct,
                "estimated_temperature": estimated_temp,
                "duration_minutes": duration,
                "timestamp": datetime.now().isoformat()
            }

            # Schedule cleanup (convert minutes to seconds)
            asyncio.create_task(self._cleanup_after_delay(f"Overload_{transformer}", duration * 60))

            return result

        except Exception as e:
            logger.error(f"Error simulating transformer overload: {e}")
            return {"status": "error", "message": str(e)}

    async def simulate_ground_fault(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate single line to ground fault

        Parameters:
            resistance: Fault resistance in ohms (0-100)
            location: Fault location (line name)
            duration: Duration in cycles
        """
        resistance = parameters.get('resistance', 10)
        location = parameters.get('location', 'Line220_1')
        duration = parameters.get('duration', 5)  # cycles

        logger.info(f"Simulating ground fault on {location}: {resistance} ohms for {duration} cycles")

        try:
            # Apply ground fault
            self.dss.Text.Command(
                f"New Fault.GroundFault bus1={location}.1.0 r={resistance} ontime=0.0 temporary=yes"
            )

            # Solve the circuit
            self.dss.Solution.Solve()

            # Get fault current
            self.dss.Text.Command(f"select fault.GroundFault")
            currents = self.dss.CktElement.Currents
            fault_current = np.abs(complex(currents[0], currents[1]))

            result = {
                "status": "active",
                "type": "ground_fault",
                "location": location,
                "fault_resistance": resistance,
                "fault_current": fault_current,
                "duration_cycles": duration,
                "timestamp": datetime.now().isoformat()
            }

            # Convert cycles to seconds (50 Hz system)
            duration_sec = duration / 50
            asyncio.create_task(self._cleanup_after_delay("GroundFault", duration_sec))

            return result

        except Exception as e:
            logger.error(f"Error simulating ground fault: {e}")
            return {"status": "error", "message": str(e)}

    async def simulate_harmonics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate harmonic distortion

        Parameters:
            thd: Total harmonic distortion percentage
            order: Dominant harmonic order (3, 5, 7, etc.)
            source: Source of harmonics
        """
        thd = parameters.get('thd', 8)
        order = int(parameters.get('order', 5))
        source = parameters.get('source', 'CAP1')

        logger.info(f"Simulating harmonics from {source}: THD={thd}%, Order={order}")

        try:
            # Add harmonic source (simplified using spectrum)
            harmonic_spectrum = [0] * 15  # Up to 15th harmonic
            harmonic_spectrum[order - 1] = thd / 100  # Set dominant harmonic

            spectrum_str = " ".join([str(h) for h in harmonic_spectrum])

            self.dss.Text.Command(
                f"New Load.Harmonic_{source} bus1={source} kW=100 kvar=50 "
                f"spectrum=[{spectrum_str}]"
            )

            # Solve harmonics
            self.dss.Solution.Solve()
            self.dss.Solution.SolveHarmonic()

            result = {
                "status": "active",
                "type": "harmonic_distortion",
                "source": source,
                "thd_percent": thd,
                "dominant_order": order,
                "timestamp": datetime.now().isoformat()
            }

            # Harmonics typically need manual clearing
            self.active_anomalies[f"Harmonic_{source}"] = result

            return result

        except Exception as e:
            logger.error(f"Error simulating harmonics: {e}")
            return {"status": "error", "message": str(e)}

    async def simulate_frequency_deviation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate system frequency deviation

        Parameters:
            deviation: Frequency deviation in Hz
            type: 'under' or 'over' frequency
            duration: Duration in seconds
        """
        deviation = parameters.get('deviation', 0.5)
        freq_type = parameters.get('type', 'under')
        duration = parameters.get('duration', 5)

        base_freq = 50  # Hz
        new_freq = base_freq - deviation if freq_type == 'under' else base_freq + deviation

        logger.info(f"Simulating {freq_type}-frequency: {new_freq} Hz for {duration}s")

        try:
            # Store original frequency
            original_freq = self.dss.Solution.Frequency

            # Set new frequency
            self.dss.Solution.Frequency = new_freq

            # Solve the circuit at new frequency
            self.dss.Solution.Solve()

            # Get system response
            total_power = self.dss.Circuit.TotalPower
            total_kw = -total_power[0]  # Negative because it's generation

            result = {
                "status": "active",
                "type": "frequency_deviation",
                "frequency": new_freq,
                "deviation": deviation,
                "freq_type": freq_type,
                "system_power_kw": total_kw,
                "timestamp": datetime.now().isoformat()
            }

            # Store original frequency for restoration
            self.original_states["frequency"] = original_freq

            # Schedule restoration
            asyncio.create_task(self._restore_frequency_after_delay(duration))

            return result

        except Exception as e:
            logger.error(f"Error simulating frequency deviation: {e}")
            return {"status": "error", "message": str(e)}

    async def _cleanup_after_delay(self, element_name: str, delay_seconds: float):
        """Clean up temporary elements after delay"""
        await asyncio.sleep(delay_seconds)

        try:
            # Remove the temporary element
            if "Fault" in element_name:
                self.dss.Text.Command(f"disable fault.{element_name}")
            elif "Load" in element_name:
                self.dss.Text.Command(f"disable load.{element_name}")
            elif "Capacitor" in element_name:
                self.dss.Text.Command(f"disable capacitor.{element_name}")

            # Re-solve circuit
            self.dss.Solution.Solve()

            # Remove from active anomalies
            if element_name in self.active_anomalies:
                del self.active_anomalies[element_name]

            logger.info(f"Cleaned up anomaly: {element_name}")

        except Exception as e:
            logger.error(f"Error cleaning up {element_name}: {e}")

    async def _restore_frequency_after_delay(self, delay_seconds: float):
        """Restore original frequency after delay"""
        await asyncio.sleep(delay_seconds)

        try:
            if "frequency" in self.original_states:
                self.dss.Solution.Frequency = self.original_states["frequency"]
                self.dss.Solution.Solve()
                del self.original_states["frequency"]
                logger.info("Frequency restored to normal")
        except Exception as e:
            logger.error(f"Error restoring frequency: {e}")

    def stop_anomaly(self, scenario_id: str) -> Dict[str, Any]:
        """Stop a specific anomaly simulation"""
        try:
            if scenario_id == "harmonics":
                # Clean up harmonic sources
                for key in list(self.active_anomalies.keys()):
                    if "Harmonic" in key:
                        self.dss.Text.Command(f"disable load.{key}")
                        del self.active_anomalies[key]

            elif scenario_id == "frequency_deviation":
                # Restore frequency
                if "frequency" in self.original_states:
                    self.dss.Solution.Frequency = self.original_states["frequency"]
                    del self.original_states["frequency"]

            else:
                # Generic cleanup
                for key in list(self.active_anomalies.keys()):
                    if scenario_id in key.lower():
                        self.dss.Text.Command(f"disable {key}")
                        del self.active_anomalies[key]

            # Re-solve circuit
            self.dss.Solution.Solve()

            return {"status": "stopped", "scenario": scenario_id}

        except Exception as e:
            logger.error(f"Error stopping anomaly {scenario_id}: {e}")
            return {"status": "error", "message": str(e)}

    def get_active_anomalies(self) -> Dict[str, Any]:
        """Get list of currently active anomalies"""
        return {
            "active_count": len(self.active_anomalies),
            "anomalies": list(self.active_anomalies.values())
        }