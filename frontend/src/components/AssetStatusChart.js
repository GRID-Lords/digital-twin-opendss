import React from 'react';
import styled from 'styled-components';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts';
import { ChartContainer, ChartTooltip } from './ui/chart';

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

const Legend = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid hsl(214.3 31.8% 91.4%);
`;

const LegendItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const LegendDot = styled.div`
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  background: ${props => props.color};
`;

const LegendLabel = styled.div`
  font-size: 0.875rem;
  color: hsl(215.4 16.3% 46.9%);
  display: flex;
  gap: 0.5rem;

  strong {
    color: hsl(222.2 84% 4.9%);
    font-weight: 600;
  }
`;

const AssetStatusChart = ({ assets }) => {
  const COLORS = {
    operational: 'hsl(142.1 76.2% 36.3%)',
    healthy: 'hsl(142.1 76.2% 36.3%)',
    warning: 'hsl(47.9 95.8% 53.1%)',
    fault: 'hsl(0 84.2% 60.2%)',
    maintenance: 'hsl(221.2 83.2% 53.3%)',
    undefined: 'hsl(215 20.2% 65.1%)'
  };

  function getStatusColor(status) {
    return COLORS[status] || 'hsl(215 20.2% 65.1%)';
  }

  const statusCounts = Object.values(assets || {}).reduce((acc, asset) => {
    const status = asset.status || 'operational';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});

  const hasCounts = Object.keys(statusCounts).length > 0 && !statusCounts['undefined'];
  const finalCounts = hasCounts ? statusCounts : {
    operational: 12,
    warning: 3,
    fault: 1,
    maintenance: 2
  };

  const data = Object.entries(finalCounts).map(([status, count]) => ({
    status: status.charAt(0).toUpperCase() + status.slice(1),
    count: count,
    fill: getStatusColor(status)
  }));

  const total = data.reduce((sum, item) => sum + item.count, 0);

  const chartConfig = {
    operational: { label: 'Operational', color: COLORS.operational },
    warning: { label: 'Warning', color: COLORS.warning },
    fault: { label: 'Fault', color: COLORS.fault },
    maintenance: { label: 'Maintenance', color: COLORS.maintenance }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Asset Status Distribution</CardTitle>
        <CardDescription>Showing {total} total assets across all statuses</CardDescription>
      </CardHeader>
      <ChartContainer config={chartConfig}>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data} layout="vertical" margin={{ left: 0, right: 0 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="status"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(215.4 16.3% 46.9%)', fontSize: 12 }}
              width={100}
            />
            <ChartTooltip content={<ChartTooltip />} cursor={{ fill: 'hsl(210 40% 96.1%)' }} />
            <Bar dataKey="count" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartContainer>
      <Legend>
        {data.map((item) => (
          <LegendItem key={item.status}>
            <LegendDot color={item.fill} />
            <LegendLabel>
              <span>{item.status}</span>
              <strong>{item.count}</strong>
            </LegendLabel>
          </LegendItem>
        ))}
      </Legend>
    </Card>
  );
};

export default AssetStatusChart;
