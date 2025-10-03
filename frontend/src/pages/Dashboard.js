import React from 'react';
import styled from 'styled-components';
import { useDigitalTwin } from '../context/DigitalTwinContext';
import MetricCard from '../components/MetricCard';
import AlertsTable from '../components/AlertsTable';
import AssetStatusChart from '../components/AssetStatusChart';
import PowerFlowChart from '../components/PowerFlowChart';
import VoltageProfileChart from '../components/VoltageProfileChart';

const DashboardContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const DashboardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
`;

const Title = styled.h1`
  color: #0f172a;
  font-size: 1.5rem;
  font-weight: 600;
`;

const LastUpdated = styled.div`
  color: #64748b;
  font-size: 0.8125rem;
  font-weight: 500;
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
`;

const ChartsGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;

  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const FullWidthChart = styled.div`
  grid-column: 1 / -1;
`;

const Dashboard = () => {
  const { metrics, assets } = useDigitalTwin();
  const [lastUpdated, setLastUpdated] = React.useState(new Date());

  // Update timestamp when metrics change
  React.useEffect(() => {
    if (metrics && Object.keys(metrics).length > 0) {
      setLastUpdated(new Date());
    }
  }, [metrics]);

  // No need to fetch on mount - DigitalTwinContext already handles auto-refresh

  const metricCards = [
    {
      title: 'Total Power',
      value: `${metrics.total_power?.toFixed(2) || 0} MW`,
      icon: '',
      color: '#10b981',
      trend: '+2.3%'
    },
    {
      title: 'Efficiency',
      value: `${metrics.efficiency?.toFixed(2) || 0}%`,
      icon: '',
      color: '#3b82f6',
      trend: '+0.5%'
    },
    {
      title: 'Voltage Stability',
      value: `${metrics.voltage_stability?.toFixed(2) || 0}%`,
      icon: '',
      color: '#8b5cf6',
      trend: '+1.2%'
    },
    {
      title: 'Frequency',
      value: `${metrics.frequency?.toFixed(2) || 0} Hz`,
      icon: '',
      color: '#f59e0b',
      trend: '±0.1%'
    }
  ];

  return (
    <DashboardContainer>
      <DashboardHeader>
        <Title>Substation Overview</Title>
        <LastUpdated>
          Last updated: {lastUpdated.toLocaleTimeString()}
        </LastUpdated>
      </DashboardHeader>

      <MetricsGrid>
        {metricCards.map((metric) => (
          <MetricCard
            key={metric.title}
            title={metric.title}
            value={metric.value}
            icon={metric.icon}
            color={metric.color}
            trend={metric.trend}
          />
        ))}
      </MetricsGrid>

      <AlertsTable />

      <ChartsGrid>
        <AssetStatusChart assets={assets} />
        <PowerFlowChart metrics={metrics} />
        <FullWidthChart>
          <VoltageProfileChart assets={assets} />
        </FullWidthChart>
      </ChartsGrid>
    </DashboardContainer>
  );
};

export default Dashboard;