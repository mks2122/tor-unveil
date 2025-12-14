from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, unique=True, index=True)
    
    # Configuration
    top_n = Column(Integer)
    simulation_count = Column(Integer)
    random_seed = Column(Integer)
    
    # Results
    ranked_guards = Column(JSON)  # List of ranked guard nodes with scores
    correlation_scores = Column(JSON)  # Detailed correlation data
    
    # Statistics
    total_guards_analyzed = Column(Integer)
    avg_confidence_score = Column(Float)
    execution_time_seconds = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AnalysisResult {self.analysis_id}>"
