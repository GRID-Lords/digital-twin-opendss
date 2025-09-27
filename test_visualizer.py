#!/usr/bin/env python3
"""
Test script for OpenDSS Circuit Visualizer
"""

import os
import sys
from pathlib import Path

# Set environment variables for headless operation
os.environ['MPLBACKEND'] = 'Agg'
os.environ['DISPLAY'] = ''

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing package imports...")
    
    try:
        import matplotlib
        matplotlib.use('Agg', force=True)
        import matplotlib.pyplot as plt
        print("✓ matplotlib imported successfully")
    except ImportError as e:
        print(f"✗ matplotlib import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ numpy imported successfully")
    except ImportError as e:
        print(f"✗ numpy import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✓ pandas imported successfully")
    except ImportError as e:
        print(f"✗ pandas import failed: {e}")
        return False
    
    try:
        import networkx as nx
        print("✓ networkx imported successfully")
    except ImportError as e:
        print(f"✗ networkx import failed: {e}")
        return False
    
    try:
        import seaborn as sns
        print("✓ seaborn imported successfully")
    except ImportError as e:
        print(f"✗ seaborn import failed: {e}")
        return False
    
    try:
        import opendssdirect as dss
        print("✓ opendssdirect imported successfully")
    except ImportError as e:
        print(f"✗ opendssdirect import failed: {e}")
        return False
    
    return True

def test_basic_plotting():
    """Test basic matplotlib functionality"""
    print("\nTesting basic plotting...")
    
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Create a simple test plot
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        ax.plot(x, y)
        ax.set_title('Test Plot')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        
        # Save the plot
        test_file = Path('test_plot.png')
        plt.savefig(test_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        if test_file.exists():
            print("✓ Basic plotting test passed")
            test_file.unlink()  # Clean up
            return True
        else:
            print("✗ Plot file was not created")
            return False
            
    except Exception as e:
        print(f"✗ Basic plotting test failed: {e}")
        return False

def test_networkx():
    """Test networkx functionality"""
    print("\nTesting networkx...")
    
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
        
        # Create a simple graph
        G = nx.Graph()
        G.add_node('A', voltage=1.0)
        G.add_node('B', voltage=0.98)
        G.add_edge('A', 'B')
        
        # Create a simple plot
        fig, ax = plt.subplots(1, 1, figsize=(6, 4))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, ax=ax, with_labels=True)
        ax.set_title('Test Network')
        
        # Save the plot
        test_file = Path('test_network.png')
        plt.savefig(test_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        if test_file.exists():
            print("✓ Networkx test passed")
            test_file.unlink()  # Clean up
            return True
        else:
            print("✗ Network plot file was not created")
            return False
            
    except Exception as e:
        print(f"✗ Networkx test failed: {e}")
        return False

def test_opendss():
    """Test OpenDSS functionality"""
    print("\nTesting OpenDSS...")
    
    try:
        import opendssdirect as dss
        
        # Test basic OpenDSS commands
        dss.run_command("Clear")
        dss.run_command("Set NoForms=Yes")
        dss.run_command("Set ShowExport=Yes")
        
        print("✓ OpenDSS basic commands work")
        return True
        
    except Exception as e:
        print(f"✗ OpenDSS test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("OpenDSS Circuit Visualizer - Test Suite")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed - missing packages")
        return False
    
    # Test basic plotting
    if not test_basic_plotting():
        print("\n❌ Basic plotting test failed")
        return False
    
    # Test networkx
    if not test_networkx():
        print("\n❌ Networkx test failed")
        return False
    
    # Test OpenDSS
    if not test_opendss():
        print("\n❌ OpenDSS test failed")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! The visualizer should work correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)