"""
Trend Calculator Service
Calculates real-time trends from historical metrics data
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TrendData:
    """Trend calculation result"""
    current_value: float
    previous_value: float
    absolute_change: float
    percentage_change: float
    trend_direction: str  # 'up', 'down', 'stable'
    comparison_period: str  # e.g., '1h', '24h'
    is_significant: bool  # Whether change is significant enough to show

class TrendCalculator:
    """
    Calculate trends from historical data stored in database
    Supports multiple comparison periods and statistical significance
    """

    def __init__(self, significance_threshold: float = 0.1):
        """
        Args:
            significance_threshold: Minimum percentage change to consider significant (default 0.1%)
        """
        self.significance_threshold = significance_threshold
        self.comparison_periods = {
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6),
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30)
        }

    def calculate_trend(
        self,
        current_value: float,
        historical_data: List[Dict],
        metric_key: str,
        period: str = '1h'
    ) -> TrendData:
        """
        Calculate trend for a metric based on historical data

        Args:
            current_value: Current metric value
            historical_data: List of historical metrics with timestamps
            metric_key: Key to extract from historical data (e.g., 'total_power')
            period: Comparison period ('1h', '6h', '24h', '7d', '30d')

        Returns:
            TrendData object with trend information
        """
        try:
            if not historical_data:
                return self._create_no_trend(current_value, period)

            # Get comparison point from historical data
            comparison_point = self._get_comparison_point(historical_data, metric_key, period)

            if comparison_point is None:
                return self._create_no_trend(current_value, period)

            # Calculate changes
            absolute_change = current_value - comparison_point
            percentage_change = ((current_value - comparison_point) / comparison_point * 100) if comparison_point != 0 else 0

            # Determine trend direction
            if abs(percentage_change) < self.significance_threshold:
                trend_direction = 'stable'
                is_significant = False
            elif percentage_change > 0:
                trend_direction = 'up'
                is_significant = True
            else:
                trend_direction = 'down'
                is_significant = True

            return TrendData(
                current_value=current_value,
                previous_value=comparison_point,
                absolute_change=absolute_change,
                percentage_change=percentage_change,
                trend_direction=trend_direction,
                comparison_period=period,
                is_significant=is_significant
            )

        except Exception as e:
            logger.error(f"Error calculating trend for {metric_key}: {e}")
            return self._create_no_trend(current_value, period)

    def _get_comparison_point(
        self,
        historical_data: List[Dict],
        metric_key: str,
        period: str
    ) -> Optional[float]:
        """Get the metric value from the comparison period"""
        try:
            if period not in self.comparison_periods:
                period = '1h'

            target_delta = self.comparison_periods[period]

            # Sort data by timestamp (newest first)
            sorted_data = sorted(
                historical_data,
                key=lambda x: datetime.fromisoformat(x.get('timestamp', '2000-01-01')),
                reverse=True
            )

            if not sorted_data:
                return None

            # Get the most recent timestamp
            latest_time = datetime.fromisoformat(sorted_data[0].get('timestamp'))
            target_time = latest_time - target_delta

            # Find the closest data point to target time
            closest_point = None
            min_time_diff = timedelta(days=365)  # Initialize with large value

            for data_point in sorted_data:
                point_time = datetime.fromisoformat(data_point.get('timestamp'))
                time_diff = abs(point_time - target_time)

                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_point = data_point

                # If we've gone past the target time by too much, stop searching
                if point_time < target_time - timedelta(minutes=30):
                    break

            if closest_point:
                return closest_point.get(metric_key)

            return None

        except Exception as e:
            logger.error(f"Error getting comparison point: {e}")
            return None

    def _create_no_trend(self, current_value: float, period: str) -> TrendData:
        """Create a TrendData object when no trend can be calculated"""
        return TrendData(
            current_value=current_value,
            previous_value=current_value,
            absolute_change=0.0,
            percentage_change=0.0,
            trend_direction='stable',
            comparison_period=period,
            is_significant=False
        )

    def calculate_multiple_trends(
        self,
        metrics: Dict[str, float],
        historical_data: List[Dict],
        period: str = '1h'
    ) -> Dict[str, TrendData]:
        """
        Calculate trends for multiple metrics at once

        Args:
            metrics: Dict of current metric values
            historical_data: Historical metrics data
            period: Comparison period

        Returns:
            Dict mapping metric names to TrendData objects
        """
        trends = {}

        for metric_name, current_value in metrics.items():
            trends[metric_name] = self.calculate_trend(
                current_value=current_value,
                historical_data=historical_data,
                metric_key=metric_name,
                period=period
            )

        return trends

    def calculate_moving_average_trend(
        self,
        historical_data: List[Dict],
        metric_key: str,
        window_size: int = 10
    ) -> Tuple[float, str]:
        """
        Calculate trend based on moving average

        Args:
            historical_data: Historical data points
            metric_key: Metric to analyze
            window_size: Number of points for moving average

        Returns:
            Tuple of (slope, direction)
        """
        try:
            if len(historical_data) < window_size:
                return 0.0, 'stable'

            # Extract values
            values = [d.get(metric_key, 0) for d in historical_data[-window_size:]]

            if not values:
                return 0.0, 'stable'

            # Calculate moving average slope using linear regression
            x = np.arange(len(values))
            y = np.array(values)

            # Remove any NaN or inf values
            mask = np.isfinite(y)
            if not mask.any():
                return 0.0, 'stable'

            x = x[mask]
            y = y[mask]

            # Calculate slope
            slope = np.polyfit(x, y, 1)[0] if len(x) > 1 else 0.0

            # Determine direction based on slope
            if abs(slope) < self.significance_threshold:
                direction = 'stable'
            elif slope > 0:
                direction = 'up'
            else:
                direction = 'down'

            return slope, direction

        except Exception as e:
            logger.error(f"Error calculating moving average trend: {e}")
            return 0.0, 'stable'

    def format_trend_display(self, trend: TrendData) -> str:
        """
        Format trend for display in UI

        Args:
            trend: TrendData object

        Returns:
            Formatted string (e.g., "+2.3456%" or "−0.5678%" or "±0.0%")
        """
        if not trend.is_significant:
            # Still show the actual value even if not significant
            sign = "+" if trend.percentage_change > 0 else ("−" if trend.percentage_change < 0 else "±")
            value = abs(trend.percentage_change)
            return f"{sign}{value:.4f}%"

        # Use proper minus sign (−) instead of hyphen (-)
        sign = "+" if trend.percentage_change > 0 else "−"
        value = abs(trend.percentage_change)

        # Show up to 4 decimal places for precision
        return f"{sign}{value:.4f}%"

    def get_trend_color(self, trend: TrendData, metric_name: str) -> str:
        """
        Get color for trend display based on whether increase is good or bad

        Args:
            trend: TrendData object
            metric_name: Name of metric to determine if increase is positive

        Returns:
            Color code for UI
        """
        # Metrics where increase is good
        positive_metrics = {
            'efficiency', 'voltage_stability', 'power_factor',
            'health_score', 'availability'
        }

        # Metrics where increase might be concerning
        negative_metrics = {
            'losses', 'temperature', 'fault_count',
            'anomaly_count', 'reactive_power'
        }

        if not trend.is_significant:
            return '#6b7280'  # Gray for stable

        is_increase = trend.percentage_change > 0

        if metric_name in positive_metrics:
            return '#10b981' if is_increase else '#ef4444'  # Green/Red
        elif metric_name in negative_metrics:
            return '#ef4444' if is_increase else '#10b981'  # Red/Green
        else:
            # Neutral metrics (like power) - just show direction
            return '#3b82f6' if is_increase else '#f59e0b'  # Blue/Orange


# Singleton instance
_trend_calculator = None

def get_trend_calculator(significance_threshold: float = 0.1) -> TrendCalculator:
    """Get or create TrendCalculator singleton"""
    global _trend_calculator
    if _trend_calculator is None:
        _trend_calculator = TrendCalculator(significance_threshold)
    return _trend_calculator
