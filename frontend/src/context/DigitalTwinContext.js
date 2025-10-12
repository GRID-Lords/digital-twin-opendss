import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const DigitalTwinContext = createContext();

export const useDigitalTwin = () => {
  const context = useContext(DigitalTwinContext);
  if (!context) {
    throw new Error('useDigitalTwin must be used within a DigitalTwinProvider');
  }
  return context;
};

export const DigitalTwinProvider = ({ children }) => {
  const [assets, setAssets] = useState({});
  const [metrics, setMetrics] = useState({});
  const [historicalMetrics, setHistoricalMetrics] = useState([]);
  const [cacheStats, setCacheStats] = useState({});
  const [realtimeSummary, setRealtimeSummary] = useState({});
  const [scadaData, setScadaData] = useState({});
  const [aiAnalysis, setAiAnalysis] = useState({});
  const [iotDevices, setIotDevices] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // WebSocket connection
  const [ws, setWs] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);

  // Initialize WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const websocket = new WebSocket(process.env.REACT_APP_WS_URL || 'wss://gridlords.dev/api/ws');
        
        websocket.onopen = () => {
          console.log('WebSocket connected');
          setWsConnected(true);
          setWs(websocket);
        };

        websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', new Date().toLocaleTimeString(), data);

            // Handle different message types
            if (data.type === 'alert_notification') {
              // Show toast notification for new alerts
              const alert = data.alert;
              const notificationType = data.notification_type;

              // Create toast with appropriate styling based on notification type
              if (notificationType === 'critical') {
                toast.error(
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                      🚨 Critical Anomaly Detected
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                      {alert.message}
                    </div>
                  </div>,
                  {
                    duration: 8000,
                    style: {
                      background: '#fef2f2',
                      border: '1px solid #fca5a5',
                      borderLeft: '4px solid #dc2626',
                      maxWidth: '500px'
                    }
                  }
                );
              } else if (notificationType === 'medium') {
                toast(
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                      ⚠️ New Alert
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                      {alert.message}
                    </div>
                  </div>,
                  {
                    duration: 6000,
                    style: {
                      background: '#fffbeb',
                      border: '1px solid #fde68a',
                      borderLeft: '4px solid #f59e0b',
                      maxWidth: '500px'
                    }
                  }
                );
              } else {
                // Default info toast
                toast(
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                      ℹ️ Alert
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                      {alert.message}
                    </div>
                  </div>,
                  {
                    duration: 5000,
                    style: {
                      background: '#eff6ff',
                      border: '1px solid #bfdbfe',
                      borderLeft: '4px solid #3b82f6',
                      maxWidth: '500px'
                    }
                  }
                );
              }

              console.log('Alert notification displayed:', alert);
            } else if (data.type === 'update') {
              setAssets(data.assets || {});
              setMetrics(data.metrics || {});
              console.log('Updated assets and metrics via WebSocket');
            } else if (data.total_power !== undefined || data.efficiency !== undefined) {
              // Real-time metrics update (sent every second)
              setMetrics(data);
              console.log('Updated metrics via WebSocket:', {
                power: data.total_power,
                efficiency: data.efficiency,
                voltage_stability: data.voltage_stability,
                frequency: data.frequency
              });
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        websocket.onclose = () => {
          console.log('WebSocket disconnected');
          setWsConnected(false);
          setWs(null);
          // Reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };

        websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
          setWsConnected(false);
        };
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setWsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  // Fetch data functions
  const fetchAssets = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/assets');
      setAssets(response.data.assets || response.data);
    } catch (error) {
      setError('Failed to fetch assets');
      toast.error('Failed to fetch assets');
    } finally {
      setLoading(false);
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await axios.get('/api/metrics');
      setMetrics(response.data);
    } catch (error) {
      setError('Failed to fetch metrics');
      toast.error('Failed to fetch metrics');
    }
  };

  const fetchSCADAData = async () => {
    try {
      const response = await axios.get('/api/scada/data');
      setScadaData(response.data);
    } catch (error) {
      setError('Failed to fetch SCADA data');
      toast.error('Failed to fetch SCADA data');
    }
  };

  const fetchAIAnalysis = async () => {
    try {
      const response = await axios.get('/api/ai/analysis');
      setAiAnalysis(response.data);
    } catch (error) {
      setError('Failed to fetch AI analysis');
      toast.error('Failed to fetch AI analysis');
    }
  };

  const fetchIoTDevices = async () => {
    try {
      const response = await axios.get('/api/iot/devices');
      setIotDevices(response.data);
    } catch (error) {
      setError('Failed to fetch IoT devices');
      toast.error('Failed to fetch IoT devices');
    }
  };

  // New API functions for optimized data management
  const fetchHistoricalMetrics = async (hours = 24) => {
    try {
      const response = await axios.get(`/api/metrics/historical?hours=${hours}`);
      setHistoricalMetrics(response.data.data || []);
      return response.data;
    } catch (error) {
      toast.error('Failed to fetch historical metrics');
      throw error;
    }
  };

  const fetchCacheStats = async () => {
    try {
      const response = await axios.get('/api/cache/stats');
      setCacheStats(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch cache stats:', error);
    }
  };

  const fetchRealtimeSummary = async () => {
    try {
      const response = await axios.get('/api/realtime/summary');
      setRealtimeSummary(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch realtime summary:', error);
    }
  };

  const triggerDataCleanup = async () => {
    try {
      const response = await axios.post('/api/data/cleanup');
      toast.success('Data cleanup completed');
      return response.data;
    } catch (error) {
      toast.error('Failed to trigger data cleanup');
      throw error;
    }
  };

  // Control functions
  const controlAsset = async (assetId, action, parameters = {}) => {
    try {
      const response = await axios.post('/api/control', {
        asset_id: assetId,
        action: action,
        parameters: parameters
      });
      toast.success(`Asset ${assetId} ${action} completed`);
      return response.data;
    } catch (error) {
      toast.error(`Failed to control asset ${assetId}`);
      throw error;
    }
  };

  const runFaultAnalysis = async (faultType, faultLocation) => {
    try {
      const response = await axios.post(`/api/faults/analyze?fault_type=${faultType}&fault_location=${faultLocation}`);
      toast.success('Fault analysis completed');
      return response.data;
    } catch (error) {
      toast.error('Failed to run fault analysis');
      throw error;
    }
  };

  // Optimized auto-refresh strategy
  useEffect(() => {
    // Fetch slower-changing data
    const refreshSlowData = () => {
      fetchAssets();
      fetchSCADAData();
      fetchAIAnalysis();
      fetchIoTDevices();
      fetchCacheStats();
    };

    // Initial load
    fetchMetrics(); // Initial metrics load
    refreshSlowData();
    fetchHistoricalMetrics(24); // Load last 24 hours

    // Slow refresh for data that changes infrequently
    // Metrics come via WebSocket (every 1 second), no need to poll
    const slowInterval = setInterval(refreshSlowData, 60000); // Every 60 seconds

    return () => {
      clearInterval(slowInterval);
    };
  }, []);

  const value = {
    // State
    assets,
    metrics,
    historicalMetrics,
    cacheStats,
    realtimeSummary,
    scadaData,
    aiAnalysis,
    iotDevices,
    loading,
    error,
    wsConnected,

    // Actions
    fetchAssets,
    fetchMetrics,
    fetchHistoricalMetrics,
    fetchCacheStats,
    fetchRealtimeSummary,
    fetchSCADAData,
    fetchAIAnalysis,
    fetchIoTDevices,
    controlAsset,
    runFaultAnalysis,
    triggerDataCleanup,
  };

  return (
    <DigitalTwinContext.Provider value={value}>
      {children}
    </DigitalTwinContext.Provider>
  );
};