# 🇮🇳 Indian EHV 400/220 kV Substation Digital Twin

A comprehensive Digital Twin solution for Indian Extra High Voltage substations, featuring real-time monitoring, AI/ML-powered predictive analytics, SCADA integration, and professional electrical visualizations.

## 🎯 Overview

This Digital Twin system provides a complete virtual replica of an Indian EHV substation, enabling:

- **Real-time Monitoring**: Live data from SCADA systems and IoT devices
- **AI/ML Analytics**: Anomaly detection, predictive maintenance, and optimization
- **Professional Visualizations**: Electrical diagrams with proper symbols and annotations
- **REST API & WebSocket**: Real-time data streaming and control interfaces
- **Asset Management**: Complete lifecycle monitoring of all substation components

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Digital Twin System                      │
├─────────────────────────────────────────────────────────────┤
│  🌐 Web Dashboard    │  📱 Mobile Apps    │  🔌 API Clients │
├─────────────────────────────────────────────────────────────┤
│  🧠 AI/ML Engine    │  📊 SCADA Integration │  🔧 Control   │
├─────────────────────────────────────────────────────────────┤
│  ⚡ OpenDSS Simulation │  📈 Real-time Data │  🎯 Analytics │
├─────────────────────────────────────────────────────────────┤
│  🏭 Physical Substation │  📡 IoT Devices  │  🖥️ SCADA     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd opendss-test

# Install dependencies
python3 -m pip install --user --break-system-packages \
    fastapi uvicorn websockets pandas numpy scikit-learn \
    matplotlib opendssdirect pymodbus requests

# Start the Digital Twin
python3 start_digital_twin.py
```

### 2. Access the System

- **Web Dashboard**: http://localhost:8000/dashboard
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

### 3. Run Demo

```bash
python3 demo_digital_twin.py
```

## 📊 Features

### 🔌 Real-time Monitoring
- **Asset Status**: Live monitoring of transformers, circuit breakers, loads
- **Power Flow**: Real-time power flow analysis and visualization
- **Voltage Profile**: Continuous voltage monitoring across all voltage levels
- **Temperature Monitoring**: Asset temperature tracking and alerts

### 🧠 AI/ML Capabilities
- **Anomaly Detection**: Automatic detection of abnormal operating conditions
- **Predictive Maintenance**: Asset health prediction and maintenance scheduling
- **Optimization**: Power flow optimization and efficiency recommendations
- **Fault Analysis**: Comprehensive fault analysis and protection coordination

### 📡 SCADA Integration
- **Real-time Data**: Integration with SCADA systems via Modbus TCP
- **Historical Data**: SQLite database for historical data storage
- **Alarm Management**: Comprehensive alarm and event management
- **IoT Integration**: Support for various IoT sensors and devices

### 🎨 Professional Visualizations
- **Network Diagrams**: Professional electrical network diagrams
- **Single-line Diagrams**: IEEE-standard electrical schematics
- **Power Flow Charts**: Real-time power flow visualization
- **Voltage Profiles**: Voltage analysis and unbalance detection

## 🔧 API Endpoints

### Asset Management
```http
GET    /api/assets              # Get all assets
GET    /api/assets/{asset_id}   # Get specific asset
POST   /api/control             # Control assets
```

### Substation Metrics
```http
GET    /api/metrics             # Get substation metrics
GET    /api/faults              # Get fault history
POST   /api/faults/analyze       # Run fault analysis
```

### SCADA Integration
```http
GET    /api/scada/data          # Get SCADA data
GET    /api/scada/alarms        # Get SCADA alarms
POST   /api/scada/alarms/{id}/acknowledge  # Acknowledge alarm
```

### AI/ML Analytics
```http
GET    /api/ai/analysis         # Get AI analysis
GET    /api/ai/anomalies        # Get detected anomalies
GET    /api/ai/predictions      # Get maintenance predictions
GET    /api/ai/optimization     # Get optimization recommendations
```

### IoT Devices
```http
GET    /api/iot/devices         # Get IoT devices
GET    /api/iot/devices/{id}/data  # Get device data
```

### Visualization
```http
GET    /api/visualization/network  # Generate network diagram
```

## 🔌 WebSocket API

Real-time data streaming via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Real-time update:', data);
};
```

## 🏭 Substation Components

### Power Transformers
- **400/220 kV Main Transformers**: 315 MVA capacity
- **220/33 kV Distribution Transformers**: 50 MVA capacity
- **Temperature Monitoring**: Oil temperature and level monitoring
- **Health Assessment**: AI-powered health scoring

