import React from 'react';
import styled from 'styled-components';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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

const VoltageProfileChart = ({ assets }) => {
  // Extract voltage data from assets
  const voltageData = Object.entries(assets)
    .filter(([_, asset]) => asset.voltage > 0)
    .map(([assetId, asset]) => ({
      name: assetId,
      voltage: asset.voltage,
      status: asset.status
    }))
    .sort((a, b) => b.voltage - a.voltage);

  const getBarColor = (status) => {
    switch (status) {
      case 'healthy': return '#4ade80';
      case 'warning': return '#f59e0b';
      case 'fault': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{
          background: 'rgba(0, 0, 0, 0.8)',
          padding: '8px 12px',
          borderRadius: '6px',
          color: 'white',
          fontSize: '0.9rem'
        }}>
          <p>{`Asset: ${label}`}</p>
          <p style={{ color: '#4ade80' }}>{`Voltage: ${data.voltage.toFixed(1)} kV`}</p>
          <p style={{ color: getBarColor(data.status) }}>{`Status: ${data.status}`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ChartContainer>
      <ChartTitle>Voltage Profile Across Assets</ChartTitle>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={voltageData}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
          <XAxis 
            dataKey="name" 
            stroke="rgba(255, 255, 255, 0.7)"
            fontSize={12}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis 
            stroke="rgba(255, 255, 255, 0.7)"
            fontSize={12}
            label={{ value: 'Voltage (kV)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey="voltage" 
            fill="#4ade80"
            radius={[4, 4, 0, 0]}
          >
            {voltageData.map((entry, index) => (
              <Bar 
                key={`cell-${index}`} 
                fill={getBarColor(entry.status)} 
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

export default VoltageProfileChart;