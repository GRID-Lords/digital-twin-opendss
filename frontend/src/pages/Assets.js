import React, { useState } from 'react';
import styled from 'styled-components';
import { useDigitalTwin } from '../context/DigitalTwinContext';
import { Cpu, Activity, Settings, Power } from 'lucide-react';
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
  color: #f1f5f9;
  font-size: 2rem;
  font-weight: 700;
`;

const ControlButton = styled.button`
  background: #334155;
  border: 1px solid #475569;
  color: #f1f5f9;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  font-weight: 500;

  &:hover {
    background: #475569;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  }
`;

const AssetsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
`;

const AssetCard = styled.div`
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  padding: 1.5rem;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
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
  color: #f1f5f9;
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
      case 'operational': return '#dcfce7';
      case 'healthy': return '#dcfce7';
      case 'warning': return '#fed7aa';
      case 'fault': return '#fee2e2';
      case 'closed': return '#dbeafe';
      default: return '#f3f4f6';
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'operational': return '#166534';
      case 'healthy': return '#166534';
      case 'warning': return '#c2410c';
      case 'fault': return '#991b1b';
      case 'closed': return '#1e40af';
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
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const MetricValue = styled.div`
  font-size: 1.1rem;
  font-weight: 600;
  color: #f1f5f9;
`;

const AssetActions = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
`;

const ActionButton = styled.button`
  background: ${props => props.variant === 'danger' ? '#fee2e2' : '#f1f5f9'};
  border: 1px solid ${props => props.variant === 'danger' ? '#fecaca' : '#e2e8f0'};
  color: ${props => props.variant === 'danger' ? '#991b1b' : '#0f172a'};
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.8rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.25rem;

  &:hover {
    background: ${props => props.variant === 'danger' ? '#fecaca' : '#e2e8f0'};
  }
`;

const Assets = () => {
  const { assets, controlAsset, loading } = useDigitalTwin();
  const [selectedAsset, setSelectedAsset] = useState(null);

  // Convert assets array to the expected format or use as-is if already an object
  const assetsData = Array.isArray(assets) ? assets : Object.values(assets || {});

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
      case 'PowerTransformer': return <Cpu />;
      case 'DistributionTransformer': return <Cpu />;
      case 'CircuitBreaker': return <Power />;
      case 'IndustrialLoad': return <Activity />;
      default: return <Settings />;
    }
  };

  const getAvailableActions = (asset) => {
    const actions = [];
    const assetType = asset.type || asset.asset_type;

    if (assetType === 'circuit_breaker' || assetType === 'CircuitBreaker') {
      if (asset.status === 'operational' || asset.status === 'healthy') {
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
        <Title>Asset Management</Title>
        <ControlButton>
          <Settings />
          Bulk Operations
        </ControlButton>
      </PageHeader>

      <AssetsGrid>
        {assetsData.map((asset) => (
          <AssetCard key={asset.id}>
            <AssetHeader>
              <AssetName>
                {getAssetIcon(asset.type || asset.asset_type)}
                {asset.name || asset.id}
              </AssetName>
              <AssetStatus status={asset.status || 'operational'}>
                {asset.status || 'operational'}
              </AssetStatus>
            </AssetHeader>

            <AssetMetrics>
              <Metric>
                <MetricLabel>Voltage</MetricLabel>
                <MetricValue>{asset.parameters?.voltage || 'N/A'}</MetricValue>
              </Metric>
              <Metric>
                <MetricLabel>Rating</MetricLabel>
                <MetricValue>{asset.parameters?.rating || 'N/A'}</MetricValue>
              </Metric>
              <Metric>
                <MetricLabel>Temperature</MetricLabel>
                <MetricValue>{asset.parameters?.temperature || 'N/A'}</MetricValue>
              </Metric>
              <Metric>
                <MetricLabel>Health</MetricLabel>
                <MetricValue>{typeof asset.health === 'number' ? asset.health.toFixed(1) : '0'}%</MetricValue>
              </Metric>
            </AssetMetrics>

            <AssetActions>
              {getAvailableActions(asset).map((action) => (
                <ActionButton
                  key={action.action}
                  variant={action.variant}
                  onClick={() => handleControlAsset(asset.id, action.action)}
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