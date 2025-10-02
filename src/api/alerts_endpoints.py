"""
Alerts and AI Insights API Endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["alerts"])

# Global references
_alert_service = None
_ai_insights_service = None
_asset_manager = None

def set_services(alert_service, ai_insights_service, asset_manager):
    """Set service instances from main app"""
    global _alert_service, _ai_insights_service, _asset_manager
    _alert_service = alert_service
    _ai_insights_service = ai_insights_service
    _asset_manager = asset_manager

# Request/Response Models
class AnomalyTriggerRequest(BaseModel):
    anomaly_type: str
    asset_id: str
    description: str
    severity: Optional[str] = "high"

class AlertAcknowledgeRequest(BaseModel):
    alert_id: int

class AlertResolveRequest(BaseModel):
    alert_id: int

@router.get("/alerts")
async def get_alerts(
    limit: int = Query(100, description="Number of alerts to fetch"),
    unresolved_only: bool = Query(False, description="Only fetch unresolved alerts")
):
    """Get alerts from database"""
    try:
        if _alert_service is None:
            raise HTTPException(status_code=503, detail="Alert service not initialized")

        alerts = _alert_service.get_recent_alerts(limit=limit, unresolved_only=unresolved_only)

        # Format alerts for frontend
        formatted_alerts = []
        for alert in alerts:
            formatted_alerts.append({
                'id': alert.get('id'),
                'timestamp': alert.get('timestamp'),
                'type': alert.get('alert_type'),
                'severity': alert.get('severity'),
                'asset_id': alert.get('asset_id'),
                'description': alert.get('message'),
                'acknowledged': bool(alert.get('acknowledged')),
                'resolved': bool(alert.get('resolved')),
                'duration': None  # Could calculate based on resolution time
            })

        return {
            'total': len(formatted_alerts),
            'alerts': formatted_alerts,
            'unresolved_count': sum(1 for a in formatted_alerts if not a['resolved'])
        }

    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/acknowledge")
async def acknowledge_alert(request: AlertAcknowledgeRequest):
    """Acknowledge an alert"""
    try:
        if _alert_service is None:
            raise HTTPException(status_code=503, detail="Alert service not initialized")

        _alert_service.acknowledge_alert(request.alert_id)

        return {
            'success': True,
            'message': f'Alert {request.alert_id} acknowledged',
            'alert_id': request.alert_id
        }

    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/resolve")
async def resolve_alert(request: AlertResolveRequest):
    """Resolve an alert"""
    try:
        if _alert_service is None:
            raise HTTPException(status_code=503, detail="Alert service not initialized")

        _alert_service.resolve_alert(request.alert_id)

        return {
            'success': True,
            'message': f'Alert {request.alert_id} resolved',
            'alert_id': request.alert_id
        }

    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/anomaly/trigger")
async def trigger_anomaly(request: AnomalyTriggerRequest):
    """Trigger an anomaly alert (from visualization page)"""
    try:
        if _alert_service is None:
            raise HTTPException(status_code=503, detail="Alert service not initialized")

        # Create alert
        alert = await _alert_service.trigger_anomaly_alert(
            anomaly_type=request.anomaly_type,
            asset_id=request.asset_id,
            description=request.description,
            severity=request.severity
        )

        if not alert:
            raise HTTPException(status_code=500, detail="Failed to create anomaly alert")

        # Optionally trigger AI analysis
        if _ai_insights_service and _asset_manager:
            try:
                asset = _asset_manager.get_asset(request.asset_id)
                if asset:
                    metrics = {}  # Could fetch current metrics
                    await _ai_insights_service.generate_asset_insight(
                        request.asset_id,
                        asset.__dict__ if hasattr(asset, '__dict__') else {},
                        metrics
                    )
            except Exception as e:
                logger.warning(f"Failed to generate AI insight for anomaly: {e}")

        return {
            'success': True,
            'message': 'Anomaly alert created successfully',
            'alert': alert
        }

    except Exception as e:
        logger.error(f"Error triggering anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/insights")
async def get_ai_insights(
    limit: int = Query(50, description="Number of insights to fetch"),
    analysis_type: Optional[str] = Query(None, description="Filter by analysis type")
):
    """Get AI insights from database"""
    try:
        if _ai_insights_service is None:
            raise HTTPException(status_code=503, detail="AI insights service not initialized")

        insights = _ai_insights_service.get_recent_insights(limit=limit, analysis_type=analysis_type)

        # Format insights for frontend
        formatted_insights = []
        for insight in insights:
            import json
            data = json.loads(insight.get('data', '{}')) if isinstance(insight.get('data'), str) else insight.get('data', {})

            formatted_insights.append({
                'id': insight.get('id'),
                'timestamp': insight.get('timestamp'),
                'analysis_type': insight.get('analysis_type'),
                'asset_id': insight.get('asset_id'),
                'anomaly_score': insight.get('anomaly_score', 0),
                'prediction': insight.get('prediction', ''),
                'recommendation': insight.get('recommendation', ''),
                'details': data
            })

        return {
            'total': len(formatted_insights),
            'insights': formatted_insights
        }

    except Exception as e:
        logger.error(f"Error fetching AI insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/analyze")
async def trigger_ai_analysis():
    """Manually trigger AI analysis for all assets"""
    try:
        if _ai_insights_service is None or _asset_manager is None:
            raise HTTPException(status_code=503, detail="Services not initialized")

        # Get all assets
        assets = {}
        for asset_id in _asset_manager.assets:
            asset = _asset_manager.get_asset(asset_id)
            if asset:
                assets[asset_id] = asset.__dict__ if hasattr(asset, '__dict__') else {}

        # Run system-wide analysis
        metrics = {}  # Could fetch current metrics
        result = await _ai_insights_service.analyze_system_health(assets, metrics)

        return {
            'success': True,
            'message': 'AI analysis completed',
            'result': result
        }

    except Exception as e:
        logger.error(f"Error triggering AI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
