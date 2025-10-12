# Real Trend Calculation Architecture

## Overview
This document describes the architecture for calculating **real, data-driven trend percentages** from historical metrics stored in the database, replacing the previously hardcoded trend values.

---

## Architecture Components

### 1. **Trend Calculator Service** (`src/services/trend_calculator.py`)

A standalone service responsible for calculating trends from historical data.

#### Key Features:
- ✅ **Real-time trend calculation** from database metrics
- ✅ **Multiple comparison periods** (1h, 6h, 24h, 7d, 30d)
- ✅ **Statistical significance** threshold to avoid showing noise
- ✅ **Direction detection** (up, down, stable)
- ✅ **Moving average trends** for smoother analysis
- ✅ **Formatted display** for UI (+2.3%, −0.5%, ±0.0%)

#### Core Classes:

```python
@dataclass
class TrendData:
    """Trend calculation result"""
    current_value: float
    previous_value: float
    absolute_change: float
    percentage_change: float
    trend_direction: str  # 'up', 'down', 'stable'
    comparison_period: str
    is_significant: bool

class TrendCalculator:
    """Calculate trends from historical database data"""
    def __init__(self, significance_threshold: float = 0.1)
    def calculate_trend(...)
    def format_trend_display(...)
    def get_trend_color(...)
```

---

### 2. **Backend Integration** (`src/backend_server.py`)

The `/api/metrics` endpoint is enhanced to include real trend data.

#### Flow:
1. Get current metrics from OpenDSS
2. Fetch historical metrics from database (last 24 hours)
3. Calculate trends for key metrics (total_power, efficiency, voltage_stability, frequency)
4. Append trends to metrics response

#### Code Example:

```python
@app.get("/api/metrics")
async def get_metrics():
    """Get current system metrics with real trend calculations"""
    metrics = await get_current_metrics()

    # Get historical data
    historical_data = await data_manager.get_historical_metrics(hours=24)

    if historical_data and len(historical_data) > 1:
        trend_calc = get_trend_calculator(significance_threshold=0.1)

        # Calculate trends for each metric
        trends = {}
        for metric_name in ['total_power', 'efficiency', 'voltage_stability', 'frequency']:
            trend = trend_calc.calculate_trend(
                current_value=metrics[metric_name],
                historical_data=historical_data,
                metric_key=metric_name,
                period='1h'  # Compare with 1 hour ago
            )

            trends[metric_name] = {
                'value': trend_calc.format_trend_display(trend),
                'percentage': round(trend.percentage_change, 2),
                'direction': trend.trend_direction,
                'is_significant': trend.is_significant
            }

        metrics['trends'] = trends

    return metrics
```

---

### 3. **Frontend Integration** (`frontend/src/pages/Dashboard.js`)

The Dashboard component now uses real trends from the API instead of hardcoded values.

#### Before (Hardcoded):
```javascript
const metricCards = [
  {
    title: 'Total Power',
    value: `${metrics.total_power?.toFixed(2)} MW`,
    trend: '+2.3%'  // ❌ HARDCODED
  },
  // ...
]
```

