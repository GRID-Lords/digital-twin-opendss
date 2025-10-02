"""
AI Insights Service
Generates AI-driven insights and analysis for the digital twin
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np
from src.database import db

logger = logging.getLogger(__name__)

class AIInsightsService:
    """Service for generating AI-driven insights and recommendations"""

    def __init__(self, ai_manager=None):
        self.ai_manager = ai_manager

    async def generate_asset_insight(
        self,
        asset_id: str,
        asset_data: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate AI insight for a specific asset"""

        try:
            params = asset_data.get('parameters', {})

            # Calculate anomaly score
            anomaly_score = await self._calculate_anomaly_score(asset_data, metrics)

            # Generate prediction
            prediction = await self._generate_prediction(asset_id, asset_data, anomaly_score)

            # Generate recommendation
            recommendation = await self._generate_recommendation(asset_id, asset_data, anomaly_score)

            # Store in database
            analysis_id = db.store_ai_analysis(
                analysis_type='asset_health',
                asset_id=asset_id,
                results={
                    'anomaly_score': anomaly_score,
                    'prediction': prediction,
                    'recommendation': recommendation,
                    'asset_status': asset_data.get('status'),
                    'health_score': asset_data.get('health', 100)
                }
            )

            logger.info(f"AI insight generated for {asset_id}: score={anomaly_score:.2f}")

            return {
                'id': analysis_id,
                'asset_id': asset_id,
                'analysis_type': 'asset_health',
                'anomaly_score': anomaly_score,
                'prediction': prediction,
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to generate insight for {asset_id}: {e}")
            return None

    async def _calculate_anomaly_score(
        self,
        asset_data: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> float:
        """Calculate anomaly score based on asset parameters"""

        params = asset_data.get('parameters', {})
        anomaly_factors = []

        # Check voltage deviation
        voltage = params.get('hv_voltage') or params.get('lv_voltage')
        if voltage:
            rated_voltage = float(params.get('voltage', '0').replace('kV', '').strip() or '0')
            if rated_voltage > 0:
                voltage_deviation = abs(voltage - rated_voltage) / rated_voltage
                anomaly_factors.append(voltage_deviation * 10)

        # Check temperature
        temperature = params.get('temperature')
        if temperature:
            temp_score = max(0, (temperature - 60) / 40)  # 60°C normal, 100°C max
            anomaly_factors.append(temp_score * 10)

        # Check loading
        loading = params.get('loading_percent')
        if loading:
            loading_score = max(0, (loading - 80) / 20)  # 80% normal, 100% max
            anomaly_factors.append(loading_score * 10)

        # Check health score
        health = asset_data.get('health', 100)
        health_score = max(0, (100 - health) / 100) * 10
        anomaly_factors.append(health_score)

        # Use AI manager if available
        if self.ai_manager and anomaly_factors:
            try:
                # Create feature vector for AI model
                features = np.array(anomaly_factors).reshape(1, -1)
                # Pad to match expected feature size if needed
                if features.shape[1] < 5:
                    features = np.pad(features, ((0, 0), (0, 5 - features.shape[1])), mode='constant')

                # Get AI prediction (if model is available)
                # For now, use simple average
                pass
            except Exception as e:
                logger.warning(f"AI model unavailable, using rule-based scoring: {e}")

        # Calculate average anomaly score (0-10 scale)
        if anomaly_factors:
            return min(10.0, sum(anomaly_factors) / len(anomaly_factors))
        return 0.0

    async def _generate_prediction(
        self,
        asset_id: str,
        asset_data: Dict[str, Any],
        anomaly_score: float
    ) -> str:
        """Generate prediction about asset condition"""

        if anomaly_score > 7.0:
            return "High risk of failure within 24-48 hours. Immediate inspection recommended."
        elif anomaly_score > 5.0:
            return "Moderate risk detected. Schedule maintenance within next 7 days."
        elif anomaly_score > 3.0:
            return "Minor anomalies detected. Monitor closely for next 30 days."
        elif anomaly_score > 1.0:
            return "Asset operating within normal parameters with slight variations."
        else:
            return "Asset operating optimally with no anomalies detected."

    async def _generate_recommendation(
        self,
        asset_id: str,
        asset_data: Dict[str, Any],
        anomaly_score: float
    ) -> str:
        """Generate actionable recommendation"""

        params = asset_data.get('parameters', {})
        recommendations = []

        # Temperature-based recommendations
        temperature = params.get('temperature')
        if temperature and temperature > 85:
            recommendations.append("Activate additional cooling systems")
            recommendations.append("Check for blockages in cooling ducts")

        # Voltage-based recommendations
        voltage = params.get('hv_voltage') or params.get('lv_voltage')
        if voltage:
            rated = float(params.get('voltage', '0').replace('kV', '').strip() or '0')
            if rated > 0:
                deviation = abs(voltage - rated) / rated
                if deviation > 0.05:  # >5% deviation
                    recommendations.append("Adjust tap changer position")
                    recommendations.append("Verify grid voltage stability")

        # Loading-based recommendations
        loading = params.get('loading_percent')
        if loading and loading > 90:
            recommendations.append("Consider load shedding or redistribution")
            recommendations.append("Prepare backup transformer for operation")

        # General recommendations based on anomaly score
        if anomaly_score > 7.0:
            recommendations.append("Immediate emergency response required")
            recommendations.append("Notify operations team and prepare contingency plan")
        elif anomaly_score > 5.0:
            recommendations.append("Schedule detailed inspection and testing")
            recommendations.append("Review recent operational history")

        if recommendations:
            return " | ".join(recommendations[:3])  # Return top 3 recommendations
        return "Continue normal monitoring. No immediate action required."

    async def analyze_system_health(
        self,
        assets: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze overall system health and generate insights"""

        try:
            # Analyze all assets
            asset_insights = []
            total_anomaly_score = 0
            critical_assets = []

            for asset_id, asset_data in assets.items():
                insight = await self.generate_asset_insight(asset_id, asset_data, metrics)
                if insight:
                    asset_insights.append(insight)
                    total_anomaly_score += insight['anomaly_score']

                    if insight['anomaly_score'] > 5.0:
                        critical_assets.append(asset_id)

            # Calculate system-wide metrics
            avg_anomaly_score = total_anomaly_score / len(assets) if assets else 0

            # Store system-level insight
            system_insight_id = db.store_ai_analysis(
                analysis_type='system_health',
                asset_id='SYSTEM',
                results={
                    'avg_anomaly_score': avg_anomaly_score,
                    'critical_assets_count': len(critical_assets),
                    'total_assets': len(assets),
                    'critical_assets': critical_assets,
                    'prediction': self._get_system_prediction(avg_anomaly_score),
                    'recommendation': self._get_system_recommendation(avg_anomaly_score, len(critical_assets))
                }
            )

            return {
                'system_insight_id': system_insight_id,
                'avg_anomaly_score': avg_anomaly_score,
                'critical_assets': critical_assets,
                'total_insights': len(asset_insights)
            }

        except Exception as e:
            logger.error(f"Failed to analyze system health: {e}")
            return {}

    def _get_system_prediction(self, avg_score: float) -> str:
        """Get system-level prediction"""
        if avg_score > 6.0:
            return "System stability at risk. Multiple assets showing critical conditions."
        elif avg_score > 4.0:
            return "System operating with elevated risk. Some assets require attention."
        elif avg_score > 2.0:
            return "System stable with minor anomalies in some assets."
        else:
            return "System operating optimally across all assets."

    def _get_system_recommendation(self, avg_score: float, critical_count: int) -> str:
        """Get system-level recommendation"""
        if critical_count > 3:
            return "Initiate emergency protocols. Multiple critical assets detected."
        elif critical_count > 0:
            return f"Prioritize inspection of {critical_count} critical asset(s). Prepare contingency plans."
        elif avg_score > 3.0:
            return "Increase monitoring frequency. Review maintenance schedules."
        else:
            return "Maintain current operational parameters. Continue routine monitoring."

    def get_recent_insights(self, limit: int = 50, analysis_type: str = None) -> List[Dict]:
        """Get recent AI insights from database"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM ai_analysis"
                params = []

                if analysis_type:
                    query += " WHERE analysis_type = ?"
                    params.append(analysis_type)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get insights: {e}")
            return []

# Global instance (will be initialized with ai_manager later)
ai_insights_service = AIInsightsService()
