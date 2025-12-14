from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.database import Base

class Relay(Base):
    __tablename__ = "relays"
    
    id = Column(Integer, primary_key=True, index=True)
    fingerprint = Column(String, unique=True, index=True, nullable=False)
    nickname = Column(String)
    
    # Relay flags
    is_guard = Column(Boolean, default=False)
    is_exit = Column(Boolean, default=False)
    is_middle = Column(Boolean, default=False)
    
    # Relay type classification
    relay_type = Column(String, index=True)  # 'guard', 'exit', 'middle'
    
    # Metadata
    bandwidth = Column(Float)  # in bytes/s
    uptime = Column(Integer)  # in seconds
    country = Column(String, index=True)
    country_name = Column(String)
    region = Column(String)
    city = Column(String)
    
    # Network info
    or_addresses = Column(JSON)  # List of addresses
    exit_policy = Column(JSON)  # Exit policy rules
    
    # Timing
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    
    # Reliability scores
    consensus_weight = Column(Float)
    guard_probability = Column(Float)
    middle_probability = Column(Float)
    exit_probability = Column(Float)
    
    # Source tracking
    data_source = Column(String)  # 'sample' or 'live'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Relay {self.nickname} ({self.relay_type})>"
