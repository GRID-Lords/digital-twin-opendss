import React, { useState } from 'react';
import styled from 'styled-components';
import { useDigitalTwin } from '../context/DigitalTwinContext';
import { FiCpu, FiActivity, FiSettings, FiPower } from 'react-icons/fi';
import toast from 'react-hot-toast';

const AssetsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
`;

const PageHeader = styled.div`
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

const ControlButton = styled.button`
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
`;

const AssetsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
`;

const AssetCard = styled.div`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
  color: white;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
  }
`;

const AssetHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`;

const AssetName = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const AssetStatus = styled.div`
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
  background: ${props => {
    switch (props.status) {
      case 'healthy': return 'rgba(74, 222, 128, 0.2)';
      case 'warning': return 'rgba(245, 158, 11, 0.2)';
      case 'fault': return 'rgba(239, 68, 68, 0.2)';
      default: return 'rgba(107, 114, 128, 0.2)';
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'healthy': return '#4ade80';
      case 'warning': return '#f59e0b';
      case 'fault': return '#ef4444';
      default: return '#6b7280';
    }
  }};
`;

const AssetMetrics = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
`;

const Metric = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const MetricLabel = styled.div`
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const MetricValue = styled.div`
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
`;

const AssetActions = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
`;

const ActionButton = styled.button`
  background: ${props => props.variant === 'danger' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255, 255, 255, 0.1)'};
  border: 1px solid ${props => props.variant === 'danger' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(255, 255, 255, 0.2)'};
  color: ${props => props.variant === 'danger' ? '#ef4444' : 'white'};
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  
  &:hover {
    background: ${props => props.variant === 'danger' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(255, 255, 255, 0.2)'};
  }
`;

const Assets = () => {
  const { assets, controlAsset, loading } = useDigitalTwin();
  const [selectedAsset, setSelectedAsset] = useState(null);

  const handleControlAsset = async (assetId, action) => {
    try {
      await controlAsset(assetId, action);
      toast.success(`Asset ${assetId} ${action} completed`);
    } catch (error) {
      toast.error(`Failed to ${action} asset ${assetId}`);
    }
  };

  const getAssetIcon = (assetType) => {
    switch (assetType) {
      case 'PowerTransformer': return <FiCpu />;
      case 'DistributionTransformer': return <FiCpu />;
      case 'CircuitBreaker': return <FiPower />;
      case 'IndustrialLoad': return <FiActivity />;
      default: return <FiSettings />;
    }
  };

  const getAvailableActions = (asset) => {
    const actions = [];
    
    if (asset.asset_type === 'CircuitBreaker') {
      if (asset.status === 'healthy') {
        actions.push({ action: 'open', label: 'Open', variant: 'danger' });
      } else {
        actions.push({ action: 'close', label: 'Close', variant: 'default' });
      }
    }
    
    if (asset.status === 'fault') {
      actions.push({ action: 'reset', label: 'Reset', variant: 'default' });
    }
    
    return actions;
  };

  if (loading) {
    return (
      <AssetsContainer>
        <Title>Loading Assets...</Title>
      </AssetsContainer>
    );
  }

  return (
    <AssetsContainer>
      <PageHeader>
        <Title>🏭 Asset Management</Title>
        <ControlButton>
          <FiSettings />
          Bulk Operations
        </ControlButton>
      </PageHeader>

      <AssetsGrid>
        {Object.entries(assets).map(([assetId, asset]) => (
          <AssetCard key={assetId}>
            <AssetHeader>
              <AssetName>
                {getAssetIcon(asset.asset_type)}
                {assetId}
              </AssetName>
              <AssetStatus status={asset.status}>
                {asset.status}
              </AssetStatus>
            </AssetHeader>

            <AssetMetrics>
              <Metric>
                <MetricLabel>Voltage</MetricLabel>
                <MetricValue>{asset.voltage?.toFixed(1) || 0} kV</MetricValue>
              </Metric>
              <Metric>
                <MetricLabel>Power</MetricLabel>
                <MetricValue>{asset.power?.toFixed(1) || 0} kW</MetricValue>
              </Metric>
              <Metric>
                <MetricLabel>Temperature</MetricLabel>
                <MetricValue>{asset.temperature?.toFixed(1) || 0}°C</MetricValue>
              </Metric>
              <Metric>
                <MetricLabel>Health</MetricLabel>
                <MetricValue>{asset.health_score?.toFixed(1) || 0}%</MetricValue>
              </Metric>
            </AssetMetrics>

            <AssetActions>
              {getAvailableActions(asset).map((action) => (
                <ActionButton
                  key={action.action}
                  variant={action.variant}
                  onClick={() => handleControlAsset(assetId, action.action)}
                >
                  {action.label}
                </ActionButton>
              ))}
            </AssetActions>
          </AssetCard>
        ))}
      </AssetsGrid>
    </AssetsContainer>
  );
};

export default Assets;