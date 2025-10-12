# Visualization Fix - Implementation Guide

## Summary
The 2D and 3D visualizations currently show components that **do not exist** in the actual DSS file. This guide provides step-by-step instructions to fix this inconsistency.

---

## What Was Done

### 1. ✅ Created New API Endpoint

**File**: `src/api/circuit_topology_endpoints.py`

**Endpoints**:
- `GET /api/circuit/topology` - Returns complete circuit topology from actual DSS file
- `GET /api/circuit/components/summary` - Returns summary count of components

**Features**:
- Parses actual DSS file line by line
- Extracts all components (transformers, lines, loads, reactors, capacitors, etc.)
- Builds connection graph
- Returns structured JSON with all circuit elements

**Response Structure**:
```json
{
  "circuit_name": "IndianEHVSubstation",
  "buses": [{"id": "Bus400kV_1", "voltage_kv": 400, ...}],
  "transformers": [{"id": "TX1_400_220", "rating_mva": 315, ...}],
  "lines": [{"id": "Feeder220kV_1", "subtype": "feeder", ...}],
  "loads": [{"id": "IndustrialLoad1", "power_mw": 15, ...}],
  "reactors": [{"id": "ShuntReactor400kV", "rating_mvar": 50, ...}],
  "capacitors": [{"id": "CapBank33kV_1", "rating_mvar": 10, ...}],
  "connections": [{"from": "Bus400kV_1", "to": "TX1_400_220", ...}]
}
```

### 2. ✅ Integrated with Backend

**File**: `src/backend_server.py` (Modified)

Changes:
- Added circuit topology router
- Set dependencies (load_flow, dss_path)
- New endpoints available at: `http://localhost:8000/api/circuit/topology`

---

## What Needs To Be Done

### Step 1: Update 2D Visualization

**File**: `frontend/src/components/SubstationVisualization2D.js`

#### Changes Required:

**1. Replace hardcoded nodes with API data**

Current (lines 139-190):
```javascript
const nodes = [
  // Hardcoded Wind Turbines, Wave Traps, etc.
  { id: 'wt1', x: 150, y: 100, type: 'wind', label: 'WT1' },
  // ...
];
```

