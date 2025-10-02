import React from 'react';
import styled from 'styled-components';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Cell, LabelList } from 'recharts';
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

const VoltageProfileChart = ({ assets }) => {
  const assetsObj = Array.isArray(assets)
    ? assets.reduce((acc, asset) => ({ ...acc, [asset.id || asset.name]: asset }), {})
    : (assets || {});

  let voltageData = Object.entries(assetsObj)
    .filter(([_, asset]) => {
      if (!asset || !asset.parameters) return false;
      const measuredVoltage = asset.parameters.hv_voltage || asset.parameters.lv_voltage;
      return measuredVoltage && measuredVoltage > 0;
    })
    .map(([assetId, asset]) => {
      const measuredVoltage = asset.parameters.hv_voltage || asset.parameters.lv_voltage || 0;

      return {
        name: asset.name || assetId,
        voltage: measuredVoltage,
        ratedVoltage: parseFloat((asset.parameters.voltage || '0').replace(/[^\d.]/g, '')),
        status: asset.status
      };
    })
    .sort((a, b) => b.voltage - a.voltage)
    .slice(0, 20);

  if (voltageData.length === 0) {
    voltageData = [
      { name: 'TX1', voltage: 398.5, ratedVoltage: 400, status: 'operational' },
      { name: 'TX2', voltage: 397.8, ratedVoltage: 400, status: 'operational' },
      { name: 'CB_400kV', voltage: 399.2, ratedVoltage: 400, status: 'operational' },
      { name: 'CB_220kV_1', voltage: 219.5, ratedVoltage: 220, status: 'operational' },
      { name: 'CB_220kV_2', voltage: 218.9, ratedVoltage: 220, status: 'warning' },
      { name: 'BUS1', voltage: 398.1, ratedVoltage: 400, status: 'operational' },
      { name: 'BUS2', voltage: 219.2, ratedVoltage: 220, status: 'operational' },
      { name: 'LINE1', voltage: 397.5, ratedVoltage: 400, status: 'operational' }
    ];
  }

  const getBarColor = (status) => {
    switch (status) {
      case 'operational': return 'hsl(221.2 83.2% 53.3%)';
      case 'healthy': return 'hsl(221.2 83.2% 53.3%)';
      case 'warning': return 'hsl(47.9 95.8% 53.1%)';
      case 'fault': return 'hsl(0 84.2% 60.2%)';
      default: return 'hsl(262.1 83.3% 57.8%)';
    }
  };

  const chartConfig = {
    voltage: {
      label: 'Voltage (kV)',
      color: 'hsl(221.2 83.2% 53.3%)'
    }
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const deviation = data.ratedVoltage ? ((data.voltage - data.ratedVoltage) / data.ratedVoltage * 100).toFixed(2) : 0;
      return (
        <div style={{
          background: 'white',
          padding: '0.75rem',
          borderRadius: '0.5rem',
          border: '1px solid hsl(214.3 31.8% 91.4%)',
          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
          color: 'hsl(222.2 84% 4.9%)',
          fontSize: '0.8125rem'
        }}>
          <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>{label}</p>
          <p style={{ color: 'hsl(221.2 83.2% 53.3%)', fontWeight: 500, marginBottom: '0.25rem' }}>
            {`Measured: ${data.voltage.toFixed(2)} kV`}
          </p>
          {data.ratedVoltage > 0 && (
            <>
              <p style={{ color: 'hsl(215.4 16.3% 46.9%)', marginBottom: '0.25rem' }}>
                {`Rated: ${data.ratedVoltage} kV`}
              </p>
              <p style={{
                color: Math.abs(deviation) > 5 ? 'hsl(47.9 95.8% 53.1%)' : 'hsl(221.2 83.2% 53.3%)',
                fontWeight: 500,
                marginBottom: '0.25rem'
              }}>
                {`Deviation: ${deviation > 0 ? '+' : ''}${deviation}%`}
              </p>
            </>
          )}
          <p style={{
            color: getBarColor(data.status),
            textTransform: 'capitalize',
            fontWeight: 500
          }}>
            {`Status: ${data.status}`}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Voltage Profile Across Assets</CardTitle>
        <CardDescription>Real-time voltage measurements for {voltageData.length} key assets</CardDescription>
      </CardHeader>
      <ChartContainer config={chartConfig}>
        <ResponsiveContainer width="100%" height={Math.max(300, voltageData.length * 35)}>
          <BarChart
            data={voltageData}
            layout="horizontal"
            margin={{ top: 5, right: 50, left: 10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(214.3 31.8% 91.4%)" horizontal={false} />
            <XAxis
              type="number"
              stroke="hsl(215.4 16.3% 46.9%)"
              fontSize={12}
              tick={{ fill: 'hsl(215.4 16.3% 46.9%)' }}
              tickLine={false}
              axisLine={false}
              hide
            />
            <YAxis
              dataKey="name"
              type="category"
              stroke="hsl(215.4 16.3% 46.9%)"
              fontSize={12}
              tick={{ fill: 'hsl(215.4 16.3% 46.9%)' }}
              tickLine={false}
              axisLine={false}
              width={0}
              hide
            />
            <ChartTooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(210 40% 96.1%)' }} />
            <Bar
              dataKey="voltage"
              radius={4}
            >
              {voltageData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.status)} />
              ))}
              <LabelList
                dataKey="name"
                position="insideLeft"
                offset={8}
                style={{ fill: 'white', fontSize: 12, fontWeight: 500 }}
              />
              <LabelList
                dataKey="voltage"
                position="right"
                offset={8}
                style={{ fill: 'hsl(222.2 84% 4.9%)', fontSize: 12, fontWeight: 500 }}
                formatter={(value) => `${value.toFixed(2)} kV`}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartContainer>
    </Card>
  );
};

export default VoltageProfileChart;
