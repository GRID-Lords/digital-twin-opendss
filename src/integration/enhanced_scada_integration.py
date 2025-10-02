"""
Enhanced SCADA and IoT Integration for EHV Substation Digital Twin
Provides comprehensive data acquisition, processing, and control interfaces
"""

import asyncio
import json
import logging
import sqlite3
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from collections import deque
import struct
import socket

logger = logging.getLogger(__name__)

class ProtocolType(Enum):
    """Communication protocols supported"""
    MODBUS_TCP = "modbus_tcp"
    IEC_61850 = "iec_61850"
    DNP3 = "dnp3"
    IEC_60870_5_104 = "iec_104"
    MQTT = "mqtt"
    OPCUA = "opcua"

class DataQuality(Enum):
    """IEC 61850 data quality flags"""
    GOOD = 0
    INVALID = 1
    QUESTIONABLE = 2
    OVERFLOW = 3
    OUT_OF_RANGE = 4
    BAD_REFERENCE = 5
    OSCILLATORY = 6
    FAILURE = 7
    OLD_DATA = 8
    INCONSISTENT = 9
    INACCURATE = 10

@dataclass
class SCADAPoint:
    """SCADA data point definition"""
    tag_name: str
    description: str
    unit: str
    data_type: str  # float, int, bool, string
    protocol: ProtocolType
    address: str
    scaling_factor: float = 1.0
    offset: float = 0.0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    deadband: float = 0.0
    scan_rate_ms: int = 1000
    alarm_enabled: bool = True
    alarm_high: Optional[float] = None
    alarm_low: Optional[float] = None
    alarm_high_high: Optional[float] = None
    alarm_low_low: Optional[float] = None
    current_value: Any = None
    quality: DataQuality = DataQuality.GOOD
    timestamp: Optional[datetime] = None
    trend_buffer: deque = field(default_factory=lambda: deque(maxlen=3600))

    def update_value(self, raw_value: Any) -> Any:
        """Process and update point value"""
        # Apply scaling
        if self.data_type in ["float", "int"]:
            value = raw_value * self.scaling_factor + self.offset

            # Check limits
            if self.min_value is not None and value < self.min_value:
                self.quality = DataQuality.OUT_OF_RANGE
            elif self.max_value is not None and value > self.max_value:
                self.quality = DataQuality.OUT_OF_RANGE
            else:
                self.quality = DataQuality.GOOD

            # Check deadband
            if self.current_value is not None:
                if abs(value - self.current_value) < self.deadband:
                    return self.current_value
        else:
            value = raw_value
            self.quality = DataQuality.GOOD

        self.current_value = value
        self.timestamp = datetime.now()
        self.trend_buffer.append((self.timestamp, value))
        return value

    def check_alarms(self) -> List[Dict]:
        """Check for alarm conditions"""
        alarms = []
        if not self.alarm_enabled or self.data_type not in ["float", "int"]:
            return alarms

        value = self.current_value
        if value is None:
            return alarms

        if self.alarm_high_high and value >= self.alarm_high_high:
            alarms.append({
                "type": "HIGH_HIGH",
                "tag": self.tag_name,
                "value": value,
                "limit": self.alarm_high_high,
                "priority": "CRITICAL"
            })
        elif self.alarm_high and value >= self.alarm_high:
            alarms.append({
                "type": "HIGH",
                "tag": self.tag_name,
                "value": value,
                "limit": self.alarm_high,
                "priority": "WARNING"
            })
        elif self.alarm_low_low and value <= self.alarm_low_low:
            alarms.append({
                "type": "LOW_LOW",
                "tag": self.tag_name,
                "value": value,
                "limit": self.alarm_low_low,
                "priority": "CRITICAL"
            })
        elif self.alarm_low and value <= self.alarm_low:
            alarms.append({
                "type": "LOW",
                "tag": self.tag_name,
                "value": value,
                "limit": self.alarm_low,
                "priority": "WARNING"
            })

        return alarms

