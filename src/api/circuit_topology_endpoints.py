"""
Circuit Topology API - Returns actual DSS file structure
Parses OpenDSS circuit and returns real component topology
"""

from fastapi import APIRouter, HTTPException
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/circuit", tags=["circuit"])

# Global references (set by backend_server.py)
_load_flow = None
_dss_path = None

def set_circuit_dependencies(load_flow, dss_path):
    """Set load flow and DSS path from backend server"""
    global _load_flow, _dss_path
    _load_flow = load_flow
    _dss_path = dss_path

def parse_dss_file(dss_path):
    """Parse DSS file and extract circuit topology"""
    topology = {
        "circuit": None,
        "buses": [],
        "transformers": [],
        "lines": [],
        "loads": [],
        "reactors": [],
        "capacitors": [],
        "monitors": [],
        "meters": [],
        "connections": []
    }

    try:
        content = Path(dss_path).read_text()
        lines = content.split('\n')

        # Parse each line
        for line in lines:
            line = line.strip()
            if not line or line.startswith('!'):
                continue

            # Parse Circuit
            if line.startswith('New Circuit.'):
                match = re.search(r'Circuit\.(\w+)', line)
                if match:
                    topology["circuit"] = {
                        "name": match.group(1),
                        "type": "circuit"
                    }

            # Parse Transformers
            elif line.startswith('New Transformer.'):
                match = re.search(r'Transformer\.(\w+)', line)
                kva_match = re.search(r'KVAs=\((\d+)\s+(\d+)\)', line)
                kv_match = re.search(r'KVs=\((\d+)\s+(\d+)\)', line)
                buses_match = re.search(r'Buses=\(([^)]+)\)', line)

                if match:
                    tx_data = {
                        "id": match.group(1),
                        "name": match.group(1),
                        "type": "transformer"
                    }

                    if kva_match:
                        tx_data["rating_mva"] = int(kva_match.group(1)) / 1000
                    if kv_match:
                        tx_data["voltage"] = f"{kv_match.group(1)}/{kv_match.group(2)} kV"
                    if buses_match:
                        buses = buses_match.group(1).split()
                        if len(buses) >= 2:
                            tx_data["bus1"] = buses[0].split('.')[0]
                            tx_data["bus2"] = buses[1].split('.')[0]

                    topology["transformers"].append(tx_data)

            # Parse Lines
            elif line.startswith('New Line.'):
                match = re.search(r'Line\.(\w+)', line)
                bus1_match = re.search(r'Bus1=([^\s]+)', line)
                bus2_match = re.search(r'Bus2=([^\s]+)', line)
                length_match = re.search(r'Length=([\d.]+)', line)

                if match:
                    line_data = {
                        "id": match.group(1),
                        "name": match.group(1),
                        "type": "line"
                    }

                    if bus1_match:
                        line_data["bus1"] = bus1_match.group(1).split('.')[0]
                    if bus2_match:
                        line_data["bus2"] = bus2_match.group(1).split('.')[0]
                    if length_match:
                        line_data["length_km"] = float(length_match.group(1))

                    # Identify circuit breakers (typically very short lines)
                    if 'CB' in match.group(1).upper():
                        line_data["subtype"] = "circuit_breaker"
                    elif 'Coupler' in match.group(1):
                        line_data["subtype"] = "bus_coupler"
                    elif 'Feeder' in match.group(1):
                        line_data["subtype"] = "feeder"
                    else:
                        line_data["subtype"] = "sectionalizer"

                    topology["lines"].append(line_data)

            # Parse Loads
            elif line.startswith('New Load.'):
                match = re.search(r'Load\.(\w+)', line)
                bus_match = re.search(r'Bus1=([^\s]+)', line)
                kw_match = re.search(r'kW=([\d]+)', line)
                kvar_match = re.search(r'kvar=([\d]+)', line)
                kv_match = re.search(r'kV=([\d]+)', line)

                if match:
                    load_data = {
                        "id": match.group(1),
                        "name": match.group(1),
                        "type": "load"
                    }

                    if bus_match:
                        load_data["bus"] = bus_match.group(1).split('.')[0]
                    if kw_match:
                        load_data["power_mw"] = int(kw_match.group(1)) / 1000
                    if kvar_match:
                        load_data["reactive_mvar"] = int(kvar_match.group(1)) / 1000
                    if kv_match:
                        load_data["voltage_kv"] = int(kv_match.group(1))

                    # Determine load type from name
                    if 'Industrial' in match.group(1):
                        load_data["subtype"] = "industrial"
                    elif 'Commercial' in match.group(1):
                        load_data["subtype"] = "commercial"
                    else:
                        load_data["subtype"] = "general"

                    topology["loads"].append(load_data)

            # Parse Reactors
            elif line.startswith('New Reactor.'):
                match = re.search(r'Reactor\.(\w+)', line)
                bus_match = re.search(r'Bus1=([^\s]+)', line)
                kvar_match = re.search(r'kvar=([-\d]+)', line)
                kv_match = re.search(r'kV=([\d]+)', line)

                if match:
                    reactor_data = {
                        "id": match.group(1),
                        "name": match.group(1),
                        "type": "reactor"
                    }

                    if bus_match:
                        reactor_data["bus"] = bus_match.group(1).split('.')[0]
                    if kvar_match:
                        reactor_data["rating_mvar"] = int(kvar_match.group(1)) / 1000
                    if kv_match:
                        reactor_data["voltage_kv"] = int(kv_match.group(1))

                    topology["reactors"].append(reactor_data)

            # Parse Capacitors
            elif line.startswith('New Capacitor.'):
                match = re.search(r'Capacitor\.(\w+)', line)
                bus_match = re.search(r'Bus1=([^\s]+)', line)
                kvar_match = re.search(r'kvar=([\d]+)', line)
                kv_match = re.search(r'kV=([\d]+)', line)

                if match:
                    cap_data = {
                        "id": match.group(1),
                        "name": match.group(1),
                        "type": "capacitor"
                    }

                    if bus_match:
                        cap_data["bus"] = bus_match.group(1).split('.')[0]
                    if kvar_match:
                        cap_data["rating_mvar"] = int(kvar_match.group(1)) / 1000
                    if kv_match:
                        cap_data["voltage_kv"] = int(kv_match.group(1))

                    topology["capacitors"].append(cap_data)

            # Parse Monitors
            elif line.startswith('New Monitor.'):
                match = re.search(r'Monitor\.(\w+)', line)
                elem_match = re.search(r'Element=([^\s]+)', line)
                mode_match = re.search(r'mode=(\d+)', line)

                if match:
                    mon_data = {
                        "id": match.group(1),
                        "name": match.group(1),
                        "type": "monitor"
                    }

                    if elem_match:
                        mon_data["element"] = elem_match.group(1)
                    if mode_match:
                        mode = int(mode_match.group(1))
                        mon_data["mode"] = "voltage" if mode == 0 else "current" if mode == 1 else "power"

                    topology["monitors"].append(mon_data)

            # Parse EnergyMeters
            elif line.startswith('New EnergyMeter.'):
                match = re.search(r'EnergyMeter\.(\w+)', line)
                elem_match = re.search(r'Element=([^\s]+)', line)

                if match:
                    meter_data = {
                        "id": match.group(1),
                        "name": match.group(1),
                        "type": "energy_meter"
                    }

                    if elem_match:
                        meter_data["element"] = elem_match.group(1)

                    topology["meters"].append(meter_data)

        # Extract unique buses from connections
        buses_set = set()

        # From transformers
        for tx in topology["transformers"]:
            if "bus1" in tx:
                buses_set.add(tx["bus1"])
            if "bus2" in tx:
                buses_set.add(tx["bus2"])

        # From lines
        for line in topology["lines"]:
            if "bus1" in line:
                buses_set.add(line["bus1"])
            if "bus2" in line:
                buses_set.add(line["bus2"])

        # From loads
        for load in topology["loads"]:
            if "bus" in load:
                buses_set.add(load["bus"])

        # From reactors
        for reactor in topology["reactors"]:
            if "bus" in reactor:
                buses_set.add(reactor["bus"])

        # From capacitors
        for cap in topology["capacitors"]:
            if "bus" in cap:
                buses_set.add(cap["bus"])

        # Create bus list with voltage levels
        for bus_name in sorted(buses_set):
            bus_data = {"id": bus_name, "name": bus_name, "type": "bus"}

            # Infer voltage level from bus name
            if '400' in bus_name or 'Grid' in bus_name:
                bus_data["voltage_kv"] = 400
            elif '220' in bus_name:
                bus_data["voltage_kv"] = 220
            elif '33' in bus_name:
                bus_data["voltage_kv"] = 33
            else:
                bus_data["voltage_kv"] = 0

            topology["buses"].append(bus_data)

        # Build connections list
        # Transformer connections
        for tx in topology["transformers"]:
            if "bus1" in tx and "bus2" in tx:
                topology["connections"].append({
                    "from": tx["bus1"],
                    "to": tx["id"],
                    "type": "transformer_primary"
                })
                topology["connections"].append({
                    "from": tx["id"],
                    "to": tx["bus2"],
                    "type": "transformer_secondary"
                })

        # Line connections
        for line in topology["lines"]:
            if "bus1" in line and "bus2" in line:
                topology["connections"].append({
                    "from": line["bus1"],
                    "to": line["bus2"],
                    "via": line["id"],
                    "type": line.get("subtype", "line")
                })

        # Load connections
        for load in topology["loads"]:
            if "bus" in load:
                topology["connections"].append({
                    "from": load["bus"],
                    "to": load["id"],
                    "type": "load"
                })

        # Reactor connections
        for reactor in topology["reactors"]:
            if "bus" in reactor:
                topology["connections"].append({
                    "from": reactor["bus"],
                    "to": reactor["id"],
                    "type": "reactor"
                })

        # Capacitor connections
        for cap in topology["capacitors"]:
            if "bus" in cap:
                topology["connections"].append({
                    "from": cap["bus"],
                    "to": cap["id"],
                    "type": "capacitor"
                })

        return topology

    except Exception as e:
        logger.error(f"Error parsing DSS file: {e}")
        raise

