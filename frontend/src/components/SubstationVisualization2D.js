import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import axios from 'axios';
import styled from 'styled-components';

const VisualizationContainer = styled.div`
  width: 100%;
  height: 800px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: auto;
`;


const StatusIndicator = styled.div`
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  padding: 10px 15px;
  font-size: 14px;
  font-weight: bold;
  color: ${props => props.status === 'normal' ? '#00c851' :
                   props.status === 'warning' ? '#ffbb33' : '#ff4444'};
`;

const Legend = styled.div`
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(30, 41, 59, 0.95);
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 10px;
  font-size: 11px;
  color: #94a3b8;

  h4 {
    margin: 0 0 8px 0;
    color: #f1f5f9;
    font-size: 12px;
  }

  .legend-item {
    display: flex;
    align-items: center;
    margin: 4px 0;

    .legend-color {
      width: 20px;
      height: 10px;
      margin-right: 8px;
      border-radius: 2px;
    }
  }
`;

const SubstationVisualization2D = () => {
  const svgRef = useRef(null);
  const animationsRef = useRef([]);
  const [systemStatus, setSystemStatus] = useState('normal');
  const [assets, setAssets] = useState({});

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

    const width = 1400;
    const height = 700;

    svg.attr('viewBox', `0 0 ${width} ${height}`)
       .attr('preserveAspectRatio', 'xMidYMid meet');

    // Create gradients and patterns
    const defs = svg.append('defs');

    // Bus gradient
    const busGradient = defs.append('linearGradient')
      .attr('id', 'busGradient')
      .attr('x1', '0%').attr('y1', '0%')
      .attr('x2', '0%').attr('y2', '100%');

    busGradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', '#FFD700')
      .attr('stop-opacity', 1);

    busGradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', '#FFA500')
      .attr('stop-opacity', 1);

    // Title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 30)
      .attr('text-anchor', 'middle')
      .attr('fill', '#f1f5f9')
      .attr('font-size', '20px')
      .attr('font-weight', 'bold')
      .text('Indian EHV 400/220 kV Substation - Single Line Diagram');

    // Draw 400kV Section
    const section400kV = svg.append('g').attr('id', 'section400kV');

    // 400kV Bus 1 & 2
    drawBus(section400kV, 'bus400_1', 200, 100, 300, '400 kV Bus 1');
    drawBus(section400kV, 'bus400_2', 600, 100, 300, '400 kV Bus 2');

    // Incoming 400kV Lines
    drawIncomingLine(svg, 'line400_1', 50, 100, 200, 100, '400kV Line 1');
    drawIncomingLine(svg, 'line400_2', 950, 100, 900, 100, '400kV Line 2');

    // Lightning Arresters at 400kV
    drawLightningArrester(svg, 'LA400_1', 150, 80);
    drawLightningArrester(svg, 'LA400_2', 950, 80);

    // CVTs at 400kV buses
    drawCVT(svg, 'CVT400_1', 250, 120);
    drawCVT(svg, 'CVT400_2', 650, 120);

    // Bus Coupler between 400kV buses
    drawIsolator(svg, 'ISO_BC', 500, 100);
    drawCircuitBreaker(svg, 'CB_BC', 450, 100);

    // Power Transformers 400/220 kV
    drawTransformer(svg, 'TR1', 350, 250, '315 MVA\n400/220 kV');
    drawTransformer(svg, 'TR2', 750, 250, '315 MVA\n400/220 kV');

    // Circuit Breakers on 400kV side
    drawCircuitBreaker(svg, 'CB400_1', 350, 150);
    drawCircuitBreaker(svg, 'CB400_2', 750, 150);

    // Isolators on 400kV side
    drawIsolator(svg, 'ISO400_1', 350, 180);
    drawIsolator(svg, 'ISO400_2', 750, 180);

    // Current Transformers
    drawCT(svg, 'CT400_1', 350, 210);
    drawCT(svg, 'CT400_2', 750, 210);

    // Draw 220kV Section
    const section220kV = svg.append('g').attr('id', 'section220kV');

    // 220kV Bus 1 & 2
    drawBus(section220kV, 'bus220_1', 200, 450, 250, '220 kV Bus 1');
    drawBus(section220kV, 'bus220_2', 500, 450, 250, '220 kV Bus 2');

    // Circuit Breakers on 220kV side
    drawCircuitBreaker(svg, 'CB220_1', 350, 380);
    drawCircuitBreaker(svg, 'CB220_2', 750, 380);

    // Isolators on 220kV side
    drawIsolator(svg, 'ISO220_1', 350, 410);
    drawIsolator(svg, 'ISO220_2', 750, 410);

    // CTs on 220kV side
    drawCT(svg, 'CT220_1', 350, 350);
    drawCT(svg, 'CT220_2', 750, 350);

    // CVTs at 220kV buses
    drawCVT(svg, 'CVT220_1', 250, 470);
    drawCVT(svg, 'CVT220_2', 550, 470);

    // Lightning Arresters at 220kV
    drawLightningArrester(svg, 'LA220_1', 300, 430);
    drawLightningArrester(svg, 'LA220_2', 600, 430);

    // Outgoing 220kV Feeders
    drawOutgoingFeeder(svg, 'feeder220_1', 150, 450, '220kV Feeder 1');
    drawOutgoingFeeder(svg, 'feeder220_2', 450, 450, '220kV Feeder 2');
    drawOutgoingFeeder(svg, 'feeder220_3', 800, 450, '220kV Feeder 3');

    // Shunt Reactors
    drawShuntReactor(svg, 'SR1', 950, 450, '50 MVAR');
    drawShuntReactor(svg, 'SR2', 1050, 450, '50 MVAR');

    // Capacitor Banks
    drawCapacitorBank(svg, 'CAP1', 1150, 450, '30 MVAR');
    drawCapacitorBank(svg, 'CAP2', 1250, 450, '30 MVAR');

    // Auxiliary Systems
    drawAuxiliaryTransformer(svg, 'AUX_TR1', 100, 550, '1 MVA');
    drawAuxiliaryTransformer(svg, 'AUX_TR2', 200, 550, '1 MVA');

    // Battery Bank & DC System
    drawBatteryBank(svg, 'BATTERY', 100, 620);

    // Control Panel
    drawControlPanel(svg, 'CONTROL', 250, 620);

    // Fire Protection System
    drawFireProtection(svg, 'FIRE', 400, 620);

    // Emergency Diesel Generator
    drawDieselGenerator(svg, 'DG', 550, 620);

    // Earthing System
    drawEarthingSystem(svg, 'EARTH', 700, 620);

    // Wave Traps
    drawWaveTrap(svg, 'WT1', 100, 100);
    drawWaveTrap(svg, 'WT2', 1000, 100);

    // Draw connections
    drawConnections(svg);

    // Add animation to power flow
    animatePowerFlow(svg);
  };

  const drawBus = (parent, id, x, y, width, label) => {
    const g = parent.append('g').attr('id', id);

    g.append('rect')
      .attr('x', x).attr('y', y)
      .attr('width', width).attr('height', 12)
      .attr('fill', 'url(#busGradient)')
      .attr('stroke', '#333')
      .attr('stroke-width', 2)
      .attr('rx', 2);

    g.append('text')
      .attr('x', x + width/2).attr('y', y - 5)
      .attr('text-anchor', 'middle')
      .attr('fill', '#f1f5f9')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .text(label);
  };

  const drawTransformer = (svg, id, x, y, label) => {
    const g = svg.append('g').attr('id', id);

    // Primary winding (400kV)
    g.append('circle')
      .attr('cx', x).attr('cy', y)
      .attr('r', 30)
      .attr('fill', 'none')
      .attr('stroke', '#4CAF50')
      .attr('stroke-width', 3);

    // Secondary winding (220kV)
    g.append('circle')
      .attr('cx', x).attr('cy', y + 70)
      .attr('r', 30)
      .attr('fill', 'none')
      .attr('stroke', '#2196F3')
      .attr('stroke-width', 3);

    // Core
    g.append('rect')
      .attr('x', x - 8).attr('y', y + 20)
      .attr('width', 16).attr('height', 30)
      .attr('fill', '#666')
      .attr('rx', 2);

    // Label
    const lines = label.split('\n');
    lines.forEach((line, i) => {
      g.append('text')
        .attr('x', x + 50).attr('y', y + 35 + (i * 15))
        .attr('fill', '#e2e8f0')
        .attr('font-size', '11px')
        .text(line);
    });
  };

  const drawCircuitBreaker = (svg, id, x, y) => {
    const g = svg.append('g')
      .attr('id', id)
      .style('cursor', 'pointer');

    // Breaker symbol
    g.append('rect')
      .attr('x', x - 12).attr('y', y - 6)
      .attr('width', 24).attr('height', 12)
      .attr('fill', '#FF5722')
      .attr('stroke', 'white')
      .attr('stroke-width', 1)
      .attr('rx', 2);

    // Contacts
    g.append('line')
      .attr('x1', x - 12).attr('y1', y)
      .attr('x2', x - 18).attr('y2', y)
      .attr('stroke', 'white')
      .attr('stroke-width', 2);

    g.append('line')
      .attr('x1', x + 12).attr('y1', y)
      .attr('x2', x + 18).attr('y2', y)
      .attr('stroke', 'white')
      .attr('stroke-width', 2);

    // Label
    g.append('text')
      .attr('x', x).attr('y', y - 10)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text(id);

    g.on('click', () => toggleBreaker(id));
  };

  const drawIsolator = (svg, id, x, y) => {
    const g = svg.append('g').attr('id', id);

    // Isolator symbol (knife switch)
    g.append('line')
      .attr('x1', x - 15).attr('y1', y)
      .attr('x2', x + 15).attr('y2', y)
      .attr('stroke', '#9C27B0')
      .attr('stroke-width', 3);

    g.append('circle')
      .attr('cx', x - 15).attr('cy', y)
      .attr('r', 3)
      .attr('fill', 'white');

    g.append('circle')
      .attr('cx', x + 15).attr('cy', y)
      .attr('r', 3)
      .attr('fill', 'white');

    g.append('text')
      .attr('x', x).attr('y', y - 8)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text(id);
  };

  const drawCT = (svg, id, x, y) => {
    const g = svg.append('g').attr('id', id);

    // CT symbol (donut shape)
    g.append('circle')
      .attr('cx', x).attr('cy', y)
      .attr('r', 12)
      .attr('fill', 'none')
      .attr('stroke', '#FF9800')
      .attr('stroke-width', 3);

    g.append('circle')
      .attr('cx', x).attr('cy', y)
      .attr('r', 4)
      .attr('fill', '#FF9800');

    g.append('text')
      .attr('x', x + 20).attr('y', y + 3)
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text(id);
  };

  const drawCVT = (svg, id, x, y) => {
    const g = svg.append('g').attr('id', id);

    // CVT symbol (capacitor + small transformer)
    g.append('line')
      .attr('x1', x - 8).attr('y1', y - 12)
      .attr('x2', x - 8).attr('y2', y + 12)
      .attr('stroke', '#00BCD4')
      .attr('stroke-width', 2);

    g.append('line')
      .attr('x1', x + 8).attr('y1', y - 12)
      .attr('x2', x + 8).attr('y2', y + 12)
      .attr('stroke', '#00BCD4')
      .attr('stroke-width', 2);

    g.append('circle')
      .attr('cx', x).attr('cy', y + 20)
      .attr('r', 8)
      .attr('fill', 'none')
      .attr('stroke', '#00BCD4')
      .attr('stroke-width', 2);

    g.append('text')
      .attr('x', x).attr('y', y - 18)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text(id);
  };

  const drawLightningArrester = (svg, id, x, y) => {
    const g = svg.append('g').attr('id', id);

    // Lightning arrester symbol
    g.append('path')
      .attr('d', `M${x},${y} L${x-8},${y+15} L${x+8},${y+15} Z`)
      .attr('fill', '#FFEB3B')
      .attr('stroke', '#333')
      .attr('stroke-width', 1);

    g.append('line')
      .attr('x1', x).attr('y1', y + 15)
      .attr('x2', x).attr('y2', y + 25)
      .attr('stroke', '#333')
      .attr('stroke-width', 2);

    // Ground symbol
    g.append('line')
      .attr('x1', x - 10).attr('y1', y + 25)
      .attr('x2', x + 10).attr('y2', y + 25)
      .attr('stroke', '#333')
      .attr('stroke-width', 2);

    g.append('text')
      .attr('x', x).attr('y', y - 5)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text(id);
  };

  const drawShuntReactor = (svg, id, x, y, rating) => {
    const g = svg.append('g').attr('id', id);

    // Reactor symbol (inductor)
    const path = d3.path();
    for (let i = 0; i < 4; i++) {
      const cx = x + i * 10 - 15;
      path.arc(cx, y, 5, Math.PI, 0, true);
    }

    g.append('path')
      .attr('d', path.toString())
      .attr('fill', 'none')
      .attr('stroke', '#8BC34A')
      .attr('stroke-width', 2);

    g.append('text')
      .attr('x', x).attr('y', y + 20)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '10px')
      .text(rating);
  };

  const drawCapacitorBank = (svg, id, x, y, rating) => {
    const g = svg.append('g').attr('id', id);

    // Capacitor bank symbol
    g.append('line')
      .attr('x1', x - 10).attr('y1', y - 15)
      .attr('x2', x - 10).attr('y2', y + 15)
      .attr('stroke', '#00E676')
      .attr('stroke-width', 3);

    g.append('line')
      .attr('x1', x + 10).attr('y1', y - 15)
      .attr('x2', x + 10).attr('y2', y + 15)
      .attr('stroke', '#00E676')
      .attr('stroke-width', 3);

    g.append('text')
      .attr('x', x).attr('y', y + 25)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '10px')
      .text(rating);
  };

  const drawWaveTrap = (svg, id, x, y) => {
    const g = svg.append('g').attr('id', id);

    // Wave trap symbol (LC circuit)
    g.append('circle')
      .attr('cx', x).attr('cy', y - 10)
      .attr('r', 8)
      .attr('fill', 'none')
      .attr('stroke', '#E91E63')
      .attr('stroke-width', 2);

    g.append('rect')
      .attr('x', x - 6).attr('y', y)
      .attr('width', 12).attr('height', 4)
      .attr('fill', '#E91E63');

    g.append('text')
      .attr('x', x).attr('y', y + 15)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text(id);
  };

  const drawAuxiliaryTransformer = (svg, id, x, y, rating) => {
    const g = svg.append('g').attr('id', id);

    // Small transformer symbol
    g.append('circle')
      .attr('cx', x).attr('cy', y)
      .attr('r', 15)
      .attr('fill', 'none')
      .attr('stroke', '#607D8B')
      .attr('stroke-width', 2);

    g.append('text')
      .attr('x', x).attr('y', y + 25)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text(`${id}\n${rating}`);
  };

  const drawBatteryBank = (svg, id, x, y) => {
    const g = svg.append('g').attr('id', id);

    // Battery symbol
    g.append('rect')
      .attr('x', x - 20).attr('y', y - 15)
      .attr('width', 40).attr('height', 30)
      .attr('fill', '#3F51B5')
      .attr('stroke', 'white')
      .attr('stroke-width', 1)
      .attr('rx', 2);

    g.append('text')
      .attr('x', x).attr('y', y + 3)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .text('DC');

    g.append('text')
      .attr('x', x).attr('y', y + 30)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text('Battery Bank');
  };

  const drawControlPanel = (svg, id, x, y) => {
    const g = svg.append('g').attr('id', id);

    g.append('rect')
      .attr('x', x - 25).attr('y', y - 15)
      .attr('width', 50).attr('height', 30)
      .attr('fill', '#795548')
      .attr('stroke', 'white')
      .attr('stroke-width', 1)
      .attr('rx', 2);

    g.append('text')
      .attr('x', x).attr('y', y + 3)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '10px')
      .text('CTRL');

    g.append('text')
      .attr('x', x).attr('y', y + 30)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text('Control Panel');
  };

  const drawFireProtection = (svg, id, x, y) => {
    const g = svg.append('g').attr('id', id);

    g.append('rect')
      .attr('x', x - 25).attr('y', y - 15)
      .attr('width', 50).attr('height', 30)
      .attr('fill', '#F44336')
      .attr('stroke', 'white')
      .attr('stroke-width', 1)
      .attr('rx', 2);

    g.append('text')
      .attr('x', x).attr('y', y + 3)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '10px')
      .text('FIRE');

    g.append('text')
      .attr('x', x).attr('y', y + 30)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text('Fire System');
  };

  const drawDieselGenerator = (svg, id, x, y) => {
    const g = svg.append('g').attr('id', id);

    g.append('rect')
      .attr('x', x - 30).attr('y', y - 15)
      .attr('width', 60).attr('height', 30)
      .attr('fill', '#FFC107')
      .attr('stroke', '#333')
      .attr('stroke-width', 1)
      .attr('rx', 2);

    g.append('text')
      .attr('x', x).attr('y', y + 3)
      .attr('text-anchor', 'middle')
      .attr('fill', '#333')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .text('DG');

    g.append('text')
      .attr('x', x).attr('y', y + 30)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text('Diesel Generator');
  };

  const drawEarthingSystem = (svg, id, x, y) => {
    const g = svg.append('g').attr('id', id);

    // Earth symbol
    g.append('line')
      .attr('x1', x).attr('y1', y - 10)
      .attr('x2', x).attr('y2', y + 10)
      .attr('stroke', '#8B4513')
      .attr('stroke-width', 3);

    for (let i = 0; i < 3; i++) {
      const width = 30 - i * 8;
      g.append('line')
        .attr('x1', x - width/2).attr('y1', y + 10 + i * 5)
        .attr('x2', x + width/2).attr('y2', y + 10 + i * 5)
        .attr('stroke', '#8B4513')
        .attr('stroke-width', 2);
    }

    g.append('text')
      .attr('x', x).attr('y', y + 35)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text('Earthing System');
  };

  const drawIncomingLine = (svg, id, x1, y1, x2, y2, label) => {
    const g = svg.append('g').attr('id', id);

    g.append('line')
      .attr('x1', x1).attr('y1', y1)
      .attr('x2', x2).attr('y2', y2)
      .attr('stroke', '#00BCD4')
      .attr('stroke-width', 4)
      .attr('stroke-linecap', 'round');

    g.append('text')
      .attr('x', (x1 + x2) / 2).attr('y', y1 - 10)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '10px')
      .text(label);
  };

  const drawOutgoingFeeder = (svg, id, x, y, label) => {
    const g = svg.append('g').attr('id', id);

    g.append('line')
      .attr('x1', x).attr('y1', y)
      .attr('x2', x).attr('y2', y + 50)
      .attr('stroke', '#2196F3')
      .attr('stroke-width', 3);

    g.append('polygon')
      .attr('points', `${x},${y+60} ${x-8},${y+50} ${x+8},${y+50}`)
      .attr('fill', '#2196F3');

    g.append('text')
      .attr('x', x).attr('y', y + 75)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '9px')
      .text(label);
  };

  const drawConnections = (svg) => {
    // 400kV connections
    drawConnection(svg, 350, 112, 350, 150, 'conn400_cb1');
    drawConnection(svg, 750, 112, 750, 150, 'conn400_cb2');

    // Transformer connections
    drawConnection(svg, 350, 180, 350, 220, 'conn_tr1_top');
    drawConnection(svg, 750, 180, 750, 220, 'conn_tr2_top');
    drawConnection(svg, 350, 320, 350, 350, 'conn_tr1_bot');
    drawConnection(svg, 750, 320, 750, 350, 'conn_tr2_bot');

    // 220kV connections
    drawConnection(svg, 350, 410, 350, 450, 'conn220_bus1');
    drawConnection(svg, 750, 410, 600, 450, 'conn220_bus2');

    // Reactor connections
    drawConnection(svg, 750, 450, 950, 450, 'conn_reactor1');
    drawConnection(svg, 750, 450, 1050, 450, 'conn_reactor2');

    // Capacitor connections
    drawConnection(svg, 750, 450, 1150, 450, 'conn_cap1');
    drawConnection(svg, 750, 450, 1250, 450, 'conn_cap2');
  };

  const drawConnection = (svg, x1, y1, x2, y2, id) => {
    svg.append('line')
      .attr('id', id)
      .attr('x1', x1).attr('y1', y1)
      .attr('x2', x2).attr('y2', y2)
      .attr('stroke', '#00BCD4')
      .attr('stroke-width', 2)
      .attr('stroke-linecap', 'round')
      .attr('opacity', 0.8);
  };

  const animatePowerFlow = (svg) => {
    const flowPaths = [
      { path: '#conn400_cb1', color: '#FFEB3B', direction: 1 },
      { path: '#conn400_cb2', color: '#FFEB3B', direction: 1 },
      { path: '#conn_tr1_top', color: '#4CAF50', direction: 1 },
      { path: '#conn_tr2_top', color: '#4CAF50', direction: 1 },
      { path: '#conn_tr1_bot', color: '#2196F3', direction: 1 },
      { path: '#conn_tr2_bot', color: '#2196F3', direction: 1 },
    ];

    flowPaths.forEach(({ path, color, direction }) => {
      const line = svg.select(path);
      if (!line.empty() && line.node()) {
        const lineNode = line.node();

        const dot = svg.append('circle')
          .attr('r', 3)
          .attr('fill', color)
          .attr('opacity', 0.8);

        const animateDot = () => {
          if (!document.contains(lineNode)) return;

          const x1 = +line.attr('x1');
          const y1 = +line.attr('y1');
          const x2 = +line.attr('x2');
          const y2 = +line.attr('y2');

          dot.attr('cx', direction > 0 ? x1 : x2)
             .attr('cy', direction > 0 ? y1 : y2)
             .transition()
             .duration(2000)
             .ease(d3.easeLinear)
             .attr('cx', direction > 0 ? x2 : x1)
             .attr('cy', direction > 0 ? y2 : y1)
             .on('end', () => {
               if (document.contains(lineNode)) {
                 animateDot();
               }
             });
        };

        animateDot();
      }
    });
  };

  const toggleBreaker = async (breakerId) => {
    try {
      const response = await axios.post('/api/control', {
        asset_id: breakerId,
        command: 'toggle',
        value: true
      });

      const breaker = d3.select(`#${breakerId}`).select('rect');
      const currentFill = breaker.attr('fill');
      breaker.attr('fill', currentFill === '#FF5722' ? '#4CAF50' : '#FF5722');
    } catch (error) {
      console.error('Error toggling breaker:', error);
    }
  };


  const updateRealtimeData = async () => {
    try {
      const response = await axios.get('/api/metrics');
      updatePowerFlows(response.data);
    } catch (error) {
      console.error('Error fetching real-time data:', error);
    }
  };

  const updatePowerFlows = (data) => {
    if (data.total_power) {
      // Calculate power distribution based on real data
      const totalPower = Math.round(data.total_power);
      const incomingPower1 = Math.round(totalPower * 0.55);
      const incomingPower2 = Math.round(totalPower * 0.45);
      const outgoingPower1 = Math.round(totalPower * 0.33);
      const outgoingPower2 = Math.round(totalPower * 0.35);
      const outgoingPower3 = Math.round(totalPower * 0.32);

      // Update incoming line labels
      d3.select('#line400_1 text').text(`400kV Line 1\n${incomingPower1} MW`);
      d3.select('#line400_2 text').text(`400kV Line 2\n${incomingPower2} MW`);

      // Update transformer labels
      d3.select('#TR1 text').text(`TR1: 315 MVA\n${incomingPower1} MW`);
      d3.select('#TR2 text').text(`TR2: 315 MVA\n${incomingPower2} MW`);

      // Update 220kV feeder labels
      d3.select('#feeder220_1 text').text(`220kV Feeder 1\n${outgoingPower1} MW`);
      d3.select('#feeder220_2 text').text(`220kV Feeder 2\n${outgoingPower2} MW`);
      d3.select('#feeder220_3 text').text(`220kV Feeder 3\n${outgoingPower3} MW`);
    }
  };

  return (
    <VisualizationContainer>
      <StatusIndicator status={systemStatus}>
        System Status: {systemStatus.toUpperCase()}
      </StatusIndicator>

      <Legend>
        <h4>Component Legend</h4>
        <div className="legend-item">
          <div className="legend-color" style={{ background: '#FFD700' }}></div>
          <span>Bus Bars</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ background: '#4CAF50' }}></div>
          <span>Transformers</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ background: '#FF5722' }}></div>
          <span>Circuit Breakers</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ background: '#9C27B0' }}></div>
          <span>Isolators</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ background: '#FF9800' }}></div>
          <span>Current Transformers</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ background: '#00BCD4' }}></div>
          <span>CVTs & Lines</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ background: '#FFEB3B' }}></div>
          <span>Lightning Arresters</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ background: '#00E676' }}></div>
          <span>Capacitor Banks</span>
        </div>
      </Legend>

      <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
    </VisualizationContainer>
  );
};

export default SubstationVisualization2D;