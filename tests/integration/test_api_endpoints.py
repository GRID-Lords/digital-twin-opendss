"""
Integration tests for API endpoints
"""

import pytest
import requests
import json
import time
from fastapi.testclient import TestClient
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backend_server import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture
def mock_digital_twin():
    """Mock digital twin for testing"""
    with Mock() as mock:
        mock.get_all_assets.return_value = {
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
            }
        }
        mock.get_substation_metrics.return_value = {
            'total_power': 100.0,
            'total_load': 100.0,
            'efficiency': 95.0,
            'voltage_stability': 98.0,
            'frequency': 50.0,
            'timestamp': '2024-01-01T00:00:00',
            'grid_connection': True,
            'fault_count': 0
        }
        mock.control_asset.return_value = {'status': 'success', 'message': 'Asset controlled'}
        mock.run_fault_analysis.return_value = {
            'fault_type': 'line_to_ground',
            'fault_location': 'Bus400kV_1',
            'fault_impedance': 0.1,
            'fault_current': 5000.0,
            'protection_operation': True,
            'clearance_time': 0.1,
            'timestamp': '2024-01-01T00:00:00'
        }
        yield mock

class TestRootEndpoints:
    """Test root and basic endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert "endpoints" in data
    
    def test_api_documentation(self, client):
        """Test API documentation endpoint"""
        response = client.get("/docs")
        assert response.status_code == 200

class TestAssetEndpoints:
    """Test asset management endpoints"""
    
    def test_get_all_assets(self, client, mock_digital_twin):
        """Test getting all assets"""
        with patch('src.api.digital_twin_server.digital_twin', mock_digital_twin):
            response = client.get("/api/assets")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, dict)
            assert 'TX1_400_220' in data
    
    def test_get_specific_asset(self, client, mock_digital_twin):
        """Test getting a specific asset"""
        with patch('src.api.digital_twin_server.digital_twin', mock_digital_twin):
            response = client.get("/api/assets/TX1_400_220")
            assert response.status_code == 200
            
            data = response.json()
            assert data['asset_id'] == 'TX1_400_220'
            assert data['asset_type'] == 'PowerTransformer'
    
    def test_get_nonexistent_asset(self, client, mock_digital_twin):
        """Test getting a non-existent asset"""
        with patch('src.api.digital_twin_server.digital_twin', mock_digital_twin):
            response = client.get("/api/assets/NONEXISTENT")
            assert response.status_code == 404
    
    def test_control_asset(self, client, mock_digital_twin):
        """Test controlling an asset"""
        with patch('src.api.digital_twin_server.digital_twin', mock_digital_twin):
            control_data = {
                "asset_id": "TX1_400_220",
                "action": "open",
                "parameters": {}
            }
            
            response = client.post("/api/control", json=control_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data['status'] == 'success'
    
    def test_control_asset_invalid(self, client, mock_digital_twin):
        """Test controlling an asset with invalid data"""
        with patch('src.api.digital_twin_server.digital_twin', mock_digital_twin):
            control_data = {
                "asset_id": "NONEXISTENT",
                "action": "invalid_action",
                "parameters": {}
            }
            
            response = client.post("/api/control", json=control_data)
            assert response.status_code == 400

class TestMetricsEndpoints:
    """Test metrics endpoints"""
    
    def test_get_metrics(self, client, mock_digital_twin):
        """Test getting substation metrics"""
        with patch('src.api.digital_twin_server.digital_twin', mock_digital_twin):
            response = client.get("/api/metrics")
            assert response.status_code == 200
            
            data = response.json()
            assert 'total_power' in data
            assert 'efficiency' in data
            assert 'voltage_stability' in data
            assert 'frequency' in data

class TestSCADAEndpoints:
    """Test SCADA endpoints"""
    
    def test_get_scada_data(self, client):
        """Test getting SCADA data"""
        response = client.get("/api/scada/data")
        assert response.status_code == 200
        
        data = response.json()
        assert 'scada_data' in data
        assert 'iot_data' in data
        assert 'timestamp' in data
    
    def test_get_scada_alarms(self, client):
        """Test getting SCADA alarms"""
        response = client.get("/api/scada/alarms")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_acknowledge_alarm(self, client):
        """Test acknowledging an alarm"""
        response = client.post("/api/scada/alarms/1/acknowledge")
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'success'

class TestAIEndpoints:
    """Test AI/ML endpoints"""
    
    def test_get_ai_analysis(self, client):
        """Test getting AI analysis"""
        response = client.get("/api/ai/analysis")
        assert response.status_code == 200
        
        data = response.json()
        assert 'timestamp' in data
        assert 'anomalies' in data
        assert 'predictions' in data
        assert 'optimization' in data
    
    def test_get_anomalies(self, client):
        """Test getting anomalies"""
        response = client.get("/api/ai/anomalies")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_predictions(self, client):
        """Test getting predictions"""
        response = client.get("/api/ai/predictions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_optimization(self, client):
        """Test getting optimization recommendations"""
        response = client.get("/api/ai/optimization")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)

class TestIoTEndpoints:
    """Test IoT device endpoints"""
    
    def test_get_iot_devices(self, client):
        """Test getting IoT devices"""
        response = client.get("/api/iot/devices")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_iot_device_data(self, client):
        """Test getting IoT device data"""
        response = client.get("/api/iot/devices/TEMP_SENSOR_001/data")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)

class TestFaultAnalysisEndpoints:
    """Test fault analysis endpoints"""
    
    def test_analyze_fault(self, client, mock_digital_twin):
        """Test fault analysis"""
        with patch('src.api.digital_twin_server.digital_twin', mock_digital_twin):
            response = client.post("/api/faults/analyze?fault_type=line_to_ground&fault_location=Bus400kV_1")
            assert response.status_code == 200
            
            data = response.json()
            assert 'fault_type' in data
            assert 'fault_location' in data
            assert 'fault_impedance' in data
            assert 'fault_current' in data
    
    def test_get_fault_history(self, client):
        """Test getting fault history"""
        response = client.get("/api/faults")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

class TestSimulationEndpoints:
    """Test simulation control endpoints"""
    
    def test_start_simulation(self, client):
        """Test starting simulation"""
        response = client.post("/api/simulation/start")
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'success'
    
    def test_stop_simulation(self, client):
        """Test stopping simulation"""
        response = client.post("/api/simulation/stop")
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'success'

class TestVisualizationEndpoints:
    """Test visualization endpoints"""
    
    def test_get_network_diagram(self, client):
        """Test getting network diagram"""
        response = client.get("/api/visualization/network")
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'success'

class TestWebSocketConnection:
    """Test WebSocket functionality"""
    
    def test_websocket_connection(self, client):
        """Test WebSocket connection"""
        with client.websocket_connect("/ws") as websocket:
            # Send a test message
            websocket.send_text("test")
            
            # Should receive a response
            data = websocket.receive_text()
            assert data is not None

class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_endpoint(self, client):
        """Test invalid endpoint"""
        response = client.get("/api/invalid")
        assert response.status_code == 404
    
    def test_invalid_method(self, client):
        """Test invalid HTTP method"""
        response = client.delete("/api/assets")
        assert response.status_code == 405
    
    def test_malformed_json(self, client):
        """Test malformed JSON"""
        response = client.post("/api/control", 
                              data="invalid json",
                              headers={"Content-Type": "application/json"})
        assert response.status_code == 422

class TestPerformance:
    """Test API performance"""
    
    def test_response_times(self, client):
        """Test that API responses are fast"""
        endpoints = [
            "/",
            "/api/assets",
            "/api/metrics",
            "/api/scada/data",
            "/api/ai/analysis"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            assert response.status_code == 200
            assert (end_time - start_time) < 1.0  # Should respond within 1 second
    
    def test_concurrent_requests(self, client):
        """Test handling concurrent requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            response = client.get("/api/assets")
            results.put(response.status_code)
        
        # Start multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check all requests succeeded
        while not results.empty():
            status_code = results.get()
            assert status_code == 200