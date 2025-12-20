from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.database import Base

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, nullable=False)
    entry_node_fingerprint = Column(String(100), index=True)
    exit_node_fingerprint = Column(String(100), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    analysis_timestamp = Column(DateTime, server_default=func.now(), index=True)
    feedback_score = Column(Float)
    was_correct = Column(Boolean)
    created_at = Column(DateTime, server_default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'entry_node_fingerprint': self.entry_node_fingerprint,
            'exit_node_fingerprint': self.exit_node_fingerprint,
            'confidence_score': self.confidence_score,
            'analysis_timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            'feedback_score': self.feedback_score,
            'was_correct': self.was_correct
        }

class MLTrainingData(Base):
    __tablename__ = "ml_training_data"
    
    id = Column(Integer, primary_key=True, index=True)
    feature_vector = Column(JSON, nullable=False)
    entry_node_fingerprint = Column(String(100), nullable=False, index=True)
    exit_node_fingerprint = Column(String(100), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    was_correct = Column(Boolean)
    created_at = Column(DateTime, server_default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'feature_vector': self.feature_vector,
            'entry_node_fingerprint': self.entry_node_fingerprint,
            'exit_node_fingerprint': self.exit_node_fingerprint,
            'confidence_score': self.confidence_score,
            'was_correct': self.was_correct
        }

class NodeCorrelation(Base):
    __tablename__ = "node_correlations"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, nullable=False, index=True)
    entry_fingerprint = Column(String(100), nullable=False, index=True)
    exit_fingerprint = Column(String(100), nullable=False, index=True)
    correlation_score = Column(Float, nullable=False)
    time_delta_seconds = Column(Integer)
    traffic_pattern_similarity = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'entry_fingerprint': self.entry_fingerprint,
            'exit_fingerprint': self.exit_fingerprint,
            'correlation_score': self.correlation_score,
            'time_delta_seconds': self.time_delta_seconds,
            'traffic_pattern_similarity': self.traffic_pattern_similarity
        }