Replace with:
```javascript
const [topology, setTopology] = useState(null);

useEffect(() => {
  fetchTopology();
}, []);

const fetchTopology = async () => {
  try {
    const response = await axios.get('/api/circuit/topology');
    setTopology(response.data);
  } catch (error) {
    console.error('Error fetching topology:', error);
  }
};

const buildNodesFromTopology = (topology) => {
  if (!topology) return [];

  const nodes = [];
  let yOffset = 100;

  // Grid Source (400kV)
  nodes.push({
    id: 'GridSource',
    x: 800,
    y: yOffset,
    type: 'grid',
    label: 'Grid Source\n400kV',
    status: 'normal',
    voltage: '400kV'
  });

  yOffset += 150;

  // 400kV Bus
  topology.buses
    .filter(b => b.voltage_kv === 400)
    .forEach((bus, i) => {
      nodes.push({
        id: bus.id,
        x: 800,
        y: yOffset,
        type: 'bus400',
        label: `${bus.name}\n400kV`,
        status: 'normal',
        voltage: '400kV'
      });
    });

  yOffset += 150;

  // Main Transformers (400/220kV)
  topology.transformers
    .filter(t => t.voltage?.includes('400'))
    .forEach((tx, i) => {
      nodes.push({
        id: tx.id,
        x: 500 + (i * 600),
        y: yOffset,
        type: 'transformer',
        label: `${tx.name}\n${tx.rating_mva} MVA\n${tx.voltage}`,
        status: 'normal',
        voltage: tx.voltage,
        rating: `${tx.rating_mva} MVA`
      });
    });

  yOffset += 200;

  // 220kV Buses
  topology.buses
    .filter(b => b.voltage_kv === 220)
    .forEach((bus, i) => {
      nodes.push({
        id: bus.id,
        x: 500 + (i * 600),
        y: yOffset,
        type: 'bus220',
        label: `${bus.name}\n220kV`,
        status: 'normal',
        voltage: '220kV'
      });
    });

  yOffset += 150;

  // Shunt Reactors
  topology.reactors.forEach((reactor, i) => {
    const voltage = reactor.voltage_kv;
    const busY = nodes.find(n => n.id.includes(`${voltage}`))?.y || yOffset;
    nodes.push({
      id: reactor.id,
      x: 200 + (i * 300),
      y: busY,
      type: 'reactor',
      label: `${reactor.name}\n${Math.abs(reactor.rating_mvar)} MVAR`,
      status: 'normal',
      rating: `${reactor.rating_mvar} MVAR`
    });
  });

  // Distribution Transformers (220/33kV)
  topology.transformers
    .filter(t => t.voltage?.includes('220/33'))
    .forEach((tx, i) => {
      nodes.push({
        id: tx.id,
        x: 500 + (i * 600),
        y: yOffset,
        type: 'transformer',
        label: `${tx.name}\n${tx.rating_mva} MVA\n${tx.voltage}`,
        status: 'normal',
        voltage: tx.voltage,
        rating: `${tx.rating_mva} MVA`
      });
    });

  yOffset += 200;

  // 33kV Buses
  topology.buses
    .filter(b => b.voltage_kv === 33)
    .forEach((bus, i) => {
      nodes.push({
        id: bus.id,
        x: 500 + (i * 600),
        y: yOffset,
        type: 'bus33',
        label: `${bus.name}\n33kV`,
        status: 'normal',
        voltage: '33kV'
      });
    });

  yOffset += 150;

  // Capacitor Banks
  topology.capacitors.forEach((cap, i) => {
    const busY = nodes.find(n => n.id === cap.bus)?.y || yOffset;
    nodes.push({
      id: cap.id,
      x: 300 + (i * 400),
      y: busY + 50,
      type: 'capacitor',
      label: `${cap.name}\n${cap.rating_mvar} MVAR`,
      status: 'normal',
      rating: `${cap.rating_mvar} MVAR`
    });
  });

  // Loads
  topology.loads.forEach((load, i) => {
    const busY = nodes.find(n => n.id === load.bus)?.y || yOffset;
    nodes.push({
      id: load.id,
      x: 400 + (i * 300),
      y: yOffset,
      type: 'load',
      label: `${load.name}\n${load.power_mw} MW`,
      status: 'normal',
      power: `${load.power_mw} MW`,
      subtype: load.subtype
    });
  });

  return nodes;
};
```

**2. Build connections from topology**

```javascript
const buildConnectionsFromTopology = (topology, nodes) => {
  if (!topology) return [];

  const connections = [];

  topology.connections.forEach(conn => {
    const fromNode = nodes.find(n => n.id === conn.from);
    const toNode = nodes.find(n => n.id === conn.to);

    if (fromNode && toNode) {
      connections.push({
        id: `conn_${conn.from}_${conn.to}`,
        from: conn.from,
        to: conn.to,
        type: conn.type,
        flow: true
      });
    }
  });

  return connections;
};
```

**3. Update drawComprehensiveSubstationDiagram**

```javascript
const drawComprehensiveSubstationDiagram = async () => {
  const svg = d3.select(svgRef.current);
  svg.selectAll("*").remove();

  const width = 1600;
  const height = 1300;

  svg.attr('viewBox', `0 0 ${width} ${height}`)
     .attr('preserveAspectRatio', 'xMidYMid meet');

  // Fetch topology
  const response = await axios.get('/api/circuit/topology');
  const topology = response.data;

  // Build nodes and connections
  const nodes = buildNodesFromTopology(topology);
  const connections = buildConnectionsFromTopology(topology, nodes);

  // Draw connections
  const connectionGroup = svg.append('g').attr('id', 'connections');
  connections.forEach(conn => {
    const fromNode = nodes.find(n => n.id === conn.from);
    const toNode = nodes.find(n => n.id === conn.to);
    if (fromNode && toNode) {
      connectionGroup.append('line')
        .attr('id', conn.id)
        .attr('class', 'connection')
        .attr('x1', fromNode.x)
        .attr('y1', fromNode.y)
        .attr('x2', toNode.x)
        .attr('y2', toNode.y)
        .attr('stroke', '#374151')
        .attr('stroke-width', 2.5);
    }
  });

  // Draw nodes
  nodes.forEach(node => {
    drawNode(svg, node, nodes, connections);
  });

  // Animate power flow
  animatePowerFlow(svg, connections);
};
```

