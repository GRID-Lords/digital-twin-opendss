# Digital Twin System - Quick Start Guide

## 🚀 One-Command Setup

The entire system can be started with a single command:

```bash
./start.sh
```

That's it! The system will automatically:
- ✅ Start Redis (cache)
- ✅ Start InfluxDB (time-series metrics)
- ✅ Initialize SQLite database
- ✅ Start backend API (port 8000)
- ✅ Start frontend UI (port 3000)

## 📦 What Gets Installed

### Databases (via Docker)
- **Redis**: Real-time cache (60s TTL)
- **InfluxDB**: High-frequency time-series data
- **SQLite**: Persistent storage (alerts, DSS versions, thresholds)

### Services
- **Backend**: FastAPI server with OpenDSS simulation
- **Frontend**: React dashboard

## 🌐 Access Points

After starting, access the system at:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Main dashboard |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| DSS Editor | http://localhost:3000/dss-editor | DSS file management |
| InfluxDB UI | http://localhost:8086 | Time-series data (admin / DT2024SecurePass) |

## 🐳 Docker-Only Mode

For production or containerized deployment:

```bash
./start.sh docker
```

This runs everything in Docker containers (backend + frontend + databases).

## 📊 System Architecture

```
┌─────────────────────────────────────────────────┐
│              Backend (Port 8000)                │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Redis   │  │  SQLite  │  │ InfluxDB │     │
│  │ (Cache)  │  │(Primary) │  │(Metrics) │     │
│  └──────────┘  └──────────┘  └──────────┘     │
│                                                  │
│  OpenDSS Simulation + AI/ML + SCADA             │
└─────────────────────────────────────────────────┘
                    ↓
        Frontend (Port 3000)
```

## 🛑 Stopping the System

Press `Ctrl+C` in the terminal running start.sh, or:

```bash
# For Docker mode
docker-compose down

# For local mode
pkill -f backend_server
pkill -f "npm start"
```

## 🔧 Configuration

All configuration is in `docker-compose.yml`. No separate `.env` file needed!

Key settings:
- Database: SQLite (no PostgreSQL required)
- Cache TTL: 60 seconds
- Metrics interval: 3600 seconds (1 hour)
- InfluxDB retention: Unlimited

## 📝 Features

- ✅ Real-time power flow simulation
- ✅ Asset health monitoring (transformers, breakers, etc.)
- ✅ AI-powered anomaly detection
- ✅ Predictive maintenance alerts
- ✅ DSS file versioning & validation
- ✅ SCADA integration
- ✅ Historical trend analysis
- ✅ Threshold management

## 🆘 Troubleshooting

**Port already in use?**
```bash
lsof -ti:8000 | xargs kill -9  # Kill process on port 8000
lsof -ti:3000 | xargs kill -9  # Kill process on port 3000
```

**Docker containers not starting?**
```bash
docker-compose down
docker-compose up -d redis influxdb
```

**Check logs:**
```bash
tail -f logs/backend.log
docker-compose logs -f backend
```

## 📚 API Documentation

Full API documentation available at:
http://localhost:8000/docs

Key endpoints:
- `/api/metrics` - Current system metrics
- `/api/assets` - Asset management
- `/api/alerts` - Alert management
- `/api/dss/current` - DSS file operations
- `/api/historical/*` - Historical data & trends

## 🎯 Data Storage

- **Real-time data**: Redis (60s TTL) → Fast access
- **Time-series metrics**: InfluxDB → 938 records/hour
- **Persistent data**: SQLite → Alerts, DSS versions, thresholds
- **Volumes**: All data persists in Docker volumes

## 💡 Pro Tips

1. **First time setup**: Models will be trained automatically (~30 seconds)
2. **Docker mode**: Uses volumes for persistence (data survives container restarts)
3. **Local mode**: Faster for development, direct file access
4. **DSS Editor**: Edit circuit files with version control
5. **InfluxDB UI**: Query time-series data at http://localhost:8086

---

**Need help?** Check logs in `logs/backend.log` or run with `--verbose` flag.
