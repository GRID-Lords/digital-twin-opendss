import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import axios from 'axios';
import styled from 'styled-components';

const VisualizationContainer = styled.div`
  width: 100%;
  height: 700px;
  background: #ffffff;
  background-image:
    radial-gradient(circle, #e5e7eb 1px, transparent 1px);
  background-size: 25px 25px;
  border-radius: 8px;
  padding: 15px;
  position: relative;
  overflow: auto;

  /* Hide scrollbar but keep scrollability */
  &::-webkit-scrollbar {
    display: none;
  }
  -ms-overflow-style: none;
  scrollbar-width: none;
`;

const StatusIndicator = styled.div`
  position: absolute;
  top: 15px;
  right: 15px;
  background: #ffffff;
  border: 2px solid ${props => props.status === 'normal' ? '#10b981' :
                   props.status === 'warning' ? '#f59e0b' : '#ef4444'};
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  color: ${props => props.status === 'normal' ? '#10b981' :
                   props.status === 'warning' ? '#f59e0b' : '#ef4444'};
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  backdrop-filter: blur(10px);
`;

const Legend = styled.div`
  position: absolute;
  bottom: 15px;
  left: 15px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  font-size: 11px;
  color: #374151;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);

  h4 {
    margin: 0 0 8px 0;
    color: #1f2937;
    font-size: 13px;
    font-weight: 600;
  }

  .legend-item {
    display: flex;
    align-items: center;
    margin: 6px 0;

    .legend-icon {
      width: 24px;
      height: 24px;
      margin-right: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
`;

const Tooltip = styled.div`
  position: fixed;
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 12px;
  pointer-events: none;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  white-space: nowrap;

  .tooltip-title {
    font-weight: 700;
    margin-bottom: 6px;
    font-size: 13px;
    color: #ffffff;
  }

  .tooltip-info {
    margin: 3px 0;
    color: #ddd;
    font-size: 11px;
  }
`;