#### After (Real Data):
```javascript
const getTrend = (metricName) => {
  if (metrics.trends && metrics.trends[metricName]) {
    return metrics.trends[metricName].value;
  }
  return '±0.0%'; // Fallback
};

const metricCards = [
  {
    title: 'Total Power',
    value: `${metrics.total_power?.toFixed(2)} MW`,
    trend: getTrend('total_power')  // ✅ REAL DATA
  },
  // ...
]
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE (SQLite/Redis)                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Historical Metrics (Last 24 hours)                  │   │
│  │  - total_power: [34.2, 35.1, 33.8, 34.07, ...]      │   │
│  │  - efficiency: [96.5, 97.2, 97.0, 97.18, ...]       │   │
│  │  - voltage_stability: [98.2, 98.5, 98.9, 98.78, ...] │   │
│  │  - timestamps                                         │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────┐
│              BACKEND: Trend Calculator Service               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Fetch historical data (24h window)               │  │
│  │  2. Find comparison point (1 hour ago)               │  │
│  │  3. Calculate: (current - previous) / previous * 100 │  │
│  │  4. Determine direction & significance               │  │
│  │  5. Format for display (+2.3%, −0.5%, ±0.0%)       │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                  API Response: /api/metrics                  │
│  {                                                           │
│    "total_power": 34.07,                                    │
│    "efficiency": 97.18,                                     │
│    "voltage_stability": 98.78,                              │
│    "trends": {                                              │
│      "total_power": {                                       │
│        "value": "+2.3%",                                    │
│        "percentage": 2.3,                                   │
│        "direction": "up",                                   │
│        "is_significant": true,                              │
│        "previous_value": 33.3                               │
│      },                                                     │
│      "efficiency": { ... },                                 │
│      "voltage_stability": { ... }                           │
│    }                                                        │
│  }                                                          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND: Dashboard                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Display Cards:                                       │  │
│  │                                                       │  │
│  │  Total Power      Efficiency    Voltage Stability    │  │
│  │  34.07 MW         97.18%        98.78%               │  │
│  │  +2.3% ↑          +0.5% ↑       −0.2% ↓             │  │
│  │  (REAL)           (REAL)        (REAL)               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Trend Calculation Logic

### 1. **Comparison Point Selection**
```python
def _get_comparison_point(historical_data, metric_key, period):
    """
    Find the metric value from 'period' ago

    Example: If period='1h' and current time is 14:00
             Find the data point closest to 13:00
    """
    target_time = current_time - timedelta(hours=1)
    closest_point = find_closest_data_point(historical_data, target_time)
    return closest_point[metric_key]
```

### 2. **Percentage Change Calculation**
```python
percentage_change = ((current - previous) / previous) * 100

Examples:
- Current: 34.07, Previous: 33.3  → +2.3%
- Current: 97.18, Previous: 96.7  → +0.5%
- Current: 98.78, Previous: 99.0  → −0.2%
```

### 3. **Significance Threshold**
```python
significance_threshold = 0.1%  # Configurable

if abs(percentage_change) < 0.1:
    direction = 'stable'
    display = '±0.0%'
else:
    direction = 'up' if percentage_change > 0 else 'down'
    display = f"+{percentage_change:.1f}%" or f"−{abs(percentage_change):.1f}%"
```

---

## Comparison Periods

The system supports multiple comparison periods:

| Period | Timedelta | Use Case |
|--------|-----------|----------|
| `1h` | 1 hour | Real-time trends (default) |
| `6h` | 6 hours | Short-term trends |
| `24h` | 24 hours | Daily trends |
| `7d` | 7 days | Weekly trends |
| `30d` | 30 days | Monthly trends |

**Current Implementation**: Uses **1 hour** comparison for dashboard display.

---

## Statistical Significance

### Why Significance Matters:
- Power systems have natural variations
- Small fluctuations (±0.05%) are not meaningful
- Threshold prevents showing "noise" as trends

### Threshold:
```python
significance_threshold = 0.1%  # Default

