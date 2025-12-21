"""
Auth Routes
Simple endpoints for getting current user info
(Login/register is handled by Clerk frontend)
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.models.user import User
from app.dependencies.auth import get_current_user, require_police, require_admin

router = APIRouter()


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get current authenticated user information
    
    Requires: Valid Clerk JWT token
    Returns: User object with role information
    """
    return {
        "user": current_user.to_dict(),
        "permissions": {
            "is_police": current_user.user_type.value == "police",
            "is_admin": current_user.user_type.value == "admin",
            "is_public": current_user.user_type.value == "public"
        }
    }


@router.get("/police-check")
async def police_check(current_user: User = Depends(require_police)) -> Dict[str, str]:
    """
    Test endpoint requiring police or admin access
    """
    return {
        "message": f"Hello {current_user.name}! You have police/admin access.",
        "role": current_user.user_type.value
    }


@router.get("/admin-check")
async def admin_check(current_user: User = Depends(require_admin)) -> Dict[str, str]:
    """
    Test endpoint requiring admin access only
    """
    return {
        "message": f"Hello {current_user.name}! You have admin access.",
        "role": current_user.user_type.value
    }
