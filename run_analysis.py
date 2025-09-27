#!/usr/bin/env python3
"""
Simple script to run the OpenDSS analysis
"""

import subprocess
import sys
import os
import importlib.util
from pathlib import Path

def check_and_install_requirements():
    """Check and install required packages"""
    print("Checking Python packages...")
    
    requirements = [
        'opendssdirect.py>=0.9.1',
        'networkx>=3.0',
        'matplotlib>=3.7.0',
        'pandas>=2.0.0',
        'numpy>=1.21.0',
        'seaborn>=0.12.0'
    ]

    # Map pip package names to import names to avoid heavy imports during checks
    pip_to_import = {
        'opendssdirect.py': 'opendssdirect',
        'networkx': 'networkx',
        'matplotlib': 'matplotlib',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'seaborn': 'seaborn',
    }
    
    missing_packages = []
    
    for requirement in requirements:
        package_name = requirement.split('>=')[0].split('==')[0]
        import_name = pip_to_import.get(package_name, package_name).replace('-', '_')

        if importlib.util.find_spec(import_name) is not None:
            print(f"✓ {package_name} is installed")
        else:
            missing_packages.append(requirement)
            print(f"✗ {package_name} is missing")
    
    if missing_packages:
        print(f"\nInstalling missing packages into current interpreter: {sys.executable}")
        print(f"Packages: {missing_packages}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check'
            ] + missing_packages)
            print("✓ All packages installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {e}")
            return False
    
    return True

def main():
    """Main function"""
    print("OpenDSS Circuit Analysis Setup")
    print("=" * 40)

    # Force headless plotting to avoid GUI blocking on Windows/CI
    os.environ.setdefault('MPLBACKEND', 'Agg')
    
    # Check if DSS file exists
    dss_file = Path("SubstationSim.dss")
    if not dss_file.exists():
        print(f"Error: {dss_file} not found!")
        print("Please make sure the SubstationSim.dss file is in the current directory.")
        return
    
    # Check and install requirements
    if not check_and_install_requirements():
        print("Failed to install required packages. Exiting...")
        return
    
    print("\n" + "=" * 40)
    print("Starting Circuit Analysis...")
    
    # Import and run the visualizer
    try:
        from circuit_visualizer import main as run_visualizer
        run_visualizer()
    except Exception as e:
        print(f"Error running analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()