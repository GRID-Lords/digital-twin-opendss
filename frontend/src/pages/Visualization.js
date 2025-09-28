import React, { useState } from 'react';
import styled from 'styled-components';
import { FiMonitor, FiDownload, FiRefreshCw, FiMaximize2 } from 'react-icons/fi';
import toast from 'react-hot-toast';

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
  color: white;
  font-size: 2rem;
  font-weight: 600;
`;

const ControlButtons = styled.div`
  display: flex;
  gap: 1rem;
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

const VisualizationGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const VisualizationCard = styled.div`
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

const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`;

const CardTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const CardActions = styled.div`
  display: flex;
  gap: 0.5rem;
`;

const ActionButton = styled.button`
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  padding: 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
`;

const VisualizationPlaceholder = styled.div`
  height: 300px;
  background: rgba(255, 255, 255, 0.05);
  border: 2px dashed rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
  gap: 1rem;
`;

const PlaceholderIcon = styled.div`
  font-size: 3rem;
  opacity: 0.5;
`;

const PlaceholderText = styled.div`
  font-size: 1rem;
  font-weight: 500;
`;

const PlaceholderSubtext = styled.div`
  font-size: 0.8rem;
  opacity: 0.7;
`;

const FullWidthCard = styled(VisualizationCard)`
  grid-column: 1 / -1;
`;

const Visualization = () => {
  const [loading, setLoading] = useState(false);

  const handleGenerateNetwork = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/visualization/network');
      if (response.ok) {
        toast.success('Network diagram generated successfully');
      } else {
        throw new Error('Failed to generate network diagram');
      }
    } catch (error) {
      toast.error('Failed to generate network diagram');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (type) => {
    toast.success(`${type} download started`);
  };

  const handleRefresh = (type) => {
    toast.success(`${type} refreshed`);
  };

  const handleFullscreen = (type) => {
    toast.success(`${type} opened in fullscreen`);
  };

  return (
    <VisualizationContainer>
      <PageHeader>
        <Title>📊 Visualization Center</Title>
        <ControlButtons>
          <ControlButton onClick={handleGenerateNetwork} disabled={loading}>
            <FiRefreshCw />
            {loading ? 'Generating...' : 'Generate All'}
          </ControlButton>
        </ControlButtons>
      </PageHeader>

      <VisualizationGrid>
        <VisualizationCard>
          <CardHeader>
            <CardTitle>
              <FiMonitor />
              Network Diagram
            </CardTitle>
            <CardActions>
              <ActionButton onClick={() => handleRefresh('Network Diagram')}>
                <FiRefreshCw />
              </ActionButton>
              <ActionButton onClick={() => handleDownload('Network Diagram')}>
                <FiDownload />
              </ActionButton>
              <ActionButton onClick={() => handleFullscreen('Network Diagram')}>
                <FiMaximize2 />
              </ActionButton>
            </CardActions>
          </CardHeader>
          <VisualizationPlaceholder>
            <PlaceholderIcon>🔌</PlaceholderIcon>
            <PlaceholderText>Network Diagram</PlaceholderText>
            <PlaceholderSubtext>Professional electrical network diagram with power flow annotations</PlaceholderSubtext>
          </VisualizationPlaceholder>
        </VisualizationCard>

        <VisualizationCard>
          <CardHeader>
            <CardTitle>
              <FiMonitor />
              Single-Line Diagram
            </CardTitle>
            <CardActions>
              <ActionButton onClick={() => handleRefresh('Single-Line Diagram')}>
                <FiRefreshCw />
              </ActionButton>
              <ActionButton onClick={() => handleDownload('Single-Line Diagram')}>
                <FiDownload />
              </ActionButton>
              <ActionButton onClick={() => handleFullscreen('Single-Line Diagram')}>
                <FiMaximize2 />
              </ActionButton>
            </CardActions>
          </CardHeader>
          <VisualizationPlaceholder>
            <PlaceholderIcon>📐</PlaceholderIcon>
            <PlaceholderText>Single-Line Diagram</PlaceholderText>
            <PlaceholderSubtext>IEEE-standard electrical schematic with professional symbols</PlaceholderSubtext>
          </VisualizationPlaceholder>
        </VisualizationCard>

        <VisualizationCard>
          <CardHeader>
            <CardTitle>
              <FiMonitor />
              Power Flow Analysis
            </CardTitle>
            <CardActions>
              <ActionButton onClick={() => handleRefresh('Power Flow')}>
                <FiRefreshCw />
              </ActionButton>
              <ActionButton onClick={() => handleDownload('Power Flow')}>
                <FiDownload />
              </ActionButton>
              <ActionButton onClick={() => handleFullscreen('Power Flow')}>
                <FiMaximize2 />
              </ActionButton>
            </CardActions>
          </CardHeader>
          <VisualizationPlaceholder>
            <PlaceholderIcon>⚡</PlaceholderIcon>
            <PlaceholderText>Power Flow Analysis</PlaceholderText>
            <PlaceholderSubtext>Real-time power flow visualization with load distribution</PlaceholderSubtext>
          </VisualizationPlaceholder>
        </VisualizationCard>

        <VisualizationCard>
          <CardHeader>
            <CardTitle>
              <FiMonitor />
              Voltage Profile
            </CardTitle>
            <CardActions>
              <ActionButton onClick={() => handleRefresh('Voltage Profile')}>
                <FiRefreshCw />
              </ActionButton>
              <ActionButton onClick={() => handleDownload('Voltage Profile')}>
                <FiDownload />
              </ActionButton>
              <ActionButton onClick={() => handleFullscreen('Voltage Profile')}>
                <FiMaximize2 />
              </ActionButton>
            </CardActions>
          </CardHeader>
          <VisualizationPlaceholder>
            <PlaceholderIcon>📈</PlaceholderIcon>
            <PlaceholderText>Voltage Profile</PlaceholderText>
            <PlaceholderSubtext>Voltage analysis and unbalance detection across all buses</PlaceholderSubtext>
          </VisualizationPlaceholder>
        </VisualizationCard>
      </VisualizationGrid>

      <FullWidthCard>
        <CardHeader>
          <CardTitle>
            <FiMonitor />
            3D Substation Model
          </CardTitle>
          <CardActions>
            <ActionButton onClick={() => handleRefresh('3D Model')}>
              <FiRefreshCw />
            </ActionButton>
            <ActionButton onClick={() => handleDownload('3D Model')}>
              <FiDownload />
            </ActionButton>
            <ActionButton onClick={() => handleFullscreen('3D Model')}>
              <FiMaximize2 />
            </ActionButton>
          </CardActions>
        </CardHeader>
        <VisualizationPlaceholder style={{ height: '400px' }}>
          <PlaceholderIcon>🏭</PlaceholderIcon>
          <PlaceholderText>3D Substation Model</PlaceholderText>
          <PlaceholderSubtext>Interactive 3D visualization of the Indian EHV substation with real-time data overlay</PlaceholderSubtext>
        </VisualizationPlaceholder>
      </FullWidthCard>
    </VisualizationContainer>
  );
};

export default Visualization;