Examples:
- Change: +0.05% → Display: ±0.0% (not significant)
- Change: +0.3%  → Display: +0.3% (significant)
- Change: −1.2%  → Display: −1.2% (significant)
```

---

## Fallback Behavior

### When No Historical Data:
```json
{
  "trends": {
    "total_power": {"value": "±0.0%", "direction": "stable"},
    "efficiency": {"value": "±0.0%", "direction": "stable"},
    "voltage_stability": {"value": "±0.0%", "direction": "stable"},
    "frequency": {"value": "±0.0%", "direction": "stable"}
  }
}
```

### When Calculation Error:
- Logs error
- Returns empty trends object `{}`
- Frontend shows fallback "±0.0%"

---

## Benefits

### ✅ **Real Data-Driven**
- Trends calculated from actual historical metrics
- No hardcoded values
- Reflects true system behavior

### ✅ **Database Integration**
- Uses existing metrics storage
- No additional infrastructure needed
- Scales with data volume

### ✅ **Configurable**
- Adjustable comparison periods
- Customizable significance threshold
- Flexible trend calculation methods

### ✅ **Robust**
- Graceful fallbacks
- Error handling
- Statistical significance filtering

### ✅ **User Experience**
- Clear visual indicators (+, −, ±)
- Percentage and direction
- Meaningful trend information

---

## API Response Example

### Full Response from `/api/metrics`:
```json
{
  "timestamp": "2025-10-12T12:34:56",
  "total_power": 34.07,
  "efficiency": 97.18,
  "voltage_stability": 98.78,
  "frequency": 50.02,
  "trends": {
    "total_power": {
      "value": "+2.3%",
      "percentage": 2.3,
      "direction": "up",
      "is_significant": true,
      "previous_value": 33.3,
      "absolute_change": 0.77
    },
    "efficiency": {
      "value": "+0.5%",
      "percentage": 0.5,
      "direction": "up",
      "is_significant": true,
      "previous_value": 96.7,
      "absolute_change": 0.48
    },
    "voltage_stability": {
      "value": "−0.2%",
      "percentage": -0.2,
      "direction": "down",
      "is_significant": true,
      "previous_value": 99.0,
      "absolute_change": -0.22
    },
    "frequency": {
      "value": "±0.0%",
      "percentage": 0.04,
      "direction": "stable",
      "is_significant": false,
      "previous_value": 50.0,
      "absolute_change": 0.02
    }
  }
}
```

---

## Testing & Verification

### Manual Testing:
```bash
# 1. Start backend
python src/backend_server.py

# 2. Check metrics endpoint
curl http://localhost:8000/api/metrics | jq '.trends'

# Expected output:
{
  "total_power": {"value": "+X.X%", ...},
  "efficiency": {"value": "+X.X%", ...},
  ...
}

# 3. Verify frontend
Open: http://localhost:3000/
Check: Dashboard cards show real trends
```

### Automated Testing:
```python
# Add to tests/unit/test_trend_calculator.py
def test_trend_calculation_with_real_data():
    historical = [
        {'total_power': 33.3, 'timestamp': '2025-10-12T11:00:00'},
        {'total_power': 34.07, 'timestamp': '2025-10-12T12:00:00'}
    ]

    trend_calc = TrendCalculator()
    trend = trend_calc.calculate_trend(34.07, historical, 'total_power', '1h')

    assert trend.percentage_change == pytest.approx(2.3, rel=0.1)
    assert trend.direction == 'up'
    assert trend.is_significant == True
```

---

## Future Enhancements

### 1. **Advanced Trend Analysis**
- Exponential moving average (EMA)
- Weighted moving average (WMA)
- Seasonal decomposition

### 2. **Predictive Trends**
- Linear regression forecasting
- ARIMA models
- ML-based prediction

### 3. **User Preferences**
- Configurable comparison period in UI
- Custom significance thresholds
- Trend visualization charts

### 4. **Alert Integration**
- Alert on significant trend changes
- Anomaly detection in trends
- Threshold-based notifications

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Trend Source** | ❌ Hardcoded | ✅ Database |
| **Data Accuracy** | ❌ Static values | ✅ Real metrics |
| **Update Frequency** | ❌ Never | ✅ Every request |
| **Historical Basis** | ❌ None | ✅ Last 24 hours |
| **Significance Filter** | ❌ No | ✅ Yes (0.1%) |
| **Comparison Period** | ❌ Fixed | ✅ Configurable |
| **Fallback Handling** | ❌ N/A | ✅ Yes |

**Result**: Dashboard now displays **100% real, data-driven trends** calculated from actual historical metrics! 🎉

---

## Files Modified/Created

### Created:
- ✅ `src/services/trend_calculator.py` - Trend calculation service
- ✅ `docs/REAL_TREND_ARCHITECTURE.md` - This documentation

### Modified:
- ✅ `src/backend_server.py` - Updated `/api/metrics` endpoint
- ✅ `frontend/src/pages/Dashboard.js` - Use real trends

---

**Date**: 2025-10-12
**Status**: ✅ Complete and Operational
