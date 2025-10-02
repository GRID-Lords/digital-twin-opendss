import React, { useState } from 'react';
import styled from 'styled-components';
import { FiMonitor, FiDownload, FiRefreshCw, FiMaximize2, FiCpu, FiGrid } from 'react-icons/fi';
import toast from 'react-hot-toast';
import SubstationVisualization2D from '../components/SubstationVisualization2D';
import SubstationVisualization3D from '../components/SubstationVisualization3D';
import AnomalySimulationPanel from '../components/AnomalySimulationPanel';

const VisualizationContainer = styled.div`
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
  font-weight: 600;
`;

const ControlButtons = styled.div`
  display: flex;
  gap: 1rem;
`;

const ControlButton = styled.button`
  background: ${props => props.active ? 'rgba(99, 102, 241, 0.8)' : '#334155'};
  border: 1px solid ${props => props.active ? '#6366f1' : '#475569'};
  color: #f1f5f9;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:hover {
    background: ${props => props.active ? 'rgba(99, 102, 241, 0.9)' : '#475569'};
  }
`;

const TabButtons = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 0;
`;

const TabButton = styled.button`
  background: ${props => props.active ? 'rgba(99, 102, 241, 0.8)' : '#334155'};
  border: 1px solid ${props => props.active ? '#6366f1' : '#475569'};
  color: #f1f5f9;
  padding: 1rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: ${props => props.active ? '600' : '400'};

  &:hover {
    background: ${props => props.active ? 'rgba(99, 102, 241, 0.9)' : '#475569'};
    transform: translateY(-2px);
  }

  svg {
    font-size: 1.2rem;
  }
`;

const VisualizationWrapper = styled.div`
  background: #1e293b;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  padding: 2rem;
  min-height: 600px;
`;

const InfoBar = styled.div`
  display: flex;
  justify-content: space-around;
  background: #1e293b;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 2rem;
`;

const InfoItem = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const InfoLabel = styled.span`
  color: #94a3b8;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
`;

const InfoValue = styled.span`
  color: #f1f5f9;
  font-size: 1.5rem;
  font-weight: 600;
`;

const Visualization = () => {
  const [viewMode, setViewMode] = useState('2D');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [systemMetrics, setSystemMetrics] = useState({
    totalLoad: 330,
    systemHealth: 92,
    activeAlarms: 2,
    onlineAssets: 45
  });

  const handleFullscreen = () => {
    if (!isFullscreen) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
    setIsFullscreen(!isFullscreen);
  };

  const handleExport = () => {
    // Export current visualization as image
    toast.success('Exporting visualization...');
    // Implementation would capture canvas/svg and download
  };

  const handleRefresh = async () => {
    toast.loading('Refreshing data...', { id: 'refresh' });

    try {
      // Fetch latest metrics from API
      const response = await fetch('/api/metrics');
      const data = await response.json();

      setSystemMetrics({
        totalLoad: data.total_load || 330,
        systemHealth: data.system_health || 92,
        activeAlarms: data.alerts?.length || 0,
        onlineAssets: data.operational_assets || 45
      });

      toast.success('Data refreshed!', { id: 'refresh' });
    } catch (error) {
      toast.error('Failed to refresh data', { id: 'refresh' });
    }
  };

  return (
    <VisualizationContainer>
      <PageHeader>
        <Title>Substation Visualization & Control</Title>
        <ControlButtons>
          <ControlButton onClick={handleRefresh}>
            <FiRefreshCw />
            Refresh
          </ControlButton>
          <ControlButton onClick={handleExport}>
            <FiDownload />
            Export
          </ControlButton>
          <ControlButton onClick={handleFullscreen}>
            <FiMaximize2 />
            Fullscreen
          </ControlButton>
        </ControlButtons>
      </PageHeader>

      <InfoBar>
        <InfoItem>
          <InfoLabel>Total Load</InfoLabel>
          <InfoValue>{systemMetrics.totalLoad} MW</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>System Health</InfoLabel>
          <InfoValue>{systemMetrics.systemHealth}%</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Active Alarms</InfoLabel>
          <InfoValue>{systemMetrics.activeAlarms}</InfoValue>
        </InfoItem>
        <InfoItem>
          <InfoLabel>Online Assets</InfoLabel>
          <InfoValue>{systemMetrics.onlineAssets}</InfoValue>
        </InfoItem>
      </InfoBar>

      <TabButtons>
        <TabButton
          active={viewMode === '2D'}
          onClick={() => setViewMode('2D')}
        >
          <FiGrid />
          2D Single-Line Diagram
        </TabButton>
        <TabButton
          active={viewMode === '3D'}
          onClick={() => setViewMode('3D')}
        >
          <FiCpu />
          3D Substation Model
        </TabButton>
      </TabButtons>

      <VisualizationWrapper>
        {viewMode === '2D' ? (
          <SubstationVisualization2D />
        ) : (
          <SubstationVisualization3D />
        )}
      </VisualizationWrapper>

      <AnomalySimulationPanel />
    </VisualizationContainer>
  );
};

export default Visualization;