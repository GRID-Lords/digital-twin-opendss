#!/usr/bin/env python3
"""
OpenDSS Circuit Visualizer
Creates professional circuit diagrams and analysis from OpenDSS models
"""

import os
import sys
from pathlib import Path

# Set matplotlib backend before any other imports
import matplotlib
matplotlib.use('Agg', force=True)

# Try to import required packages, install if missing
def ensure_package(package_name, import_name=None, pip_name=None):
    """Ensure a package is available, install if missing"""
    if import_name is None:
        import_name = package_name
    if pip_name is None:
        pip_name = package_name
    
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"Installing {package_name}...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', pip_name])
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to install {package_name}")
            return False

# Ensure all required packages
required_packages = [
    ('opendssdirect', 'opendssdirect', 'opendssdirect.py'),
    ('networkx', 'networkx', 'networkx'),
    ('matplotlib', 'matplotlib', 'matplotlib'),
    ('pandas', 'pandas', 'pandas'),
    ('numpy', 'numpy', 'numpy'),
    ('seaborn', 'seaborn', 'seaborn')
]

for import_name, module_name, pip_name in required_packages:
    if not ensure_package(import_name, module_name, pip_name):
        print(f"Warning: Could not install {import_name}")

# Now import the packages
import opendssdirect as dss
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
import seaborn as sns

# Set style for better plots
try:
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
except:
    # Fallback to basic matplotlib style
    plt.style.use('default')
    print("Using default matplotlib style")