class ModbusClient:
    """Modbus TCP client for data acquisition"""

    def __init__(self, host: str, port: int = 502):
        self.host = host
        self.port = port
        self.socket = None
        self.transaction_id = 0
        self.connected = False

    def connect(self) -> bool:
        """Connect to Modbus TCP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"Connected to Modbus server {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Modbus connection failed: {e}")
            return False

    def read_holding_registers(self, address: int, count: int) -> List[int]:
        """Read holding registers"""
        if not self.connected:
            return []

        try:
            # Build Modbus request
            self.transaction_id += 1
            request = struct.pack('>HHHBBHH',
                                self.transaction_id,  # Transaction ID
                                0,  # Protocol ID
                                6,  # Length
                                1,  # Unit ID
                                3,  # Function code (read holding registers)
                                address,  # Starting address
                                count)  # Quantity

            self.socket.send(request)

            # Receive response
            response = self.socket.recv(1024)
            if len(response) > 9:
                # Parse response
                byte_count = response[8]
                values = []
                for i in range(0, byte_count, 2):
                    value = struct.unpack('>H', response[9+i:11+i])[0]
                    values.append(value)
                return values
        except Exception as e:
            logger.error(f"Modbus read error: {e}")
            self.connected = False

        return []

    def write_single_register(self, address: int, value: int) -> bool:
        """Write single register"""
        if not self.connected:
            return False

        try:
            self.transaction_id += 1
            request = struct.pack('>HHHBBHH',
                                self.transaction_id,
                                0,
                                6,
                                1,
                                6,  # Function code (write single register)
                                address,
                                value)

            self.socket.send(request)
            response = self.socket.recv(1024)
            return len(response) > 0
        except Exception as e:
            logger.error(f"Modbus write error: {e}")
            return False

    def disconnect(self):
        """Disconnect from Modbus server"""
        if self.socket:
            self.socket.close()
            self.connected = False

class IEC61850Client:
    """IEC 61850 client for substation automation"""

    def __init__(self, server_address: str):
        self.server_address = server_address
        self.connected = False
        self.logical_devices = {}
        self.goose_subscriptions = []
        self.sampled_values = {}

    def connect(self) -> bool:
        """Connect to IEC 61850 server"""
        # Simplified IEC 61850 connection
        try:
            # In real implementation, would use libiec61850
            self.connected = True
            self._discover_data_model()
            logger.info(f"Connected to IEC 61850 server: {self.server_address}")
            return True
        except Exception as e:
            logger.error(f"IEC 61850 connection failed: {e}")
            return False

    def _discover_data_model(self):
        """Discover IED data model"""
        # Simulate discovering logical devices and nodes
        self.logical_devices = {
            "CTRL": {
                "XCBR1": {  # Circuit breaker
                    "Pos": {"stVal": False, "quality": "good"},
                    "OpCnt": {"stVal": 1250}
                },
                "XSWI1": {  # Isolator
                    "Pos": {"stVal": True, "quality": "good"}
                }
            },
            "MEAS": {
                "MMXU1": {  # Measurement unit
                    "PhV": {"phsA": 230000, "phsB": 230500, "phsC": 229800},
                    "A": {"phsA": 850, "phsB": 845, "phsC": 855},
                    "W": {"phsA": 85000, "phsB": 84500, "phsC": 85500}
                }
            },
            "PROT": {
                "PDIF1": {  # Differential protection
                    "Op": {"general": False},
                    "Str": {"general": False}
                }
            }
        }

    def read_data_object(self, path: str) -> Any:
        """Read data object value"""
        # Parse path like "CTRL/XCBR1.Pos.stVal"
        parts = path.replace(".", "/").split("/")
        value = self.logical_devices
        for part in parts:
            if part in value:
                value = value[part]
            else:
                return None
        return value

    def write_data_object(self, path: str, value: Any) -> bool:
        """Write data object value"""
        # Implement control operations
        logger.info(f"IEC 61850 write: {path} = {value}")
        return True

    def subscribe_goose(self, goose_id: str, callback: Callable):
        """Subscribe to GOOSE messages"""
        self.goose_subscriptions.append({
            "id": goose_id,
            "callback": callback
        })

class HistorianDatabase:
    """Time-series historian for SCADA data"""

    def __init__(self, db_path: str = "scada_historian.db"):
        self.db_path = db_path
        self.conn = None
        self.init_database()

    def init_database(self):
        """Initialize historian database"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()

        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT NOT NULL,
                value REAL,
                quality INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_tag_time (tag_name, timestamp)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                source TEXT,
                description TEXT,
                severity TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT,
                alarm_type TEXT,
                value REAL,
                limit_value REAL,
                priority TEXT,
                acknowledged BOOLEAN DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ack_timestamp DATETIME,
                ack_user TEXT
            )
        """)

        self.conn.commit()

    def store_measurement(self, tag_name: str, value: float,
                         quality: int, timestamp: datetime):
        """Store measurement in historian"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO measurements (tag_name, value, quality, timestamp)
            VALUES (?, ?, ?, ?)
        """, (tag_name, value, quality, timestamp))
        self.conn.commit()

    def store_event(self, event_type: str, source: str,
                   description: str, severity: str):
        """Store event in historian"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO events (event_type, source, description, severity)
            VALUES (?, ?, ?, ?)
        """, (event_type, source, description, severity))
        self.conn.commit()

    def store_alarm(self, alarm_data: Dict):
        """Store alarm in historian"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO alarms (tag_name, alarm_type, value, limit_value, priority)
            VALUES (?, ?, ?, ?, ?)
        """, (alarm_data["tag"], alarm_data["type"], alarm_data["value"],
              alarm_data["limit"], alarm_data["priority"]))
        self.conn.commit()

    def get_trend_data(self, tag_name: str, start_time: datetime,
                      end_time: datetime) -> pd.DataFrame:
        """Retrieve trend data"""
        query = """
            SELECT timestamp, value, quality
            FROM measurements
            WHERE tag_name = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        """
        return pd.read_sql_query(query, self.conn,
                                params=(tag_name, start_time, end_time))

    def get_statistics(self, tag_name: str, period_hours: int = 24) -> Dict:
        """Calculate statistics for a tag"""
        start_time = datetime.now() - timedelta(hours=period_hours)
        df = self.get_trend_data(tag_name, start_time, datetime.now())

        if df.empty:
            return {}

        return {
            "min": float(df["value"].min()),
            "max": float(df["value"].max()),
            "mean": float(df["value"].mean()),
            "std": float(df["value"].std()),
            "count": len(df)
        }

class IoTDeviceManager:
    """Manager for IoT sensors and devices"""

    def __init__(self):
        self.devices: Dict[str, Dict] = {}
        self.mqtt_client = None
        self.websocket_connections = []

    def register_device(self, device_id: str, device_type: str,
                       protocol: str, config: Dict):
        """Register an IoT device"""
        self.devices[device_id] = {
            "type": device_type,
            "protocol": protocol,
            "config": config,
            "status": "offline",
            "last_seen": None,
            "data": {}
        }

    def process_iot_data(self, device_id: str, data: Dict):
        """Process incoming IoT data"""
        if device_id in self.devices:
            device = self.devices[device_id]
            device["data"].update(data)
            device["last_seen"] = datetime.now()
            device["status"] = "online"

            # Process based on device type
            if device["type"] == "temperature_sensor":
                self._process_temperature(device_id, data)
            elif device["type"] == "vibration_sensor":
                self._process_vibration(device_id, data)
            elif device["type"] == "gas_sensor":
                self._process_gas_sensor(device_id, data)

    def _process_temperature(self, device_id: str, data: Dict):
        """Process temperature sensor data"""
        temp = data.get("temperature")
        if temp and temp > 80:
            logger.warning(f"High temperature alert: {device_id} = {temp}°C")

    def _process_vibration(self, device_id: str, data: Dict):
        """Process vibration sensor data"""
        vibration = data.get("vibration_mm_s")
        if vibration and vibration > 5.0:
            logger.warning(f"High vibration alert: {device_id} = {vibration} mm/s")

    def _process_gas_sensor(self, device_id: str, data: Dict):
        """Process gas sensor data"""
        sf6_ppm = data.get("sf6_concentration")
        if sf6_ppm and sf6_ppm > 1000:
            logger.critical(f"SF6 leak detected: {device_id} = {sf6_ppm} ppm")

class EnhancedSCADASystem:
    """Main enhanced SCADA system integrating all components"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.points: Dict[str, SCADAPoint] = {}
        self.protocols: Dict[ProtocolType, Any] = {}
        self.historian = HistorianDatabase(config.get("historian_db", "scada.db"))
        self.iot_manager = IoTDeviceManager()

        self.scan_tasks = {}
        self.alarm_queue = queue.Queue()
        self.event_queue = queue.Queue()
        self.running = False

        self._initialize_protocols()
        self._configure_points()

    def _initialize_protocols(self):
        """Initialize communication protocols"""
        # Modbus TCP
        if "modbus" in self.config:
            modbus_config = self.config["modbus"]
            self.protocols[ProtocolType.MODBUS_TCP] = ModbusClient(
                modbus_config["host"],
                modbus_config.get("port", 502)
            )

        # IEC 61850
        if "iec61850" in self.config:
            iec_config = self.config["iec61850"]
            self.protocols[ProtocolType.IEC_61850] = IEC61850Client(
                iec_config["server"]
            )

    def _configure_points(self):
        """Configure SCADA points"""
        # Configure standard substation points

        # Transformer points
        transformer_points = [
            ("TR1_LOAD_MVA", "Transformer 1 Load", "MVA", "float", ProtocolType.MODBUS_TCP, "400001"),
            ("TR1_OIL_TEMP", "Transformer 1 Oil Temperature", "°C", "float", ProtocolType.MODBUS_TCP, "400002"),
            ("TR1_WINDING_TEMP", "Transformer 1 Winding Temperature", "°C", "float", ProtocolType.MODBUS_TCP, "400003"),
            ("TR1_TAP_POSITION", "Transformer 1 Tap Position", "", "int", ProtocolType.MODBUS_TCP, "400004"),
        ]

        for tag, desc, unit, dtype, protocol, address in transformer_points:
            point = SCADAPoint(
                tag_name=tag,
                description=desc,
                unit=unit,
                data_type=dtype,
                protocol=protocol,
                address=address,
                scan_rate_ms=1000,
                alarm_high=280 if "LOAD" in tag else 85 if "TEMP" in tag else None,
                alarm_high_high=300 if "LOAD" in tag else 95 if "TEMP" in tag else None
            )
            self.points[tag] = point

        # Breaker points
        breaker_points = [
            ("CB1_POSITION", "Circuit Breaker 1 Position", "", "bool", ProtocolType.IEC_61850, "CTRL/XCBR1.Pos.stVal"),
            ("CB1_CURRENT", "Circuit Breaker 1 Current", "A", "float", ProtocolType.IEC_61850, "MEAS/MMXU1.A.phsA"),
            ("CB1_OPERATIONS", "Circuit Breaker 1 Operations", "", "int", ProtocolType.IEC_61850, "CTRL/XCBR1.OpCnt.stVal"),
        ]

        for tag, desc, unit, dtype, protocol, address in breaker_points:
            point = SCADAPoint(
                tag_name=tag,
                description=desc,
                unit=unit,
                data_type=dtype,
                protocol=protocol,
                address=address,
                scan_rate_ms=500 if "POSITION" in tag else 1000
            )
            self.points[tag] = point

    async def start(self):
        """Start SCADA system"""
        self.running = True
        logger.info("Starting Enhanced SCADA System")

        # Connect protocols
        for protocol_type, client in self.protocols.items():
            if hasattr(client, "connect"):
                client.connect()

        # Start scanning tasks
        for tag, point in self.points.items():
            scan_rate = point.scan_rate_ms / 1000.0
            task = asyncio.create_task(self._scan_point(tag, scan_rate))
            self.scan_tasks[tag] = task

        # Start alarm processor
        asyncio.create_task(self._process_alarms())

        # Start event processor
        asyncio.create_task(self._process_events())

        logger.info("SCADA System started successfully")

    async def stop(self):
        """Stop SCADA system"""
        self.running = False

        # Cancel scan tasks
        for task in self.scan_tasks.values():
            task.cancel()

        # Disconnect protocols
        for client in self.protocols.values():
            if hasattr(client, "disconnect"):
                client.disconnect()

        logger.info("SCADA System stopped")

    async def _scan_point(self, tag: str, scan_rate: float):
        """Scan a SCADA point"""
        point = self.points[tag]

        while self.running:
            try:
                # Read value based on protocol
                raw_value = await self._read_point(point)

                if raw_value is not None:
                    # Update point value
                    value = point.update_value(raw_value)

                    # Store in historian
                    self.historian.store_measurement(
                        tag, value, point.quality.value, datetime.now()
                    )

                    # Check alarms
                    alarms = point.check_alarms()
                    for alarm in alarms:
                        self.alarm_queue.put(alarm)

                await asyncio.sleep(scan_rate)

            except Exception as e:
                logger.error(f"Error scanning {tag}: {e}")
                point.quality = DataQuality.FAILURE
                await asyncio.sleep(scan_rate * 2)

    async def _read_point(self, point: SCADAPoint) -> Any:
        """Read point value from protocol"""
        protocol = self.protocols.get(point.protocol)

        if not protocol:
            return None

        if point.protocol == ProtocolType.MODBUS_TCP:
            # Read Modbus register
            address = int(point.address) - 400001  # Convert to 0-based
            values = protocol.read_holding_registers(address, 1)
            return values[0] if values else None

        elif point.protocol == ProtocolType.IEC_61850:
            # Read IEC 61850 data object
            return protocol.read_data_object(point.address)

        return None

    async def _process_alarms(self):
        """Process alarm queue"""
        while self.running:
            try:
                if not self.alarm_queue.empty():
                    alarm = self.alarm_queue.get()
                    logger.warning(f"ALARM: {alarm}")
                    self.historian.store_alarm(alarm)

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Alarm processing error: {e}")

    async def _process_events(self):
        """Process event queue"""
        while self.running:
            try:
                if not self.event_queue.empty():
                    event = self.event_queue.get()
                    logger.info(f"EVENT: {event}")
                    self.historian.store_event(
                        event["type"],
                        event["source"],
                        event["description"],
                        event["severity"]
                    )

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Event processing error: {e}")

    def write_point(self, tag: str, value: Any) -> bool:
        """Write value to a point"""
        if tag not in self.points:
            return False

        point = self.points[tag]
        protocol = self.protocols.get(point.protocol)

        if not protocol:
            return False

        # Log control action
        self.event_queue.put({
            "type": "CONTROL",
            "source": "SCADA",
            "description": f"Write {tag} = {value}",
            "severity": "INFO"
        })

        if point.protocol == ProtocolType.MODBUS_TCP:
            address = int(point.address) - 400001
            return protocol.write_single_register(address, int(value))

        elif point.protocol == ProtocolType.IEC_61850:
            return protocol.write_data_object(point.address, value)

        return False

    def get_current_values(self) -> Dict[str, Any]:
        """Get current values of all points"""
        values = {}
        for tag, point in self.points.items():
            values[tag] = {
                "value": point.current_value,
                "quality": point.quality.name,
                "timestamp": point.timestamp.isoformat() if point.timestamp else None,
                "unit": point.unit
            }
        return values

    def get_alarms(self, acknowledged: bool = False) -> List[Dict]:
        """Get active alarms"""
        cursor = self.historian.conn.cursor()
        query = "SELECT * FROM alarms WHERE acknowledged = ? ORDER BY timestamp DESC LIMIT 100"
        cursor.execute(query, (1 if acknowledged else 0,))

        columns = [col[0] for col in cursor.description]
        alarms = []
        for row in cursor.fetchall():
            alarms.append(dict(zip(columns, row)))

        return alarms

    def acknowledge_alarm(self, alarm_id: int, user: str) -> bool:
        """Acknowledge an alarm"""
        cursor = self.historian.conn.cursor()
        cursor.execute("""
            UPDATE alarms
            SET acknowledged = 1, ack_timestamp = ?, ack_user = ?
            WHERE id = ?
        """, (datetime.now(), user, alarm_id))
        self.historian.conn.commit()
        return cursor.rowcount > 0

    def get_system_status(self) -> Dict[str, Any]:
        """Get SCADA system status"""
        total_points = len(self.points)
        good_quality = sum(1 for p in self.points.values()
                          if p.quality == DataQuality.GOOD)
        active_alarms = len(self.get_alarms(acknowledged=False))

        protocol_status = {}
        for ptype, protocol in self.protocols.items():
            if hasattr(protocol, "connected"):
                protocol_status[ptype.value] = protocol.connected
            else:
                protocol_status[ptype.value] = True

        return {
            "running": self.running,
            "total_points": total_points,
            "good_quality_points": good_quality,
            "data_quality_percent": (good_quality / total_points * 100) if total_points > 0 else 0,
            "active_alarms": active_alarms,
            "protocol_status": protocol_status,
            "timestamp": datetime.now().isoformat()
        }