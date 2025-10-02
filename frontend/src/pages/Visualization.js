import React, { useState, useRef } from 'react';
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
    totalLoad: 0,
    systemHealth: 0,
    activeAlarms: 0,
    onlineAssets: 0
  });
  const [activeAnomalies, setActiveAnomalies] = useState({});
  const visualizationRef = useRef(null);

  // Fetch real metrics on mount and periodically
  React.useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const [metricsRes, assetsRes, alertsRes] = await Promise.all([
          fetch('/api/metrics').then(r => r.json()),
          fetch('/api/assets').then(r => r.json()),
          fetch('/api/alerts?limit=100').then(r => r.json())
        ]);

        const assets = assetsRes.assets || assetsRes;
        const operationalAssets = Object.values(assets).filter(a => a.status === 'operational' || a.status?.toLowerCase() === 'operational').length;

        setSystemMetrics({
          totalLoad: Math.round((metricsRes.total_load || metricsRes.total_power || 0) * 100) / 100, // Already in MW, round to 2 decimals
          systemHealth: Math.round((metricsRes.system_health || metricsRes.efficiency || 0) * 100) / 100, // Round to 2 decimals
          activeAlarms: alertsRes.unresolved_count || alertsRes.alerts?.filter(a => !a.resolved).length || 0,
          onlineAssets: operationalAssets
        });
      } catch (error) {
        console.error('Error fetching metrics:', error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  // Listen for fullscreen changes
  React.useEffect(() => {
    const handleFullscreenChange = () => {
      const isCurrentlyFullscreen = !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.mozFullScreenElement ||
        document.msFullscreenElement
      );
      setIsFullscreen(isCurrentlyFullscreen);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
      document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
      document.removeEventListener('MSFullscreenChange', handleFullscreenChange);
    };
  }, []);

  const handleFullscreen = () => {
    const isCurrentlyFullscreen = !!(
      document.fullscreenElement ||
      document.webkitFullscreenElement ||
      document.mozFullScreenElement ||
      document.msFullscreenElement
    );

    if (!isCurrentlyFullscreen) {
      if (visualizationRef.current) {
        if (visualizationRef.current.requestFullscreen) {
          visualizationRef.current.requestFullscreen();
        } else if (visualizationRef.current.webkitRequestFullscreen) {
          visualizationRef.current.webkitRequestFullscreen();
        } else if (visualizationRef.current.mozRequestFullScreen) {
          visualizationRef.current.mozRequestFullScreen();
        } else if (visualizationRef.current.msRequestFullscreen) {
          visualizationRef.current.msRequestFullscreen();
        }
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
    }
  };

  const handleExport = () => {
    // Export current visualization as image
    toast.success('Exporting visualization...');
    // Implementation would capture canvas/svg and download
  };

  const handleRefresh = async () => {
    toast.loading('Refreshing data...', { id: 'refresh' });

    try {
      const [metricsRes, assetsRes, alertsRes] = await Promise.all([
        fetch('/api/metrics').then(r => r.json()),
        fetch('/api/assets').then(r => r.json()),
        fetch('/api/alerts?limit=100').then(r => r.json())
      ]);

      const assets = assetsRes.assets || assetsRes;
      const operationalAssets = Object.values(assets).filter(a => a.status === 'operational' || a.status?.toLowerCase() === 'operational').length;

      setSystemMetrics({
        totalLoad: Math.round((metricsRes.total_load || metricsRes.total_power || 0) * 100) / 100, // Already in MW, round to 2 decimals
        systemHealth: Math.round((metricsRes.system_health || metricsRes.efficiency || 0) * 100) / 100, // Round to 2 decimals
        activeAlarms: alertsRes.unresolved_count || alertsRes.alerts?.filter(a => !a.resolved).length || 0,
        onlineAssets: operationalAssets
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
          <ControlButton onClick={handleRefresh} title="Refresh">
            <FiRefreshCw />
          </ControlButton>
          <ControlButton onClick={handleExport} title="Export">
            <FiDownload />
          </ControlButton>
          <ControlButton onClick={handleFullscreen} title="Fullscreen">
            <FiMaximize2 />
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

      <VisualizationWrapper ref={visualizationRef}>
        {viewMode === '2D' ? (
          <SubstationVisualization2D activeAnomalies={activeAnomalies} />
        ) : (
          <SubstationVisualization3D activeAnomalies={activeAnomalies} />
        )}
      </VisualizationWrapper>

      <AnomalySimulationPanel onAnomalyChange={setActiveAnomalies} />
    </VisualizationContainer>
  );
};

export default Visualization;