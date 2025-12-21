"""
Authentication Dependencies for FastAPI
Uses Clerk SDK to verify JWT tokens
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
import logging

from app.database import get_db
from app.models.user import User, UserType
from app.services.clerk_service import ClerkService

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Clerk configuration
CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY', '')
CLERK_PUBLISHABLE_KEY = os.getenv('CLERK_PUBLISHABLE_KEY', '')


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Verify Clerk JWT token and return current user
    
    This dependency:
    1. Extracts Bearer token from Authorization header
    2. Verifies token with Clerk SDK
    3. Gets user data from JWT claims
    4. Looks up user in local database by clerk_id
    5. Returns User object
    """
    try:
        token = credentials.credentials
        
        # Import Clerk SDK
        from clerk_backend_api import Clerk
        
        # Initialize Clerk client
        clerk_client = Clerk(bearer_auth=CLERK_SECRET_KEY)
        
        # Verify JWT token
        # This validates the signature and expiration
        try:
            # Decode and verify the JWT
            verified_token = clerk_client.jwt_templates.verify_token(
                token,
                authorized_parties=[CLERK_PUBLISHABLE_KEY.split('_')[1]] if CLERK_PUBLISHABLE_KEY else None
            )
            
            # Extract claims from verified token
            user_id = verified_token.get('user_id') or verified_token.get('sub')
            email = verified_token.get('email')
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user_id"
                )
            
        except Exception as verify_error:
            logger.error(f"Token verification failed: {str(verify_error)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(verify_error)}"
            )
        
        # Look up user in local database
        clerk_service = ClerkService(db)
        user = clerk_service.get_user_by_clerk_id(user_id)
        
        if not user:
            # User exists in Clerk but not in our DB
            # This means webhook hasn't fired yet or failed
            logger.warning(f"User {user_id} from Clerk not found in DB, will sync now")
            
            # Try to get user details from Clerk and sync
            try:
                clerk_user = clerk_client.users.get(user_id)
                
                # Extract user data
                first_name = clerk_user.first_name or ''
                last_name = clerk_user.last_name or ''
                email_addresses = clerk_user.email_addresses or []
                primary_email = next(
                    (e.email_address for e in email_addresses if e.id == clerk_user.primary_email_address_id),
                    email if email else None
                )
                
                if not primary_email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No email address found for user"
                    )
                
                # Sync user to database
                user = clerk_service.sync_user_from_clerk(
                    clerk_user_id=user_id,
                    email=primary_email,
                    first_name=first_name,
                    last_name=last_name
                )
                
            except Exception as sync_error:
                logger.error(f"Failed to sync user: {str(sync_error)}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found. Please contact support."
                )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        # Update last login
        clerk_service.update_last_login(user)
        
        return user
        
    except ImportError:
        logger.error("Clerk SDK not installed. Run: pip install clerk-backend-sdk")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not configured"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure user is active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def require_police(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require user to be police or admin
    """
    if current_user.user_type not in [UserType.POLICE, UserType.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Police or admin access required"
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require user to be admin
    """
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
