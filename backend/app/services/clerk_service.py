"""
Clerk Service - Handles Clerk webhook events and user synchronization
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

from app.models.user import User, UserType
from app.models.session import UserSession

logger = logging.getLogger(__name__)


class ClerkService:
    """Service for handling Clerk webhook events and user management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def sync_user_from_clerk(
        self,
        clerk_user_id: str,
        email: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> User:
        """
        Create or update user from Clerk data
        Automatically assigns role based on email domain
        """
        # Check if user already exists
        user = self.db.query(User).filter(User.clerk_id == clerk_user_id).first()
        
        # Determine user type from email domain
        user_type = User.determine_user_type_from_email(email)
        
        full_name = f"{first_name} {last_name}".strip()
        
        if user:
            # Update existing user
            user.email = email
            user.name = full_name
            user.phone = phone
            user.user_type = user_type
            user.updated_at = datetime.now(timezone.utc)
            
            logger.info(f"Updated user: {email} (type: {user_type.value})")
        else:
            # Create new user
            user = User(
                clerk_id=clerk_user_id,
                email=email,
                name=full_name,
                phone=phone,
                user_type=user_type,
                is_active=True,
                is_verified=True,
                email_verified=True
            )
            self.db.add(user)
            
            logger.info(f"Created new user: {email} (type: {user_type.value})")
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def handle_user_created(self, webhook_data: Dict[str, Any]) -> User:
        """Handle user.created webhook event"""
        data = webhook_data.get('data', {})
        
        clerk_id = data.get('id')
        email_addresses = data.get('email_addresses', [])
        primary_email = next(
            (e['email_address'] for e in email_addresses if e.get('id') == data.get('primary_email_address_id')),
            email_addresses[0]['email_address'] if email_addresses else None
        )
        
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        phone_numbers = data.get('phone_numbers', [])
        phone = phone_numbers[0].get('phone_number') if phone_numbers else None
        
        if not primary_email:
            raise ValueError("No email address found in Clerk user data")
        
        return self.sync_user_from_clerk(
            clerk_user_id=clerk_id,
            email=primary_email,
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
    
    def handle_user_updated(self, webhook_data: Dict[str, Any]) -> User:
        """Handle user.updated webhook event"""
        return self.handle_user_created(webhook_data)  # Same logic
    
    def handle_user_deleted(self, webhook_data: Dict[str, Any]) -> bool:
        """Handle user.deleted webhook event"""
        data = webhook_data.get('data', {})
        clerk_id = data.get('id')
        
        user = self.db.query(User).filter(User.clerk_id == clerk_id).first()
        
        if user:
            # Soft delete - deactivate user
            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Deactivated user: {user.email}")
            return True
        
        return False
    
    def create_session_tracking(
        self,
        user: User,
        clerk_session_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """Create session tracking record"""
        session = UserSession(
            user_id=user.id,
            clerk_session_id=clerk_session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            expires_at=None  # Clerk manages expiration
        )
        self.db.add(session)
        self.db.commit()
        
        logger.info(f"Created session for user: {user.email}")
        
        return session
    
    def end_session(self, clerk_session_id: str) -> bool:
        """End session tracking"""
        session = self.db.query(UserSession).filter(
            UserSession.clerk_session_id == clerk_session_id
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()
            logger.info(f"Ended session: {clerk_session_id}")
            return True
        
        return False
    
    def get_user_by_clerk_id(self, clerk_id: str) -> Optional[User]:
        """Get user by Clerk ID"""
        return self.db.query(User).filter(
            User.clerk_id == clerk_id,
            User.is_active == True
        ).first()
    
    def update_last_login(self, user: User) -> None:
        """Update user's last login timestamp"""
        user.last_login = datetime.now(timezone.utc)
        self.db.commit()
