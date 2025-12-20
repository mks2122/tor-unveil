from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class TrafficPattern(Base):
    __tablename__ = "traffic_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(String, unique=True, index=True)
    
    # Pattern type
    pattern_type = Column(String)  # 'entry' or 'exit'
    
    # Raw data
    timestamps = Column(JSON)  # List of timestamp values
    packet_sizes = Column(JSON)  # List of packet sizes
    source_location = Column(JSON)  # Synthetic metadata about where traffic originated
    
    # Extracted features
    feature_vector = Column(JSON)  # Computed feature vector
    
    # Traffic characteristics
    burst_count = Column(Integer)
    avg_burst_duration = Column(Float)
    avg_inter_packet_delay = Column(Float)
    total_packets = Column(Integer)
    total_bytes = Column(Integer)
    
    # Configuration
    random_seed = Column(Integer)
    generation_params = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<TrafficPattern {self.pattern_id} ({self.pattern_type})>"
