"""
Threshold Configuration API Endpoints
Allows users to configure custom thresholds for SCADA components
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/thresholds", tags=["thresholds"])

# Global reference to database
_db = None

def set_database(db):
    """Set database instance from main app"""
    global _db
    _db = db

# Request/Response Models
class ThresholdCreateRequest(BaseModel):
    component_id: str
    component_name: str
    component_type: str
    metric_name: str
    metric_unit: Optional[str] = ""
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    severity: Optional[str] = "medium"
    enabled: Optional[bool] = True
    description: Optional[str] = ""

class ThresholdUpdateRequest(BaseModel):
    component_name: Optional[str] = None
    component_type: Optional[str] = None
    metric_name: Optional[str] = None
    metric_unit: Optional[str] = None
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    severity: Optional[str] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None

class ThresholdBulkCreateRequest(BaseModel):
    thresholds: List[ThresholdCreateRequest]

@router.get("")
async def get_all_thresholds(
    enabled_only: bool = Query(False, description="Only fetch enabled thresholds")
):
    """Get all threshold configurations"""
    try:
        if _db is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        thresholds = _db.get_all_thresholds(enabled_only=enabled_only)

        return {
            'success': True,
            'total': len(thresholds),
            'thresholds': thresholds
        }

    except Exception as e:
        logger.error(f"Error fetching thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{threshold_id}")
async def get_threshold(threshold_id: int):
    """Get a specific threshold by ID"""
    try:
        if _db is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        threshold = _db.get_threshold_by_id(threshold_id)

        if not threshold:
            raise HTTPException(status_code=404, detail=f"Threshold {threshold_id} not found")

        return {
            'success': True,
            'threshold': threshold
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/component/{component_id}")
async def get_component_thresholds(component_id: str):
    """Get all thresholds for a specific component"""
    try:
        if _db is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        thresholds = _db.get_thresholds_for_component(component_id)

        return {
            'success': True,
            'component_id': component_id,
            'total': len(thresholds),
            'thresholds': thresholds
        }

    except Exception as e:
        logger.error(f"Error fetching component thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def create_threshold(request: ThresholdCreateRequest):
    """Create a new threshold configuration"""
    try:
        if _db is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        # Validate that at least one threshold is set
        if request.threshold_min is None and request.threshold_max is None:
            raise HTTPException(
                status_code=400,
                detail="At least one of threshold_min or threshold_max must be set"
            )

        threshold_data = request.dict()
        threshold_id = _db.create_threshold(threshold_data)

        if not threshold_id:
            raise HTTPException(status_code=500, detail="Failed to create threshold")

        return {
            'success': True,
            'message': 'Threshold created successfully',
            'threshold_id': threshold_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk")
async def create_thresholds_bulk(request: ThresholdBulkCreateRequest):
    """Create multiple thresholds at once"""
    try:
        if _db is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        created_ids = []
        errors = []

        for idx, threshold_req in enumerate(request.thresholds):
            try:
                threshold_data = threshold_req.dict()
                threshold_id = _db.upsert_threshold(threshold_data)
                created_ids.append(threshold_id)
            except Exception as e:
                errors.append({
                    'index': idx,
                    'component_id': threshold_req.component_id,
                    'error': str(e)
                })

        return {
            'success': len(errors) == 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'errors': errors
        }

    except Exception as e:
        logger.error(f"Error creating thresholds in bulk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{threshold_id}")
async def update_threshold(threshold_id: int, request: ThresholdUpdateRequest):
    """Update an existing threshold"""
    try:
        if _db is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        # Check if threshold exists
        existing = _db.get_threshold_by_id(threshold_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Threshold {threshold_id} not found")

        # Only include fields that were actually provided
        update_data = {k: v for k, v in request.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        success = _db.update_threshold(threshold_id, update_data)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update threshold")

        return {
            'success': True,
            'message': f'Threshold {threshold_id} updated successfully'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{threshold_id}")
async def delete_threshold(threshold_id: int):
    """Delete a threshold configuration"""
    try:
        if _db is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        # Check if threshold exists
        existing = _db.get_threshold_by_id(threshold_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Threshold {threshold_id} not found")

        success = _db.delete_threshold(threshold_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete threshold")

        return {
            'success': True,
            'message': f'Threshold {threshold_id} deleted successfully'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize-defaults")
async def initialize_default_thresholds():
    """Initialize default thresholds for common SCADA components"""
    try:
        if _db is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        # Default thresholds for typical EHV substation components
        default_thresholds = [
            # 400kV Bus Voltage
            {
                'component_id': '400kV_VOLTAGE_A',
                'component_name': '400kV Bus A Voltage',
                'component_type': 'voltage',
                'metric_name': 'voltage',
                'metric_unit': 'kV',
                'threshold_min': 380.0,
                'threshold_max': 420.0,
                'severity': 'high',
                'enabled': True,
                'description': '400kV bus voltage must be within ±5% of nominal'
            },
            # 220kV Bus Voltage
            {
                'component_id': '220kV_VOLTAGE_A',
                'component_name': '220kV Bus A Voltage',
                'component_type': 'voltage',
                'metric_name': 'voltage',
                'metric_unit': 'kV',
                'threshold_min': 209.0,
                'threshold_max': 231.0,
                'severity': 'high',
                'enabled': True,
                'description': '220kV bus voltage must be within ±5% of nominal'
            },
            # Transformer Temperature
            {
                'component_id': 'TX1_TEMP',
                'component_name': 'Transformer TX1 Temperature',
                'component_type': 'temperature',
                'metric_name': 'temperature',
                'metric_unit': '°C',
                'threshold_min': None,
                'threshold_max': 85.0,
                'severity': 'medium',
                'enabled': True,
                'description': 'Transformer oil temperature warning threshold'
            },
            # Transformer Oil Level
            {
                'component_id': 'TX1_OIL_LEVEL',
                'component_name': 'Transformer TX1 Oil Level',
                'component_type': 'level',
                'metric_name': 'oil_level',
                'metric_unit': '%',
                'threshold_min': 85.0,
                'threshold_max': None,
                'severity': 'medium',
                'enabled': True,
                'description': 'Transformer oil level must remain above 85%'
            },
            # Power Flow
            {
                'component_id': '400kV_POWER_MW',
                'component_name': '400kV Power Flow',
                'component_type': 'power',
                'metric_name': 'power',
                'metric_unit': 'MW',
                'threshold_min': None,
                'threshold_max': 200.0,
                'severity': 'medium',
                'enabled': True,
                'description': 'Maximum power flow limit for 400kV line'
            },
            # Current
            {
                'component_id': '400kV_CURRENT_A',
                'component_name': '400kV Current',
                'component_type': 'current',
                'metric_name': 'current',
                'metric_unit': 'A',
                'threshold_min': None,
                'threshold_max': 300.0,
                'severity': 'medium',
                'enabled': True,
                'description': 'Maximum current limit for 400kV line'
            },
            # Load
            {
                'component_id': 'LOAD_INDUSTRIAL_MW',
                'component_name': 'Industrial Load',
                'component_type': 'load',
                'metric_name': 'load',
                'metric_unit': 'MW',
                'threshold_min': None,
                'threshold_max': 25.0,
                'severity': 'low',
                'enabled': True,
                'description': 'Industrial load monitoring threshold'
            }
        ]

        created_count = 0
        for threshold_data in default_thresholds:
            try:
                result = _db.upsert_threshold(threshold_data)
                if result:
                    created_count += 1
                    logger.info(f"Created threshold {threshold_data['component_id']}/{threshold_data['metric_name']}: ID={result}")
                else:
                    logger.error(f"Failed to create threshold {threshold_data['component_id']}/{threshold_data['metric_name']}: No ID returned")
            except Exception as e:
                logger.error(f"Failed to create default threshold for {threshold_data['component_id']}: {e}", exc_info=True)

        return {
            'success': True,
            'message': f'Initialized {created_count} default thresholds',
            'created_count': created_count
        }

    except Exception as e:
        logger.error(f"Error initializing default thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))
