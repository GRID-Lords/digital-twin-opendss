#!/usr/bin/env python3
"""
Demo script for Indian EHV Substation Digital Twin
Shows how to interact with the digital twin via API
"""

import requests
import json
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

BASE_URL = "http://localhost:8000"

def demo_digital_twin():
    """Demonstrate digital twin capabilities"""
    print("🇮🇳 Indian EHV Substation Digital Twin Demo")
    print("=" * 60)
    
    # Test basic endpoints
    print("\n1. Testing basic endpoints...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✓ Root endpoint: {response.json()['message']}")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
        return
    
    # Get asset status
    print("\n2. Getting asset status...")
    try:
        response = requests.get(f"{BASE_URL}/api/assets", timeout=5)
        assets = response.json()
        print(f"✓ Found {len(assets)} assets")
        for asset_id, asset in list(assets.items())[:3]:  # Show first 3
            print(f"  - {asset_id}: {asset['status']} ({asset['health_score']:.1f}%)")
    except Exception as e:
        print(f"✗ Assets endpoint failed: {e}")
    
    # Get substation metrics
    print("\n3. Getting substation metrics...")
    try:
        response = requests.get(f"{BASE_URL}/api/metrics", timeout=5)
        metrics = response.json()
        print(f"✓ Total Power: {metrics['total_power']:.1f} MW")
        print(f"✓ Efficiency: {metrics['efficiency']:.1f}%")
        print(f"✓ Voltage Stability: {metrics['voltage_stability']:.1f}%")
    except Exception as e:
        print(f"✗ Metrics endpoint failed: {e}")
    
    # Get SCADA data
    print("\n4. Getting SCADA data...")
    try:
        response = requests.get(f"{BASE_URL}/api/scada/data", timeout=5)
        scada_data = response.json()
        print(f"✓ SCADA points: {len(scada_data['scada_data'])}")
        print(f"✓ IoT devices: {len(scada_data['iot_data'])}")
    except Exception as e:
        print(f"✗ SCADA endpoint failed: {e}")
    
    # Get AI analysis
    print("\n5. Getting AI analysis...")
    try:
        response = requests.get(f"{BASE_URL}/api/ai/analysis", timeout=5)
        analysis = response.json()
        print(f"✓ Anomalies detected: {len(analysis.get('anomalies', []))}")
        print(f"✓ Predictions: {len(analysis.get('predictions', []))}")
        print(f"✓ Optimization score: {analysis.get('optimization', {}).get('optimization_score', 0):.1f}")
    except Exception as e:
        print(f"✗ AI analysis endpoint failed: {e}")
    
    # Get IoT devices
    print("\n6. Getting IoT devices...")
    try:
        response = requests.get(f"{BASE_URL}/api/iot/devices", timeout=5)
        devices = response.json()
        print(f"✓ IoT devices: {len(devices)}")
        for device_id, device in list(devices.items())[:3]:  # Show first 3
            print(f"  - {device_id}: {device['device_type']} ({device['status']})")
    except Exception as e:
        print(f"✗ IoT devices endpoint failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Digital Twin Demo completed successfully!")
    print("🌐 Dashboard: http://localhost:8000/dashboard")
    print("📚 API Docs: http://localhost:8000/docs")

if __name__ == "__main__":
    demo_digital_twin()