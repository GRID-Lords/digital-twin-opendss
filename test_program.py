#!/usr/bin/env python3
"""
Test script to verify the OpenDSS Circuit Visualizer works correctly
"""

import os
import sys
from pathlib import Path

# Set environment for headless operation
os.environ['MPLBACKEND'] = 'Agg'
os.environ['DISPLAY'] = ''

def test_visualizer():
    """Test the circuit visualizer"""
    print("Testing OpenDSS Circuit Visualizer...")
    print("=" * 50)
    
    try:
        # Import and run the visualizer
        from circuit_visualizer import main as run_visualizer
        run_visualizer()
        
        # Check if results were generated
        results_dir = Path("/workspace/visualization_results")
        expected_files = [
            'circuit_diagram.png',
            'electrical_schematic.png', 
            'power_analysis.png',
            'voltage_analysis.png',
            'power_data.csv',
            'voltage_data.csv',
            'analysis_report.txt'
        ]
        
        print(f"\nChecking generated files in: {results_dir}")
        print(f"Directory exists: {results_dir.exists()}")
        all_files_exist = True
        for file in expected_files:
            file_path = results_dir / file
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"✓ {file} ({size:,} bytes)")
            else:
                print(f"✗ {file} - Missing! (Looking for: {file_path})")
                all_files_exist = False
        
        if all_files_exist:
            print("\n✅ All tests passed! The visualizer is working correctly.")
            print(f"Results saved in: {results_dir.absolute()}")
            return True
        else:
            print("\n❌ Some files are missing.")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_visualizer()
    sys.exit(0 if success else 1)