from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    node_fingerprint = Column(String(100))
    event_metadata = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'node_fingerprint': self.node_fingerprint,
            'event_metadata': self.event_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
