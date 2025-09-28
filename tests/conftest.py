"""
Pytest configuration and fixtures for Digital Twin tests
"""

import pytest
import sys
import os
from pathlib import Path
import tempfile
import sqlite3
import json
from unittest.mock import Mock, patch

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing"""
    db_fd, db_path = tempfile.mkstemp()
    conn = sqlite3.connect(db_path)
    
    # Create test tables
    conn.execute('''
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
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS iot_devices (
            device_id TEXT PRIMARY KEY,
            device_type TEXT NOT NULL,
            location TEXT NOT NULL,
            status TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            data_points TEXT
        )
    ''')
    
    conn.execute('''
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
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def mock_assets():
    """Mock asset data for testing"""
    return {
        'TX1_400_220': {
            'asset_id': 'TX1_400_220',
            'asset_type': 'PowerTransformer',
            'status': 'healthy',
            'voltage': 400.0,
            'current': 200.0,
            'power': 80000.0,
            'temperature': 45.0,
            'health_score': 95.0,
            'timestamp': '2024-01-01T00:00:00'
        },
        'CB_400kV': {
            'asset_id': 'CB_400kV',
            'asset_type': 'CircuitBreaker',
            'status': 'healthy',
            'voltage': 0.0,
            'current': 0.0,
            'power': 0.0,
            'temperature': 30.0,
            'health_score': 98.0,
            'timestamp': '2024-01-01T00:00:00'
        }
    }

@pytest.fixture
def mock_metrics():
    """Mock substation metrics for testing"""
    return {
        'total_power': 100.0,
        'total_load': 100.0,
        'efficiency': 95.0,
        'voltage_stability': 98.0,
        'frequency': 50.0,
        'timestamp': '2024-01-01T00:00:00',
        'grid_connection': True,
        'fault_count': 0
    }

@pytest.fixture
def mock_scada_data():
    """Mock SCADA data for testing"""
    return {
        'scada_data': {
            '400kV_VOLTAGE_A': {
                'value': 400.0,
                'quality': 'good',
                'timestamp': '2024-01-01T00:00:00',
                'unit': 'kV'
            },
            '400kV_CURRENT_A': {
                'value': 200.0,
                'quality': 'good',
                'timestamp': '2024-01-01T00:00:00',
                'unit': 'A'
            }
        },
        'iot_data': {
            'TEMP_SENSOR_001': {
                'temperature': 45.0,
                'humidity': 60.0,
                'timestamp': '2024-01-01T00:00:00'
            }
        }
    }

@pytest.fixture
def mock_ai_analysis():
    """Mock AI analysis results for testing"""
    return {
        'anomalies': [
            {
                'asset_id': 'TX1_400_220',
                'asset_type': 'PowerTransformer',
                'anomaly_score': -0.5,
                'severity': 'medium',
                'timestamp': '2024-01-01T00:00:00'
            }
        ],
        'predictions': [
            {
                'asset_id': 'TX1_400_220',
                'asset_type': 'PowerTransformer',
                'current_health': 95.0,
                'predicted_health': 90.0,
                'degradation_rate': 0.5,
                'urgency': 'medium',
                'maintenance_window': 'within_30_days',
                'timestamp': '2024-01-01T00:00:00'
            }
        ],
        'optimization': {
            'current_efficiency': 95.0,
            'target_efficiency': 98.0,
            'optimization_score': 85.0,
            'recommendations': [
                {
                    'type': 'efficiency',
                    'action': 'adjust_transformer_taps',
                    'priority': 'high',
                    'description': 'Current efficiency 95.0% is below target 98.0%'
                }
            ]
        }
    }

@pytest.fixture
def mock_digital_twin():
    """Mock digital twin instance for testing"""
    with patch('src.api.digital_twin_server.IndianEHVSubstationDigitalTwin') as mock:
        instance = Mock()
        instance.get_all_assets.return_value = mock_assets()
        instance.get_substation_metrics.return_value = mock_metrics()
        instance.control_asset.return_value = {'status': 'success'}
        instance.run_fault_analysis.return_value = {
            'fault_type': 'line_to_ground',
            'fault_location': 'Bus400kV_1',
            'fault_impedance': 0.1,
            'fault_current': 5000.0,
            'protection_operation': True,
            'clearance_time': 0.1,
            'timestamp': '2024-01-01T00:00:00'
        }
        mock.return_value = instance
        yield instance