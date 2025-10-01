"""
Comprehensive Asset Models for EHV 400/220 kV Substation Digital Twin
Implements detailed models for all substation equipment as per SIH requirements
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import json

class AssetType(Enum):
    """All asset types in EHV substation"""
    POWER_TRANSFORMER = "power_transformer"
    DISTRIBUTION_TRANSFORMER = "distribution_transformer"
    CIRCUIT_BREAKER = "circuit_breaker"
    ISOLATOR = "isolator"
    CURRENT_TRANSFORMER = "ct"
    CAPACITOR_VOLTAGE_TRANSFORMER = "cvt"
    POTENTIAL_TRANSFORMER = "pt"
    BUSBAR = "busbar"
    SURGE_ARRESTER = "surge_arrester"
    REACTOR = "reactor"
    CAPACITOR_BANK = "capacitor_bank"
    PROTECTION_RELAY = "protection_relay"
    SCADA_RTU = "scada_rtu"
    CONTROL_PANEL = "control_panel"
    BATTERY_BANK = "battery_bank"
    DC_SYSTEM = "dc_system"

class AssetStatus(Enum):
    """Asset operational status"""
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    FAULTY = "faulty"
    STANDBY = "standby"
    TESTING = "testing"
    OFFLINE = "offline"

class ProtectionType(Enum):
    """Protection relay types"""
    DIFFERENTIAL = "differential"
    DISTANCE = "distance"
    OVERCURRENT = "overcurrent"
    EARTH_FAULT = "earth_fault"
    BUSBAR_PROTECTION = "busbar_protection"
    BREAKER_FAILURE = "breaker_failure"

@dataclass
class AssetHealth:
    """Asset health metrics"""
    overall_health: float = 100.0  # 0-100%
    degradation_rate: float = 0.01  # % per day
    failure_probability: float = 0.001
    maintenance_urgency: str = "low"
    estimated_remaining_life_days: int = 3650
    last_maintenance: Optional[datetime] = None
    next_scheduled_maintenance: Optional[datetime] = None

    def calculate_health_score(self, operational_hours: int, fault_count: int) -> float:
        """Calculate comprehensive health score"""
        age_factor = max(0, 100 - (operational_hours / 8760) * 5)  # 5% reduction per year
        fault_factor = max(0, 100 - fault_count * 2)  # 2% reduction per fault
        base_health = (age_factor * 0.7 + fault_factor * 0.3)

        # Apply degradation
        days_since_maintenance = 30
        if self.last_maintenance:
            days_since_maintenance = (datetime.now() - self.last_maintenance).days

        degradation = min(20, days_since_maintenance * self.degradation_rate)
        return max(0, min(100, base_health - degradation))

@dataclass
class ElectricalParameters:
    """Electrical parameters for assets"""
    voltage_rating_kv: float
    current_rating_a: float
    power_rating_mva: Optional[float] = None
    frequency_hz: float = 50.0
    power_factor: float = 0.95
    impedance_ohms: Optional[float] = None
    resistance_ohms: Optional[float] = None
    reactance_ohms: Optional[float] = None
    insulation_resistance_mohms: float = 1000.0

    def calculate_losses(self, current: float) -> Dict[str, float]:
        """Calculate power losses"""
        if self.resistance_ohms:
            copper_losses = 3 * (current ** 2) * self.resistance_ohms / 1000  # kW
        else:
            copper_losses = 0.02 * self.power_rating_mva * 1000 if self.power_rating_mva else 0

        if self.power_rating_mva:
            iron_losses = 0.01 * self.power_rating_mva * 1000  # kW
        else:
            iron_losses = 0

        return {
            "copper_losses_kw": copper_losses,
            "iron_losses_kw": iron_losses,
            "total_losses_kw": copper_losses + iron_losses
        }

@dataclass
class ThermalParameters:
    """Thermal parameters for assets"""
    temperature_celsius: float = 25.0
    max_temperature_celsius: float = 85.0
    hotspot_temperature_celsius: float = 30.0
    ambient_temperature_celsius: float = 25.0
    thermal_time_constant_minutes: float = 30.0
    cooling_type: str = "ONAN"  # Oil Natural Air Natural

    def calculate_thermal_stress(self) -> float:
        """Calculate thermal stress factor"""
        temp_ratio = self.temperature_celsius / self.max_temperature_celsius
        if temp_ratio < 0.7:
            return 0.0
        elif temp_ratio < 0.85:
            return (temp_ratio - 0.7) / 0.15 * 50
        else:
            return 50 + (temp_ratio - 0.85) / 0.15 * 50

@dataclass
class MechanicalParameters:
    """Mechanical parameters for assets"""
    vibration_level_mm_s: float = 0.5
    max_vibration_mm_s: float = 5.0
    noise_level_db: float = 60.0
    max_noise_db: float = 85.0
    operating_cycles: int = 0
    max_operating_cycles: int = 10000
    spring_charge_status: bool = True

    def calculate_mechanical_wear(self) -> float:
        """Calculate mechanical wear factor"""
        cycle_wear = (self.operating_cycles / self.max_operating_cycles) * 50
        vibration_wear = (self.vibration_level_mm_s / self.max_vibration_mm_s) * 30
        noise_wear = max(0, (self.noise_level_db - 60) / (self.max_noise_db - 60)) * 20
        return min(100, cycle_wear + vibration_wear + noise_wear)

class BaseAsset:
    """Base class for all substation assets"""

    def __init__(self, asset_id: str, name: str, asset_type: AssetType,
                 location: str, voltage_level_kv: float):
        self.asset_id = asset_id or str(uuid.uuid4())
        self.name = name
        self.asset_type = asset_type
        self.location = location
        self.voltage_level_kv = voltage_level_kv
        self.status = AssetStatus.OPERATIONAL
        self.commissioned_date = datetime.now() - timedelta(days=np.random.randint(365, 3650))

        # Health and parameters
        self.health = AssetHealth()
        self.electrical = ElectricalParameters(
            voltage_rating_kv=voltage_level_kv,
            current_rating_a=1000.0
        )
        self.thermal = ThermalParameters()
        self.mechanical = MechanicalParameters()

        # Operational data
        self.operational_hours = np.random.randint(1000, 50000)
        self.fault_history: List[Dict] = []
        self.maintenance_history: List[Dict] = []
        self.real_time_data: Dict[str, Any] = {}
        self.alarms: List[Dict] = []

    def update_real_time_data(self, data: Dict[str, Any]):
        """Update real-time measurements"""
        self.real_time_data.update(data)
        self.real_time_data['timestamp'] = datetime.now().isoformat()

        # Check for alarms
        self.check_alarms()

    def check_alarms(self):
        """Check for alarm conditions"""
        # Temperature alarm
        if self.thermal.temperature_celsius > self.thermal.max_temperature_celsius * 0.9:
            self.add_alarm("HIGH_TEMPERATURE", "critical",
                          f"Temperature {self.thermal.temperature_celsius}°C exceeds threshold")

        # Vibration alarm
        if self.mechanical.vibration_level_mm_s > self.mechanical.max_vibration_mm_s * 0.8:
            self.add_alarm("HIGH_VIBRATION", "warning",
                          f"Vibration {self.mechanical.vibration_level_mm_s} mm/s is high")

    def add_alarm(self, alarm_type: str, severity: str, description: str):
        """Add an alarm"""
        alarm = {
            "id": str(uuid.uuid4()),
            "type": alarm_type,
            "severity": severity,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "acknowledged": False
        }
        self.alarms.append(alarm)

    def calculate_reliability(self) -> float:
        """Calculate asset reliability index"""
        age_years = self.operational_hours / 8760
        fault_rate = len(self.fault_history) / max(1, age_years)

        # Reliability decreases with age and faults
        base_reliability = 99.9
        age_factor = max(0, 1 - age_years / 30)  # 30 year expected life
        fault_factor = max(0, 1 - fault_rate / 2)  # 2 faults/year is critical

        return base_reliability * age_factor * fault_factor

    def to_dict(self) -> Dict[str, Any]:
        """Convert asset to dictionary"""
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "type": self.asset_type.value,
            "location": self.location,
            "voltage_level_kv": self.voltage_level_kv,
            "status": self.status.value,
            "health_score": self.health.calculate_health_score(
                self.operational_hours, len(self.fault_history)
            ),
            "reliability": self.calculate_reliability(),
            "electrical": {
                "voltage_rating": self.electrical.voltage_rating_kv,
                "current_rating": self.electrical.current_rating_a,
                "power_factor": self.electrical.power_factor
            },
            "thermal": {
                "temperature": self.thermal.temperature_celsius,
                "max_temperature": self.thermal.max_temperature_celsius,
                "thermal_stress": self.thermal.calculate_thermal_stress()
            },
            "mechanical": {
                "vibration": self.mechanical.vibration_level_mm_s,
                "noise": self.mechanical.noise_level_db,
                "wear": self.mechanical.calculate_mechanical_wear()
            },
            "real_time_data": self.real_time_data,
            "alarms": self.alarms[-5:] if self.alarms else []  # Last 5 alarms
        }

class PowerTransformer(BaseAsset):
    """400/220 kV Power Transformer Model"""

    def __init__(self, asset_id: str, name: str, location: str,
                 power_rating_mva: float = 315, tap_positions: int = 17):
        super().__init__(asset_id, name, AssetType.POWER_TRANSFORMER, location, 400)

        self.power_rating_mva = power_rating_mva
        self.electrical.power_rating_mva = power_rating_mva
        self.voltage_ratio = "400/220"
        self.cooling_type = "OFAF"  # Oil Forced Air Forced
        self.vector_group = "YNyn0"

        # Tap changer
        self.tap_positions = tap_positions
        self.current_tap = 9  # Middle position
        self.tap_step_percent = 1.25

        # Oil parameters
        self.oil_temperature = 65.0
        self.oil_level_percent = 95.0
        self.oil_moisture_ppm = 10
        self.breakdown_voltage_kv = 60

        # Dissolved Gas Analysis (DGA)
        self.dga_data = {
            "hydrogen": 50,  # ppm
            "methane": 30,
            "ethane": 10,
            "ethylene": 5,
            "acetylene": 0,
            "carbon_monoxide": 200,
            "carbon_dioxide": 1500
        }

        # Bushings
        self.hv_bushings = ["R", "Y", "B", "N"]
        self.lv_bushings = ["r", "y", "b", "n"]
        self.bushing_tan_delta = {b: 0.3 for b in self.hv_bushings + self.lv_bushings}

    def change_tap(self, direction: int) -> bool:
        """Change tap position"""
        new_tap = self.current_tap + direction
        if 1 <= new_tap <= self.tap_positions:
            self.current_tap = new_tap
            self.mechanical.operating_cycles += 1
            return True
        return False

    def analyze_dga(self) -> Dict[str, Any]:
        """Analyze dissolved gases for fault detection"""
        total_combustible = sum([
            self.dga_data["hydrogen"],
            self.dga_data["methane"],
            self.dga_data["ethane"],
            self.dga_data["ethylene"],
            self.dga_data["acetylene"],
            self.dga_data["carbon_monoxide"]
        ])

        # Duval Triangle analysis
        condition = "normal"
        if self.dga_data["acetylene"] > 2:
            condition = "arcing"
        elif self.dga_data["ethylene"] > 50:
            condition = "overheating_oil"
        elif self.dga_data["hydrogen"] > 100:
            condition = "partial_discharge"

        return {
            "total_combustible_gas": total_combustible,
            "condition": condition,
            "severity": "normal" if total_combustible < 500 else "warning" if total_combustible < 1000 else "critical"
        }

    def calculate_loading_percent(self, current_load_mva: float) -> float:
        """Calculate transformer loading percentage"""
        return (current_load_mva / self.power_rating_mva) * 100

class CircuitBreaker(BaseAsset):
    """High Voltage Circuit Breaker Model"""

    def __init__(self, asset_id: str, name: str, location: str,
                 voltage_kv: float = 400, breaking_capacity_ka: float = 50):
        super().__init__(asset_id, name, AssetType.CIRCUIT_BREAKER, location, voltage_kv)

        self.breaking_capacity_ka = breaking_capacity_ka
        self.rated_current_a = 4000
        self.breaker_type = "SF6"  # SF6 Gas Insulated
        self.operating_mechanism = "spring_charged"

        # SF6 gas parameters
        self.sf6_pressure_bar = 6.5
        self.sf6_nominal_pressure = 6.5
        self.sf6_alarm_pressure = 6.0
        self.sf6_lockout_pressure = 5.5

        # Contact parameters
        self.contact_resistance_micro_ohm = 50
        self.contact_wear_percent = 10
        self.arcing_time_ms = 40

        # Position and control
        self.position = "closed"  # open/closed
        self.control_voltage_v = 110
        self.trip_coil_1_healthy = True
        self.trip_coil_2_healthy = True
        self.close_coil_healthy = True

        # Operation counters
        self.total_operations = 1250
        self.operations_since_maintenance = 250
        self.sum_interrupted_current_ka = 5000

    def operate(self, command: str) -> Tuple[bool, str]:
        """Operate circuit breaker"""
        if command == "open" and self.position == "closed":
            if self.mechanical.spring_charge_status:
                self.position = "open"
                self.mechanical.operating_cycles += 1
                self.total_operations += 1
                self.operations_since_maintenance += 1
                return True, "Circuit breaker opened successfully"
            return False, "Spring not charged"

        elif command == "close" and self.position == "open":
            if self.close_coil_healthy:
                self.position = "closed"
                self.mechanical.operating_cycles += 1
                self.total_operations += 1
                self.operations_since_maintenance += 1
                return True, "Circuit breaker closed successfully"
            return False, "Close coil faulty"

        return False, f"Invalid operation: {command} from {self.position}"

    def calculate_remaining_life(self) -> Dict[str, float]:
        """Calculate remaining operational life"""
        electrical_life = max(0, 100 - (self.sum_interrupted_current_ka / 100000) * 100)
        mechanical_life = max(0, 100 - (self.total_operations / 10000) * 100)
        contact_life = max(0, 100 - self.contact_wear_percent)

        return {
            "electrical_life_percent": electrical_life,
            "mechanical_life_percent": mechanical_life,
            "contact_life_percent": contact_life,
            "overall_life_percent": min(electrical_life, mechanical_life, contact_life)
        }

class CurrentTransformer(BaseAsset):
    """Current Transformer (CT) Model"""

    def __init__(self, asset_id: str, name: str, location: str,
                 voltage_kv: float = 400, ratio: str = "2000/1"):
        super().__init__(asset_id, name, AssetType.CURRENT_TRANSFORMER, location, voltage_kv)

        self.ct_ratio = ratio
        self.primary_current, self.secondary_current = map(int, ratio.split("/"))
        self.accuracy_class = "0.2S"
        self.burden_va = 30
        self.insulation_class = "Oil-filled"

        # Measurements
        self.primary_current_measured = 0
        self.secondary_current_measured = 0
        self.phase_error_minutes = 5
        self.ratio_error_percent = 0.2

        # Insulation parameters
        self.tan_delta_percent = 0.3
        self.insulation_resistance_mohm = 5000
        self.partial_discharge_pc = 5

    def calculate_burden(self, secondary_current: float) -> float:
        """Calculate CT burden"""
        return (secondary_current ** 2) * 0.1  # Assuming 0.1 ohm burden

    def check_saturation(self, fault_current: float) -> bool:
        """Check if CT will saturate during fault"""
        max_secondary = fault_current / self.primary_current * self.secondary_current
        return max_secondary > 20 * self.secondary_current  # 20x is typical saturation

class CapacitorVoltageTransformer(BaseAsset):
    """Capacitor Voltage Transformer (CVT) Model"""

    def __init__(self, asset_id: str, name: str, location: str, voltage_kv: float = 400):
        super().__init__(asset_id, name, AssetType.CAPACITOR_VOLTAGE_TRANSFORMER, location, voltage_kv)

        self.voltage_ratio = f"{voltage_kv}kV/110V"
        self.rated_burden_va = 100
        self.accuracy_class = "0.2"

        # Capacitor stack
        self.c1_capacitance_pf = 4400
        self.c2_capacitance_pf = 40000
        self.capacitor_tan_delta = 0.05

        # Electromagnetic unit
        self.intermediate_voltage_v = 20000
        self.ferroresonance_damping = True

        # Measurements
        self.primary_voltage_measured = 0
        self.secondary_voltage_measured = 0
        self.frequency_response_ok = True

class Isolator(BaseAsset):
    """Disconnect Switch / Isolator Model"""

    def __init__(self, asset_id: str, name: str, location: str, voltage_kv: float = 400):
        super().__init__(asset_id, name, AssetType.ISOLATOR, location, voltage_kv)

        self.isolator_type = "double_break"
        self.operating_mechanism = "motor"
        self.position = "closed"  # open/closed
        self.earth_switch_position = "open"

        # Interlocking
        self.interlocked_with: List[str] = []
        self.interlock_bypass = False

        # Motor parameters
        self.motor_current_a = 5.0
        self.operation_time_seconds = 10
        self.auxiliary_contacts_ok = True

    def operate(self, command: str, check_interlocks: bool = True) -> Tuple[bool, str]:
        """Operate isolator with interlock checking"""
        if check_interlocks and not self.interlock_bypass:
            # Check if associated breaker is open
            if command == "open" and self.position == "closed":
                # Would check breaker status here
                pass

        if command in ["open", "close"]:
            self.position = command + "d" if command == "close" else command
            self.mechanical.operating_cycles += 1
            return True, f"Isolator {command}d"

        return False, "Invalid command"

class ProtectionRelay(BaseAsset):
    """Digital Protection Relay Model"""

    def __init__(self, asset_id: str, name: str, location: str,
                 protection_type: ProtectionType):
        super().__init__(asset_id, name, AssetType.PROTECTION_RELAY, location, 0)

        self.protection_type = protection_type
        self.relay_model = "SEL-421"
        self.firmware_version = "V3.2.1"

        # Settings
        self.settings = {
            "pickup_current": 1000,
            "time_delay": 0.5,
            "curve_type": "IEC_normal_inverse",
            "zone_1_reach": 80,
            "zone_2_reach": 120
        }

        # Status
        self.in_service = True
        self.test_mode = False
        self.last_operated = None
        self.operation_counter = 0

        # Communication
        self.communication_protocol = "IEC61850"
        self.communication_healthy = True
        self.goose_subscriptions = []

        # Event recording
        self.events: List[Dict] = []
        self.disturbance_records: List[Dict] = []

    def process_measurement(self, measurement: Dict) -> Optional[str]:
        """Process measurement and determine if trip needed"""
        if not self.in_service or self.test_mode:
            return None

        # Simple overcurrent logic
        if self.protection_type == ProtectionType.OVERCURRENT:
            if measurement.get("current", 0) > self.settings["pickup_current"]:
                self.operation_counter += 1
                self.last_operated = datetime.now()
                self.record_event("TRIP", measurement)
                return "TRIP"

        return None

    def record_event(self, event_type: str, data: Dict):
        """Record protection event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
            "settings": self.settings.copy()
        }
        self.events.append(event)

