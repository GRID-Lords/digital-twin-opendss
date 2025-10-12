// API Service for Digital Twin Frontend
// Handles all communication with backend endpoints

import axios from 'axios';
import toast from 'react-hot-toast';

// Configure axios defaults
axios.defaults.baseURL = process.env.REACT_APP_API_URL || 'https://gridlords.dev/api';
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Request interceptor for auth
axios.interceptors.request.use(
  config => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// Response interceptor for error handling
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      toast.error('Session expired. Please login again.');
    } else if (error.response?.status === 500) {
      toast.error('Server error. Please try again.');
    }
    return Promise.reject(error);
  }
);

// Asset Management APIs
export const assetAPI = {
  // Get all assets
  getAssets: async () => {
    const response = await axios.get('/api/assets');
    return response.data;
  },

  // Get specific asset details
  getAssetById: async (assetId) => {
    const response = await axios.get(`/api/assets/${assetId}`);
    return response.data;
  },

  // Update asset parameters
  updateAsset: async (assetId, data) => {
    const response = await axios.put(`/api/assets/${assetId}`, data);
    return response.data;
  },

  // Get asset health
  getAssetHealth: async (assetId) => {
    const response = await axios.get(`/api/assets/${assetId}/health`);
    return response.data;
  }
};

// SCADA Integration APIs
export const scadaAPI = {
  // Get real-time SCADA data
  getRealtimeData: async () => {
    const response = await axios.get('/api/scada/data');
    return response.data;
  },

  // Get historical data
  getHistoricalData: async (startTime, endTime, tags) => {
    const response = await axios.post('/api/scada/historical', {
      start_time: startTime,
      end_time: endTime,
      tags: tags
    });
    return response.data;
  },

  // Send control command
  sendControl: async (assetId, command, value) => {
    const response = await axios.post('/api/control', {
      asset_id: assetId,
      command: command,
      value: value
    });
    return response.data;
  },

  // Get alarms
  getAlarms: async (acknowledged = false) => {
    const response = await axios.get(`/api/scada/alarms?acknowledged=${acknowledged}`);
    return response.data;
  },

  // Acknowledge alarm
  acknowledgeAlarm: async (alarmId) => {
    const response = await axios.post(`/api/scada/alarms/${alarmId}/acknowledge`);
    return response.data;
  }
};

// Simulation APIs
export const simulationAPI = {
  // Trigger anomaly simulation
  triggerAnomaly: async (type, severity, location) => {
    const response = await axios.post('/api/simulation/anomaly', {
      type,
      severity,
      location
    });
    return response.data;
  },

  // Run predefined scenario
  runScenario: async (scenario, parameters = {}) => {
    const response = await axios.post('/api/simulation/scenario', {
      scenario,
      parameters
    });
    return response.data;
  },

  // Get simulation status
  getSimulationStatus: async () => {
    const response = await axios.get('/api/simulation/status');
    return response.data;
  },

  // Clear all anomalies
  clearAnomalies: async () => {
    const response = await axios.post('/api/simulation/clear');
    return response.data;
  },

  // Generate training dataset
  generateDataset: async (numSamples = 1000) => {
    const response = await axios.post('/api/simulation/generate-dataset', {
      num_samples: numSamples
    });
    return response.data;
  },

  // Run load flow analysis
  runLoadFlow: async () => {
    const response = await axios.post('/api/simulation', {
      scenario: 'load_flow'
    });
    return response.data;
  },

  // Run contingency analysis
  runContingencyAnalysis: async () => {
    const response = await axios.post('/api/simulation', {
      scenario: 'contingency'
    });
    return response.data;
  },

  // Run fault analysis
  runFaultAnalysis: async (busId, faultType) => {
    const response = await axios.post('/api/simulation', {
      scenario: 'fault',
      bus_id: busId,
      fault_type: faultType
    });
    return response.data;
  }
};

