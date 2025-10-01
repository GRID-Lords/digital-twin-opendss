import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import axios from 'axios';
import { motion } from 'framer-motion';
import styled from 'styled-components';

const VisualizationContainer = styled.div`
  width: 100%;
  height: 600px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  position: relative;
`;

const ControlPanel = styled.div`
  position: absolute;
  top: 20px;
  right: 20px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  z-index: 10;
`;

const AnomalyButton = styled(motion.button)`
  display: block;
  width: 100%;
  margin: 5px 0;
  padding: 8px 12px;
  background: ${props => props.severity === 'high' ? '#ff4444' :
                         props.severity === 'medium' ? '#ff8800' : '#ffbb33'};
  color: #ffffff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  transition: all 0.3s;

  &:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
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

const SubstationVisualization2D = () => {
  const svgRef = useRef(null);
  const animationsRef = useRef([]);
  const [systemStatus, setSystemStatus] = useState('normal');
  const [isSimulating, setIsSimulating] = useState(false);
  const [currentAnomaly, setCurrentAnomaly] = useState(null);

  useEffect(() => {
    drawSubstationDiagram();
    const interval = setInterval(updateRealtimeData, 10000); // Update every 10 seconds instead of 2
    return () => {
      clearInterval(interval);
      // Stop all animations when component unmounts
      if (svgRef.current) {
        d3.select(svgRef.current).selectAll('*').interrupt();
        d3.select(svgRef.current).selectAll('*').remove();
      }
    };
  }, []);

  const drawSubstationDiagram = () => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 1000;
    const height = 500;

    svg.attr('viewBox', `0 0 ${width} ${height}`)
       .attr('preserveAspectRatio', 'xMidYMid meet');

    // Create gradients
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

    // Draw 400kV buses
    const bus400_1 = svg.append('g').attr('id', 'bus400_1');
    bus400_1.append('rect')
      .attr('x', 100).attr('y', 100)
      .attr('width', 200).attr('height', 15)
      .attr('fill', 'url(#busGradient)')
      .attr('stroke', '#333')
      .attr('stroke-width', 2)
      .attr('rx', 3);

    bus400_1.append('text')
      .attr('x', 200).attr('y', 95)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '14px')
      .attr('font-weight', 'bold')
      .text('400 kV Bus 1');

    const bus400_2 = svg.append('g').attr('id', 'bus400_2');
    bus400_2.append('rect')
      .attr('x', 400).attr('y', 100)
      .attr('width', 200).attr('height', 15)
      .attr('fill', 'url(#busGradient)')
      .attr('stroke', '#333')
      .attr('stroke-width', 2)
      .attr('rx', 3);

    bus400_2.append('text')
      .attr('x', 500).attr('y', 95)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '14px')
      .attr('font-weight', 'bold')
      .text('400 kV Bus 2');

    // Draw 220kV buses
    const bus220_1 = svg.append('g').attr('id', 'bus220_1');
    bus220_1.append('rect')
      .attr('x', 100).attr('y', 350)
      .attr('width', 150).attr('height', 15)
      .attr('fill', 'url(#busGradient)')
      .attr('stroke', '#333')
      .attr('stroke-width', 2)
      .attr('rx', 3);

    bus220_1.append('text')
      .attr('x', 175).attr('y', 380)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '14px')
      .attr('font-weight', 'bold')
      .text('220 kV Bus 1');

    const bus220_2 = svg.append('g').attr('id', 'bus220_2');
    bus220_2.append('rect')
      .attr('x', 300).attr('y', 350)
      .attr('width', 150).attr('height', 15)
      .attr('fill', 'url(#busGradient)')
      .attr('stroke', '#333')
      .attr('stroke-width', 2)
      .attr('rx', 3);

    bus220_2.append('text')
      .attr('x', 375).attr('y', 380)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '14px')
      .attr('font-weight', 'bold')
      .text('220 kV Bus 2');

    // Draw transformers
    drawTransformer(svg, 'TR1', 200, 200, '315 MVA');
    drawTransformer(svg, 'TR2', 500, 200, '315 MVA');

    // Draw connections
    drawConnection(svg, 200, 115, 200, 200, 'line400_tr1');
    drawConnection(svg, 500, 115, 500, 200, 'line400_tr2');
    drawConnection(svg, 200, 260, 175, 350, 'tr1_220');
    drawConnection(svg, 500, 260, 375, 350, 'tr2_220');

    // Draw circuit breakers
    drawCircuitBreaker(svg, 'CB1', 200, 150);
    drawCircuitBreaker(svg, 'CB2', 500, 150);
    drawCircuitBreaker(svg, 'CB3', 175, 300);
    drawCircuitBreaker(svg, 'CB4', 375, 300);

    // Draw loads
    drawLoad(svg, 'Load1', 175, 400, '150 MW');
    drawLoad(svg, 'Load2', 375, 400, '100 MW');

    // Draw capacitor banks
    drawCapacitor(svg, 'Cap1', 700, 350, '30 MVAR');
    drawCapacitor(svg, 'Cap2', 750, 350, '20 MVAR');

    // Add animation to power flow
    animatePowerFlow(svg);
  };

  const drawTransformer = (svg, id, x, y, rating) => {
    const g = svg.append('g').attr('id', id);

    // Primary winding
    g.append('circle')
      .attr('cx', x).attr('cy', y)
      .attr('r', 25)
      .attr('fill', 'none')
      .attr('stroke', '#4CAF50')
      .attr('stroke-width', 3);

    // Secondary winding
    g.append('circle')
      .attr('cx', x).attr('cy', y + 60)
      .attr('r', 25)
      .attr('fill', 'none')
      .attr('stroke', '#2196F3')
      .attr('stroke-width', 3);

    // Core
    g.append('rect')
      .attr('x', x - 5).attr('y', y + 15)
      .attr('width', 10).attr('height', 30)
      .attr('fill', '#666');

    // Label
    g.append('text')
      .attr('x', x + 40).attr('y', y + 30)
      .attr('fill', 'white')
      .attr('font-size', '12px')
      .text(`${id}: ${rating}`);
  };

  const drawCircuitBreaker = (svg, id, x, y) => {
    const g = svg.append('g')
      .attr('id', id)
      .style('cursor', 'pointer');

    // Breaker symbol
    g.append('rect')
      .attr('x', x - 10).attr('y', y - 5)
      .attr('width', 20).attr('height', 10)
      .attr('fill', '#FF5722')
      .attr('stroke', 'white')
      .attr('stroke-width', 1)
      .attr('rx', 2);

    g.append('line')
      .attr('x1', x - 10).attr('y1', y)
      .attr('x2', x - 15).attr('y2', y)
      .attr('stroke', 'white')
      .attr('stroke-width', 2);

    g.append('line')
      .attr('x1', x + 10).attr('y1', y)
      .attr('x2', x + 15).attr('y2', y)
      .attr('stroke', 'white')
      .attr('stroke-width', 2);

    // Add click handler
    g.on('click', () => toggleBreaker(id));
  };

  const drawConnection = (svg, x1, y1, x2, y2, id) => {
    svg.append('line')
      .attr('id', id)
      .attr('x1', x1).attr('y1', y1)
      .attr('x2', x2).attr('y2', y2)
      .attr('stroke', '#00BCD4')
      .attr('stroke-width', 3)
      .attr('stroke-linecap', 'round');
  };

  const drawLoad = (svg, id, x, y, power) => {
    const g = svg.append('g').attr('id', id);

    g.append('polygon')
      .attr('points', `${x},${y} ${x-15},${y+25} ${x+15},${y+25}`)
      .attr('fill', '#9C27B0')
      .attr('stroke', 'white')
      .attr('stroke-width', 1);

    g.append('text')
      .attr('x', x).attr('y', y + 40)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '11px')
      .text(power);
  };

  const drawCapacitor = (svg, id, x, y, rating) => {
    const g = svg.append('g').attr('id', id);

    // Capacitor symbol (two parallel lines)
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
      .attr('x', x).attr('y', y + 30)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '11px')
      .text(rating);
  };

  const animatePowerFlow = (svg) => {
    // Create animated dots for power flow
    const flowPaths = [
      { path: 'line400_tr1', color: '#FFEB3B' },
      { path: 'line400_tr2', color: '#FFEB3B' },
      { path: 'tr1_220', color: '#4CAF50' },
      { path: 'tr2_220', color: '#4CAF50' }
    ];

    flowPaths.forEach(({ path, color }) => {
      const line = svg.select(`#${path}`);
      if (!line.empty() && line.node()) {
        const lineNode = line.node();
        // Check if the element supports getTotalLength (path or line elements)
        if (typeof lineNode.getTotalLength === 'function') {
          const dot = svg.append('circle')
            .attr('r', 4)
            .attr('fill', color);

          const animateDot = () => {
            // Check if the SVG is still in the document before animating
            if (!document.contains(lineNode)) {
              return;
            }

            dot.transition()
              .duration(2000)
              .ease(d3.easeLinear)
              .attrTween('transform', () => {
                try {
                  const length = lineNode.getTotalLength();
                  return (t) => {
                    // Check again during animation
                    if (!document.contains(lineNode)) {
                      return '';
                    }
                    const point = lineNode.getPointAtLength(t * length);
                    return `translate(${point.x},${point.y})`;
                  };
                } catch (e) {
                  // If getTotalLength fails, return a no-op function
                  return () => '';
                }
              })
              .on('end', () => {
                // Only continue animation if element still exists
                if (document.contains(lineNode)) {
                  animateDot();
                }
              });
          };

          animateDot();
        }
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

      // Update visualization
      const breaker = d3.select(`#${breakerId}`).select('rect');
      const currentFill = breaker.attr('fill');
      breaker.attr('fill', currentFill === '#FF5722' ? '#4CAF50' : '#FF5722');
    } catch (error) {
      console.error('Error toggling breaker:', error);
    }
  };

  const triggerAnomaly = async (anomalyType, severity) => {
    setIsSimulating(true);
    setCurrentAnomaly(anomalyType);
    setSystemStatus(severity === 'high' ? 'critical' : 'warning');

    try {
      const response = await axios.post('/api/simulation/anomaly', {
        type: anomalyType,
        severity: severity,
        location: 'Bus220_1',
        duration: 5000
      });

      // Visualize anomaly
      visualizeAnomaly(anomalyType, severity);

      // Reset after duration
      setTimeout(() => {
        setIsSimulating(false);
        setCurrentAnomaly(null);
        setSystemStatus('normal');
        resetVisualization();
      }, 5000);

    } catch (error) {
      console.error('Error triggering anomaly:', error);
      setIsSimulating(false);
    }
  };

  const visualizeAnomaly = (type, severity) => {
    const svg = d3.select(svgRef.current);

    switch (type) {
      case 'voltage_sag':
        // Animate voltage drop on buses
        svg.selectAll('#bus220_1 rect, #bus220_2 rect')
          .transition()
          .duration(500)
          .attr('fill', severity === 'high' ? '#FF0000' : '#FF9800')
          .transition()
          .duration(500)
          .attr('fill', 'url(#busGradient)');
        break;

      case 'transformer_overload':
        // Animate transformer overheating
        svg.select('#TR1 circle')
          .transition()
          .duration(500)
          .attr('stroke', '#FF0000')
          .attr('stroke-width', 5);
        break;

      case 'ground_fault':
        // Show fault location
        const faultMarker = svg.append('g').attr('id', 'fault-marker');
        faultMarker.append('circle')
          .attr('cx', 175).attr('cy', 350)
          .attr('r', 0)
          .attr('fill', 'none')
          .attr('stroke', '#FF0000')
          .attr('stroke-width', 3)
          .transition()
          .duration(300)
          .attr('r', 30)
          .attr('opacity', 0.5)
          .transition()
          .duration(300)
          .attr('r', 50)
          .attr('opacity', 0);
        break;

      case 'harmonic_distortion':
        // Show harmonic waves
        svg.selectAll('line')
          .style('stroke-dasharray', '5,5')
          .transition()
          .duration(100)
          .style('stroke-dashoffset', (d, i) => i * 2);
        break;

      case 'capacitor_switching':
        // Animate capacitor switching
        svg.selectAll('#Cap1, #Cap2')
          .selectAll('line')
          .transition()
          .duration(200)
          .attr('stroke', '#FFFF00')
          .transition()
          .duration(200)
          .attr('stroke', '#00E676');
        break;
    }
  };

  const resetVisualization = () => {
    const svg = d3.select(svgRef.current);
    svg.select('#fault-marker').remove();
    svg.selectAll('line').style('stroke-dasharray', null);
    svg.select('#TR1 circle').attr('stroke', '#4CAF50').attr('stroke-width', 3);
  };

  const updateRealtimeData = async () => {
    try {
      const response = await axios.get('/api/metrics');
      // Update visualization based on real-time data
      updatePowerFlows(response.data);
    } catch (error) {
      console.error('Error fetching real-time data:', error);
    }
  };

  const updatePowerFlows = (data) => {
    // Update power flow values in visualization
    if (data.total_load) {
      d3.select('#Load1 text').text(`${Math.round(data.total_load * 0.6)} MW`);
      d3.select('#Load2 text').text(`${Math.round(data.total_load * 0.4)} MW`);
    }
  };

  return (
    <VisualizationContainer>
      <StatusIndicator status={systemStatus}>
        System Status: {systemStatus.toUpperCase()}
        {currentAnomaly && ` - ${currentAnomaly.replace('_', ' ').toUpperCase()}`}
      </StatusIndicator>

      <ControlPanel>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>Anomaly Simulation</h4>

        <AnomalyButton
          severity="high"
          disabled={isSimulating}
          onClick={() => triggerAnomaly('voltage_sag', 'high')}
          whileTap={{ scale: 0.95 }}
        >
          Voltage Sag (Severe)
        </AnomalyButton>

        <AnomalyButton
          severity="medium"
          disabled={isSimulating}
          onClick={() => triggerAnomaly('transformer_overload', 'medium')}
          whileTap={{ scale: 0.95 }}
        >
          Transformer Overload
        </AnomalyButton>

        <AnomalyButton
          severity="high"
          disabled={isSimulating}
          onClick={() => triggerAnomaly('ground_fault', 'high')}
          whileTap={{ scale: 0.95 }}
        >
          Ground Fault
        </AnomalyButton>

        <AnomalyButton
          severity="low"
          disabled={isSimulating}
          onClick={() => triggerAnomaly('harmonic_distortion', 'low')}
          whileTap={{ scale: 0.95 }}
        >
          Harmonic Distortion
        </AnomalyButton>

        <AnomalyButton
          severity="medium"
          disabled={isSimulating}
          onClick={() => triggerAnomaly('capacitor_switching', 'medium')}
          whileTap={{ scale: 0.95 }}
        >
          Capacitor Switching
        </AnomalyButton>

        {isSimulating && (
          <div style={{ marginTop: '10px', fontSize: '11px', color: '#666' }}>
            Simulating anomaly...
          </div>
        )}
      </ControlPanel>

      <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
    </VisualizationContainer>
  );
};

export default SubstationVisualization2D;