class SubstationAssetManager:
    """Manager class for all substation assets"""

    def __init__(self):
        self.assets: Dict[str, BaseAsset] = {}
        self.asset_groups: Dict[str, List[str]] = {}
        self.initialize_standard_substation()

    def initialize_standard_substation(self):
        """Initialize a standard 400/220 kV substation configuration"""

        # Power Transformers
        for i in range(1, 3):
            transformer = PowerTransformer(
                f"TR{i}",
                f"400/220kV Transformer {i}",
                f"Bay {i}",
                power_rating_mva=315
            )
            self.add_asset(transformer, "transformers")

        # Circuit Breakers - 400kV side
        for i in range(1, 7):
            breaker = CircuitBreaker(
                f"CB_400_{i}",
                f"400kV Breaker {i}",
                f"400kV Bay {i}",
                voltage_kv=400,
                breaking_capacity_ka=50
            )
            self.add_asset(breaker, "breakers_400kv")

        # Circuit Breakers - 220kV side
        for i in range(1, 11):
            breaker = CircuitBreaker(
                f"CB_220_{i}",
                f"220kV Breaker {i}",
                f"220kV Bay {i}",
                voltage_kv=220,
                breaking_capacity_ka=40
            )
            self.add_asset(breaker, "breakers_220kv")

        # Current Transformers
        for voltage in [400, 220]:
            for phase in ["R", "Y", "B"]:
                for bay in range(1, 4):
                    ct = CurrentTransformer(
                        f"CT_{voltage}_{bay}_{phase}",
                        f"{voltage}kV CT Bay{bay} Phase{phase}",
                        f"{voltage}kV Bay {bay}",
                        voltage_kv=voltage,
                        ratio="2000/1" if voltage == 400 else "1000/1"
                    )
                    self.add_asset(ct, f"cts_{voltage}kv")

        # CVTs
        for voltage in [400, 220]:
            for bay in range(1, 4):
                cvt = CapacitorVoltageTransformer(
                    f"CVT_{voltage}_{bay}",
                    f"{voltage}kV CVT Bay{bay}",
                    f"{voltage}kV Bay {bay}",
                    voltage_kv=voltage
                )
                self.add_asset(cvt, f"cvts_{voltage}kv")

        # Isolators
        for voltage in [400, 220]:
            for bay in range(1, 6):
                for position in ["line", "bus"]:
                    isolator = Isolator(
                        f"ISO_{voltage}_{bay}_{position}",
                        f"{voltage}kV Isolator Bay{bay} {position}",
                        f"{voltage}kV Bay {bay}",
                        voltage_kv=voltage
                    )
                    self.add_asset(isolator, f"isolators_{voltage}kv")

        # Protection Relays
        protection_configs = [
            ("transformer_differential", ProtectionType.DIFFERENTIAL, 2),
            ("line_distance", ProtectionType.DISTANCE, 6),
            ("busbar_protection", ProtectionType.BUSBAR_PROTECTION, 2),
            ("breaker_failure", ProtectionType.BREAKER_FAILURE, 4)
        ]

        for config_name, protection_type, count in protection_configs:
            for i in range(1, count + 1):
                relay = ProtectionRelay(
                    f"RELAY_{config_name}_{i}",
                    f"{config_name.replace('_', ' ').title()} {i}",
                    f"Control Room Panel {i}",
                    protection_type
                )
                self.add_asset(relay, "protection_relays")

    def add_asset(self, asset: BaseAsset, group: str = "general"):
        """Add an asset to the manager"""
        self.assets[asset.asset_id] = asset
        if group not in self.asset_groups:
            self.asset_groups[group] = []
        self.asset_groups[group].append(asset.asset_id)

    def get_asset(self, asset_id: str) -> Optional[BaseAsset]:
        """Get asset by ID"""
        return self.assets.get(asset_id)

    def get_assets_by_type(self, asset_type: AssetType) -> List[BaseAsset]:
        """Get all assets of a specific type"""
        return [asset for asset in self.assets.values()
                if asset.asset_type == asset_type]

    def get_assets_by_group(self, group: str) -> List[BaseAsset]:
        """Get all assets in a group"""
        asset_ids = self.asset_groups.get(group, [])
        return [self.assets[aid] for aid in asset_ids if aid in self.assets]

    def get_assets_by_location(self, location: str) -> List[BaseAsset]:
        """Get all assets at a location"""
        return [asset for asset in self.assets.values()
                if location in asset.location]

    def get_critical_assets(self, health_threshold: float = 70) -> List[BaseAsset]:
        """Get assets with health below threshold"""
        critical = []
        for asset in self.assets.values():
            health_score = asset.health.calculate_health_score(
                asset.operational_hours, len(asset.fault_history)
            )
            if health_score < health_threshold:
                critical.append(asset)
        return critical

    def simulate_asset_measurements(self):
        """Simulate real-time measurements for all assets"""
        for asset in self.assets.values():
            if isinstance(asset, PowerTransformer):
                asset.update_real_time_data({
                    "load_mva": 250 + np.random.normal(0, 20),
                    "hv_voltage": 398 + np.random.normal(0, 2),
                    "lv_voltage": 218 + np.random.normal(0, 1),
                    "oil_temp": 65 + np.random.normal(0, 3),
                    "winding_temp": 70 + np.random.normal(0, 3)
                })
                asset.thermal.temperature_celsius = asset.real_time_data["winding_temp"]

            elif isinstance(asset, CircuitBreaker):
                asset.update_real_time_data({
                    "current": 2000 + np.random.normal(0, 100) if asset.position == "closed" else 0,
                    "sf6_pressure": asset.sf6_pressure_bar + np.random.normal(0, 0.1),
                    "spring_charged": True
                })

            elif isinstance(asset, CurrentTransformer):
                primary = 1800 + np.random.normal(0, 100)
                asset.update_real_time_data({
                    "primary_current": primary,
                    "secondary_current": primary / asset.primary_current * asset.secondary_current
                })

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        total_assets = len(self.assets)
        operational = sum(1 for a in self.assets.values()
                         if a.status == AssetStatus.OPERATIONAL)

        critical_assets = self.get_critical_assets()
        total_alarms = sum(len(a.alarms) for a in self.assets.values())

        # Calculate system health
        health_scores = []
        for asset in self.assets.values():
            health_scores.append(asset.health.calculate_health_score(
                asset.operational_hours, len(asset.fault_history)
            ))

        return {
            "total_assets": total_assets,
            "operational_assets": operational,
            "critical_assets": len(critical_assets),
            "system_health": np.mean(health_scores),
            "total_alarms": total_alarms,
            "asset_availability": (operational / total_assets * 100),
            "timestamp": datetime.now().isoformat()
        }

    def export_assets_json(self) -> str:
        """Export all assets as JSON"""
        export_data = {
            "substation": "400/220 kV EHV Substation",
            "export_time": datetime.now().isoformat(),
            "system_status": self.get_system_status(),
            "assets": [asset.to_dict() for asset in self.assets.values()],
            "asset_groups": self.asset_groups
        }
        return json.dumps(export_data, indent=2, default=str)