**4. Remove these node types from getNodeColor and drawNodeIcon**:
- `'wind'` (Wind Turbines)
- `'line'` (Line Arresters - use 'grid' instead)
- Keep all others but ensure they match DSS component types

---

### Step 2: Update 3D Visualization

**File**: `frontend/src/components/SubstationVisualization3D.js`

#### Changes Required:

**1. Fetch topology in Scene component**

Add to Scene component (line 537):
```javascript
const [topology, setTopology] = useState(null);

useEffect(() => {
  const fetchTopology = async () => {
    try {
      const response = await axios.get('/api/circuit/topology');
      setTopology(response.data);
    } catch (error) {
      console.error('Error fetching topology:', error);
    }
  };
  fetchTopology();
}, []);
```

**2. Remove fictional components**

Delete these component instances (lines 595-671):
- `<LightningArrester>` at 400kV level (lines 600-601)
- `<WaveTrap>` components (lines 603-604)
- `<CVT>` components (lines 606-607)
- `<CurrentTransformer>` components (lines 609-610)
- `<Isolator>` components (lines 615-616)
- `<AuxiliaryTransformer>` components (lines 668-669)
- `<DieselGenerator>` component (line 670)
- `<ControlBuilding>` component (line 667)

Keep only:
- `<Busbar>` components
- `<CircuitBreaker>` components (simplified)
- `<PowerTransformer>` components
- `<ShuntReactor>` components
- `<CapacitorBank>` components (fix voltage level)

**3. Add 33kV distribution level**

After 220kV section (around line 654), add:
```javascript
{/* 33kV Distribution Level */}
<group position={[0, 0, 25]}>
  {/* 33kV Buses */}
  <Busbar position={[-10, 3, 0]} voltage={33} length={8} />
  <Busbar position={[10, 3, 0]} voltage={33} length={8} />

  {/* Distribution Transformers */}
  {topology?.transformers
    .filter(t => t.voltage?.includes('220/33'))
    .map((tx, i) => (
      <PowerTransformer
        key={tx.id}
        position={[-10 + (i * 20), 0, 10]}
        id={tx.id}
        data={{ loading: 65, temperature: 60 }}
      />
    ))}

  {/* Capacitor Banks at 33kV */}
  {topology?.capacitors.map((cap, i) => (
    <CapacitorBank
      key={cap.id}
      position={[-5 + (i * 10), 0, 5]}
      id={cap.id}
      capacity={cap.rating_mvar}
    />
  ))}

  {/* Loads */}
  {topology?.loads.map((load, i) => (
    <group key={load.id} position={[-10 + (i * 5), -2, 0]}>
      <Box args={[2, 1.5, 1]}>
        <meshStandardMaterial color={load.subtype === 'industrial' ? '#ff9800' : '#2196f3'} />
      </Box>
      <Text position={[0, 1.5, 0]} fontSize={0.3} color="white" anchorX="center">
        {load.name}
      </Text>
      <Text position={[0, 1, 0]} fontSize={0.25} color="#94a3b8" anchorX="center">
        {load.power_mw} MW
      </Text>
    </group>
  ))}
</group>
```

**4. Fix Capacitor Bank placement**

Move capacitor banks from 220kV level (lines 657-662) to 33kV level as shown above.

**5. Update power flow lines**

Add 33kV power flow lines after 220kV lines (around line 733):
```javascript
{/* 220kV to 33kV Distribution Transformers */}
<PowerFlowLine
  start={[-10, 5, 15]}
  end={[-10, 2, 25]}
  voltage={220}
  power={outgoingPower1 * 0.5}
/>
<PowerFlowLine
  start={[10, 5, 15]}
  end={[10, 2, 25]}
  voltage={220}
  power={outgoingPower2 * 0.5}
/>

{/* 33kV to Loads */}
{topology?.loads.map((load, i) => (
  <PowerFlowLine
    key={`flow_${load.id}`}
    start={[-10 + (i * 10), 3, 25]}
    end={[-10 + (i * 5), -2, 25]}
    voltage={33}
    power={load.power_mw}
  />
))}
```

