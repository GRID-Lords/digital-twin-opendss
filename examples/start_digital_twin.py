#!/usr/bin/env python3
"""
Startup Script for Indian EHV Substation Digital Twin
Complete system initialization and testing
"""

import os
import sys
import time
import logging
from pathlib import Path
import subprocess
import requests
import json

# Set environment for headless operation
os.environ['MPLBACKEND'] = 'Agg'
os.environ['DISPLAY'] = ''

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed"""
    logger.info("Checking dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'websockets', 'pandas', 'numpy',
        'scikit-learn', 'matplotlib', 'opendssdirect', 'pymodbus',
        'requests', 'sqlite3'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.warning(f"Missing packages: {missing_packages}")
        logger.info("Installing missing packages...")
        
        for package in missing_packages:
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', 
                    '--user', '--break-system-packages', package
                ])
                logger.info(f"✓ Installed {package}")
            except subprocess.CalledProcessError:
                logger.error(f"✗ Failed to install {package}")
    
    logger.info("✓ Dependencies check completed")

def test_digital_twin_components():
    """Test all digital twin components"""
    logger.info("Testing Digital Twin components...")
    
    try:
        # Test OpenDSS circuit
        logger.info("Testing OpenDSS circuit...")
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from visualization.circuit_visualizer import OpenDSSVisualizer
        visualizer = OpenDSSVisualizer("src/models/IndianEHVSubstation.dss")
        visualizer.load_and_solve()
        logger.info("✓ OpenDSS circuit test passed")
        
        # Test AI/ML models
        logger.info("Testing AI/ML models...")
        from models.ai_ml_models import SubstationAIManager
        ai_manager = SubstationAIManager()
        ai_manager.initialize_with_synthetic_data()
        logger.info("✓ AI/ML models test passed")
        
        # Test SCADA integration
        logger.info("Testing SCADA integration...")
        from integration.scada_integration import SCADAIntegrationManager
        scada_config = {'collection_interval': 1.0}
        scada_manager = SCADAIntegrationManager(scada_config)
        scada_manager.start_integration()
        time.sleep(2)  # Let it collect some data
        scada_manager.stop_integration()
        logger.info("✓ SCADA integration test passed")
        
        logger.info("✓ All component tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Component test failed: {e}")
        return False

def start_digital_twin_server():
    """Start the digital twin server"""
    logger.info("Starting Digital Twin Server...")
    
    try:
        # Import and start the server
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from api.digital_twin_server import app, digital_twin
        import uvicorn
        
        # Start the server in a separate process
        server_process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 
            'digital_twin_server:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload'
        ])
        
        # Wait for server to start
        logger.info("Waiting for server to start...")
        time.sleep(5)
        
        # Test server endpoints
        test_server_endpoints()
        
        logger.info("✓ Digital Twin Server started successfully")
        logger.info("🌐 Server running at: http://localhost:8000")
        logger.info("📊 Dashboard available at: http://localhost:8000/dashboard")
        logger.info("📚 API documentation at: http://localhost:8000/docs")
        
        return server_process
        
    except Exception as e:
        logger.error(f"✗ Failed to start server: {e}")
        return None

def test_server_endpoints():
    """Test server endpoints"""
    logger.info("Testing server endpoints...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/",
        "/api/assets",
        "/api/metrics",
        "/api/scada/data",
        "/api/ai/analysis",
        "/api/iot/devices"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                logger.info(f"✓ {endpoint} - OK")
            else:
                logger.warning(f"⚠ {endpoint} - Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ {endpoint} - Error: {e}")

def create_demo_script():
    """Create a demo script for the digital twin"""
    demo_script = '''#!/usr/bin/env python3
"""
Demo script for Indian EHV Substation Digital Twin
Shows how to interact with the digital twin via API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def demo_digital_twin():
    """Demonstrate digital twin capabilities"""
    print("🇮🇳 Indian EHV Substation Digital Twin Demo")
    print("=" * 60)
    
    # Test basic endpoints
    print("\\n1. Testing basic endpoints...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✓ Root endpoint: {response.json()['message']}")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
        return
    
    # Get asset status
    print("\\n2. Getting asset status...")
    try:
        response = requests.get(f"{BASE_URL}/api/assets")
        assets = response.json()
        print(f"✓ Found {len(assets)} assets")
        for asset_id, asset in list(assets.items())[:3]:  # Show first 3
            print(f"  - {asset_id}: {asset['status']} ({asset['health_score']:.1f}%)")
    except Exception as e:
        print(f"✗ Assets endpoint failed: {e}")
    
    # Get substation metrics
    print("\\n3. Getting substation metrics...")
    try:
        response = requests.get(f"{BASE_URL}/api/metrics")
        metrics = response.json()
        print(f"✓ Total Power: {metrics['total_power']:.1f} MW")
        print(f"✓ Efficiency: {metrics['efficiency']:.1f}%")
        print(f"✓ Voltage Stability: {metrics['voltage_stability']:.1f}%")
    except Exception as e:
        print(f"✗ Metrics endpoint failed: {e}")
    
    # Get SCADA data
    print("\\n4. Getting SCADA data...")
    try:
        response = requests.get(f"{BASE_URL}/api/scada/data")
        scada_data = response.json()
        print(f"✓ SCADA points: {len(scada_data['scada_data'])}")
        print(f"✓ IoT devices: {len(scada_data['iot_data'])}")
    except Exception as e:
        print(f"✗ SCADA endpoint failed: {e}")
    
    # Get AI analysis
    print("\\n5. Getting AI analysis...")
    try:
        response = requests.get(f"{BASE_URL}/api/ai/analysis")
        analysis = response.json()
        print(f"✓ Anomalies detected: {len(analysis.get('anomalies', []))}")
        print(f"✓ Predictions: {len(analysis.get('predictions', []))}")
        print(f"✓ Optimization score: {analysis.get('optimization', {}).get('optimization_score', 0):.1f}")
    except Exception as e:
        print(f"✗ AI analysis endpoint failed: {e}")
    
    # Get IoT devices
    print("\\n6. Getting IoT devices...")
    try:
        response = requests.get(f"{BASE_URL}/api/iot/devices")
        devices = response.json()
        print(f"✓ IoT devices: {len(devices)}")
        for device_id, device in list(devices.items())[:3]:  # Show first 3
            print(f"  - {device_id}: {device['device_type']} ({device['status']})")
    except Exception as e:
        print(f"✗ IoT devices endpoint failed: {e}")
    
    print("\\n" + "=" * 60)
    print("🎉 Digital Twin Demo completed successfully!")
    print("🌐 Dashboard: http://localhost:8000/dashboard")
    print("📚 API Docs: http://localhost:8000/docs")

