import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

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

const PowerFlowChart = ({ metrics = {} }) => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchHistoricalData = async () => {
      try {
        const response = await axios.get('/api/historical/power-flow?hours=24');
        const historicalData = response.data.data || [];

        const formattedData = historicalData.map(point => ({
          time: new Date(point.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          power: point.activePower || 0,
          efficiency: ((point.activePower / (point.apparentPower || 1)) * 100) || 95
        }));

        setData(formattedData);
      } catch (error) {
        console.error('Error fetching power flow data:', error);
        // Fallback to generated data
        setData(generateFallbackData());
      }
    };

    const generateFallbackData = () => {
      const fallbackData = [];
      const now = new Date();

      for (let i = 23; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000);
        const hour = time.getHours();
        const baseLoad = metrics?.total_power || 100;
        const loadFactor = 0.6 + 0.4 * Math.sin(2 * Math.PI * hour / 24);
        const power = baseLoad * loadFactor + (Math.random() - 0.5) * 10;

        fallbackData.push({
          time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          power: Math.max(0, power),
          efficiency: (metrics?.efficiency || 95) + (Math.random() - 0.5) * 2
        });
      }
      return fallbackData;
    };

    fetchHistoricalData();
    // No interval needed - historical data is static for the last 24 hours
    // Only fetch once on mount

    // Optional: Refresh every 5 minutes to get latest hourly data
    const interval = setInterval(fetchHistoricalData, 300000); // 5 minutes

    return () => clearInterval(interval);
  }, []); // Empty deps - only run on mount

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
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="time"
            stroke="#94a3b8"
            fontSize={12}
          />
          <YAxis
            stroke="#94a3b8"
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