---

## Testing Steps

### 1. Test API Endpoint

```bash
# Start backend
cd /root/opendss-test
python src/backend_server.py

# Test endpoint
curl http://localhost:8000/api/circuit/topology | jq .

# Check summary
curl http://localhost:8000/api/circuit/components/summary | jq .
```

**Expected Output**:
```json
{
  "circuit_name": "IndianEHVSubstation",
  "total_buses": 9,
  "total_transformers": 4,
  "total_lines": 9,
  "total_loads": 4,
  "total_reactors": 2,
  "total_capacitors": 2,
  ...
}
```

### 2. Test Visualization

```bash
# Start frontend
cd frontend
npm start

# Open browser
http://localhost:3000

# Navigate to Visualization page
# Check:
# - No Wind Turbines
# - No Wave Traps
# - 33kV distribution level visible
# - Capacitor banks at 33kV (not 220kV)
# - 4 loads shown
# - 2 shunt reactors shown
# - Distribution transformers (220/33kV) visible
```

### 3. Verify Components Match DSS File

```bash
# Count components in DSS file
grep -E "^New " src/models/IndianEHVSubstation.dss | awk '{print $2}' | cut -d'.' -f1 | sort | uniq -c

# Should match API response counts
```

---

## Quick Reference: Component Mapping

| DSS Component | Visualization Type | Notes |
|---------------|-------------------|-------|
| TX1_400_220, TX2_400_220 | PowerTransformer (large) | 315 MVA, 400/220kV |
| DTX1_220_33, DTX2_220_33 | PowerTransformer (small) | 50 MVA, 220/33kV |
| ShuntReactor400kV | ShuntReactor | 50 MVAR @ 400kV |
| ShuntReactor220kV | ShuntReactor | 30 MVAR @ 220kV |
| CapBank33kV_1, CapBank33kV_2 | CapacitorBank | 10/8 MVAR @ 33kV |
| IndustrialLoad1/2 | Load (orange) | 15/12 MW @ 33kV |
| CommercialLoad1/2 | Load (blue) | 8/6 MW @ 33kV |
| CB_400kV, CB_220kV_* | CircuitBreaker | Simplified in DSS |
| Feeder220kV_1/2 | Line (feeder) | 5/4.5 km |
| Feeder33kV_1/2 | Line (feeder) | 10/8 km |

---

## Files Modified

✅ **Created**:
- `src/api/circuit_topology_endpoints.py` - New API endpoint
- `VISUALIZATION_FIX_IMPLEMENTATION_GUIDE.md` - This guide
- `VISUALIZATION_MISMATCH_ANALYSIS.md` - Problem analysis

✅ **Modified**:
- `src/backend_server.py` - Added circuit router

⏳ **To Modify**:
- `frontend/src/components/SubstationVisualization2D.js` - Update nodes/connections
- `frontend/src/components/SubstationVisualization3D.js` - Remove fictional components

---

## Summary

### Problem
Visualizations showed components not in DSS file (Wind Turbines, Wave Traps, CVTs, CTs, Isolators, etc.)

### Solution
1. ✅ Created `/api/circuit/topology` endpoint that parses actual DSS file
2. ✅ Integrated with backend
3. ⏳ Update 2D visualization to fetch and use real topology
4. ⏳ Update 3D visualization to remove fictional components and add 33kV level

### Benefits
- ✅ Visualizations match actual DSS file
- ✅ Consistent representation across 2D/3D/Backend
- ✅ No redundant/fictional components
- ✅ Proper 33kV distribution level
- ✅ Correct component placement and connections

### Next Steps
1. Follow Steps 1 & 2 above to update visualizations
2. Test with API endpoint
3. Verify all components match DSS file
4. Optionally add option to switch to enhanced model

---

*Implementation guide created: 2025-10-12*
*All backend work complete - frontend updates pending*