const SubstationVisualization2D = () => {
  const svgRef = useRef(null);
  const animationsRef = useRef([]);
  const [systemStatus, setSystemStatus] = useState('normal');
  const [assets, setAssets] = useState({});
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, data: null });

  useEffect(() => {
    drawComprehensiveSubstationDiagram();

    // Update realtime data every 30 seconds (assets come from context)
    const interval = setInterval(() => {
      updateRealtimeData();
    }, 30000);

    return () => {
      clearInterval(interval);
      if (svgRef.current) {
        d3.select(svgRef.current).selectAll('*').interrupt();
        d3.select(svgRef.current).selectAll('*').remove();
      }
    };
  }, []);

  const drawComprehensiveSubstationDiagram = () => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 1600;
    const height = 1300;

    svg.attr('viewBox', `0 0 ${width} ${height}`)
       .attr('preserveAspectRatio', 'xMidYMid meet');

    // Define network topology layout with additional info
    const nodes = [
      // Incoming Lines & Wind Turbines (top level - y: 100)
      { id: 'wt1', x: 150, y: 100, type: 'wind', label: 'WT1', status: 'normal', power: '2MW' },
      { id: 'wt2', x: 1450, y: 100, type: 'wind', label: 'WT2', status: 'normal', power: '2MW' },
      { id: 'line400_1', x: 300, y: 100, type: 'line', label: 'LA400_1', status: 'normal', voltage: '400kV' },
      { id: 'line400_2', x: 1300, y: 100, type: 'line', label: 'LA400_2', status: 'normal', voltage: '400kV' },

      // Circuit Breakers (y: 180)
      { id: 'cb400_1', x: 450, y: 180, type: 'breaker', label: 'CB400_1', status: 'normal' },
      { id: 'cb400_2', x: 1150, y: 180, type: 'breaker', label: 'CB400_2', status: 'normal' },

      // 400kV Buses (y: 260)
      { id: 'bus400_1', x: 600, y: 260, type: 'bus400', label: '400kV Bus-1', status: 'normal', voltage: '400kV', current: '260A' },
      { id: 'bus400_2', x: 1000, y: 260, type: 'bus400', label: '400kV Bus-2', status: 'normal', voltage: '400kV', current: '215A' },

      // Isolators (400kV) (y: 360)
      { id: 'iso400_1', x: 600, y: 360, type: 'isolator', label: 'ISO400_1', status: 'normal' },
      { id: 'iso400_2', x: 1000, y: 360, type: 'isolator', label: 'ISO400_2', status: 'normal' },

      // CTs (400kV) (y: 460)
      { id: 'ct400_1', x: 600, y: 460, type: 'ct', label: 'CT400_1', status: 'normal' },
      { id: 'ct400_2', x: 1000, y: 460, type: 'ct', label: 'CT400_2', status: 'normal' },

      // Transformers (y: 600)
      { id: 'transformer1', x: 600, y: 600, type: 'transformer', label: 'T1 315MVA\n400/220kV', status: 'warning', voltage: '400/220kV', temp: '85°C' },
      { id: 'transformer2', x: 1000, y: 600, type: 'transformer', label: 'T2 315MVA\n400/220kV', status: 'normal', voltage: '400/220kV', temp: '72°C' },

      // CTs (220kV) (y: 740)
      { id: 'ct220_1', x: 600, y: 740, type: 'ct', label: 'CT220_1', status: 'normal' },
      { id: 'ct220_2', x: 1000, y: 740, type: 'ct', label: 'CT220_2', status: 'normal' },

      // Isolators (220kV) (y: 840)
      { id: 'iso220_1', x: 600, y: 840, type: 'isolator', label: 'ISO220_1', status: 'normal' },
      { id: 'iso220_2', x: 1000, y: 840, type: 'isolator', label: 'ISO220_2', status: 'normal' },

      // 220kV Buses (y: 940)
      { id: 'bus220_1', x: 450, y: 940, type: 'bus220', label: '220kV Bus-1', status: 'normal', voltage: '220kV', current: '472A' },
      { id: 'bus220_2', x: 1150, y: 940, type: 'bus220', label: '220kV Bus-2', status: 'normal', voltage: '220kV', current: '391A' },

      // 220kV Feeders (y: 1080)
      { id: 'feeder1', x: 250, y: 1080, type: 'feeder', label: '220kV Feeder-1', status: 'normal', power: '40MW' },
      { id: 'feeder2', x: 650, y: 1080, type: 'feeder', label: '220kV Feeder-2', status: 'normal', power: '35MW' },
      { id: 'feeder3', x: 1050, y: 1080, type: 'feeder', label: '220kV Feeder-3', status: 'normal', power: '30MW' },

      // Capacitor Banks (y: 1040)
      { id: 'cap1', x: 1280, y: 1040, type: 'capacitor', label: '50 MVAR', status: 'normal', rating: '50MVAR' },
      { id: 'cap2', x: 1400, y: 1040, type: 'capacitor', label: '50 MVAR', status: 'normal', rating: '50MVAR' },

      // Auxiliary Transformers (y: 1080)
      { id: 'aux_tr1', x: 200, y: 1200, type: 'aux_transformer', label: 'AUX TR1\n1 MVA', status: 'normal', rating: '1MVA' },
      { id: 'aux_tr2', x: 350, y: 1200, type: 'aux_transformer', label: 'AUX TR2\n1 MVA', status: 'normal', rating: '1MVA' },
    ];

    const connections = [
      // Wind turbines to incoming lines
      { id: 'conn_wt1', from: 'wt1', to: 'line400_1', flow: true },
      { id: 'conn_wt2', from: 'wt2', to: 'line400_2', flow: true },

      // Incoming lines to circuit breakers
      { id: 'conn1', from: 'line400_1', to: 'cb400_1', flow: true },
      { id: 'conn2', from: 'line400_2', to: 'cb400_2', flow: true },

      // Circuit breakers to 400kV buses
      { id: 'conn3', from: 'cb400_1', to: 'bus400_1', flow: true },
      { id: 'conn4', from: 'cb400_2', to: 'bus400_2', flow: true },

      // 400kV path to transformers (through isolators and CTs)
      { id: 'conn5', from: 'bus400_1', to: 'iso400_1', flow: true },
      { id: 'conn6', from: 'bus400_2', to: 'iso400_2', flow: true },
      { id: 'conn7', from: 'iso400_1', to: 'ct400_1', flow: true },
      { id: 'conn8', from: 'iso400_2', to: 'ct400_2', flow: true },
      { id: 'conn9', from: 'ct400_1', to: 'transformer1', flow: true },
      { id: 'conn10', from: 'ct400_2', to: 'transformer2', flow: true },

      // Transformers to 220kV (through CTs and isolators)
      { id: 'conn11', from: 'transformer1', to: 'ct220_1', flow: true },
      { id: 'conn12', from: 'transformer2', to: 'ct220_2', flow: true },
      { id: 'conn13', from: 'ct220_1', to: 'iso220_1', flow: true },
      { id: 'conn14', from: 'ct220_2', to: 'iso220_2', flow: true },
      { id: 'conn15', from: 'iso220_1', to: 'bus220_1', flow: true },
      { id: 'conn16', from: 'iso220_2', to: 'bus220_2', flow: true },

      // 220kV buses to feeders
      { id: 'conn17', from: 'bus220_1', to: 'feeder1', flow: true },
      { id: 'conn18', from: 'bus220_1', to: 'feeder2', flow: true },
      { id: 'conn19', from: 'bus220_2', to: 'feeder3', flow: true },

      // Capacitor banks
      { id: 'conn20', from: 'bus220_2', to: 'cap1', flow: false },
      { id: 'conn21', from: 'bus220_2', to: 'cap2', flow: false },

      // Auxiliary transformers
      { id: 'conn22', from: 'bus220_1', to: 'aux_tr1', flow: true },
      { id: 'conn23', from: 'bus220_1', to: 'aux_tr2', flow: true },

      // Bus couplers
      { id: 'conn_coupler400', from: 'bus400_1', to: 'bus400_2', type: 'coupler', flow: false },
      { id: 'conn_coupler220', from: 'bus220_1', to: 'bus220_2', type: 'coupler', flow: false },
    ];

    // Draw connections first (so they appear behind nodes)
    const connectionGroup = svg.append('g').attr('id', 'connections');

    connections.forEach(conn => {
      const fromNode = nodes.find(n => n.id === conn.from);
      const toNode = nodes.find(n => n.id === conn.to);

      connectionGroup.append('line')
        .attr('id', conn.id)
        .attr('class', 'connection')
        .attr('x1', fromNode.x)
        .attr('y1', fromNode.y)
        .attr('x2', toNode.x)
        .attr('y2', toNode.y)
        .attr('stroke', conn.type === 'coupler' ? '#9ca3af' : '#374151')
        .attr('stroke-width', 2.5)
        .attr('stroke-dasharray', conn.type === 'coupler' ? '5,5' : 'none')
        .attr('data-from', conn.from)
        .attr('data-to', conn.to);
    });

    // Draw nodes with drag behavior
    nodes.forEach(node => {
      drawNode(svg, node, nodes, connections);
    });

    // Animate power flow
    animatePowerFlow(svg, connections);

    // Add legend
    // addLegend(svg, width, height);
  };

  // Draw a node with icon
  const drawNode = (svg, node, nodes, connections) => {
    const g = svg.append('g')
      .attr('id', node.id)
      .attr('class', 'node')
      .attr('transform', `translate(${node.x}, ${node.y})`)
      .style('cursor', 'move');

    // Store position data
    g.datum({ ...node });

    // Alert circle for alarm/warning status
    if (node.status === 'alarm' || node.status === 'warning') {
      g.append('circle')
        .attr('r', 45)
        .attr('fill', 'none')
        .attr('stroke', node.status === 'alarm' ? '#ef4444' : '#f59e0b')
        .attr('stroke-width', 3)
        .attr('opacity', 0.8);
    }

    // Icon background
    g.append('rect')
      .attr('x', -30)
      .attr('y', -30)
      .attr('width', 60)
      .attr('height', 60)
      .attr('rx', 8)
      .attr('fill', getNodeColor(node.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))');

    // Icon symbol/text
    drawNodeIcon(g, node.type);

    // Label below node
    const lines = node.label.split('\n');
    lines.forEach((line, i) => {
      g.append('text')
        .attr('y', 50 + (i * 16))
        .attr('text-anchor', 'middle')
        .attr('fill', '#1f2937')
        .attr('font-size', '13px')
        .attr('font-weight', '600')
        .style('text-shadow', '0px 1px 2px rgba(255, 255, 255, 0.8)')
        .text(line);
    });

    // Add drag behavior
    const drag = d3.drag()
      .on('start', function(event) {
        d3.select(this).raise().style('cursor', 'grabbing');
      })
      .on('drag', function(event) {
        const newX = event.x;
        const newY = event.y;

        d3.select(this).attr('transform', `translate(${newX}, ${newY})`);

        // Update datum
        const nodeData = d3.select(this).datum();
        nodeData.x = newX;
        nodeData.y = newY;

        // Update connected lines
        updateConnections(node.id, newX, newY);
      })
      .on('end', function() {
        d3.select(this).style('cursor', 'move');
      });

    g.call(drag);

    // Add tooltip handlers
    g.on('mouseenter', function(event) {
      const nodeData = d3.select(this).datum();
      showTooltip(event.sourceEvent || event, nodeData);
    })
    .on('mousemove', function(event) {
      const nodeData = d3.select(this).datum();
      showTooltip(event.sourceEvent || event, nodeData);
    })
    .on('mouseleave', hideTooltip);
  };

  const getNodeColor = (type) => {
    const colors = {
      'wind': '#10b981',
      'line': '#64748b',
      'breaker': '#ef4444',
      'bus400': '#f59e0b',
      'bus220': '#f59e0b',
      'isolator': '#94a3b8',
      'ct': '#facc15',
      'transformer': '#3b82f6',
      'feeder': '#06b6d4',
      'capacitor': '#14b8a6',
      'aux_transformer': '#8b5cf6'
    };
    return colors[type] || '#6b7280';
  };

  const drawNodeIcon = (g, type) => {
    if (type === 'wind') {
      // Wind turbine icon
      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('fill', '#fff')
        .attr('font-size', '28px')
        .text('🌀');
    } else if (type === 'line') {
      // Incoming line
      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('fill', '#fff')
        .attr('font-size', '24px')
        .text('⚡');
    } else if (type === 'breaker') {
      // Circuit breaker
      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('fill', '#fff')
        .attr('font-size', '20px')
        .attr('font-weight', 'bold')
        .text('CB');
    } else if (type === 'bus400' || type === 'bus220') {
      // Bus bar
      g.append('line')
        .attr('x1', -25)
        .attr('y1', 0)
        .attr('x2', 25)
        .attr('y2', 0)
        .attr('stroke', '#fff')
        .attr('stroke-width', 8);
    } else if (type === 'isolator') {
      // Isolator (disconnector symbol)
      g.append('line')
        .attr('x1', -15)
        .attr('y1', 0)
        .attr('x2', 15)
        .attr('y2', 0)
        .attr('stroke', '#fff')
        .attr('stroke-width', 4);
      g.append('circle')
        .attr('cx', -15)
        .attr('cy', 0)
        .attr('r', 4)
        .attr('fill', '#fff');
      g.append('circle')
        .attr('cx', 15)
        .attr('cy', 0)
        .attr('r', 4)
        .attr('fill', '#fff');
    } else if (type === 'ct') {
      // Current transformer (circle)
      g.append('circle')
        .attr('r', 20)
        .attr('fill', 'none')
        .attr('stroke', '#fff')
        .attr('stroke-width', 3);
      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('fill', '#fff')
        .attr('font-size', '16px')
        .attr('font-weight', 'bold')
        .text('CT');
    } else if (type === 'transformer') {
      // Transformer (two circles)
      g.append('circle')
        .attr('cx', -10)
        .attr('cy', 0)
        .attr('r', 15)
        .attr('fill', 'none')
        .attr('stroke', '#fff')
        .attr('stroke-width', 3);
      g.append('circle')
        .attr('cx', 10)
        .attr('cy', 0)
        .attr('r', 15)
        .attr('fill', 'none')
        .attr('stroke', '#fff')
        .attr('stroke-width', 3);
    } else if (type === 'feeder') {
      // Feeder/load
      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('fill', '#fff')
        .attr('font-size', '26px')
        .text('⬇');
    } else if (type === 'capacitor') {
      // Capacitor bank
      g.append('line')
        .attr('x1', -12)
        .attr('y1', -15)
        .attr('x2', -12)
        .attr('y2', 15)
        .attr('stroke', '#fff')
        .attr('stroke-width', 3);
      g.append('line')
        .attr('x1', 12)
        .attr('y1', -15)
        .attr('x2', 12)
        .attr('y2', 15)
        .attr('stroke', '#fff')
        .attr('stroke-width', 3);
    } else if (type === 'aux_transformer') {
      // Auxiliary transformer (small circles)
      g.append('circle')
        .attr('cx', -8)
        .attr('cy', 0)
        .attr('r', 12)
        .attr('fill', 'none')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
      g.append('circle')
        .attr('cx', 8)
        .attr('cy', 0)
        .attr('r', 12)
        .attr('fill', 'none')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
    }
  };

  const addLegend = (svg, width, height) => {
    const legendData = [
      { type: 'wind', label: 'Wind Turbine', color: '#10b981' },
      { type: 'breaker', label: 'Circuit Breaker', color: '#ef4444' },
      { type: 'ct', label: 'Current Transformer', color: '#facc15' },
      { type: 'bus400', label: 'Bus Bar', color: '#f59e0b' },
      { type: 'transformer', label: 'Transformer', color: '#3b82f6' },
      { type: 'capacitor', label: 'Capacitor Bank', color: '#14b8a6' },
      { type: 'feeder', label: 'Feeder', color: '#06b6d4' },
    ];

    const legend = svg.append('g')
      .attr('id', 'legend')
      .attr('transform', `translate(40, ${height - 210})`);

    legend.append('rect')
      .attr('width', 180)
      .attr('height', 190)
      .attr('fill', '#ffffff')
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1)
      .attr('rx', 8);

    legend.append('text')
      .attr('x', 12)
      .attr('y', 22)
      .attr('fill', '#1f2937')
      .attr('font-size', '13px')
      .attr('font-weight', '600')
      .text('Component Legend');

    legendData.forEach((item, i) => {
      const yPos = 45 + (i * 23);

      legend.append('rect')
        .attr('x', 12)
        .attr('y', yPos - 9)
        .attr('width', 18)
        .attr('height', 18)
        .attr('fill', item.color)
        .attr('rx', 4);

      legend.append('text')
        .attr('x', 38)
        .attr('y', yPos + 4)
        .attr('fill', '#374151')
        .attr('font-size', '10px')
        .text(item.label);
    });
  };

  // Update connection lines when nodes are dragged
  const updateConnections = (nodeId, newX, newY) => {
    d3.selectAll('.connection').each(function() {
      const line = d3.select(this);
      const fromId = line.attr('data-from');
      const toId = line.attr('data-to');

      if (fromId === nodeId) {
        line.attr('x1', newX).attr('y1', newY);
      }
      if (toId === nodeId) {
        line.attr('x2', newX).attr('y2', newY);
      }
    });
  };

  // Show tooltip
  const showTooltip = (event, nodeData) => {
    // Get mouse position relative to the page
    const mouseX = event.clientX || event.pageX || 0;
    const mouseY = event.clientY || event.pageY || 0;

    setTooltip({
      visible: true,
      x: mouseX + 15,
      y: mouseY + 10,
      data: nodeData
    });
  };

  // Hide tooltip
  const hideTooltip = () => {
    setTooltip({ visible: false, x: 0, y: 0, data: null });
  };

  // Animate power flow
  const animatePowerFlow = (svg, connections) => {
    connections.forEach(conn => {
      if (!conn.flow) return; // Skip if no flow

      const line = svg.select(`#${conn.id}`);
      if (line.empty()) return;

      // Create flowing dots
      const createFlowDot = () => {
        const dot = svg.append('circle')
          .attr('class', 'flow-dot')
          .attr('r', 4)
          .attr('fill', '#ef4444')
          .attr('opacity', 0);

        const x1 = +line.attr('x1');
        const y1 = +line.attr('y1');
        const x2 = +line.attr('x2');
        const y2 = +line.attr('y2');

        dot.attr('cx', x1).attr('cy', y1)
          .transition()
          .duration(0)
          .attr('opacity', 0.8)
          .transition()
          .duration(2000)
          .ease(d3.easeLinear)
          .attr('cx', x2)
          .attr('cy', y2)
          .transition()
          .duration(0)
          .attr('opacity', 0)
          .on('end', function() {
            d3.select(this).remove();
            createFlowDot(); // Create next dot
          });
      };

      createFlowDot();
    });
  };

  const updateRealtimeData = async () => {
    try {
      await axios.get('/api/metrics');
      // Update node statuses based on real-time data
      // You can implement logic to update node colors/alerts based on metrics
    } catch (error) {
      console.error('Error fetching real-time data:', error);
    }
  };

  return (
    <VisualizationContainer>
      <StatusIndicator status={systemStatus}>
        System Status: {systemStatus.toUpperCase()}
      </StatusIndicator>

      <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />

      {tooltip.visible && tooltip.data && (
        <Tooltip style={{ left: tooltip.x, top: tooltip.y }}>
          <div className="tooltip-title">{tooltip.data.label.split('\n')[0]}</div>
          <div className="tooltip-info">Type: {tooltip.data.type}</div>
          {tooltip.data.voltage && <div className="tooltip-info">Voltage: {tooltip.data.voltage}</div>}
          {tooltip.data.power && <div className="tooltip-info">Power: {tooltip.data.power}</div>}
          {tooltip.data.current && <div className="tooltip-info">Current: {tooltip.data.current}</div>}
          {tooltip.data.temp && <div className="tooltip-info">Temperature: {tooltip.data.temp}</div>}
          {tooltip.data.pf && <div className="tooltip-info">Power Factor: {tooltip.data.pf}</div>}
          <div className="tooltip-info">Status: {tooltip.data.status}</div>
        </Tooltip>
      )}
    </VisualizationContainer>
  );
};

export default SubstationVisualization2D;