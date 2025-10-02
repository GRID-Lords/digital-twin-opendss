"""
Asset management endpoints for the Digital Twin API
Provides proper integration with SubstationAssetManager
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["assets"])

# Global reference to asset manager (will be set by main app)
_asset_manager = None

def set_asset_manager(manager):
    """Set the asset manager instance from the main app"""
    global _asset_manager
    _asset_manager = manager

def get_asset_manager():
    """Dependency to get asset manager"""
    if _asset_manager is None:
        raise HTTPException(status_code=503, detail="Asset manager not initialized")
    return _asset_manager

class AssetUpdate(BaseModel):
    """Model for asset updates"""
    asset_id: str
    real_time_data: Dict[str, Any]

class AssetControl(BaseModel):
    """Model for asset control commands"""
    asset_id: str
    command: str
    value: Any

@router.get("/assets")
async def get_all_assets(asset_manager = Depends(get_asset_manager)):
    """Get all substation assets with their current status"""

    try:
        # Get all assets as dictionaries
        assets = []
        for asset in asset_manager.assets.values():
            asset_dict = asset.to_dict()
            # Format for frontend compatibility
            formatted_asset = {
                "id": asset_dict["asset_id"],
                "name": asset_dict["name"],
                "type": asset_dict["type"],
                "status": asset_dict["status"],
                "health": asset_dict["health_score"],
                "parameters": {
                    "voltage": f"{asset_dict['voltage_level_kv']} kV",
                    "location": asset_dict["location"],
                    "temperature": f"{asset_dict['thermal']['temperature']:.1f}°C",
                    "reliability": f"{asset_dict['reliability']:.1f}%",
                    **asset_dict.get("real_time_data", {})
                }
            }

            # Add type-specific parameters
            if asset.__class__.__name__ == "PowerTransformer":
                formatted_asset["parameters"]["rating"] = f"{asset.power_rating_mva} MVA"
                formatted_asset["parameters"]["voltage_ratio"] = asset.voltage_ratio
                formatted_asset["parameters"]["oil_level"] = f"{asset.oil_level_percent}%"
                formatted_asset["parameters"]["tap_position"] = str(asset.current_tap)

                # Add DGA analysis
                dga_analysis = asset.analyze_dga()
                formatted_asset["parameters"]["dga_condition"] = dga_analysis["condition"]
                formatted_asset["parameters"]["dga_severity"] = dga_analysis["severity"]

            elif asset.__class__.__name__ == "CircuitBreaker":
                formatted_asset["parameters"]["position"] = asset.position
                formatted_asset["parameters"]["breaking_capacity"] = f"{asset.breaking_capacity_ka} kA"
                formatted_asset["parameters"]["sf6_pressure"] = f"{asset.sf6_pressure_bar:.1f} bar"
                formatted_asset["parameters"]["operations"] = str(asset.total_operations)

                # Add remaining life calculation
                life_data = asset.calculate_remaining_life()
                formatted_asset["parameters"]["remaining_life"] = f"{life_data['overall_life_percent']:.1f}%"

            elif asset.__class__.__name__ == "CurrentTransformer":
                formatted_asset["parameters"]["ratio"] = asset.ct_ratio
                formatted_asset["parameters"]["accuracy_class"] = asset.accuracy_class
                formatted_asset["parameters"]["burden"] = f"{asset.burden_va} VA"

            elif asset.__class__.__name__ == "CapacitorVoltageTransformer":
                formatted_asset["parameters"]["ratio"] = asset.voltage_ratio
                formatted_asset["parameters"]["accuracy_class"] = asset.accuracy_class
                formatted_asset["parameters"]["capacitance"] = f"{asset.c1_capacitance_pf} pF"

            elif asset.__class__.__name__ == "Isolator":
                formatted_asset["parameters"]["position"] = asset.position
                formatted_asset["parameters"]["earth_switch"] = asset.earth_switch_position
                formatted_asset["parameters"]["type"] = asset.isolator_type

            elif asset.__class__.__name__ == "ProtectionRelay":
                formatted_asset["parameters"]["protection_type"] = asset.protection_type.value
                formatted_asset["parameters"]["in_service"] = asset.in_service
                formatted_asset["parameters"]["operation_count"] = asset.operation_counter
                formatted_asset["parameters"]["communication"] = asset.communication_protocol

            # Add alarms if any
            if asset.alarms:
                formatted_asset["alarms"] = asset.alarms[-3:]  # Last 3 alarms

            assets.append(formatted_asset)

        # Include system status
        system_status = asset_manager.get_system_status()

        return {
            "assets": assets,
            "system_status": system_status,
            "total_assets": len(assets)
        }

    except Exception as e:
        logger.error(f"Error fetching assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assets/{asset_id}")
async def get_asset_by_id(asset_id: str, asset_manager = Depends(get_asset_manager)):
    """Get specific asset details"""

    asset = asset_manager.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

    return asset.to_dict()

@router.post("/assets/update")
async def update_asset_data(update: AssetUpdate, asset_manager = Depends(get_asset_manager)):
    """Update asset real-time data"""

    asset = asset_manager.get_asset(update.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {update.asset_id} not found")

    try:
        asset.update_real_time_data(update.real_time_data)
        return {"status": "success", "message": f"Asset {update.asset_id} updated"}
    except Exception as e:
        logger.error(f"Error updating asset {update.asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assets/control")
async def control_asset(control: AssetControl, asset_manager = Depends(get_asset_manager)):
    """Send control command to an asset"""

    asset = asset_manager.get_asset(control.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {control.asset_id} not found")

    try:
        # Handle specific asset control commands
        if asset.__class__.__name__ == "CircuitBreaker":
            if control.command in ["open", "close"]:
                success, message = asset.operate(control.command)
                return {"status": "success" if success else "failed", "message": message}

        elif asset.__class__.__name__ == "PowerTransformer":
            if control.command == "change_tap":
                success = asset.change_tap(control.value)
                return {
                    "status": "success" if success else "failed",
                    "message": f"Tap changed to {asset.current_tap}" if success else "Tap change failed"
                }

        elif asset.__class__.__name__ == "Isolator":
            if control.command in ["open", "close"]:
                success, message = asset.operate(control.command)
                return {"status": "success" if success else "failed", "message": message}

        return {"status": "failed", "message": "Command not supported for this asset type"}

    except Exception as e:
        logger.error(f"Error controlling asset {control.asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assets/critical")
async def get_critical_assets(health_threshold: float = 70.0, asset_manager = Depends(get_asset_manager)):
    """Get assets with health below threshold"""

    critical = asset_manager.get_critical_assets(health_threshold)
    return {
        "critical_assets": [asset.to_dict() for asset in critical],
        "count": len(critical),
        "threshold": health_threshold
    }

@router.get("/assets/by-type/{asset_type}")
async def get_assets_by_type(asset_type: str, asset_manager = Depends(get_asset_manager)):
    """Get all assets of a specific type"""
    import src.backend_server as backend
    asset_manager = backend.asset_manager
    from src.models.asset_models import AssetType

    if not asset_manager:
        raise HTTPException(status_code=503, detail="Asset manager not initialized")

    try:
        # Convert string to AssetType enum
        asset_enum = AssetType(asset_type.lower())
        assets = asset_manager.get_assets_by_type(asset_enum)
        return {
            "asset_type": asset_type,
            "assets": [asset.to_dict() for asset in assets],
            "count": len(assets)
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid asset type: {asset_type}")

@router.get("/assets/by-location/{location}")
async def get_assets_by_location(location: str, asset_manager = Depends(get_asset_manager)):
    """Get all assets at a specific location"""

    assets = asset_manager.get_assets_by_location(location)
    return {
        "location": location,
        "assets": [asset.to_dict() for asset in assets],
        "count": len(assets)
    }