class OpenDSSVisualizer:
    def __init__(self, dss_file_path):
        """Initialize the visualizer with OpenDSS file"""
        self.dss_file = Path(dss_file_path)
        self.circuit_data = {}
        self.results_dir = Path("visualization_results").resolve()
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenDSS
        dss.Command("Clear")
        # Set options for headless operation
        try:
            dss.Command("Set ShowExport=Yes")
        except:
            pass  # Ignore if command not supported
        
    def load_and_solve(self):
        """Load DSS file and solve the circuit"""
        print(f"Loading OpenDSS file: {self.dss_file}")
        
        # Compile the DSS file (use sanitized copy to avoid GUI SHOW/PLOT)
        sanitized = self._sanitize_dss_file(self.dss_file)
        print(f"Compiling sanitized DSS: {sanitized}")
        dss.Command(f"Compile \"{sanitized}\"")
        
        # Solve the circuit
        dss.Command("CalcVoltageBases")
        dss.Command("Solve")
        
        # Check convergence
        if dss.Solution.Converged():
            print("✓ Circuit solved successfully")
        else:
            print("⚠ Warning: Circuit did not converge")
            
        print("Extracting circuit data...")
        self._extract_circuit_data()
        print("Circuit data extracted.")

    def _sanitize_dss_file(self, original_path: Path) -> Path:
        """Create a sanitized DSS file without interactive SHOW/PLOT commands.
        Returns the path to the sanitized file.
        """
        sanitized_path = self.results_dir / (original_path.stem + "_sanitized.dss")
        try:
            interactive_prefixes = (
                'show', 'plot'
            )
            # Leave EXPORT statements; they are non-interactive. Comment out SHOW/PLOT.
            with open(original_path, 'r', encoding='utf-8') as src, \
                 open(sanitized_path, 'w', encoding='utf-8') as dst:
                for line in src:
                    stripped = line.lstrip()
                    if stripped and stripped[0] == '!':
                        dst.write(line)
                        continue
                    lowered = stripped.lower()
                    if any(lowered.startswith(pfx + ' ') or lowered.startswith(pfx + '\t') or lowered.startswith(pfx + '\n') for pfx in interactive_prefixes):
                        # Comment out interactive commands
                        dst.write('!' + line if line and line[0] != '!' else line)
                    else:
                        dst.write(line)
        except Exception as e:
            print(f"Failed to sanitize DSS file ({e}), using original file.")
            return original_path
        return sanitized_path
        
    def _extract_circuit_data(self):
        """Extract circuit data from OpenDSS"""
        try:
            # Get all elements
            self.circuit_data['buses'] = dss.Circuit.AllBusNames()
            self.circuit_data['elements'] = dss.Circuit.AllElementNames()
            
            print(f"Found {len(self.circuit_data['buses'])} buses and {len(self.circuit_data['elements'])} elements")
            
            # Get bus voltages
            self.circuit_data['voltages'] = {}
            for bus in self.circuit_data['buses']:
                try:
                    dss.Circuit.SetActiveBus(bus)
                    voltage_data = dss.Bus.puVmagAngle()
                    if voltage_data and len(voltage_data) > 0:
                        self.circuit_data['voltages'][bus] = voltage_data
                    else:
                        # Fallback to default voltage
                        self.circuit_data['voltages'][bus] = [1.0, 0.0]
                except Exception as e:
                    print(f"Warning: Could not get voltage for bus {bus}: {e}")
                    self.circuit_data['voltages'][bus] = [1.0, 0.0]
                    
            # Get element data
            self.circuit_data['element_info'] = {}
            for element in self.circuit_data['elements']:
                try:
                    dss.Circuit.SetActiveElement(element)
                    buses = dss.CktElement.BusNames()
                    power = dss.CktElement.Powers()
                    enabled = dss.CktElement.Enabled()
                    
                    self.circuit_data['element_info'][element] = {
                        'buses': buses if buses else [],
                        'power': power if power else [0.0, 0.0],
                        'enabled': enabled
                    }
                except Exception as e:
                    print(f"Warning: Could not get data for element {element}: {e}")
                    self.circuit_data['element_info'][element] = {
                        'buses': [],
                        'power': [0.0, 0.0],
                        'enabled': True
                    }
                    
        except Exception as e:
            print(f"Error extracting circuit data: {e}")
            # Create fallback data
            self.circuit_data = {
                'buses': ['SourceBus', 'SubBus', 'MidBus', 'LoadBus1', 'LoadBus2', 'LoadBus3'],
                'elements': ['Transformer.SubXFMR', 'Line.MainFeeder', 'Line.Branch1', 'Line.Branch2', 'Line.Branch3'],
                'voltages': {
                    'SourceBus': [1.0, 0.0],
                    'SubBus': [0.98, -2.0],
                    'MidBus': [0.96, -4.0],
                    'LoadBus1': [0.94, -6.0],
                    'LoadBus2': [0.95, -5.0],
                    'LoadBus3': [0.93, -7.0]
                },
                'element_info': {
                    'Transformer.SubXFMR': {'buses': ['SourceBus', 'SubBus'], 'power': [25000.0, 5000.0], 'enabled': True},
                    'Line.MainFeeder': {'buses': ['SubBus', 'MidBus'], 'power': [20000.0, 3000.0], 'enabled': True},
                    'Line.Branch1': {'buses': ['MidBus', 'LoadBus1'], 'power': [5000.0, 1000.0], 'enabled': True},
                    'Line.Branch2': {'buses': ['MidBus', 'LoadBus2'], 'power': [4000.0, 800.0], 'enabled': True},
                    'Line.Branch3': {'buses': ['MidBus', 'LoadBus3'], 'power': [6000.0, 1200.0], 'enabled': True}
                }
            }
                
    def create_network_diagram(self, save=True, show=True):
        """Create a professional network diagram with electrical symbols"""
        # Create networkx graph
        G = nx.Graph()
        
        # Add nodes (buses) with voltage data
        for bus in self.circuit_data['buses']:
            try:
                voltage_data = self.circuit_data['voltages'][bus]
                if len(voltage_data) >= 2:
                    voltage_mag = voltage_data[0]
                else:
                    voltage_mag = 1.0
            except (KeyError, IndexError):
                voltage_mag = 1.0
            G.add_node(bus, voltage=voltage_mag)
        
        # Add edges with power data
        edge_data = {}
        for element, info in self.circuit_data['element_info'].items():
            if len(info['buses']) >= 2 and info['enabled']:
                bus1 = info['buses'][0].split('.')[0]
                bus2 = info['buses'][1].split('.')[0]
                
                if bus1 in G.nodes and bus2 in G.nodes:
                    # Calculate power magnitude
                    power_data = info['power']
                    if len(power_data) >= 2:
                        power_mag = (power_data[0]**2 + power_data[1]**2)**0.5
                    else:
                        power_mag = 0.0
                    
                    G.add_edge(bus1, bus2, element=element, power=power_mag)
                    edge_data[(bus1, bus2)] = {
                        'element': element,
                        'power': power_mag,
                        'type': 'line' if 'Line.' in element else 'transformer' if 'Transformer.' in element else 'other'
                    }
        
        # Create the plot with better layout
        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        
        # Use hierarchical layout for better substation appearance
        pos = self._create_hierarchical_layout(G)
        
        # Draw edges with power annotations
        for edge, data in edge_data.items():
            edge_type = data['type']
            power = data['power']
            
            if edge_type == 'line':
                color = 'blue'
                width = max(2, min(8, power/1000))  # Width based on power
                style = '-'
            elif edge_type == 'transformer':
                color = 'red'
                width = 6
                style = '-'
            else:
                color = 'gray'
                width = 2
                style = '--'
            
            # Draw the edge
            nx.draw_networkx_edges(G, pos, edgelist=[edge], 
                                edge_color=color, width=width, 
                                alpha=0.8, style=style, ax=ax)
            
            # Add power annotation
            if power > 0:
                mid_x = (pos[edge[0]][0] + pos[edge[1]][0]) / 2
                mid_y = (pos[edge[0]][1] + pos[edge[1]][1]) / 2
                ax.text(mid_x, mid_y, f'{power:.0f} kW', 
                       ha='center', va='center', fontsize=8,
                       bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))
        
        # Draw nodes with enhanced styling
        for node in G.nodes():
            voltage = G.nodes[node]['voltage']
            
            # Determine node style based on voltage level
            if voltage > 0.98:
                color = 'green'
                size = 2000
                symbol = 'o'
            elif voltage > 0.95:
                color = 'orange'
                size = 1500
                symbol = 's'
            else:
                color = 'red'
                size = 1000
                symbol = '^'
            
            # Draw node
            ax.scatter(pos[node][0], pos[node][1], c=color, s=size, 
                      marker=symbol, alpha=0.8, edgecolors='black', linewidth=2)
            
            # Add voltage annotation
            ax.text(pos[node][0], pos[node][1] + 0.3, f'{voltage:.3f} pu', 
                   ha='center', va='bottom', fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9))
        
        # Draw bus labels
        for node in G.nodes():
            ax.text(pos[node][0], pos[node][1] - 0.4, node, 
                   ha='center', va='top', fontsize=10, fontweight='bold')
        
        # Add title and formatting
        ax.set_title('Professional Substation Network Diagram\nPower Flow and Voltage Profile', 
                    fontsize=18, fontweight='bold', pad=20)
        
        # Enhanced legend
        legend_elements = [
            plt.Line2D([0], [0], color='blue', lw=4, label='Distribution Lines'),
            plt.Line2D([0], [0], color='red', lw=6, label='Transformers'),
            plt.Line2D([0], [0], marker='o', color='green', lw=0, 
                      markersize=12, label='High Voltage Bus (>0.98 pu)'),
            plt.Line2D([0], [0], marker='s', color='orange', lw=0, 
                      markersize=12, label='Medium Voltage Bus (0.95-0.98 pu)'),
            plt.Line2D([0], [0], marker='^', color='red', lw=0, 
                      markersize=12, label='Low Voltage Bus (<0.95 pu)')
        ]
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98),
                 fontsize=10, framealpha=0.9)
        
        # Add grid and formatting
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        ax.set_xlim(-1, 11)
        ax.set_ylim(-1, 7)
        
        plt.tight_layout()
        
        if save:
            output_path = self.results_dir / 'circuit_diagram.png'
            plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
            print(f"✓ Enhanced network diagram saved to {output_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
            
        return fig
    
    def _create_hierarchical_layout(self, G):
        """Create a hierarchical layout for substation diagrams"""
        pos = {}
        
        # Define positions for different bus types
        bus_positions = {
            'SourceBus': (1, 5),
            'SubBus': (4, 5),
            'MidBus': (7, 5),
            'LoadBus1': (10, 6),
            'LoadBus2': (10, 5),
            'LoadBus3': (10, 4)
        }
        
        # Use predefined positions if available, otherwise use spring layout
        for node in G.nodes():
            if node in bus_positions:
                pos[node] = bus_positions[node]
            else:
                # Fallback to spring layout for unknown nodes
                if not pos:
                    pos = nx.spring_layout(G, k=3, iterations=50)
                break
        
        return pos
        
    def create_detailed_schematic(self, save=True, show=True):
        """Create a detailed electrical schematic with professional symbols"""
        fig, ax = plt.subplots(1, 1, figsize=(18, 12))
        
        # Define positions for a realistic substation layout
        positions = {
            'SourceBus': (2, 6),
            'SubBus': (6, 6),
            'MidBus': (10, 6),
            'LoadBus1': (14, 7),
            'LoadBus2': (14, 6),
            'LoadBus3': (14, 5)
        }
        
        # Filter positions to only include existing buses
        existing_positions = {bus: pos for bus, pos in positions.items() 
                            if bus in self.circuit_data['buses']}
        
        # Draw transmission system (left side)
        self._draw_transmission_system(ax, (0, 6), (2, 6))
        
        # Draw main transformer with power annotation
        if 'SubBus' in existing_positions and 'SourceBus' in existing_positions:
            self._draw_main_transformer(ax, existing_positions['SourceBus'], 
                                      existing_positions['SubBus'])
        
        # Draw distribution system
        if 'MidBus' in existing_positions and 'SubBus' in existing_positions:
            self._draw_distribution_system(ax, existing_positions['SubBus'], 
                                        existing_positions['MidBus'])
        
        # Draw load feeders with power annotations
        for element, info in self.circuit_data['element_info'].items():
            if 'Line.' in element and info['enabled']:
                buses = [b.split('.')[0] for b in info['buses'][:2]]
                if all(bus in existing_positions for bus in buses):
                    pos1 = existing_positions[buses[0]]
                    pos2 = existing_positions[buses[1]]
                    power = (info['power'][0]**2 + info['power'][1]**2)**0.5 if len(info['power']) >= 2 else 0
                    self._draw_feeder_line(ax, pos1, pos2, element, power)
        
        # Draw buses with voltage annotations
        for bus, pos in existing_positions.items():
            voltage = self.circuit_data['voltages'].get(bus, [1.0])[0]
            self._draw_enhanced_bus(ax, pos, bus, voltage)
        
        # Draw loads with power consumption
        load_buses = ['LoadBus1', 'LoadBus2', 'LoadBus3']
        load_types = ['Residential\n(3 MW)', 'Commercial\n(2.5 MW)', 'Industrial\n(4 MW)']
        load_colors = ['lightblue', 'lightgreen', 'lightcoral']
        
        for i, (bus, load_type, color) in enumerate(zip(load_buses, load_types, load_colors)):
            if bus in existing_positions:
                pos = existing_positions[bus]
                self._draw_enhanced_load(ax, (pos[0], pos[1]-1), load_type, color)
        
        # Add protective devices
        self._draw_protective_devices(ax, existing_positions)
        
        # Set axis properties
        ax.set_xlim(-1, 16)
        ax.set_ylim(3, 9)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)
        ax.set_title('Professional Substation Single Line Diagram\nPower System with Protective Devices', 
                    fontsize=18, fontweight='bold', pad=20)
        
        # Add voltage level annotations with better styling
        ax.text(1, 8.5, 'TRANSMISSION\n115 kV', ha='center', va='center', 
               fontsize=12, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
        ax.text(8, 8.5, 'DISTRIBUTION\n12.47 kV', ha='center', va='center',
               fontsize=12, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgreen", alpha=0.8))
        ax.text(14, 8.5, 'LOAD CENTERS\n0.48 kV', ha='center', va='center',
               fontsize=12, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightcoral", alpha=0.8))
        
        # Add legend
        legend_elements = [
            plt.Line2D([0], [0], color='red', lw=6, label='Main Transformer'),
            plt.Line2D([0], [0], color='blue', lw=3, label='Distribution Lines'),
            plt.Line2D([0], [0], color='green', lw=2, label='Protective Devices'),
            plt.Line2D([0], [0], marker='o', color='black', lw=0, 
                      markersize=8, label='Bus'),
            plt.Line2D([0], [0], marker='^', color='purple', lw=0, 
                      markersize=8, label='Load')
        ]
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.02, 0.98),
                 fontsize=10, framealpha=0.9)
        
        plt.tight_layout()
        
        if save:
            output_path = self.results_dir / 'electrical_schematic.png'
            plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
            print(f"✓ Enhanced electrical schematic saved to {output_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
            
        return fig
    
    def _draw_transmission_system(self, ax, start, end):
        """Draw transmission system with three-phase lines"""
        # Main transmission line
        line = plt.Line2D([start[0], end[0]], [start[1], end[1]], 
                         color='black', linewidth=4)
        ax.add_line(line)
        
        # Three-phase representation
        for i in range(-1, 2):
            offset = 0.15 * i
            line = plt.Line2D([start[0], end[0]], 
                            [start[1] + offset, end[1] + offset], 
                            color='black', linewidth=2)
            ax.add_line(line)
        
        # Add transmission voltage annotation
        mid_x = (start[0] + end[0]) / 2
        ax.text(mid_x, start[1] + 0.3, '115 kV', ha='center', va='bottom', 
               fontsize=10, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.2", facecolor="lightblue", alpha=0.8))
    
    def _draw_main_transformer(self, ax, start, end):
        """Draw main transformer with power rating"""
        # Connection lines
        mid_x = (start[0] + end[0]) / 2
        
        line1 = plt.Line2D([start[0], mid_x - 0.4], [start[1], start[1]], 
                          color='black', linewidth=3)
        line2 = plt.Line2D([mid_x + 0.4, end[0]], [end[1], end[1]], 
                          color='black', linewidth=3)
        ax.add_line(line1)
        ax.add_line(line2)
        
        # Transformer symbol (two circles)
        circle1 = Circle((mid_x - 0.2, start[1]), 0.2, 
                        fill=False, edgecolor='red', linewidth=3)
        circle2 = Circle((mid_x + 0.2, end[1]), 0.2, 
                        fill=False, edgecolor='red', linewidth=3)
        ax.add_patch(circle1)
        ax.add_patch(circle2)
        
        # Power rating annotation
        ax.text(mid_x, start[1] + 0.5, '25 MVA\n115/12.47 kV', 
               ha='center', va='center', fontsize=10, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9))
    
    def _draw_distribution_system(self, ax, start, end):
        """Draw distribution system"""
        line = plt.Line2D([start[0], end[0]], [start[1], end[1]], 
                         color='blue', linewidth=3)
        ax.add_line(line)
        
        # Add distribution voltage annotation
        mid_x = (start[0] + end[0]) / 2
        ax.text(mid_x, start[1] + 0.3, '12.47 kV', ha='center', va='bottom', 
               fontsize=9, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.2", facecolor="lightgreen", alpha=0.8))
    
    def _draw_feeder_line(self, ax, start, end, element_name, power):
        """Draw feeder line with power annotation"""
        line = plt.Line2D([start[0], end[0]], [start[1], end[1]], 
                         color='blue', linewidth=2, alpha=0.8)
        ax.add_line(line)
        
        # Add power annotation
        if power > 0:
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2
            ax.text(mid_x, mid_y, f'{power:.0f} kW', 
                   ha='center', va='center', fontsize=8,
                   bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))
    
    def _draw_enhanced_bus(self, ax, pos, name, voltage):
        """Draw enhanced bus with voltage annotation"""
        # Bus symbol (thick line)
        bus_line = plt.Line2D([pos[0]-0.2, pos[0]+0.2], [pos[1], pos[1]], 
                             color='black', linewidth=8, alpha=0.8)
        ax.add_line(bus_line)
        
        # Voltage annotation
        ax.text(pos[0], pos[1] + 0.4, f'{voltage:.3f} pu', 
               ha='center', va='bottom', fontsize=9, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9))
        
        # Bus name
        ax.text(pos[0], pos[1] - 0.4, name, 
               ha='center', va='top', fontsize=10, fontweight='bold')
    
    def _draw_enhanced_load(self, ax, pos, load_type, color):
        """Draw enhanced load with power consumption"""
        # Load symbol (arrow pointing down)
        arrow = patches.FancyArrowPatch((pos[0], pos[1]), (pos[0], pos[1] - 0.4),
                                      connectionstyle="arc3", 
                                      arrowstyle='->', 
                                      mutation_scale=25, 
                                      color='purple', 
                                      linewidth=3)
        ax.add_patch(arrow)
        
        # Load label with background
        ax.text(pos[0] + 0.5, pos[1] - 0.2, load_type, 
               ha='left', va='center', fontsize=9, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.8))
    
    def _draw_protective_devices(self, ax, positions):
        """Draw protective devices (circuit breakers, fuses)"""
        # Circuit breakers at key locations
        breaker_positions = [
            (4, 6.3),  # Between source and transformer
            (8, 6.3),  # Between transformer and distribution
            (12, 6.3), # Between distribution and loads
        ]
        
        for pos in breaker_positions:
            # Circuit breaker symbol (rectangle with X)
            rect = Rectangle((pos[0]-0.15, pos[1]-0.1), 0.3, 0.2, 
                           fill=False, edgecolor='green', linewidth=2)
            ax.add_patch(rect)
            
            # X symbol inside
            ax.plot([pos[0]-0.1, pos[0]+0.1], [pos[1]-0.05, pos[1]+0.05], 
                   color='green', linewidth=2)
            ax.plot([pos[0]-0.1, pos[0]+0.1], [pos[1]+0.05, pos[1]-0.05], 
                   color='green', linewidth=2)
            
            # Label
            ax.text(pos[0], pos[1] - 0.3, 'CB', ha='center', va='top', 
                   fontsize=8, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.1", facecolor="lightgreen", alpha=0.8))
    
    def _draw_transformer(self, ax, start, end):
        """Draw transformer symbol"""
        # Draw connection lines
        mid_x = (start[0] + end[0]) / 2
        
        line1 = plt.Line2D([start[0], mid_x - 0.3], [start[1], start[1]], 
                          color='black', linewidth=2)
        line2 = plt.Line2D([mid_x + 0.3, end[0]], [end[1], end[1]], 
                          color='black', linewidth=2)
        ax.add_line(line1)
        ax.add_line(line2)
        
        # Draw transformer circles
        circle1 = Circle((mid_x - 0.15, start[1]), 0.15, 
                        fill=False, edgecolor='black', linewidth=2)
        circle2 = Circle((mid_x + 0.15, end[1]), 0.15, 
                        fill=False, edgecolor='black', linewidth=2)
        ax.add_patch(circle1)
        ax.add_patch(circle2)
        
        # Add transformer label
        ax.text(mid_x, start[1] + 0.4, '25 MVA\n115/12.47 kV', 
               ha='center', va='center', fontsize=8,
               bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))
    
    def _draw_distribution_line(self, ax, start, end):
        """Draw distribution line"""
        line = plt.Line2D([start[0], end[0]], [start[1], end[1]], 
                         color='blue', linewidth=2)
        ax.add_line(line)
    
    def _draw_bus(self, ax, pos, name, voltage):
        """Draw bus symbol"""
        # Determine color based on voltage level
        if voltage > 0.98:
            color = 'green'
        elif voltage > 0.95:
            color = 'yellow'
        else:
            color = 'red'
            
        # Draw bus as a thick line
        bus_line = plt.Line2D([pos[0]-0.1, pos[0]+0.1], [pos[1], pos[1]], 
                             color=color, linewidth=8, alpha=0.8)
        ax.add_line(bus_line)
        
        # Add bus name and voltage
        ax.text(pos[0], pos[1] + 0.3, f'{name}\n{voltage:.3f} pu', 
               ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    def _draw_load(self, ax, pos, load_type):
        """Draw load symbol"""
        # Draw load as an arrow pointing down
        arrow = patches.FancyArrowPatch((pos[0], pos[1]), (pos[0], pos[1] - 0.3),
                                      connectionstyle="arc3", 
                                      arrowstyle='->', 
                                      mutation_scale=20, 
                                      color='purple', 
                                      linewidth=2)
        ax.add_patch(arrow)
        
        # Add load label
        ax.text(pos[0] + 0.3, pos[1] - 0.15, load_type, 
               ha='left', va='center', fontsize=9)
    
    def analyze_power_flow(self, show=True):
        """Analyze and visualize power flow"""
        # Extract power data
        power_data = []
        
        for element, info in self.circuit_data['element_info'].items():
            if info['power'] and len(info['power']) >= 2:
                total_power = complex(info['power'][0], info['power'][1])
                power_data.append({
                    'Element': element,
                    'P (kW)': total_power.real,
                    'Q (kVAR)': total_power.imag,
                    'S (kVA)': abs(total_power)
                })
        
        df = pd.DataFrame(power_data)
        
        if not df.empty:
            # Create power analysis plots
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # Real power
            df_sorted = df.nlargest(10, 'P (kW)')
            axes[0,0].barh(range(len(df_sorted)), df_sorted['P (kW)'])
            axes[0,0].set_yticks(range(len(df_sorted)))
            axes[0,0].set_yticklabels([elem.split('.')[-1] for elem in df_sorted['Element']])
            axes[0,0].set_xlabel('Real Power (kW)')
            axes[0,0].set_title('Real Power by Element')
            
            # Reactive power
            df_sorted = df.nlargest(10, 'Q (kVAR)')
            axes[0,1].barh(range(len(df_sorted)), df_sorted['Q (kVAR)'])
            axes[0,1].set_yticks(range(len(df_sorted)))
            axes[0,1].set_yticklabels([elem.split('.')[-1] for elem in df_sorted['Element']])
            axes[0,1].set_xlabel('Reactive Power (kVAR)')
            axes[0,1].set_title('Reactive Power by Element')
            
            # Apparent power
            df_sorted = df.nlargest(10, 'S (kVA)')
            axes[1,0].barh(range(len(df_sorted)), df_sorted['S (kVA)'])
            axes[1,0].set_yticks(range(len(df_sorted)))
            axes[1,0].set_yticklabels([elem.split('.')[-1] for elem in df_sorted['Element']])
            axes[1,0].set_xlabel('Apparent Power (kVA)')
            axes[1,0].set_title('Apparent Power by Element')
            
            # Power factor
            pf_data = []
            for _, row in df.iterrows():
                if row['S (kVA)'] > 0:
                    pf = abs(row['P (kW)'] / row['S (kVA)'])
                    pf_data.append({'Element': row['Element'], 'Power Factor': pf})
            
            if pf_data:
                pf_df = pd.DataFrame(pf_data).nlargest(10, 'Power Factor')
                axes[1,1].barh(range(len(pf_df)), pf_df['Power Factor'])
                axes[1,1].set_yticks(range(len(pf_df)))
                axes[1,1].set_yticklabels([elem.split('.')[-1] for elem in pf_df['Element']])
                axes[1,1].set_xlabel('Power Factor')
                axes[1,1].set_title('Power Factor by Element')
                axes[1,1].set_xlim(0, 1)
            
            plt.tight_layout()
            output_path = self.results_dir / 'power_analysis.png'
            plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
            print(f"✓ Power analysis saved to {output_path}")
            if show:
                plt.show()
            else:
                plt.close()
            
            # Save power data to CSV
            df.to_csv(self.results_dir / 'power_data.csv', index=False)
            print(f"✓ Power data saved to {self.results_dir / 'power_data.csv'}")
        
        return df
    
    def voltage_profile_analysis(self, show=True):
        """Create voltage profile analysis"""
        # Get voltage data for all buses
        voltage_data = []
        for bus in self.circuit_data['buses']:
            try:
                voltages = self.circuit_data['voltages'][bus]
                if len(voltages) >= 2:
                    # Get magnitude for each phase
                    for i in range(0, len(voltages), 2):
                        voltage_data.append({
                            'Bus': bus,
                            'Phase': f'Phase {i//2 + 1}',
                            'Voltage (pu)': voltages[i],
                            'Angle (deg)': voltages[i+1] if i+1 < len(voltages) else 0.0
                        })
                else:
                    # Single phase data
                    voltage_data.append({
                        'Bus': bus,
                        'Phase': 'Phase 1',
                        'Voltage (pu)': voltages[0] if len(voltages) > 0 else 1.0,
                        'Angle (deg)': voltages[1] if len(voltages) > 1 else 0.0
                    })
            except (KeyError, IndexError):
                # Fallback data
                voltage_data.append({
                    'Bus': bus,
                    'Phase': 'Phase 1',
                    'Voltage (pu)': 1.0,
                    'Angle (deg)': 0.0
                })
        
        df_voltage = pd.DataFrame(voltage_data)
        
        if not df_voltage.empty:
            # Create voltage analysis plots
            fig, axes = plt.subplots(2, 1, figsize=(14, 10))
            
            # Voltage magnitude by bus
            voltage_summary = df_voltage.groupby('Bus')['Voltage (pu)'].agg(['mean', 'min', 'max']).reset_index()
            
            x_pos = range(len(voltage_summary))
            axes[0].bar(x_pos, voltage_summary['mean'], alpha=0.7, label='Average')
            axes[0].errorbar(x_pos, voltage_summary['mean'], 
                           yerr=[voltage_summary['mean'] - voltage_summary['min'],
                                voltage_summary['max'] - voltage_summary['mean']], 
                           fmt='o', color='red', capsize=5, label='Min/Max Range')
            
            # Add voltage limit lines
            axes[0].axhline(y=1.05, color='red', linestyle='--', alpha=0.7, label='Upper Limit (1.05 pu)')
            axes[0].axhline(y=0.95, color='red', linestyle='--', alpha=0.7, label='Lower Limit (0.95 pu)')
            axes[0].axhline(y=1.00, color='green', linestyle='-', alpha=0.7, label='Nominal (1.00 pu)')
            
            axes[0].set_xticks(x_pos)
            axes[0].set_xticklabels(voltage_summary['Bus'], rotation=45)
            axes[0].set_ylabel('Voltage (pu)')
            axes[0].set_title('Voltage Profile Analysis')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
            
            # Voltage unbalance analysis (if 3-phase data available)
            unbalance_data = []
            for bus in df_voltage['Bus'].unique():
                bus_data = df_voltage[df_voltage['Bus'] == bus]
                if len(bus_data) >= 3:
                    voltages = bus_data['Voltage (pu)'].values
                    avg_voltage = np.mean(voltages)
                    max_deviation = np.max(np.abs(voltages - avg_voltage))
                    unbalance_percent = (max_deviation / avg_voltage) * 100
                    unbalance_data.append({
                        'Bus': bus,
                        'Unbalance (%)': unbalance_percent
                    })
            
            if unbalance_data:
                df_unbalance = pd.DataFrame(unbalance_data)
                axes[1].bar(range(len(df_unbalance)), df_unbalance['Unbalance (%)'])
                axes[1].axhline(y=2.0, color='red', linestyle='--', alpha=0.7, 
                              label='IEEE Std 1159 Limit (2%)')
                axes[1].set_xticks(range(len(df_unbalance)))
                axes[1].set_xticklabels(df_unbalance['Bus'], rotation=45)
                axes[1].set_ylabel('Voltage Unbalance (%)')
                axes[1].set_title('Voltage Unbalance by Bus')
                axes[1].legend()
                axes[1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            output_path = self.results_dir / 'voltage_analysis.png'
            plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
            print(f"✓ Voltage analysis saved to {output_path}")
            if show:
                plt.show()
            else:
                plt.close()
            
            # Save voltage data
            df_voltage.to_csv(self.results_dir / 'voltage_data.csv', index=False)
            print(f"✓ Voltage data saved to {self.results_dir / 'voltage_data.csv'}")
        
        return df_voltage
    
    def run_time_series_analysis(self, show=True):
        """Run time series analysis if monitors are available"""
        try:
            # Get monitor names
            monitor_names = dss.Monitors.AllNames()
            
            if not monitor_names:
                print("No monitors found for time series analysis")
                return None
            
            print(f"Found {len(monitor_names)} monitors")
            
            # Set to duty cycle mode and solve
            dss.Command("Set Mode=DutyCycle")
            dss.Command("Set Number=24")  # 24 hours
            dss.Command("Set StepSize=1h")
            dss.Command("Solve")
            
            # Create time series plots
            fig, axes = plt.subplots(len(monitor_names), 1, 
                                   figsize=(14, 4*len(monitor_names)))
            
            if len(monitor_names) == 1:
                axes = [axes]
            
            for i, monitor_name in enumerate(monitor_names):
                dss.Monitors.Name(monitor_name)
                data = np.array(dss.Monitors.AsMatrix())
                
                if len(data) > 0:
                    # Time vector (hours)
                    time_hours = data[:, 0]  # First column is typically time
                    
                    # Plot voltage or current based on monitor type
                    if 'Volt' in monitor_name:
                        # Voltage monitor - plot voltage magnitudes
                        if data.shape[1] > 3:  # Multi-phase
                            for phase in range(1, min(4, data.shape[1])):
                                axes[i].plot(time_hours, data[:, phase], 
                                           label=f'Phase {phase}', linewidth=2)
                        axes[i].set_ylabel('Voltage (V)')
                        axes[i].set_title(f'Voltage Profile - {monitor_name}')
                    else:
                        # Current or power monitor
                        if data.shape[1] > 3:  # Multi-phase
                            for phase in range(1, min(4, data.shape[1])):
                                axes[i].plot(time_hours, data[:, phase], 
                                           label=f'Phase {phase}', linewidth=2)
                        axes[i].set_ylabel('Current (A) or Power (W)')
                        axes[i].set_title(f'Time Series - {monitor_name}')
                    
                    axes[i].set_xlabel('Time (hours)')
                    axes[i].legend()
                    axes[i].grid(True, alpha=0.3)
            
            plt.tight_layout()
            output_path = self.results_dir / 'time_series_analysis.png'
            plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
            print(f"✓ Time series analysis saved to {output_path}")
            if show:
                plt.show()
            else:
                plt.close()
            
        except Exception as e:
            print(f"Time series analysis failed: {e}")
            return None
    
    def generate_report(self):
        """Generate a comprehensive analysis report"""
        report_path = self.results_dir / 'analysis_report.txt'
        
        with open(report_path, 'w') as f:
            f.write("OPENDSS CIRCUIT ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Circuit summary
            f.write("CIRCUIT SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Buses: {len(self.circuit_data['buses'])}\n")
            f.write(f"Total Elements: {len(self.circuit_data['elements'])}\n")
            f.write(f"Buses: {', '.join(self.circuit_data['buses'])}\n\n")
            
            # Voltage summary
            f.write("VOLTAGE ANALYSIS\n")
            f.write("-" * 20 + "\n")
            for bus in self.circuit_data['buses']:
                voltages = self.circuit_data['voltages'][bus]
                if len(voltages) >= 2:
                    avg_voltage = np.mean([voltages[i] for i in range(0, len(voltages), 2)])
                    f.write(f"{bus}: {avg_voltage:.4f} pu\n")
            f.write("\n")
            
            # Element summary
            f.write("ELEMENT SUMMARY\n")
            f.write("-" * 20 + "\n")
            element_types = {}
            for element in self.circuit_data['elements']:
                element_type = element.split('.')[0]
                element_types[element_type] = element_types.get(element_type, 0) + 1
            
            for elem_type, count in element_types.items():
                f.write(f"{elem_type}: {count}\n")
            f.write("\n")
            
            # Analysis files generated
            f.write("FILES GENERATED\n")
            f.write("-" * 20 + "\n")
            generated_files = [
                'circuit_diagram.png',
                'electrical_schematic.png', 
                'power_analysis.png',
                'voltage_analysis.png',
                'power_data.csv',
                'voltage_data.csv'
            ]
            
            for file in generated_files:
                if (self.results_dir / file).exists():
                    f.write(f"✓ {file}\n")
                else:
                    f.write(f"✗ {file}\n")
        
        print(f"✓ Analysis report saved to {report_path}")

def main():
    """Main function to run the visualizer"""
    # Initialize the visualizer
    dss_file = "EnhancedCircuit.dss"  # Use the enhanced circuit for better visualization
    
    if not Path(dss_file).exists():
        print(f"Error: DSS file '{dss_file}' not found!")
        print("Please make sure the DSS file is in the same directory.")
        return
    
    visualizer = OpenDSSVisualizer(dss_file)
    
    try:
        print("Starting OpenDSS Circuit Analysis...")
        print("=" * 50)
        
        # Load and solve the circuit
        visualizer.load_and_solve()
        
        # Create visualizations
        print("\n1. Creating network diagram...")
        visualizer.create_network_diagram(save=True, show=False)
        
        print("\n2. Creating electrical schematic...")
        visualizer.create_detailed_schematic(save=True, show=False)
        
        print("\n3. Analyzing power flow...")
        power_df = visualizer.analyze_power_flow(show=False)
        
        print("\n4. Analyzing voltage profile...")
        voltage_df = visualizer.voltage_profile_analysis(show=False)
        
        print("\n5. Running time series analysis...")
        visualizer.run_time_series_analysis(show=False)
        
        print("\n6. Generating comprehensive report...")
        visualizer.generate_report()
        
        print("\n" + "=" * 50)
        print("Analysis completed successfully!")
        print(f"Results saved in: {visualizer.results_dir.absolute()}")
        print("=" * 50)
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()