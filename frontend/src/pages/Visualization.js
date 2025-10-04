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
  gap: 1.25rem;
`;

const PageHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-radius: 12px;
`;

const Title = styled.h1`
  color: #2563eb;
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;

  svg {
    font-size: 2rem;
  }
`;

const ControlButtons = styled.div`
  display: flex;
  gap: 0.75rem;
`;

const ControlButton = styled.button`
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  background: #2563eb;
  padding: 0.625rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  backdrop-filter: blur(10px);

  &:hover {
    background: rgba(255, 255, 255, 0.25);
    transform: translateY(-1px);
  }

  svg {
    font-size: 1.1rem;
  }
`;

const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 1.25rem;

  @media (max-width: 1400px) {
    grid-template-columns: 1fr;
  }
`;

const MainContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
`;

const InfoBar = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  background: #ffffff;
  border-radius: 10px;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
`;

const InfoItem = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-radius: 8px;
  border: 1px solid #bfdbfe;
`;

const InfoLabel = styled.span`
  color: #64748b;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const InfoValue = styled.span`
  color: #1e40af;
  font-size: 1.5rem;
  font-weight: 700;
`;

const TabButtons = styled.div`
  display: flex;
  gap: 0.75rem;
  background: #ffffff;
  padding: 0.75rem;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
`;

const TabButton = styled.button`
  flex: 1;
  background: ${props => props.active ? 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)' : '#f8fafc'};
  border: 1px solid ${props => props.active ? '#2563eb' : '#e2e8f0'};
  color: ${props => props.active ? '#ffffff' : '#475569'};
  padding: 0.875rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.95rem;
  font-weight: ${props => props.active ? '600' : '500'};
  box-shadow: ${props => props.active ? '0 2px 4px rgba(37, 99, 235, 0.2)' : 'none'};

  &:hover {
    background: ${props => props.active ? 'linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%)' : '#f1f5f9'};
    transform: translateY(-1px);
  }

  svg {
    font-size: 1.15rem;
  }
`;

const VisualizationWrapper = styled.div`
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
  height: fit-content;
`;

const SidePanel = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.25rem;

  @media (max-width: 1400px) {
    width: 100%;
  }
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
        <Title>
          <FiMonitor />
          Substation Visualization & Control
        </Title>
        <ControlButtons>
          <ControlButton onClick={handleRefresh} title="Refresh Data">
            <FiRefreshCw />
            Refresh
          </ControlButton>
          <ControlButton onClick={handleExport} title="Export Image">
            <FiDownload />
            Export
          </ControlButton>
          <ControlButton onClick={handleFullscreen} title="Fullscreen Mode">
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

      <ContentGrid>
        <MainContent>
          <TabButtons>
            <TabButton
              active={viewMode === '2D'}
              onClick={() => setViewMode('2D')}
            >
              <FiGrid />
              2D Diagram
            </TabButton>
            <TabButton
              active={viewMode === '3D'}
              onClick={() => setViewMode('3D')}
            >
              <FiCpu />
              3D Model
            </TabButton>
          </TabButtons>

          <VisualizationWrapper ref={visualizationRef}>
            {viewMode === '2D' ? (
              <SubstationVisualization2D activeAnomalies={activeAnomalies} />
            ) : (
              <SubstationVisualization3D activeAnomalies={activeAnomalies} />
            )}
          </VisualizationWrapper>
        </MainContent>

        <SidePanel>
          <AnomalySimulationPanel onAnomalyChange={setActiveAnomalies} />
        </SidePanel>
      </ContentGrid>
    </VisualizationContainer>
  );
};

export default Visualization;