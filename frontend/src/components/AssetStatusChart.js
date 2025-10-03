import React from 'react';
import styled from 'styled-components';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

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
  margin-bottom: 1rem;
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

const ChartWrapper = styled.div`
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-top: 1rem;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
  }
`;

const Legend = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  flex: 1;
`;

const LegendItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  background: ${props => `${props.color}10`};
  border-radius: 0.375rem;
  border-left: 3px solid ${props => props.color};
  transition: all 0.2s ease;

  &:hover {
    background: ${props => `${props.color}20`};
    transform: translateX(4px);
  }
`;

const LegendLabel = styled.div`
  display: flex;
  align-items: center;
  gap: 0.625rem;
  font-size: 0.8125rem;
  color: hsl(215.4 16.3% 46.9%);
  font-weight: 500;
`;

const LegendDot = styled.div`
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: ${props => props.color};
`;

const LegendValue = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const LegendCount = styled.span`
  font-size: 0.875rem;
  font-weight: 600;
  color: hsl(222.2 84% 4.9%);
`;

const LegendPercent = styled.span`
  font-size: 0.75rem;
  color: hsl(215.4 16.3% 46.9%);
  background: hsl(210 40% 96.1%);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
`;

/**
 * AssetStatusChart - Donut chart showing asset health distribution
 *
 * Expected Backend Format (from /api/assets):
 * {
 *   "assets": [
 *     {
 *       "id": "TX1_400_220",
 *       "name": "TX1 Main Transformer",
 *       "status": "operational",  // operational, warning, fault, maintenance
 *       "health": 95.0,
 *       "parameters": { ... }
 *     }
 *   ],
 *   "total_assets": 76
 * }
 */
const AssetStatusChart = ({ assets }) => {
  const COLORS = {
    operational: '#10b981',  // Green
    healthy: '#10b981',      // Green (same as operational)
    warning: '#f59e0b',      // Amber
    fault: '#ef4444',        // Red
    maintenance: '#3b82f6', // Blue
    offline: '#6b7280'       // Gray
  };

  function getStatusColor(status) {
    return COLORS[status?.toLowerCase()] || '#94a3b8';
  }

  // Handle both array and object formats from backend
  const assetsArray = Array.isArray(assets)
    ? assets
    : (assets?.assets || []);

  // Count assets by status
  const statusCounts = assetsArray.reduce((acc, asset) => {
    const status = (asset.status || 'operational').toLowerCase();
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});

  // Use dummy data if no real data available (in backend format)
  const hasCounts = Object.keys(statusCounts).length > 0;
  const finalCounts = hasCounts ? statusCounts : {
    operational: 65,
    warning: 8,
    fault: 2,
    maintenance: 1
  };

  const data = Object.entries(finalCounts).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
    color: getStatusColor(status)
  }));

  const total = data.reduce((sum, item) => sum + item.value, 0);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      const percentage = ((data.value / total) * 100).toFixed(1);
      return (
        <div style={{
          background: 'white',
          padding: '0.75rem',
          borderRadius: '0.5rem',
          border: '1px solid #e5e7eb',
          boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
          minWidth: '150px'
        }}>
          <div style={{
            fontWeight: 600,
            fontSize: '0.8125rem',
            marginBottom: '0.5rem',
            color: data.payload.color,
            textTransform: 'capitalize'
          }}>
            {data.name}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
            <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>Assets:</span>
            <span style={{ fontWeight: 600, fontSize: '0.8125rem', color: '#1f2937' }}>
              {data.value}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
            <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>Percentage:</span>
            <span style={{ fontWeight: 600, fontSize: '0.8125rem', color: '#1f2937' }}>
              {percentage}%
            </span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Asset Health Overview</CardTitle>
        <CardDescription>Distribution of {total} assets by operational status</CardDescription>
      </CardHeader>
      <ChartWrapper>
        <ResponsiveContainer width="50%" height={220}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color}
                  stroke={entry.color}
                  strokeWidth={2}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        <Legend>
          {data.map((item) => {
            const percentage = ((item.value / total) * 100).toFixed(1);
            return (
              <LegendItem key={item.name} color={item.color}>
                <LegendLabel>
                  <LegendDot color={item.color} />
                  <span>{item.name}</span>
                </LegendLabel>
                <LegendValue>
                  <LegendCount>{item.value}</LegendCount>
                  <LegendPercent>{percentage}%</LegendPercent>
                </LegendValue>
              </LegendItem>
            );
          })}
        </Legend>
      </ChartWrapper>
    </Card>
  );
};

export default AssetStatusChart;
