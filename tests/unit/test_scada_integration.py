"""
Unit tests for SCADA integration
"""

import pytest
import sqlite3
from datetime import datetime
from integration.scada_integration import (
    SCADADataCollector,
    IoTDeviceManager,
    SCADAIntegrationManager
)

class TestSCADADataCollector:
    """Test SCADA data collection functionality"""
    
    def test_initialization(self, temp_db):
        """Test SCADA collector initialization"""
        config = {
            'collection_interval': 1.0,
            'modbus_host': 'localhost',
            'modbus_port': 502
        }
        
        collector = SCADADataCollector(config)
        assert collector.config == config
        assert collector.is_running == False
        assert len(collector.scada_points) > 0
    
    def test_scada_points_initialization(self, temp_db):
        """Test SCADA points are properly initialized"""
        config = {'collection_interval': 1.0}
        collector = SCADADataCollector(config)
        
        # Check that key SCADA points exist
        assert '400kV_VOLTAGE_A' in collector.scada_points
        assert '400kV_CURRENT_A' in collector.scada_points
        assert 'TX1_TEMP' in collector.scada_points
        assert 'CB_400kV_STATUS' in collector.scada_points
        
        # Check point structure
        point = collector.scada_points['400kV_VOLTAGE_A']
        assert hasattr(point, 'point_id')
        assert hasattr(point, 'point_name')
        assert hasattr(point, 'data_type')
        assert hasattr(point, 'value')
        assert hasattr(point, 'quality')
        assert hasattr(point, 'timestamp')
        assert hasattr(point, 'unit')
        assert hasattr(point, 'description')
    
    def test_simulate_scada_data(self, temp_db):
        """Test SCADA data simulation"""
        config = {'collection_interval': 1.0}
        collector = SCADADataCollector(config)

        # Store initial timestamps
        initial_timestamps = {pid: point.timestamp for pid, point in collector.scada_points.items()}

        # Simulate data
        collector._simulate_scada_data()

        # Check that timestamps have changed (data was updated)
        changed_count = 0
        for pid, point in collector.scada_points.items():
            if point.timestamp != initial_timestamps[pid]:
                changed_count += 1

        # At least some points should have been updated
        assert changed_count > 0, "No SCADA points were updated during simulation"
    
    def test_store_scada_data(self, temp_db):
        """Test storing SCADA data in database"""
        config = {'collection_interval': 1.0}
        collector = SCADADataCollector(config)
        collector.db_connection = sqlite3.connect(temp_db)
        
        # Store data
        collector._store_scada_data()
        
        # Check data was stored
        cursor = collector.db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM scada_data")
        count = cursor.fetchone()[0]
        assert count > 0
        
        # Check specific data
        cursor.execute("SELECT point_id, value, quality FROM scada_data LIMIT 1")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] in collector.scada_points
        assert isinstance(row[1], float)
        assert row[2] in ['good', 'bad', 'uncertain']
    
    def test_check_alarms(self, temp_db):
        """Test alarm checking functionality"""
        config = {'collection_interval': 1.0}
        collector = SCADADataCollector(config)
        collector.db_connection = sqlite3.connect(temp_db)
        
        # Set up alarm condition
        collector.scada_points['400kV_VOLTAGE_A'].value = 350.0  # Below threshold
        collector.scada_points['400kV_VOLTAGE_A'].quality = 'good'
        
        # Check alarms
        collector._check_alarms()
        
        # Check alarm was created
        cursor = collector.db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM alarms")
        count = cursor.fetchone()[0]
        assert count > 0
    
    def test_get_historical_data(self, temp_db):
        """Test retrieving historical data"""
        config = {'collection_interval': 1.0}
        collector = SCADADataCollector(config)
        collector.db_connection = sqlite3.connect(temp_db)
        
        # Insert test data
        cursor = collector.db_connection.cursor()
        cursor.execute('''
            INSERT INTO scada_data (point_id, point_name, data_type, value, quality, timestamp, unit, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('TEST_POINT', 'Test Point', 'analog', 100.0, 'good', '2024-01-01T00:00:00', 'kV', 'Test'))
        collector.db_connection.commit()
        
        # Retrieve data
        data = collector.get_historical_data('TEST_POINT', '2024-01-01T00:00:00', '2024-01-01T23:59:59')
        assert len(data) == 1
        assert data[0]['point_id'] == 'TEST_POINT'
        assert data[0]['value'] == 100.0
    
    def test_get_alarms(self, temp_db):
        """Test retrieving alarms"""
        config = {'collection_interval': 1.0}
        collector = SCADADataCollector(config)
        collector.db_connection = sqlite3.connect(temp_db)
        
        # Insert test alarm
        cursor = collector.db_connection.cursor()
        cursor.execute('''
            INSERT INTO alarms (point_id, alarm_type, severity, message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', ('TEST_POINT', 'voltage_out_of_range', 'high', 'Test alarm', '2024-01-01T00:00:00'))
        collector.db_connection.commit()
        
        # Retrieve alarms
        alarms = collector.get_alarms()
        assert len(alarms) == 1
        assert alarms[0]['point_id'] == 'TEST_POINT'
        assert alarms[0]['alarm_type'] == 'voltage_out_of_range'
    
    def test_acknowledge_alarm(self, temp_db):
        """Test acknowledging alarms"""
        config = {'collection_interval': 1.0}
        collector = SCADADataCollector(config)
        collector.db_connection = sqlite3.connect(temp_db)
        
        # Insert test alarm
        cursor = collector.db_connection.cursor()
        cursor.execute('''
            INSERT INTO alarms (point_id, alarm_type, severity, message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', ('TEST_POINT', 'voltage_out_of_range', 'high', 'Test alarm', '2024-01-01T00:00:00'))
        collector.db_connection.commit()
        
        # Get alarm ID
        cursor.execute("SELECT id FROM alarms WHERE point_id = 'TEST_POINT'")
        alarm_id = cursor.fetchone()[0]
        
        # Acknowledge alarm
        collector.acknowledge_alarm(alarm_id)
        
        # Check alarm is acknowledged
        cursor.execute("SELECT acknowledged FROM alarms WHERE id = ?", (alarm_id,))
        acknowledged = cursor.fetchone()[0]
        assert acknowledged == 1

class TestIoTDeviceManager:
    """Test IoT device management functionality"""
    
    def test_initialization(self):
        """Test IoT device manager initialization"""
        manager = IoTDeviceManager()
        assert len(manager.devices) > 0
        assert len(manager.device_data) > 0
    
    def test_device_types(self):
        """Test that different device types are created"""
        manager = IoTDeviceManager()
        
        device_types = set(device.device_type for device in manager.devices.values())
        expected_types = {
            'Temperature Sensor',
            'Vibration Sensor',
            'Gas Sensor',
            'Current Sensor',
            'Voltage Sensor'
        }
        
        assert device_types == expected_types
    
    def test_get_device_data(self):
        """Test getting data from IoT devices"""
        manager = IoTDeviceManager()
        
        # Test temperature sensor
        temp_data = manager.get_device_data('TEMP_SENSOR_001')
        assert 'temperature' in temp_data
        assert 'humidity' in temp_data
        assert 'timestamp' in temp_data
        assert isinstance(temp_data['temperature'], float)
        
        # Test vibration sensor
        vib_data = manager.get_device_data('VIBRATION_SENSOR_001')
        assert 'vibration_x' in vib_data
        assert 'vibration_y' in vib_data
        assert 'vibration_z' in vib_data
        assert 'timestamp' in vib_data
        
        # Test gas sensor
        gas_data = manager.get_device_data('GAS_SENSOR_001')
        assert 'h2_gas' in gas_data
        assert 'co_gas' in gas_data
        assert 'c2h2_gas' in gas_data
        assert 'timestamp' in gas_data
    
    def test_get_nonexistent_device_data(self):
        """Test getting data from non-existent device"""
        manager = IoTDeviceManager()
        data = manager.get_device_data('NONEXISTENT_DEVICE')
        assert data == {}
    
    def test_get_all_devices(self):
        """Test getting all devices"""
        manager = IoTDeviceManager()
        devices = manager.get_all_devices()
        
        assert len(devices) > 0
        for device_id, device in devices.items():
            assert hasattr(device, 'device_id')
            assert hasattr(device, 'device_type')
            assert hasattr(device, 'location')
            assert hasattr(device, 'status')
            assert hasattr(device, 'last_seen')
    
    def test_get_device_status(self):
        """Test getting device status"""
        manager = IoTDeviceManager()
        status = manager.get_device_status('TEMP_SENSOR_001')
        
        assert 'device_id' in status
        assert 'device_type' in status
        assert 'location' in status
        assert 'status' in status
        assert 'last_seen' in status
        assert status['device_id'] == 'TEMP_SENSOR_001'

class TestSCADAIntegrationManager:
    """Test SCADA integration manager functionality"""
    
    def test_initialization(self):
        """Test SCADA integration manager initialization"""
        config = {'collection_interval': 1.0}
        manager = SCADAIntegrationManager(config)
        
        assert manager.config == config
        assert manager.is_running == False
        assert manager.data_collector is not None
        assert manager.iot_manager is not None
    
    def test_get_integrated_data(self):
        """Test getting integrated data"""
        config = {'collection_interval': 1.0}
        manager = SCADAIntegrationManager(config)
        
        data = manager.get_integrated_data()
        
        assert 'scada_data' in data
        assert 'iot_data' in data
        assert 'timestamp' in data
        assert isinstance(data['scada_data'], dict)
        assert isinstance(data['iot_data'], dict)
    
    def test_get_alarms(self, temp_db):
        """Test getting alarms"""
        config = {'collection_interval': 1.0}
        manager = SCADAIntegrationManager(config)
        manager.data_collector.db_connection = sqlite3.connect(temp_db)
        
        # Insert test alarm
        cursor = manager.data_collector.db_connection.cursor()
        cursor.execute('''
            INSERT INTO alarms (point_id, alarm_type, severity, message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', ('TEST_POINT', 'voltage_out_of_range', 'high', 'Test alarm', '2024-01-01T00:00:00'))
        manager.data_collector.db_connection.commit()
        
        alarms = manager.get_alarms()
        assert len(alarms) == 1
        assert alarms[0]['point_id'] == 'TEST_POINT'
    
    def test_acknowledge_alarm(self, temp_db):
        """Test acknowledging alarms"""
        config = {'collection_interval': 1.0}
        manager = SCADAIntegrationManager(config)
        manager.data_collector.db_connection = sqlite3.connect(temp_db)
        
        # Insert test alarm
        cursor = manager.data_collector.db_connection.cursor()
        cursor.execute('''
            INSERT INTO alarms (point_id, alarm_type, severity, message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', ('TEST_POINT', 'voltage_out_of_range', 'high', 'Test alarm', '2024-01-01T00:00:00'))
        manager.data_collector.db_connection.commit()
        
        # Get alarm ID
        cursor.execute("SELECT id FROM alarms WHERE point_id = 'TEST_POINT'")
        alarm_id = cursor.fetchone()[0]
        
        # Acknowledge alarm
        manager.acknowledge_alarm(alarm_id)
        
        # Check alarm is acknowledged
        cursor.execute("SELECT acknowledged FROM alarms WHERE id = ?", (alarm_id,))
        acknowledged = cursor.fetchone()[0]
        assert acknowledged == 1