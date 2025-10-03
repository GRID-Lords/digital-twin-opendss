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

    const width = 1600;
    const height = 900;

    svg.attr('viewBox', `0 0 ${width} ${height}`)
       .attr('preserveAspectRatio', 'xMidYMid meet');

    // Create gradients and patterns
    const defs = svg.append('defs');

    // Bus gradient - 400kV
    const busGradient400 = defs.append('linearGradient')
      .attr('id', 'busGradient400')
      .attr('x1', '0%').attr('y1', '0%')
      .attr('x2', '0%').attr('y2', '100%');
    busGradient400.append('stop').attr('offset', '0%').attr('stop-color', '#DC143C').attr('stop-opacity', 1);
    busGradient400.append('stop').attr('offset', '100%').attr('stop-color', '#8B0000').attr('stop-opacity', 1);

    // Bus gradient - 220kV
    const busGradient220 = defs.append('linearGradient')
      .attr('id', 'busGradient220')
      .attr('x1', '0%').attr('y1', '0%')
      .attr('x2', '0%').attr('y2', '100%');
    busGradient220.append('stop').attr('offset', '0%').attr('stop-color', '#FFD700').attr('stop-opacity', 1);
    busGradient220.append('stop').attr('offset', '100%').attr('stop-color', '#FFA500').attr('stop-opacity', 1);

    // Title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 40)
      .attr('text-anchor', 'middle')
      .attr('fill', '#f1f5f9')
      .attr('font-size', '24px')
      .attr('font-weight', 'bold')
      .text('Indian EHV 400/220 kV Substation - Single Line Diagram');

    // ========== 400 kV SECTION (TOP) ==========
    const y400 = 120;

    // 400kV Incoming Lines
    drawIncomingLine(svg, 'line400_1', 100, y400, 250, y400, '400kV Line 1');
    drawIncomingLine(svg, 'line400_2', 1500, y400, 1350, y400, '400kV Line 2');

    // Lightning Arresters
    drawLightningArrester(svg, 'LA400_1', 200, y400 - 30);
    drawLightningArrester(svg, 'LA400_2', 1400, y400 - 30);

    // 400kV Bus 1 (Left)
    drawBus(svg, 'bus400_1', 250, y400 - 6, 400, '400 kV Bus 1', 'busGradient400');

    // Bus Coupler CB and Isolators with connecting lines
    // Left isolator connected to Bus 1
    svg.append('line')
      .attr('x1', 650).attr('y1', y400)
      .attr('x2', 770).attr('y2', y400)
      .attr('stroke', '#DC143C').attr('stroke-width', 3);
    drawIsolator(svg, 'ISO_BC_L', 770, y400);

    // Circuit Breaker
    drawCircuitBreaker(svg, 'CB_BC', 800, y400);

    // Right isolator connected to Bus 2
    svg.append('line')
      .attr('x1', 830).attr('y1', y400)
      .attr('x2', 950).attr('y2', y400)
      .attr('stroke', '#DC143C').attr('stroke-width', 3);
    drawIsolator(svg, 'ISO_BC_R', 830, y400);

    // 400kV Bus 2 (Right)
    drawBus(svg, 'bus400_2', 950, y400 - 6, 400, '400 kV Bus 2', 'busGradient400');

    // ========== TRANSFORMER BAY 1 (LEFT) ==========
    const tx1_x = 450;
    const tx1_y_top = y400 + 80;

    // Connection from Bus 1 to TX1 - complete vertical line
    svg.append('line')
      .attr('x1', tx1_x).attr('y1', y400 + 9)
      .attr('x2', tx1_x).attr('y2', tx1_y_top + 170)
      .attr('stroke', '#DC143C').attr('stroke-width', 3);

    // 400kV side equipment
    drawCircuitBreaker(svg, 'CB400_1', tx1_x, tx1_y_top - 50);
    drawIsolator(svg, 'ISO400_1', tx1_x, tx1_y_top - 20);
    drawCT(svg, 'CT400_1', tx1_x + 30, tx1_y_top);
    drawCVT(svg, 'CVT400_1', tx1_x - 30, tx1_y_top);

    // Transformer 1
    drawTransformer(svg, 'TR1', tx1_x, tx1_y_top + 120, '315 MVA\n400/220 kV');

    // ========== TRANSFORMER BAY 2 (RIGHT) ==========
    const tx2_x = 1150;
    const tx2_y_top = y400 + 80;

    // Connection from Bus 2 to TX2 - complete vertical line
    svg.append('line')
      .attr('x1', tx2_x).attr('y1', y400 + 9)
      .attr('x2', tx2_x).attr('y2', tx2_y_top + 170)
      .attr('stroke', '#DC143C').attr('stroke-width', 3);

    // 400kV side equipment
    drawCircuitBreaker(svg, 'CB400_2', tx2_x, tx2_y_top - 50);
    drawIsolator(svg, 'ISO400_2', tx2_x, tx2_y_top - 20);
    drawCT(svg, 'CT400_2', tx2_x + 30, tx2_y_top);
    drawCVT(svg, 'CVT400_2', tx2_x - 30, tx2_y_top);

    // Transformer 2
    drawTransformer(svg, 'TR2', tx2_x, tx2_y_top + 120, '315 MVA\n400/220 kV');

    // ========== 220 kV SECTION (BOTTOM) ==========
    const y220 = 550;

    // 220kV side equipment for TX1
    drawCT(svg, 'CT220_1', tx1_x + 30, y220 - 120);
    drawCVT(svg, 'CVT220_1', tx1_x - 30, y220 - 120);
    drawIsolator(svg, 'ISO220_1', tx1_x, y220 - 90);
    drawCircuitBreaker(svg, 'CB220_1', tx1_x, y220 - 60);

    // 220kV side equipment for TX2
    drawCT(svg, 'CT220_2', tx2_x + 30, y220 - 120);
    drawCVT(svg, 'CVT220_2', tx2_x - 30, y220 - 120);
    drawIsolator(svg, 'ISO220_2', tx2_x, y220 - 90);
    drawCircuitBreaker(svg, 'CB220_2', tx2_x, y220 - 60);

    // 220kV Bus 1 & 2
    drawBus(svg, 'bus220_1', 300, y220 - 6, 350, '220 kV Bus 1', 'busGradient220');
    drawBus(svg, 'bus220_2', 950, y220 - 6, 350, '220 kV Bus 2', 'busGradient220');

    // 220kV Bus Coupler with connecting lines
    // Left isolator connected to Bus 1
    svg.append('line')
      .attr('x1', 650).attr('y1', y220)
      .attr('x2', 770).attr('y2', y220)
      .attr('stroke', '#FFD700').attr('stroke-width', 3);
    drawIsolator(svg, 'ISO_BC_220_L', 770, y220);

    // Circuit Breaker
    drawCircuitBreaker(svg, 'CB_BC_220', 800, y220);

    // Right isolator connected to Bus 2
    svg.append('line')
      .attr('x1', 830).attr('y1', y220)
      .attr('x2', 950).attr('y2', y220)
      .attr('stroke', '#FFD700').attr('stroke-width', 3);
    drawIsolator(svg, 'ISO_BC_220_R', 830, y220);

    // Connections from transformers to 220kV buses - complete lines
    svg.append('line')
      .attr('x1', tx1_x).attr('y1', tx1_y_top + 170)
      .attr('x2', tx1_x).attr('y2', y220 - 9)
      .attr('stroke', '#FFD700').attr('stroke-width', 3);

    svg.append('line')
      .attr('x1', tx2_x).attr('y1', tx2_y_top + 170)
      .attr('x2', tx2_x).attr('y2', y220 - 9)
      .attr('stroke', '#FFD700').attr('stroke-width', 3);

    // ========== 220 kV FEEDERS ==========
    const feeder_y = y220 + 100;

    // Feeder 1 from Bus 1
    svg.append('line')
      .attr('x1', 350).attr('y1', y220 + 9)
      .attr('x2', 350).attr('y2', feeder_y + 60)
      .attr('stroke', '#FFD700').attr('stroke-width', 3);
    drawCircuitBreaker(svg, 'CB_F1', 350, feeder_y + 20);
    drawOutgoingFeeder(svg, 'feeder220_1', 350, feeder_y + 60, '220kV Feeder 1\n(50 km)');

    // Feeder 2 from Bus 1
    svg.append('line')
      .attr('x1', 500).attr('y1', y220 + 9)
      .attr('x2', 500).attr('y2', feeder_y + 60)
      .attr('stroke', '#FFD700').attr('stroke-width', 3);
    drawCircuitBreaker(svg, 'CB_F2', 500, feeder_y + 20);
    drawOutgoingFeeder(svg, 'feeder220_2', 500, feeder_y + 60, '220kV Feeder 2\n(35 km)');

    // Feeder 3 from Bus 2
    svg.append('line')
      .attr('x1', 1050).attr('y1', y220 + 9)
      .attr('x2', 1050).attr('y2', feeder_y + 60)
      .attr('stroke', '#FFD700').attr('stroke-width', 3);
    drawCircuitBreaker(svg, 'CB_F3', 1050, feeder_y + 20);
    drawOutgoingFeeder(svg, 'feeder220_3', 1050, feeder_y + 60, '220kV Feeder 3\n(45 km)');

    // Feeder 4 from Bus 2
    svg.append('line')
      .attr('x1', 1200).attr('y1', y220 + 9)
      .attr('x2', 1200).attr('y2', feeder_y + 60)
      .attr('stroke', '#FFD700').attr('stroke-width', 3);
    drawCircuitBreaker(svg, 'CB_F4', 1200, feeder_y + 20);
    drawOutgoingFeeder(svg, 'feeder220_4', 1200, feeder_y + 60, '220kV Feeder 4\n(30 km)');

    // Shunt Reactor on Bus 2
    svg.append('line')
      .attr('x1', 1300).attr('y1', y220 + 9)
      .attr('x2', 1300).attr('y2', feeder_y + 40)
      .attr('stroke', '#a78bfa').attr('stroke-width', 3);
    drawShuntReactor(svg, 'SR1', 1300, feeder_y + 40, '63 MVAR');

    // Legend with voltage color coding
    const legend = svg.append('g').attr('id', 'legend').attr('transform', `translate(50, ${height - 120})`);

    legend.append('rect').attr('x', 0).attr('y', 0).attr('width', 250).attr('height', 100).attr('fill', 'rgba(30, 41, 59, 0.9)').attr('stroke', '#475569').attr('rx', 8);

    legend.append('text').attr('x', 10).attr('y', 25).attr('fill', '#f1f5f9').attr('font-size', '14px').attr('font-weight', 'bold').text('Legend');

    legend.append('line').attr('x1', 10).attr('y1', 40).attr('x2', 40).attr('y2', 40).attr('stroke', '#DC143C').attr('stroke-width', 4);
    legend.append('text').attr('x', 50).attr('y', 45).attr('fill', '#cbd5e1').attr('font-size', '12px').text('400 kV System');

    legend.append('line').attr('x1', 10).attr('y1', 60).attr('x2', 40).attr('y2', 60).attr('stroke', '#FFD700').attr('stroke-width', 4);
    legend.append('text').attr('x', 50).attr('y', 65).attr('fill', '#cbd5e1').attr('font-size', '12px').text('220 kV System');

    legend.append('circle').attr('cx', 25).attr('cy', 82).attr('r', 8).attr('fill', 'none').attr('stroke', '#4CAF50').attr('stroke-width', 2);
    legend.append('text').attr('x', 50).attr('y', 87).attr('fill', '#cbd5e1').attr('font-size', '12px').text('Transformer');

    // Add animation to power flow
    animatePowerFlow(svg);
  };

  const drawBus = (parent, id, x, y, width, label, gradient = 'busGradient400') => {
    const g = parent.append('g').attr('id', id).attr('class', 'bus');

    g.append('rect')
      .attr('x', x).attr('y', y)
      .attr('width', width).attr('height', 15)
      .attr('fill', `url(#${gradient})`)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('rx', 3)
      .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))');

    g.append('text')
      .attr('x', x + width/2).attr('y', y - 10)
      .attr('text-anchor', 'middle')
      .attr('fill', '#f1f5f9')
      .attr('font-size', '14px')
      .attr('font-weight', '600')
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

      <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
    </VisualizationContainer>
  );
};

export default SubstationVisualization2D;