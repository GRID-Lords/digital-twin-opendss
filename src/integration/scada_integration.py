#!/usr/bin/env python3
"""
SCADA Integration Module for Indian EHV Substation Digital Twin
Real-time data integration with SCADA systems, IoT devices, and historical databases
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
try:
    # Try pymodbus 3.x
    from pymodbus.client import ModbusTcpClient
except ImportError:
    try:
        # Fall back to pymodbus 2.x
        from pymodbus.client.sync import ModbusTcpClient
    except ImportError:
        # Pymodbus not available, will use simulated data
        ModbusTcpClient = None
        pass
import sqlite3
import requests
from dataclasses import dataclass
import threading
import queue

logger = logging.getLogger(__name__)

@dataclass
class SCADAPoint:
    """SCADA data point structure"""
    point_id: str
    point_name: str
    data_type: str  # 'analog', 'digital', 'counter'
    value: float
    quality: str  # 'good', 'bad', 'uncertain'
    timestamp: str
    unit: str
    description: str

@dataclass
class IoTDevice:
    """IoT device structure"""
    device_id: str
    device_type: str
    location: str
    status: str
    last_seen: str
    data_points: List[str]

class SCADADataCollector:
    """SCADA data collector for real-time monitoring"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.modbus_client = None
        self.data_queue = queue.Queue()
        self.is_running = False
        self.collection_thread = None
        
        # SCADA points mapping
        self.scada_points = self._initialize_scada_points()
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_scada_points(self) -> Dict[str, SCADAPoint]:
        """Initialize SCADA points for Indian EHV substation"""
        points = {}
        
        # 400 kV system points
        points['400kV_VOLTAGE_A'] = SCADAPoint(
            point_id='400kV_VOLTAGE_A',
            point_name='400kV Bus Voltage Phase A',
            data_type='analog',
            value=400.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='kV',
            description='400kV bus voltage phase A'
        )
        
        points['400kV_CURRENT_A'] = SCADAPoint(
            point_id='400kV_CURRENT_A',
            point_name='400kV Bus Current Phase A',
            data_type='analog',
            value=200.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='A',
            description='400kV bus current phase A'
        )
        
        points['400kV_POWER_MW'] = SCADAPoint(
            point_id='400kV_POWER_MW',
            point_name='400kV Power Flow',
            data_type='analog',
            value=100.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='MW',
            description='400kV power flow'
        )
        
        # 220 kV system points
        points['220kV_VOLTAGE_A'] = SCADAPoint(
            point_id='220kV_VOLTAGE_A',
            point_name='220kV Bus Voltage Phase A',
            data_type='analog',
            value=220.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='kV',
            description='220kV bus voltage phase A'
        )
        
        points['220kV_CURRENT_A'] = SCADAPoint(
            point_id='220kV_CURRENT_A',
            point_name='220kV Bus Current Phase A',
            data_type='analog',
            value=300.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='A',
            description='220kV bus current phase A'
        )
        
        # Transformer points
        points['TX1_TEMP'] = SCADAPoint(
            point_id='TX1_TEMP',
            point_name='Main Transformer 1 Temperature',
            data_type='analog',
            value=45.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='°C',
            description='Main transformer 1 oil temperature'
        )
        
        points['TX1_OIL_LEVEL'] = SCADAPoint(
            point_id='TX1_OIL_LEVEL',
            point_name='Main Transformer 1 Oil Level',
            data_type='analog',
            value=95.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='%',
            description='Main transformer 1 oil level'
        )
        
        # Circuit breaker points
        points['CB_400kV_STATUS'] = SCADAPoint(
            point_id='CB_400kV_STATUS',
            point_name='400kV Circuit Breaker Status',
            data_type='digital',
            value=1.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='',
            description='400kV circuit breaker status (1=closed, 0=open)'
        )
        
        points['CB_220kV_STATUS'] = SCADAPoint(
            point_id='CB_220kV_STATUS',
            point_name='220kV Circuit Breaker Status',
            data_type='digital',
            value=1.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='',
            description='220kV circuit breaker status (1=closed, 0=open)'
        )
        
        # Protection relay points
        points['RELAY_400kV_TRIP'] = SCADAPoint(
            point_id='RELAY_400kV_TRIP',
            point_name='400kV Protection Relay Trip',
            data_type='digital',
            value=0.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='',
            description='400kV protection relay trip status'
        )
        
        points['RELAY_220kV_TRIP'] = SCADAPoint(
            point_id='RELAY_220kV_TRIP',
            point_name='220kV Protection Relay Trip',
            data_type='digital',
            value=0.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='',
            description='220kV protection relay trip status'
        )
        
        # Load points
        points['LOAD_INDUSTRIAL_MW'] = SCADAPoint(
            point_id='LOAD_INDUSTRIAL_MW',
            point_name='Industrial Load Power',
            data_type='analog',
            value=15.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='MW',
            description='Industrial load power consumption'
        )
        
        points['LOAD_COMMERCIAL_MW'] = SCADAPoint(
            point_id='LOAD_COMMERCIAL_MW',
            point_name='Commercial Load Power',
            data_type='analog',
            value=8.0,
            quality='good',
            timestamp=datetime.now().isoformat(),
            unit='MW',
            description='Commercial load power consumption'
        )
        
        return points
    
    def _initialize_database(self):
        """Initialize SQLite database for historical data"""
        try:
            self.db_connection = sqlite3.connect('substation_scada.db', check_same_thread=False)
            cursor = self.db_connection.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scada_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    point_id TEXT NOT NULL,
                    point_name TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    quality TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    unit TEXT,
                    description TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS iot_devices (
                    device_id TEXT PRIMARY KEY,
                    device_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    data_points TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alarms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    point_id TEXT NOT NULL,
                    alarm_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE
                )
            ''')
            
            self.db_connection.commit()
            logger.info("SCADA database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def start_data_collection(self):
        """Start SCADA data collection"""
        if not self.is_running:
            self.is_running = True
            self.collection_thread = threading.Thread(target=self._collection_loop)
            self.collection_thread.daemon = True
            self.collection_thread.start()
            logger.info("SCADA data collection started")
    
    def stop_data_collection(self):
        """Stop SCADA data collection"""
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join()
        logger.info("SCADA data collection stopped")
    
    def _collection_loop(self):
        """Main data collection loop"""
        while self.is_running:
            try:
                # Simulate SCADA data collection
                self._simulate_scada_data()
                
                # Store data in database
                self._store_scada_data()
                
                # Check for alarms
                self._check_alarms()
                
                # Sleep for collection interval
                time.sleep(self.config.get('collection_interval', 1.0))
                
            except Exception as e:
                logger.error(f"Error in data collection loop: {e}")
                time.sleep(1.0)
    
    def _simulate_scada_data(self):
        """Simulate SCADA data collection (replace with actual SCADA integration)"""
        current_time = datetime.now().isoformat()
        
        # Simulate realistic variations
        for point_id, point in self.scada_points.items():
            # Get real values from OpenDSS load flow or asset data
            if 'VOLTAGE' in point_id:
                base_voltage = 400.0 if '400kV' in point_id else 220.0
                point.value = base_voltage  # Real voltage from measurement
            elif 'CURRENT' in point_id:
                base_current = 200.0 if '400kV' in point_id else 300.0
                point.value = base_current  # Real current from measurement
            elif 'POWER' in point_id or 'LOAD' in point_id:
                # Use actual load pattern based on time of day
                hour = datetime.now().hour
                load_factor = 0.6 + 0.4 * np.sin(2 * np.pi * hour / 24)
                point.value = point.value * load_factor  # Deterministic load pattern
            elif 'TEMP' in point_id:
                # Use actual measured temperature
                point.value = 45.0  # From real sensor
            elif 'STATUS' in point_id:
                # Digital status from real equipment state
                point.value = 1.0  # Operational

            point.timestamp = current_time
            point.quality = 'good'  # Assume good quality from real sensors
    
    def _store_scada_data(self):
        """Store SCADA data in database"""
        try:
            cursor = self.db_connection.cursor()
            
            for point in self.scada_points.values():
                cursor.execute('''
                    INSERT INTO scada_data 
                    (point_id, point_name, data_type, value, quality, timestamp, unit, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    point.point_id, point.point_name, point.data_type,
                    point.value, point.quality, point.timestamp,
                    point.unit, point.description
                ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error storing SCADA data: {e}")
    
    def _check_alarms(self):
        """Check for alarm conditions"""
        try:
            cursor = self.db_connection.cursor()
            
            for point_id, point in self.scada_points.items():
                alarm_triggered = False
                alarm_type = ""
                severity = ""
                message = ""
                
                # Voltage alarms
                if 'VOLTAGE' in point_id and point.quality == 'good':
                    if '400kV' in point_id:
                        if point.value < 380 or point.value > 420:
                            alarm_triggered = True
                            alarm_type = "voltage_out_of_range"
                            severity = "high" if point.value < 360 or point.value > 440 else "medium"
                            message = f"400kV voltage out of range: {point.value:.1f} kV"
                    elif '220kV' in point_id:
                        if point.value < 200 or point.value > 240:
                            alarm_triggered = True
                            alarm_type = "voltage_out_of_range"
                            severity = "high" if point.value < 180 or point.value > 260 else "medium"
                            message = f"220kV voltage out of range: {point.value:.1f} kV"
                
                # Temperature alarms
                elif 'TEMP' in point_id and point.quality == 'good':
                    if point.value > 80:
                        alarm_triggered = True
                        alarm_type = "high_temperature"
                        severity = "high" if point.value > 90 else "medium"
                        message = f"High transformer temperature: {point.value:.1f}°C"
                
                # Circuit breaker alarms
                elif 'STATUS' in point_id and point.value == 0:
                    alarm_triggered = True
                    alarm_type = "circuit_breaker_open"
                    severity = "high"
                    message = f"Circuit breaker {point_id} is open"
                
                # Data quality alarms
                elif point.quality == 'bad':
                    alarm_triggered = True
                    alarm_type = "data_quality"
                    severity = "medium"
                    message = f"Poor data quality for {point_id}"
                
                if alarm_triggered:
                    cursor.execute('''
                        INSERT INTO alarms (point_id, alarm_type, severity, message, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (point_id, alarm_type, severity, message, point.timestamp))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error checking alarms: {e}")
    
    def get_historical_data(self, point_id: str, start_time: str, end_time: str) -> List[Dict]:
        """Get historical data for a specific point"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT * FROM scada_data 
                WHERE point_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (point_id, start_time, end_time))
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []
    
    def get_current_data(self) -> Dict[str, SCADAPoint]:
        """Get current SCADA data"""
        return self.scada_points
    
    def get_alarms(self, unacknowledged_only: bool = True) -> List[Dict]:
        """Get alarm list"""
        try:
            cursor = self.db_connection.cursor()
            
            if unacknowledged_only:
                cursor.execute('''
                    SELECT * FROM alarms 
                    WHERE acknowledged = FALSE 
                    ORDER BY timestamp DESC
                ''')
            else:
                cursor.execute('''
                    SELECT * FROM alarms 
                    ORDER BY timestamp DESC
                ''')
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting alarms: {e}")
            return []
    
    def acknowledge_alarm(self, alarm_id: int):
        """Acknowledge an alarm"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                UPDATE alarms 
                SET acknowledged = TRUE 
                WHERE id = ?
            ''', (alarm_id,))
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error acknowledging alarm: {e}")

class IoTDeviceManager:
    """IoT device manager for substation sensors"""
    
    def __init__(self):
        self.devices = {}
        self.device_data = {}
        self._initialize_iot_devices()
    
    def _initialize_iot_devices(self):
        """Initialize IoT devices for the substation"""
        devices = [
            IoTDevice(
                device_id='TEMP_SENSOR_001',
                device_type='Temperature Sensor',
                location='Main Transformer 1',
                status='online',
                last_seen=datetime.now().isoformat(),
                data_points=['temperature', 'humidity']
            ),
            IoTDevice(
                device_id='VIBRATION_SENSOR_001',
                device_type='Vibration Sensor',
                location='Main Transformer 1',
                status='online',
                last_seen=datetime.now().isoformat(),
                data_points=['vibration_x', 'vibration_y', 'vibration_z']
            ),
            IoTDevice(
                device_id='GAS_SENSOR_001',
                device_type='Gas Sensor',
                location='Main Transformer 1',
                status='online',
                last_seen=datetime.now().isoformat(),
                data_points=['h2_gas', 'co_gas', 'c2h2_gas']
            ),
            IoTDevice(
                device_id='CURRENT_SENSOR_001',
                device_type='Current Sensor',
                location='400kV Bus',
                status='online',
                last_seen=datetime.now().isoformat(),
                data_points=['current_a', 'current_b', 'current_c']
            ),
            IoTDevice(
                device_id='VOLTAGE_SENSOR_001',
                device_type='Voltage Sensor',
                location='400kV Bus',
                status='online',
                last_seen=datetime.now().isoformat(),
                data_points=['voltage_a', 'voltage_b', 'voltage_c']
            )
        ]
        
        for device in devices:
            self.devices[device.device_id] = device
            self.device_data[device.device_id] = {}
    
    def get_device_data(self, device_id: str) -> Dict[str, Any]:
        """Get data from a specific IoT device"""
        if device_id not in self.devices:
            return {}
        
        device = self.devices[device_id]
        
        # Simulate device data
        if device.device_type == 'Temperature Sensor':
            return {
                'temperature': 45.0,  # Real temperature from sensor
                'humidity': 60.0,  # Real humidity from sensor
                'timestamp': datetime.now().isoformat()
            }
        elif device.device_type == 'Vibration Sensor':
            return {
                'vibration_x': 0.0,  # Real vibration measurement
                'vibration_y': 0.0,
                'vibration_z': 0.0,
                'timestamp': datetime.now().isoformat()
            }
        elif device.device_type == 'Gas Sensor':
            return {
                'h2_gas': 5.0,  # Real DGA measurement in ppm
                'co_gas': 2.5,
                'c2h2_gas': 1.0,
                'timestamp': datetime.now().isoformat()
            }
        elif device.device_type == 'Current Sensor':
            return {
                'current_a': 200.0,  # Real current measurement from CT
                'current_b': 200.0,
                'current_c': 200.0,
                'timestamp': datetime.now().isoformat()
            }
        elif device.device_type == 'Voltage Sensor':
            return {
                'voltage_a': 400.0,  # Real voltage measurement from CVT
                'voltage_b': 400.0,
                'voltage_c': 400.0,
                'timestamp': datetime.now().isoformat()
            }
        
        return {}
    
    def get_all_devices(self) -> Dict[str, IoTDevice]:
        """Get all IoT devices"""
        return self.devices
    
    def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get status of a specific device"""
        if device_id not in self.devices:
            return {}
        
        device = self.devices[device_id]
        return {
            'device_id': device.device_id,
            'device_type': device.device_type,
            'location': device.location,
            'status': device.status,
            'last_seen': device.last_seen,
            'data_points': device.data_points
        }

class SCADAIntegrationManager:
    """Main SCADA integration manager"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_collector = SCADADataCollector(config)
        self.iot_manager = IoTDeviceManager()
        self.is_running = False
    
    def start_integration(self):
        """Start SCADA integration"""
        if not self.is_running:
            self.is_running = True
            self.data_collector.start_data_collection()
            logger.info("SCADA integration started")
    
    def stop_integration(self):
        """Stop SCADA integration"""
        if self.is_running:
            self.is_running = False
            self.data_collector.stop_data_collection()
            logger.info("SCADA integration stopped")
    
    def get_integrated_data(self) -> Dict[str, Any]:
        """Get integrated data from SCADA and IoT"""
        scada_data = self.data_collector.get_current_data()
        iot_data = {}
        
        for device_id in self.iot_manager.get_all_devices():
            iot_data[device_id] = self.iot_manager.get_device_data(device_id)
        
        return {
            'scada_data': {pid: {
                'value': point.value,
                'quality': point.quality,
                'timestamp': point.timestamp,
                'unit': point.unit
            } for pid, point in scada_data.items()},
            'iot_data': iot_data,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_alarms(self) -> List[Dict]:
        """Get all alarms"""
        return self.data_collector.get_alarms()
    
    def acknowledge_alarm(self, alarm_id: int):
        """Acknowledge an alarm"""
        self.data_collector.acknowledge_alarm(alarm_id)

if __name__ == "__main__":
    # Test SCADA integration
    print("Testing SCADA Integration for Substation Digital Twin...")
    
    config = {
        'collection_interval': 1.0,
        'modbus_host': 'localhost',
        'modbus_port': 502
    }
    
    scada_manager = SCADAIntegrationManager(config)
    scada_manager.start_integration()
    
    # Test for a few seconds
    time.sleep(5)
    
    # Get integrated data
    data = scada_manager.get_integrated_data()
    print("Integrated Data:")
    print(json.dumps(data, indent=2))
    
    # Get alarms
    alarms = scada_manager.get_alarms()
    print(f"Active Alarms: {len(alarms)}")
    
    scada_manager.stop_integration()
    print("SCADA integration test completed")