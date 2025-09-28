import React from 'react';
import styled from 'styled-components';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const ChartContainer = styled.div`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
  color: white;
`;

const ChartTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: white;
`;

const PowerFlowChart = ({ metrics }) => {
  // Generate sample data for the last 24 hours
  const generatePowerData = () => {
    const data = [];
    const now = new Date();
    
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      const hour = time.getHours();
      
      // Simulate daily load pattern
      const baseLoad = metrics.total_power || 100;
      const loadFactor = 0.6 + 0.4 * Math.sin(2 * Math.PI * hour / 24);
      const power = baseLoad * loadFactor + (Math.random() - 0.5) * 10;
      
      data.push({
        time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        power: Math.max(0, power),
        efficiency: (metrics.efficiency || 95) + (Math.random() - 0.5) * 2
      });
    }
    
    return data;
  };

  const data = generatePowerData();

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          background: 'rgba(0, 0, 0, 0.8)',
          padding: '8px 12px',
          borderRadius: '6px',
          color: 'white',
          fontSize: '0.9rem'
        }}>
          <p>{`Time: ${label}`}</p>
          <p style={{ color: '#4ade80' }}>{`Power: ${payload[0].value.toFixed(1)} MW`}</p>
          <p style={{ color: '#3b82f6' }}>{`Efficiency: ${payload[1].value.toFixed(1)}%`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ChartContainer>
      <ChartTitle>Power Flow & Efficiency</ChartTitle>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
          <XAxis 
            dataKey="time" 
            stroke="rgba(255, 255, 255, 0.7)"
            fontSize={12}
          />
          <YAxis 
            stroke="rgba(255, 255, 255, 0.7)"
            fontSize={12}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line 
            type="monotone" 
            dataKey="power" 
            stroke="#4ade80" 
            strokeWidth={2}
            dot={{ fill: '#4ade80', strokeWidth: 2, r: 4 }}
            name="Power (MW)"
          />
          <Line 
            type="monotone" 
            dataKey="efficiency" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
            name="Efficiency (%)"
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

export default PowerFlowChart;