@router.get("/topology")
async def get_circuit_topology():
    """Get circuit topology from actual DSS file"""
    if not _dss_path or not Path(_dss_path).exists():
        raise HTTPException(status_code=404, detail="DSS file not found")

    try:
        topology = parse_dss_file(_dss_path)

        return {
            "circuit_name": topology["circuit"]["name"] if topology["circuit"] else "Unknown",
            "total_buses": len(topology["buses"]),
            "total_transformers": len(topology["transformers"]),
            "total_lines": len(topology["lines"]),
            "total_loads": len(topology["loads"]),
            "total_reactors": len(topology["reactors"]),
            "total_capacitors": len(topology["capacitors"]),
            "buses": topology["buses"],
            "transformers": topology["transformers"],
            "lines": topology["lines"],
            "loads": topology["loads"],
            "reactors": topology["reactors"],
            "capacitors": topology["capacitors"],
            "monitors": topology["monitors"],
            "meters": topology["meters"],
            "connections": topology["connections"]
        }
    except Exception as e:
        logger.error(f"Error getting circuit topology: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/components/summary")
async def get_components_summary():
    """Get summary count of all circuit components"""
    if not _dss_path or not Path(_dss_path).exists():
        raise HTTPException(status_code=404, detail="DSS file not found")

    try:
        topology = parse_dss_file(_dss_path)

        return {
            "circuit": topology["circuit"]["name"] if topology["circuit"] else "Unknown",
            "summary": {
                "buses": len(topology["buses"]),
                "transformers": {
                    "total": len(topology["transformers"]),
                    "main_transformers": len([t for t in topology["transformers"] if 'TX' in t["id"]]),
                    "dist_transformers": len([t for t in topology["transformers"] if 'DTX' in t["id"]])
                },
                "lines": {
                    "total": len(topology["lines"]),
                    "circuit_breakers": len([l for l in topology["lines"] if l.get("subtype") == "circuit_breaker"]),
                    "feeders": len([l for l in topology["lines"] if l.get("subtype") == "feeder"]),
                    "bus_couplers": len([l for l in topology["lines"] if l.get("subtype") == "bus_coupler"])
                },
                "loads": {
                    "total": len(topology["loads"]),
                    "industrial": len([l for l in topology["loads"] if l.get("subtype") == "industrial"]),
                    "commercial": len([l for l in topology["loads"] if l.get("subtype") == "commercial"]),
                    "total_mw": sum(l.get("power_mw", 0) for l in topology["loads"])
                },
                "reactors": len(topology["reactors"]),
                "capacitors": len(topology["capacitors"]),
                "monitors": len(topology["monitors"]),
                "meters": len(topology["meters"])
            }
        }
    except Exception as e:
        logger.error(f"Error getting components summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
