import React from 'react';
import styled from 'styled-components';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const ChartContainer = styled.div`
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  padding: 1.5rem;
  color: #f1f5f9;
`;

const ChartTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #f1f5f9;
`;

const VoltageProfileChart = ({ assets }) => {
  // Extract voltage data from assets - handle arrays and objects
  const assetsObj = Array.isArray(assets)
    ? assets.reduce((acc, asset) => ({ ...acc, [asset.id || asset.name]: asset }), {})
    : (assets || {});

  const voltageData = Object.entries(assetsObj)
    .filter(([_, asset]) => {
      if (!asset || !asset.parameters) return false;
      // Extract voltage value from parameters.voltage string (e.g., "400 kV" -> 400)
      const voltageStr = asset.parameters.voltage || asset.parameters.hv_voltage || '';
      const voltageNum = typeof voltageStr === 'string'
        ? parseFloat(voltageStr.replace(/[^\d.]/g, ''))
        : voltageStr;
      return voltageNum > 0;
    })
    .map(([assetId, asset]) => {
      // Extract voltage value from parameters
      const voltageStr = asset.parameters.voltage || asset.parameters.hv_voltage || '0';
      const voltageNum = typeof voltageStr === 'string'
        ? parseFloat(voltageStr.replace(/[^\d.]/g, ''))
        : voltageStr;

      return {
        name: asset.name || assetId,
        voltage: voltageNum,
        status: asset.status
      };
    })
    .sort((a, b) => b.voltage - a.voltage)
    .slice(0, 20); // Show top 20 assets

  const getBarColor = (status) => {
    switch (status) {
      case 'operational': return '#4ade80';
      case 'healthy': return '#4ade80';
      case 'warning': return '#f59e0b';
      case 'fault': return '#ef4444';
      default: return '#3b82f6';
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
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="name"
            stroke="#94a3b8"
            fontSize={12}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis
            stroke="#94a3b8"
            fontSize={12}
            label={{ value: 'Voltage (kV)', angle: -90, position: 'insideLeft', style: { fill: '#94a3b8' } }}
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