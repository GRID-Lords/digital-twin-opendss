# Indian EHV Substation Digital Twin

A comprehensive Digital Twin solution for Indian Extra High Voltage (EHV) 400/220 kV substations, featuring real-time monitoring, AI/ML-powered predictive analytics, SCADA integration, and professional electrical visualizations.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the Digital Twin
python3 main.py
```

## 📁 Project Structure

```
├── src/
│   ├── api/                    # REST API and WebSocket server
│   │   └── digital_twin_server.py
│   ├── integration/            # SCADA and IoT integration
│   │   └── scada_integration.py
│   ├── models/                # AI/ML models and OpenDSS models
│   │   ├── ai_ml_models.py
│   │   └── IndianEHVSubstation.dss
│   └── visualization/          # Circuit visualization
│       └── circuit_visualizer.py
├── examples/                   # Example circuits and demos
│   ├── EnhancedCircuit.dss
│   └── start_digital_twin.py
├── docs/                       # Documentation
│   └── README_DIGITAL_TWIN.md
├── main.py                     # Main entry point
└── requirements.txt            # Dependencies
```

## 🌐 Access Points

- **Web Dashboard**: http://localhost:8000/dashboard
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

## 📚 Documentation

See `docs/README_DIGITAL_TWIN.md` for comprehensive documentation.

## 🔧 Development

```bash
# Run examples
python3 examples/start_digital_twin.py

# Test individual components
python3 -c "from src.visualization.circuit_visualizer import OpenDSSVisualizer; print('Visualizer OK')"
python3 -c "from src.models.ai_ml_models import SubstationAIManager; print('AI/ML OK')"
python3 -c "from src.integration.scada_integration import SCADAIntegrationManager; print('SCADA OK')"
```

## 📄 License

MIT License - see LICENSE file for details.