### Circuit Breakers
- **400 kV Circuit Breakers**: Main transmission protection
- **220 kV Circuit Breakers**: Distribution protection
- **Status Monitoring**: Open/close status and health
- **Protection Coordination**: Fault clearing and coordination

### Load Centers
- **Industrial Loads**: 15 MW capacity
- **Commercial Loads**: 8 MW capacity
- **Load Monitoring**: Real-time power consumption
- **Demand Forecasting**: AI-powered load prediction

### Protection Systems
- **Relay Protection**: Overcurrent, differential, distance protection
- **Fault Analysis**: Comprehensive fault analysis capabilities
- **Protection Coordination**: Time-current coordination
- **Event Recording**: Fault event logging and analysis

## 🧠 AI/ML Models

### Anomaly Detection
- **Isolation Forest**: Unsupervised anomaly detection
- **Real-time Monitoring**: Continuous anomaly scanning
- **Severity Classification**: High, medium, low severity levels
- **Alert Generation**: Automatic alert generation

### Predictive Maintenance
- **Random Forest**: Asset health prediction
- **Maintenance Scheduling**: Optimal maintenance timing
- **Health Degradation**: Asset degradation modeling
- **Risk Assessment**: Asset failure risk evaluation

### Optimization
- **Power Flow Optimization**: Efficiency maximization
- **Load Balancing**: Optimal load distribution
- **Voltage Control**: Voltage stability optimization
- **Cost Optimization**: Operational cost minimization

## 📊 Data Sources

### SCADA Data
- **Voltage Measurements**: All voltage levels
- **Current Measurements**: Phase currents
- **Power Measurements**: Active and reactive power
- **Status Information**: Circuit breaker and switch status

### IoT Sensors
- **Temperature Sensors**: Asset temperature monitoring
- **Vibration Sensors**: Mechanical condition monitoring
- **Gas Sensors**: Transformer oil condition monitoring
- **Environmental Sensors**: Ambient condition monitoring

### Historical Data
- **Operational Data**: Historical operating conditions
- **Maintenance Records**: Asset maintenance history
- **Fault Records**: Historical fault data
- **Performance Data**: Asset performance metrics

## 🔒 Security Features

### Authentication
- **API Authentication**: Secure API access
- **Role-based Access**: Different access levels
- **Session Management**: Secure session handling

### Data Security
- **Data Encryption**: Encrypted data transmission
- **Secure Storage**: Encrypted data storage
- **Access Control**: Granular access permissions

### Cybersecurity
- **Input Validation**: Secure input handling
- **SQL Injection Protection**: Database security
- **XSS Protection**: Cross-site scripting protection

## 🚀 Deployment

### Development Environment
```bash
# Start development server
python3 start_digital_twin.py
```

### Production Deployment
```bash
# Using Docker
docker build -t substation-digital-twin .
docker run -p 8000:8000 substation-digital-twin

# Using systemd service
sudo systemctl start substation-digital-twin
sudo systemctl enable substation-digital-twin
```

## 📈 Performance Metrics

- **Real-time Updates**: 1 Hz update rate
- **Response Time**: < 100ms API response
- **Data Throughput**: 1000+ data points/second
- **Uptime**: 99.9% availability target

## 🔧 Configuration

### SCADA Configuration
```python
scada_config = {
    'collection_interval': 1.0,  # seconds
    'modbus_host': 'localhost',
    'modbus_port': 502,
    'timeout': 5.0
}
```

### AI/ML Configuration
```python
ai_config = {
    'anomaly_threshold': 0.1,
    'prediction_horizon': 30,  # days
    'optimization_interval': 300  # seconds
}
```

## 📚 Documentation

- **API Documentation**: http://localhost:8000/docs
- **WebSocket Documentation**: http://localhost:8000/redoc
- **User Manual**: Available in `/docs` directory
- **Developer Guide**: Available in `/docs` directory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- **Documentation**: Check the API documentation
- **Issues**: Create an issue on GitHub
- **Email**: Contact the development team

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ Basic Digital Twin functionality
- ✅ Real-time monitoring
- ✅ AI/ML integration
- ✅ SCADA integration

### Phase 2 (Next)
- 🔄 3D visualization
- 🔄 Advanced AI models
- 🔄 Mobile applications
- 🔄 Cloud deployment

### Phase 3 (Future)
- 📋 Multi-substation support
- 📋 Grid-wide optimization
- 📋 Advanced analytics
- 📋 Machine learning pipeline

---

**🇮🇳 Indian EHV Substation Digital Twin - Powering the Future of Grid Intelligence**