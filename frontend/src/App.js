import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import styled, { createGlobalStyle } from 'styled-components';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Assets from './pages/Assets';
import SCADA from './pages/SCADA';
import Analytics from './pages/Analytics';
import Visualization from './pages/Visualization';
import Logging from './pages/Logging';
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
    background: #0f172a;
    min-height: 100vh;
    color: #e2e8f0;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

const AppContainer = styled.div`
  display: flex;
  min-height: 100vh;
  background: #0f172a;
`;

const MainContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 250px;
  transition: margin-left 0.3s ease;
  background: #1e293b;

  @media (max-width: 768px) {
    margin-left: 0;
  }
`;

const Header = styled.header`
  background: #1e293b;
  border-bottom: 1px solid #334155;
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
`;

const HeaderTitle = styled.h1`
  font-size: 1.5rem;
  font-weight: 600;
  color: #f1f5f9;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #94a3b8;
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
  padding: 2rem;
  overflow-y: auto;
`;

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState(false);

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
                <Route path="/visualization" element={<Visualization />} />
                <Route path="/logging" element={<Logging />} />
              </Routes>
            </Content>
          </MainContent>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#0f172a',
                color: '#fff',
                borderRadius: '8px',
              },
            }}
          />
        </AppContainer>
      </Router>
    </DigitalTwinProvider>
  );
}

export default App;