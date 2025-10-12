import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import styled, { createGlobalStyle } from 'styled-components';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Assets from './pages/Assets';
import SCADA from './pages/SCADA';
import Analytics from './pages/Analytics';
import AnomalyDetail from './pages/AnomalyDetail';
import Visualization from './pages/Visualization';
import Logging from './pages/Logging';
import Trends from './pages/Trends';
import DSSEditor from './pages/DSSEditor';
import { DigitalTwinProvider } from './context/DigitalTwinContext';

const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
      'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
      sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background: #f8fafc;
    min-height: 100vh;
    color: #0f172a;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

const AppContainer = styled.div`
  display: flex;
  min-height: 100vh;
  background: #f8fafc;
`;

const MainContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 250px;
  transition: margin-left 0.3s ease;
  background: #f8fafc;

  @media (max-width: 768px) {
    margin-left: 0;
  }
`;

const Header = styled.header`
  position: fixed;
  top: 0;
  left: 250px;
  right: 0;
  z-index: 100;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 0.75rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);

  @media (max-width: 768px) {
    left: 0;
  }
`;

const HeaderTitle = styled.h1`
  font-size: 1.25rem;
  font-weight: 600;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: #64748b;
  font-weight: 500;
`;

const StatusDot = styled.div`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${props => props.connected ? '#10b981' : '#ef4444'};
  animation: ${props => props.connected ? 'pulse 2s infinite' : 'none'};
`;

const Content = styled.main`
  flex: 1;
  padding: 1.5rem;
  padding-top: 5rem;
  overflow-y: auto;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
`;

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState(false);

  useEffect(() => {
    // Handle responsive sidebar behavior
    const handleResize = () => {
      if (window.innerWidth > 768) {
        setSidebarOpen(true);
      }
    };

    // Set initial state
    handleResize();

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    // Check connection status with reduced frequency
    const checkConnection = async () => {
      try {
        const response = await fetch('/api/metrics');
        setConnectionStatus(response.ok);
      } catch (error) {
        setConnectionStatus(false);
        // Retry after 2 seconds if initial connection fails
        setTimeout(checkConnection, 2000);
      }
    };

    // Initial check with a small delay to ensure backend is ready
    setTimeout(checkConnection, 1000);
    const interval = setInterval(checkConnection, 30000); // Reduced to 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <DigitalTwinProvider>
      <GlobalStyle />
      <Router>
        <AppContainer>
          <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
          <MainContent>
            <Header>
              <HeaderTitle>
                EHV Substation Digital Twin
              </HeaderTitle>
              <StatusIndicator>
                <StatusDot connected={connectionStatus} />
                {connectionStatus ? 'Connected' : 'Disconnected'}
              </StatusIndicator>
            </Header>
            <Content>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/assets" element={<Assets />} />
                <Route path="/scada" element={<SCADA />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/analytics/:id" element={<AnomalyDetail />} />
                <Route path="/visualization" element={<Visualization />} />
                <Route path="/logging" element={<Logging />} />
                <Route path="/trends" element={<Trends />} />
                <Route path="/dss-editor" element={<DSSEditor />} />
              </Routes>
            </Content>
          </MainContent>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'white',
                color: '#0f172a',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              },
            }}
          />
        </AppContainer>
      </Router>
    </DigitalTwinProvider>
  );
}

export default App;