// AI/ML APIs
export const aiAPI = {
  // Get AI analysis
  getAnalysis: async () => {
    const response = await axios.get('/api/ai/analysis');
    return response.data;
  },

  // Get predictions
  getPredictions: async (assetId) => {
    const response = await axios.get(`/api/ai/predictions/${assetId}`);
    return response.data;
  },

  // Get anomaly detection results
  getAnomalies: async () => {
    const response = await axios.get('/api/ai/anomalies');
    return response.data;
  },

  // Train model with new data
  trainModel: async (modelType, data) => {
    const response = await axios.post('/api/ai/train', {
      model_type: modelType,
      training_data: data
    });
    return response.data;
  }
};

// Metrics and Monitoring APIs
export const metricsAPI = {
  // Get current system metrics
  getMetrics: async () => {
    const response = await axios.get('/api/metrics');
    return response.data;
  },

  // Get system health status
  getHealth: async () => {
    const response = await axios.get('/health');
    return response.data;
  },

  // Get performance metrics
  getPerformance: async () => {
    const response = await axios.get('/api/metrics/performance');
    return response.data;
  }
};

// WebSocket Connection for real-time updates
export class WebSocketService {
  constructor() {
    this.ws = null;
    this.subscribers = new Map();
  }

  connect() {
    const wsUrl = process.env.REACT_APP_WS_URL || 'wss://gridlords.dev/api/ws';

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      toast.success('Real-time connection established');
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.notifySubscribers(data.type, data);
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      toast.error('Real-time connection error');
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      toast.warning('Real-time connection lost. Reconnecting...');
      // Attempt reconnection after 3 seconds
      setTimeout(() => this.connect(), 3000);
    };
  }

  subscribe(eventType, callback) {
    if (!this.subscribers.has(eventType)) {
      this.subscribers.set(eventType, new Set());
    }
    this.subscribers.get(eventType).add(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.subscribers.get(eventType);
      if (callbacks) {
        callbacks.delete(callback);
      }
    };
  }

  notifySubscribers(eventType, data) {
    const callbacks = this.subscribers.get(eventType);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }

    // Also notify wildcard subscribers
    const wildcardCallbacks = this.subscribers.get('*');
    if (wildcardCallbacks) {
      wildcardCallbacks.forEach(callback => callback(data));
    }
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// WebSocket for anomaly updates
export class AnomalyWebSocket {
  constructor() {
    this.ws = null;
    this.callbacks = [];
  }

  connect() {
    const wsUrl = 'wss://gridlords.dev/api/api/simulation/ws/anomaly';

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('Anomaly WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.callbacks.forEach(callback => callback(data));
      } catch (error) {
        console.error('Anomaly WebSocket parse error:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('Anomaly WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('Anomaly WebSocket disconnected');
      // Reconnect after 5 seconds
      setTimeout(() => this.connect(), 5000);
    };
  }

  onUpdate(callback) {
    this.callbacks.push(callback);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Visualization APIs
export const visualizationAPI = {
  // Get 2D visualization data
  get2DData: async () => {
    const response = await axios.get('/api/visualization/2d');
    return response.data;
  },

  // Get 3D visualization data
  get3DData: async () => {
    const response = await axios.get('/api/visualization/3d');
    return response.data;
  },

  // Update visualization settings
  updateSettings: async (settings) => {
    const response = await axios.post('/api/visualization/settings', settings);
    return response.data;
  },

  // Export visualization
  exportVisualization: async (format = 'png') => {
    const response = await axios.get(`/api/visualization/export?format=${format}`, {
      responseType: 'blob'
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `substation_viz_${Date.now()}.${format}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
};

// Create singleton instances
export const wsService = new WebSocketService();
export const anomalyWS = new AnomalyWebSocket();

// Export default API object
const api = {
  assets: assetAPI,
  scada: scadaAPI,
  simulation: simulationAPI,
  ai: aiAPI,
  metrics: metricsAPI,
  visualization: visualizationAPI,
  ws: wsService,
  anomalyWS: anomalyWS
};

export default api;