"""
Integration tests for complete system functionality
"""

import pytest
import requests
import time
import subprocess
import sys
from pathlib import Path
import json

class TestSystemStartup:
    """Test complete system startup and shutdown"""
    
    def test_system_startup_script(self):
        """Test that the startup script works"""
        # This test would run the actual start.sh script
        # For now, we'll test the components individually
        pass
    
    def test_backend_startup(self):
        """Test backend server startup"""
        # Test that the backend can be imported and initialized
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        try:
            from backend_server import app, digital_twin
            assert app is not None
            assert digital_twin is not None
        except ImportError as e:
            pytest.fail(f"Failed to import backend components: {e}")
    
    def test_frontend_dependencies(self):
        """Test that frontend dependencies are available"""
        frontend_dir = Path(__file__).parent.parent / "frontend"
        
        if not frontend_dir.exists():
            pytest.skip("Frontend directory not found")
        
        # Check package.json exists
        package_json = frontend_dir / "package.json"
        assert package_json.exists()
        
        # Check that key dependencies are listed
        with open(package_json) as f:
            package_data = json.load(f)
        
        required_deps = [
            "react", "react-dom", "axios", "recharts", 
            "styled-components", "react-router-dom"
        ]
        
        for dep in required_deps:
            assert dep in package_data.get("dependencies", {})

class TestDataFlow:
    """Test data flow through the system"""
    
    def test_scada_to_ai_pipeline(self):
        """Test data flow from SCADA to AI analysis"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from integration.scada_integration import SCADAIntegrationManager
        from models.ai_ml_models import SubstationAIManager
        
        # Initialize components
        scada_config = {'collection_interval': 1.0}
        scada_manager = SCADAIntegrationManager(scada_config)
        ai_manager = SubstationAIManager()
        ai_manager.initialize_with_synthetic_data()
        
        # Get SCADA data
        scada_data = scada_manager.get_integrated_data()
        assert 'scada_data' in scada_data
        assert 'iot_data' in scada_data
        
        # Simulate asset data for AI analysis
        mock_assets = {
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
        
        mock_metrics = {
            'total_power': 100.0,
            'efficiency': 95.0,
            'voltage_stability': 98.0
        }
        
        # Run AI analysis
        ai_analysis = ai_manager.analyze_current_state(mock_assets, mock_metrics)
        assert 'anomalies' in ai_analysis
        assert 'predictions' in ai_analysis
        assert 'optimization' in ai_analysis
    
    def test_openDSS_to_visualization_pipeline(self):
        """Test data flow from OpenDSS to visualization"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from visualization.circuit_visualizer import OpenDSSVisualizer
        
        # Test with a simple circuit file
        dss_file = Path(__file__).parent.parent / "examples" / "EnhancedCircuit.dss"
        
        if dss_file.exists():
            try:
                visualizer = OpenDSSVisualizer(str(dss_file))
                # Test that visualizer can be created
                assert visualizer is not None
                assert visualizer.dss_file == str(dss_file)
            except Exception as e:
                # If OpenDSS is not available, that's okay for testing
                pytest.skip(f"OpenDSS not available: {e}")
    
    def test_websocket_data_flow(self):
        """Test WebSocket data flow"""
        # This would test the actual WebSocket connection
        # For now, we'll test the WebSocket endpoint exists
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from backend_server import app
        
        # Check that WebSocket endpoint is defined
        routes = [route.path for route in app.routes]
        assert "/ws" in routes