if __name__ == "__main__":
    demo_digital_twin()
'''
    
    with open("demo_digital_twin.py", "w") as f:
        f.write(demo_script)
    
    logger.info("✓ Demo script created: demo_digital_twin.py")

def main():
    """Main startup function"""
    print("🚀 Starting Indian EHV Substation Digital Twin")
    print("=" * 60)
    
    # Check dependencies
    check_dependencies()
    
    # Test components
    if not test_digital_twin_components():
        logger.error("Component tests failed. Exiting.")
        sys.exit(1)
    
    # Create demo script
    create_demo_script()
    
    # Start server
    server_process = start_digital_twin_server()
    
    if server_process:
        print("\n" + "=" * 60)
        print("🎉 Digital Twin System Started Successfully!")
        print("=" * 60)
        print("🌐 Web Dashboard: http://localhost:8000/dashboard")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🔌 WebSocket: ws://localhost:8000/ws")
        print("📊 Demo Script: python3 demo_digital_twin.py")
        print("\n📋 Available API Endpoints:")
        print("  • GET  /api/assets - Asset status")
        print("  • GET  /api/metrics - Substation metrics")
        print("  • GET  /api/scada/data - SCADA data")
        print("  • GET  /api/ai/analysis - AI analysis")
        print("  • GET  /api/iot/devices - IoT devices")
        print("  • POST /api/control - Control assets")
        print("  • POST /api/faults/analyze - Fault analysis")
        print("\n🛑 Press Ctrl+C to stop the server")
        
        try:
            # Keep the server running
            server_process.wait()
        except KeyboardInterrupt:
            logger.info("Shutting down Digital Twin...")
            server_process.terminate()
            server_process.wait()
            logger.info("Digital Twin stopped")
    else:
        logger.error("Failed to start Digital Twin server")
        sys.exit(1)

if __name__ == "__main__":
    main()