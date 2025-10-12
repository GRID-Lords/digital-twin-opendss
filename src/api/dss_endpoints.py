"""
DSS File Management Endpoints
Handles versioning, validation, and management of OpenDSS circuit files
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.database import db
from src.utils.dss_validator import validate_dss_file_changes

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Global references (set by backend_server)
digital_twin_server = None
load_flow_analyzer = None
dss_file_path = None

def set_dss_dependencies(dt_server, lf_analyzer, dss_path):
    """Set dependencies from backend server"""
    global digital_twin_server, load_flow_analyzer, dss_file_path
    digital_twin_server = dt_server
    load_flow_analyzer = lf_analyzer
    dss_file_path = dss_path
    logger.info("DSS endpoints dependencies configured")

class DSSFileRequest(BaseModel):
    """Request model for DSS file operations"""
    content: str
    description: Optional[str] = ""
    created_by: Optional[str] = "user"

class DSSValidateRequest(BaseModel):
    """Request model for DSS file validation"""
    content: str

@router.get("/api/dss/current")
async def get_current_dss():
    """Get currently active DSS file content"""
    try:
        # Try to get from database first
        active_version = db.get_active_dss_version()
        if active_version:
            return {
                "content": active_version['content'],
                "version_id": active_version['id'],
                "version_number": active_version['version_number'],
                "created_at": active_version['created_at'],
                "description": active_version.get('description', ''),
                "is_active": True
            }

        # Fallback to reading from file
        if dss_file_path and dss_file_path.exists():
            content = dss_file_path.read_text()
            return {
                "content": content,
                "version_id": None,
                "version_number": 0,
                "created_at": None,
                "description": "Original file",
                "is_active": True
            }
        else:
            raise HTTPException(status_code=404, detail="DSS file not found")
    except Exception as e:
        logger.error(f"Error getting current DSS file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/dss/validate")
async def validate_dss(request: DSSValidateRequest):
    """Validate DSS file changes without saving"""
    try:
        # Get current/original content
        active_version = db.get_active_dss_version()
        if active_version:
            original_content = active_version['content']
        elif dss_file_path and dss_file_path.exists():
            original_content = dss_file_path.read_text()
        else:
            raise HTTPException(status_code=404, detail="No original DSS file found")

        # Validate changes
        validation_result = validate_dss_file_changes(original_content, request.content)

        return {
            "valid": validation_result['valid'],
            "errors": validation_result['errors'],
            "warnings": validation_result['warnings'],
            "message": validation_result['message']
        }
    except Exception as e:
        logger.error(f"Error validating DSS file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/dss/save")
async def save_dss_version(request: DSSFileRequest):
    """Save a new version of the DSS file after validation"""
    try:
        # Get current/original content for validation
        active_version = db.get_active_dss_version()
        if active_version:
            original_content = active_version['content']
        elif dss_file_path and dss_file_path.exists():
            original_content = dss_file_path.read_text()
        else:
            raise HTTPException(status_code=404, detail="No original DSS file found")

        # Validate changes
        validation_result = validate_dss_file_changes(original_content, request.content)

        if not validation_result['valid']:
            return {
                "success": False,
                "errors": validation_result['errors'],
                "warnings": validation_result['warnings'],
                "message": "Validation failed. Cannot save invalid DSS file."
            }

        # Save new version to database
        version_id = db.create_dss_version(
            content=request.content,
            created_by=request.created_by,
            description=request.description
        )

        # Reload the DSS file in the simulation
        reload_success = False
        if load_flow_analyzer:
            try:
                # Write content to temporary file and reload
                temp_dss_path = dss_file_path.parent / "temp_circuit.dss"
                temp_dss_path.write_text(request.content)
                load_flow_analyzer.load_circuit(str(temp_dss_path))
                load_flow_analyzer.solve()
                reload_success = True
                logger.info("Reloaded DSS file in simulation")
            except Exception as e:
                logger.warning(f"DSS file saved but failed to reload in simulation: {e}")

        return {
            "success": True,
            "version_id": version_id,
            "warnings": validation_result['warnings'],
            "message": "DSS file saved successfully",
            "reload_status": "success" if reload_success else "failed"
        }
    except Exception as e:
        logger.error(f"Error saving DSS file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/dss/versions")
async def get_dss_versions(limit: int = 50):
    """Get all DSS file versions"""
    try:
        versions = db.get_all_dss_versions(limit=limit)
        return {
            "versions": versions,
            "total": len(versions)
        }
    except Exception as e:
        logger.error(f"Error getting DSS versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/dss/versions/{version_id}")
async def get_dss_version(version_id: int):
    """Get a specific DSS file version by ID"""
    try:
        version = db.get_dss_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail=f"Version {version_id} not found")
        return version
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting DSS version {version_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/dss/activate/{version_id}")
async def activate_dss_version(version_id: int):
    """Activate a specific DSS file version"""
    try:
        # Get the version
        version = db.get_dss_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail=f"Version {version_id} not found")

        # Activate in database
        success = db.activate_dss_version(version_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to activate version")

        # Reload the DSS file in the simulation
        reload_success = False
        if load_flow_analyzer:
            try:
                temp_dss_path = dss_file_path.parent / "active_circuit.dss"
                temp_dss_path.write_text(version['content'])
                load_flow_analyzer.load_circuit(str(temp_dss_path))
                load_flow_analyzer.solve()
                reload_success = True
                logger.info(f"Activated and reloaded DSS version {version['version_number']}")
            except Exception as e:
                logger.warning(f"Version activated but failed to reload: {e}")

        return {
            "success": True,
            "version_id": version_id,
            "version_number": version['version_number'],
            "message": f"Activated version {version['version_number']}",
            "reload_status": "success" if reload_success else "failed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating DSS version {version_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
