import React, { useEffect } from 'react';
import styled from 'styled-components';
import { useDigitalTwin } from '../context/DigitalTwinContext';
import MetricCard from '../components/MetricCard';
import AssetStatusChart from '../components/AssetStatusChart';
import PowerFlowChart from '../components/PowerFlowChart';
import VoltageProfileChart from '../components/VoltageProfileChart';
import RecentAlerts from '../components/RecentAlerts';

const DashboardContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
`;

const DashboardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`;

const Title = styled.h1`
  color: white;
  font-size: 2rem;
  font-weight: 600;
`;

const LastUpdated = styled.div`
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
`;

const ChartsGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const FullWidthChart = styled.div`
  grid-column: 1 / -1;
`;

const Dashboard = () => {
  const { metrics, assets, fetchMetrics, fetchAssets } = useDigitalTwin();

  useEffect(() => {
    fetchMetrics();
    fetchAssets();
  }, [fetchMetrics, fetchAssets]);

  const metricCards = [
    {
      title: 'Total Power',
      value: `${metrics.total_power?.toFixed(1) || 0} MW`,
      icon: '⚡',
      color: '#4ade80',
      trend: '+2.3%'
    },
    {
      title: 'Efficiency',
      value: `${metrics.efficiency?.toFixed(1) || 0}%`,
      icon: '📊',
      color: '#3b82f6',
      trend: '+0.5%'
    },
    {
      title: 'Voltage Stability',
      value: `${metrics.voltage_stability?.toFixed(1) || 0}%`,
      icon: '📈',
      color: '#8b5cf6',
      trend: '+1.2%'
    },
    {
      title: 'Frequency',
      value: `${metrics.frequency?.toFixed(2) || 0} Hz`,
      icon: '🔄',
      color: '#f59e0b',
      trend: '±0.1%'
    }
  ];

  return (
    <DashboardContainer>
      <DashboardHeader>
        <Title>🇮🇳 Substation Overview</Title>
        <LastUpdated>
          Last updated: {new Date().toLocaleTimeString()}
        </LastUpdated>
      </DashboardHeader>

      <MetricsGrid>
        {metricCards.map((metric, index) => (
          <MetricCard
            key={index}
            title={metric.title}
            value={metric.value}
            icon={metric.icon}
            color={metric.color}
            trend={metric.trend}
          />
        ))}
      </MetricsGrid>

      <ChartsGrid>
        <AssetStatusChart assets={assets} />
        <PowerFlowChart metrics={metrics} />
      </ChartsGrid>

      <FullWidthChart>
        <VoltageProfileChart assets={assets} />
      </FullWidthChart>

      <RecentAlerts />
    </DashboardContainer>
  );
};

export default Dashboard;