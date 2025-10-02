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
        const websocket = new WebSocket('ws://localhost:8000/ws');
        
        websocket.onopen = () => {
          console.log('WebSocket connected');
          setWsConnected(true);
          setWs(websocket);
        };

        websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'update') {
              setAssets(data.assets || {});
              setMetrics(data.metrics || {});
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
    // Fetch real-time data from cache frequently
    const refreshRealtimeData = () => {
      fetchRealtimeSummary(); // Get cached real-time data
      fetchMetrics(); // Get current metrics
    };

    // Fetch slower-changing data less frequently
    const refreshSlowData = () => {
      fetchAssets();
      fetchSCADAData();
      fetchAIAnalysis();
      fetchCacheStats();
    };

    // Initial load
    refreshRealtimeData();
    refreshSlowData();
    fetchHistoricalMetrics(24); // Load last 24 hours

    // Different refresh intervals for different data types
    const realtimeInterval = setInterval(refreshRealtimeData, 10000); // Every 10 seconds for real-time
    const slowInterval = setInterval(refreshSlowData, 60000); // Every 60 seconds for slow data

    return () => {
      clearInterval(realtimeInterval);
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