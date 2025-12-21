from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class UserType(enum.Enum):
    """User role types"""
    PUBLIC = "public"
    POLICE = "police"
    ADMIN = "admin"

class User(Base):
    """User table - stores core user information"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # User identification (Clerk user ID)
    clerk_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # User role/type (auto-assigned based on email domain)
    user_type = Column(Enum(UserType), nullable=False, default=UserType.PUBLIC, index=True)
    
    # Status flags
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    profile_data = Column(Text, nullable=True)  # JSON stored as text
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email} ({self.user_type.value})>"
    
    @staticmethod
    def determine_user_type_from_email(email: str) -> UserType:
        """
        Determine user type based on email domain
        - stjosephs.ac.in or tn.gov.in → POLICE
        - All others → PUBLIC
        """
        email_lower = email.lower()
        police_domains = ['stjosephs.ac.in', 'tn.gov.in']
        
        for domain in police_domains:
            if email_lower.endswith(f'@{domain}'):
                return UserType.POLICE
        
        return UserType.PUBLIC
    
    def to_dict(self):
        return {
            "id": self.id,
            "clerk_id": self.clerk_id,
            "email": self.email,
            "name": self.name,
            "user_type": self.user_type.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "email_verified": self.email_verified,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }