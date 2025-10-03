import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from 'recharts';
import axios from 'axios';

const Card = styled.div`
  background: hsl(0 0% 100%);
  border: 1px solid hsl(214.3 31.8% 91.4%);
  border-radius: 0.5rem;
  padding: 1.5rem;
`;

const CardHeader = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
`;

const CardTitle = styled.h3`
  font-size: 0.875rem;
  font-weight: 600;
  color: hsl(222.2 84% 4.9%);
  letter-spacing: -0.025em;
`;

const CardDescription = styled.p`
  font-size: 0.875rem;
  color: hsl(215.4 16.3% 46.9%);
  line-height: 1.5;
`;

/**
 * PowerFlowChart - Displays power flow and efficiency trends
 *
 * Expected Backend Format (from /api/historical/power-flow?hours=24):
 * {
 *   "start": "2025-10-03T10:00:00+05:30",
 *   "end": "2025-10-03T18:00:00+05:30",
 *   "resolution": "15m",
 *   "data": [
 *     {
 *       "timestamp": "2025-10-03T10:00:00+05:30",
 *       "activePower": 250.5,
 *       "reactivePower": 50.2,
 *       "apparentPower": 255.0,
 *       "powerFactor": 0.95
 *     }
 *   ],
 *   "summary": {
 *     "avgActivePower": 245.3,
 *     "maxActivePower": 280.1,
 *     "minActivePower": 180.5,
 *     "totalEnergy": 5880.0
 *   }
 * }
 */
const PowerFlowChart = ({ metrics = {} }) => {
  // Generate dummy data function (outside useEffect so we can use it for initial state)
  const generateBackendFormatDummyData = () => {
    // Generate dummy data matching backend API response format
    const now = new Date();
    const backendData = [];

    for (let i = 23; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);
      const hour = timestamp.getHours();

      // Realistic daily load pattern (IST hours)
      let loadFactor;
      if (hour >= 6 && hour < 10) {
        // Morning ramp (6am - 10am)
        loadFactor = 0.7 + (hour - 6) * 0.075;
      } else if (hour >= 10 && hour < 12) {
        // Peak morning (10am - 12pm)
        loadFactor = 1.0;
      } else if (hour >= 12 && hour < 17) {
        // Afternoon dip (12pm - 5pm)
        loadFactor = 0.85;
      } else if (hour >= 17 && hour < 21) {
        // Evening peak (5pm - 9pm)
        loadFactor = 0.95;
      } else {
        // Night (9pm - 6am)
        loadFactor = 0.6;
      }

      const baseLoad = 250; // MW
      const activePower = baseLoad * loadFactor + (Math.random() - 0.5) * 20;
      const reactivePower = activePower * 0.3 + (Math.random() - 0.5) * 10;
      const apparentPower = Math.sqrt(activePower ** 2 + reactivePower ** 2);
      const powerFactor = activePower / apparentPower;

      backendData.push({
        timestamp: timestamp.toISOString(),
        activePower: Math.round(activePower * 100) / 100,
        reactivePower: Math.round(reactivePower * 100) / 100,
        apparentPower: Math.round(apparentPower * 100) / 100,
        powerFactor: Math.round(powerFactor * 1000) / 1000
      });
    }

    // Transform to chart format (same as real data)
    return backendData.map(point => ({
      time: new Date(point.timestamp).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
        timeZone: 'Asia/Kolkata'
      }),
      power: point.activePower,
      powerFactor: point.powerFactor * 100 // Convert to percentage (0.95 -> 95%)
    }));
  };

  // Initialize with dummy data so chart is always visible
  const [data, setData] = useState(generateBackendFormatDummyData());

  useEffect(() => {
    const fetchHistoricalData = async () => {
      try {
        const response = await axios.get('/api/historical/power-flow?hours=24&resolution=1h');
        const historicalData = response.data.data || [];

        // Only update if we got data
        if (historicalData.length > 0) {
          // Transform backend data to chart format
          const formattedData = historicalData.map(point => ({
            time: new Date(point.timestamp).toLocaleTimeString('en-IN', {
              hour: '2-digit',
              minute: '2-digit',
              hour12: false,
              timeZone: 'Asia/Kolkata'
            }),
            power: point.activePower || 0,
            powerFactor: (point.powerFactor || 0.95) * 100 // Convert to percentage
          }));

          setData(formattedData);
        }
      } catch (error) {
        console.error('Error fetching power flow data:', error);
        // Keep using the initial dummy data (already set in state)
      }
    };

    fetchHistoricalData();
    const interval = setInterval(fetchHistoricalData, 300000); // 5 minutes

    return () => clearInterval(interval);
  }, []);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{
          background: 'white',
          padding: '0.75rem',
          borderRadius: '0.5rem',
          border: '1px solid #e5e7eb',
          boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
          minWidth: '180px'
        }}>
          <div style={{
            fontWeight: 600,
            fontSize: '0.8125rem',
            marginBottom: '0.5rem',
            color: '#1f2937',
            borderBottom: '1px solid #e5e7eb',
            paddingBottom: '0.375rem'
          }}>
            {data.time}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>Power:</span>
              <span style={{ fontWeight: 600, fontSize: '0.8125rem', color: '#3b82f6' }}>
                {data.power.toFixed(2)} MW
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>Power Factor:</span>
              <span style={{ fontWeight: 600, fontSize: '0.8125rem', color: '#f65c5cff' }}>
                {data.powerFactor.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Power Flow & Power Factor</CardTitle>
        <CardDescription>24-hour trend showing active power consumption and power factor</CardDescription>
      </CardHeader>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorPower" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorPowerFactor" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f65c5cff" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#f65c5cff" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(214.3 31.8% 91.4%)" vertical={false} />
          <XAxis
            dataKey="time"
            stroke="hsl(215.4 16.3% 46.9%)"
            fontSize={12}
            tick={{ fill: 'hsl(215.4 16.3% 46.9%)' }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="hsl(215.4 16.3% 46.9%)"
            fontSize={12}
            tick={{ fill: 'hsl(215.4 16.3% 46.9%)' }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(210 40% 96.1%)' }} />
          <Area
            type="monotone"
            dataKey="power"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#colorPower)"
            name="Power (MW)"
          />
          <Area
            type="monotone"
            dataKey="powerFactor"
            stroke="#f65c5cff"
            strokeWidth={2}
            fill="url(#colorPowerFactor)"
            name="Power Factor (%)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default PowerFlowChart;