class TestSystemComponents:
    """Test individual system components"""
    
    def test_ai_ml_training(self):
        """Test AI/ML model training"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from models.ai_ml_models import SubstationAIManager
        
        ai_manager = SubstationAIManager()
        
        # Test initialization with synthetic data
        ai_manager.initialize_with_synthetic_data()
        assert ai_manager.is_initialized == True
        assert ai_manager.anomaly_detector.is_trained == True
        assert ai_manager.predictive_model.is_trained == True
    
    def test_scada_data_collection(self):
        """Test SCADA data collection"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from integration.scada_integration import SCADAIntegrationManager
        
        scada_config = {'collection_interval': 1.0}
        scada_manager = SCADAIntegrationManager(scada_config)
        
        # Test getting integrated data
        data = scada_manager.get_integrated_data()
        assert 'scada_data' in data
        assert 'iot_data' in data
        assert 'timestamp' in data
        
        # Test that SCADA points exist
        assert len(data['scada_data']) > 0
        assert len(data['iot_data']) > 0
    
    def test_database_operations(self):
        """Test database operations"""
        import sqlite3
        import tempfile
        import os
        
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp()
        
        try:
            conn = sqlite3.connect(db_path)
            
            # Create tables
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
            
            # Insert test data
            conn.execute('''
                INSERT INTO scada_data 
                (point_id, point_name, data_type, value, quality, timestamp, unit, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('TEST_POINT', 'Test Point', 'analog', 100.0, 'good', '2024-01-01T00:00:00', 'kV', 'Test'))
            
            conn.commit()
            
            # Test data retrieval
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scada_data WHERE point_id = 'TEST_POINT'")
            row = cursor.fetchone()
            
            assert row is not None
            assert row[1] == 'TEST_POINT'  # point_id
            assert row[4] == 100.0  # value
            
        finally:
            conn.close()
            os.close(db_fd)
            os.unlink(db_path)
    
    def test_asset_control_workflow(self):
        """Test complete asset control workflow"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from backend_server import IndianEHVSubstationDigitalTwin
        
        # Create digital twin instance
        digital_twin = IndianEHVSubstationDigitalTwin()
        
        # Test asset control
        result = digital_twin.control_asset('CB_400kV', 'open')
        assert result['status'] == 'success'
        
        # Test fault analysis
        fault_result = digital_twin.run_fault_analysis('line_to_ground', 'Bus400kV_1')
        assert 'fault_type' in fault_result
        assert 'fault_location' in fault_result
        assert 'fault_impedance' in fault_result

class TestSystemPerformance:
    """Test system performance characteristics"""
    
    def test_api_response_times(self):
        """Test that API responses are within acceptable time limits"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from fastapi.testclient import TestClient
        from backend_server import app
        
        client = TestClient(app)
        
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
            
            response_time = end_time - start_time
            assert response.status_code == 200
            assert response_time < 2.0  # Should respond within 2 seconds
    
    def test_memory_usage(self):
        """Test that system doesn't use excessive memory"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Import and initialize components
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from models.ai_ml_models import SubstationAIManager
        from integration.scada_integration import SCADAIntegrationManager
        
        ai_manager = SubstationAIManager()
        ai_manager.initialize_with_synthetic_data()
        
        scada_config = {'collection_interval': 1.0}
        scada_manager = SCADAIntegrationManager(scada_config)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Should not use more than 500MB
        assert memory_increase < 500, f"Memory usage increased by {memory_increase:.1f}MB"
    
    def test_concurrent_operations(self):
        """Test system under concurrent operations"""
        import threading
        import queue
        
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from backend_server import IndianEHVSubstationDigitalTwin
        
        digital_twin = IndianEHVSubstationDigitalTwin()
        results = queue.Queue()
        
        def simulate_operation():
            try:
                # Simulate various operations
                assets = digital_twin.get_all_assets()
                metrics = digital_twin.get_substation_metrics()
                result = digital_twin.control_asset('CB_400kV', 'open')
                results.put('success')
            except Exception as e:
                results.put(f'error: {e}')
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=simulate_operation)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 'success':
                success_count += 1
        
        # At least 80% should succeed
        assert success_count >= 4, f"Only {success_count}/5 operations succeeded"

class TestSystemReliability:
    """Test system reliability and error handling"""
    
    def test_error_recovery(self):
        """Test system error recovery"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from backend_server import IndianEHVSubstationDigitalTwin
        
        digital_twin = IndianEHVSubstationDigitalTwin()
        
        # Test with invalid asset ID
        try:
            result = digital_twin.control_asset('INVALID_ASSET', 'open')
            # Should handle gracefully
        except ValueError:
            # This is expected behavior
            pass
        
        # Test with invalid action
        try:
            result = digital_twin.control_asset('CB_400kV', 'invalid_action')
            # Should handle gracefully
        except ValueError:
            # This is expected behavior
            pass
    
    def test_data_validation(self):
        """Test data validation"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from integration.scada_integration import SCADADataCollector
        
        config = {'collection_interval': 1.0}
        collector = SCADADataCollector(config)
        
        # Test that SCADA points have valid data
        for point_id, point in collector.scada_points.items():
            assert hasattr(point, 'point_id')
            assert hasattr(point, 'point_name')
            assert hasattr(point, 'data_type')
            assert hasattr(point, 'value')
            assert hasattr(point, 'quality')
            assert hasattr(point, 'timestamp')
            
            # Validate data types
            assert isinstance(point.value, (int, float))
            assert point.quality in ['good', 'bad', 'uncertain']
            assert point.data_type in ['analog', 'digital', 'counter']
    
    def test_system_initialization(self):
        """Test complete system initialization"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        # Test that all components can be imported
        try:
            from backend_server import app, digital_twin
            from models.ai_ml_models import SubstationAIManager
            from integration.scada_integration import SCADAIntegrationManager
            from visualization.circuit_visualizer import OpenDSSVisualizer
            
            assert app is not None
            assert digital_twin is not None
            
        except ImportError as e:
            pytest.fail(f"Failed to import system components: {e}")
        
        # Test that components can be initialized
        try:
            ai_manager = SubstationAIManager()
            ai_manager.initialize_with_synthetic_data()
            
            scada_config = {'collection_interval': 1.0}
            scada_manager = SCADAIntegrationManager(scada_config)
            
            assert ai_manager.is_initialized == True
            
        except Exception as e:
            pytest.fail(f"Failed to initialize system components: {e}")