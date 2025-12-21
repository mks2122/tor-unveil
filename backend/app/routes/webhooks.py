"""
Clerk Webhook Handler
Receives and processes Clerk webhook events
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session
import logging
import json
import hmac
import hashlib
import os

from app.database import get_db
from app.services.clerk_service import ClerkService

logger = logging.getLogger(__name__)

router = APIRouter()

CLERK_WEBHOOK_SECRET = os.getenv('CLERK_WEBHOOK_SECRET', '')


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify Clerk webhook signature using HMAC-SHA256
    """
    if not CLERK_WEBHOOK_SECRET:
        logger.warning("CLERK_WEBHOOK_SECRET not set - skipping signature verification")
        return True  # In development, skip verification
    
    expected_signature = hmac.new(
        CLERK_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@router.post("/clerk")
async def handle_clerk_webhook(
    request: Request,
    svix_id: str = Header(None, alias="svix-id"),
    svix_timestamp: str = Header(None, alias="svix-timestamp"),
    svix_signature: str = Header(None, alias="svix-signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Clerk webhook events
    
    Events handled:
    - user.created: Create user in database
    - user.updated: Update user in database  
    - user.deleted: Deactivate user in database
    - session.created: Track session
    - session.ended: End session
    """
    try:
        # Get raw body
        body = await request.body()
        
        # Verify signature (if configured)
        if svix_signature and not verify_webhook_signature(body, svix_signature):
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse webhook payload
        payload = json.loads(body.decode('utf-8'))
        event_type = payload.get('type')
        
        logger.info(f"Received Clerk webhook: {event_type}")
        
        clerk_service = ClerkService(db)
        
        # Handle different event types
        if event_type == 'user.created':
            user = clerk_service.handle_user_created(payload)
            return {
                "message": "User created successfully",
                "user": user.to_dict()
            }
        
        elif event_type == 'user.updated':
            user = clerk_service.handle_user_updated(payload)
            return {
                "message": "User updated successfully",
                "user": user.to_dict()
            }
        
        elif event_type == 'user.deleted':
            success = clerk_service.handle_user_deleted(payload)
            return {
                "message": "User deleted successfully" if success else "User not found",
                "success": success
            }
        
        elif event_type == 'session.created':
            data = payload.get('data', {})
            clerk_id = data.get('user_id')
            session_id = data.get('id')
            
            user = clerk_service.get_user_by_clerk_id(clerk_id)
            if user:
                session = clerk_service.create_session_tracking(
                    user=user,
                    clerk_session_id=session_id
                )
                return {
                    "message": "Session tracked successfully",
                    "session_id": session.id
                }
            return {"message": "User not found", "success": False}
        
        elif event_type == 'session.ended':
            data = payload.get('data', {})
            session_id = data.get('id')
            success = clerk_service.end_session(session_id)
            return {
                "message": "Session ended successfully" if success else "Session not found",
                "success": success
            }
        
        else:
            logger.warning(f"Unhandled webhook event type: {event_type}")
            return {"message": f"Event type {event_type} not handled"}
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
