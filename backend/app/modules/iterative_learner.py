"""
Iterative Learning Module for TOR-Unveil
Combines weighted averaging of historical data with ML models for improved accuracy over time
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import joblib
import os

from app.models.analysis_history import AnalysisHistory, MLTrainingData

# ML Models (lazy loaded)
_ml_models = None
MODEL_PATH = "/app/models/"

def get_ml_models():
    """Lazy load ML models"""
    global _ml_models
    if _ml_models is None:
        try:
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
            from sklearn.preprocessing import StandardScaler
            
            # Try to load existing models
            if os.path.exists(f"{MODEL_PATH}rf_model.pkl"):
                rf_model = joblib.load(f"{MODEL_PATH}rf_model.pkl")
                gb_model = joblib.load(f"{MODEL_PATH}gb_model.pkl")
                scaler = joblib.load(f"{MODEL_PATH}scaler.pkl")
            else:
                # Initialize new models
                rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
                gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
                scaler = StandardScaler()
                
            _ml_models = {
                'random_forest': rf_model,
                'gradient_boost': gb_model,
                'scaler': scaler
            }
        except Exception as e:
            print(f"Warning: Could not load ML models: {e}")
            _ml_models = {}
    
    return _ml_models

class IterativeLearner:
    """
    Implements iterative learning that improves with each analysis
    Uses both weighted averaging and ML models
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.models = get_ml_models()
    
    def weighted_historical_adjustment(
        self, 
        entry_node: str, 
        exit_node: str, 
        current_confidence: float
    ) -> float:
        """
        Adjust confidence score based on historical performance
        Uses time-weighted averaging with exponential decay
        
        Args:
            entry_node: Entry node fingerprint
            exit_node: Exit node fingerprint
            current_confidence: Current analysis confidence score
            
        Returns:
            Adjusted confidence score (0-1)
        """
        # Get historical data for this node pair
        history = self.db.query(AnalysisHistory).filter(
            AnalysisHistory.entry_node_fingerprint == entry_node,
            AnalysisHistory.exit_node_fingerprint == exit_node
        ).order_by(desc(AnalysisHistory.analysis_timestamp)).limit(10).all()
        
        if not history:
            return current_confidence
        
        # Calculate time-weighted average
        now = datetime.utcnow()
        weighted_scores = []
        total_weight = 0.0
        
        for record in history:
            # Calculate time decay (more recent = higher weight)
            time_diff = now - record.analysis_timestamp
            days_ago = time_diff.total_seconds() / (24 * 3600)
            
            # Exponential decay: weight = e^(-days/30)
            weight = np.exp(-days_ago / 30.0)
            
            # Use feedback score if available, otherwise use confidence
            score = record.feedback_score if record.feedback_score is not None else record.confidence_score
            
            weighted_scores.append(score * weight)
            total_weight += weight
        
        historical_avg = sum(weighted_scores) / total_weight if total_weight > 0 else current_confidence
        
        # Blend current and historical (40% current, 30% historical, 30% reserved for ML)
        adjusted_confidence = 0.4 * current_confidence + 0.3 * historical_avg
        
        return min(1.0, max(0.0, adjusted_confidence))
    
    def ml_predict_confidence(
        self,
        feature_vector: Dict,
        entry_node: str,
        exit_node: str
    ) -> Optional[float]:
        """
        Use ML models to predict confidence adjustment
        
        Args:
            feature_vector: Features extracted from correlation analysis
            entry_node: Entry node fingerprint
            exit_node: Exit node fingerprint
            
        Returns:
            ML-predicted confidence boost (0-1) or None if models not ready
        """
        if not self.models or len(self.models) == 0:
            return None
        
        try:
            # Check if we have enough training data
            training_count = self.db.query(func.count(MLTrainingData.id)).scalar()
            if training_count < 10:
                return None
            
            # Prepare feature array
            features = [
                feature_vector.get('dtw_score', 0.0),
                feature_vector.get('vector_score', 0.0),
                feature_vector.get('euclidean_score', 0.0),
                feature_vector.get('temporal_score', 0.0),
                feature_vector.get('combined_score', 0.0)
            ]
            
            X = np.array([features])
            X_scaled = self.models['scaler'].transform(X)
            
            # Ensemble prediction: average of RF and GB
            rf_pred = self.models['random_forest'].predict_proba(X_scaled)[0][1]
            gb_pred = self.models['gradient_boost'].predict_proba(X_scaled)[0][1]
            
            ml_confidence = (rf_pred + gb_pred) / 2.0
            
            return ml_confidence
            
        except Exception as e:
            print(f"ML prediction error: {e}")
            return None
    
    def hybrid_confidence_score(
        self,
        entry_node: str,
        exit_node: str,
        current_confidence: float,
        feature_vector: Dict
    ) -> float:
        """
        Combine weighted averaging and ML for final confidence score
        
        Args:
            entry_node: Entry node fingerprint
            exit_node: Exit node fingerprint
            current_confidence: Current confidence from correlation analysis
            feature_vector: Features for ML prediction
            
        Returns:
            Final adjusted confidence score (0-1)
        """
        # Get weighted historical adjustment
        weighted_conf = self.weighted_historical_adjustment(entry_node, exit_node, current_confidence)
        
        # Get ML prediction
        ml_conf = self.ml_predict_confidence(feature_vector, entry_node, exit_node)
        
        if ml_conf is not None:
            # Hybrid: 40% current, 30% historical, 30% ML
            final_confidence = weighted_conf + (0.3 * ml_conf)
        else:
            # No ML available: 40% current + 30% historical from weighted_conf
            # Add remaining 30% as current
            final_confidence = weighted_conf + (0.3 * current_confidence)
        
        return min(1.0, max(0.0, final_confidence))
    
    def record_analysis(
        self,
        analysis_id: int,
        entry_node: str,
        exit_node: str,
        confidence_score: float,
        feature_vector: Dict
    ):
        """
        Record analysis for future learning
        
        Args:
            analysis_id: Analysis ID
            entry_node: Entry node fingerprint
            exit_node: Exit node fingerprint
            confidence_score: Final confidence score
            feature_vector: Features used in analysis
        """
        # Save to analysis history
        history_record = AnalysisHistory(
            analysis_id=analysis_id,
            entry_node_fingerprint=entry_node,
            exit_node_fingerprint=exit_node,
            confidence_score=confidence_score,
            analysis_timestamp=datetime.utcnow()
        )
        self.db.add(history_record)
        
        # Save training data for ML
        training_record = MLTrainingData(
            feature_vector=feature_vector,
            entry_node_fingerprint=entry_node,
            exit_node_fingerprint=exit_node,
            confidence_score=confidence_score
        )
        self.db.add(training_record)
        
        self.db.commit()
    
    def train_ml_models(self, min_samples: int = 50):
        """
        Retrain ML models with accumulated data
        Should be called periodically (e.g., after every 50 analyses)
        
        Args:
            min_samples: Minimum number of samples required for training
        """
        if not self.models or len(self.models) == 0:
            return
        
        try:
            # Get training data
            training_data = self.db.query(MLTrainingData).filter(
                MLTrainingData.was_correct.isnot(None)
            ).all()
            
            if len(training_data) < min_samples:
                print(f"Not enough training data: {len(training_data)} < {min_samples}")
                return
            
            # Prepare features and labels
            X = []
            y = []
            
            for record in training_data:
                features = [
                    record.feature_vector.get('dtw_score', 0.0),
                    record.feature_vector.get('vector_score', 0.0),
                    record.feature_vector.get('euclidean_score', 0.0),
                    record.feature_vector.get('temporal_score', 0.0),
                    record.feature_vector.get('combined_score', 0.0)
                ]
                X.append(features)
                y.append(1 if record.was_correct else 0)
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.models['scaler'].fit_transform(X)
            
            # Train models
            self.models['random_forest'].fit(X_scaled, y)
            self.models['gradient_boost'].fit(X_scaled, y)
            
            # Save models
            os.makedirs(MODEL_PATH, exist_ok=True)
            joblib.dump(self.models['random_forest'], f"{MODEL_PATH}rf_model.pkl")
            joblib.dump(self.models['gradient_boost'], f"{MODEL_PATH}gb_model.pkl")
            joblib.dump(self.models['scaler'], f"{MODEL_PATH}scaler.pkl")
            
            print(f"ML models trained successfully with {len(training_data)} samples")
            
        except Exception as e:
            print(f"ML training error: {e}")
    
    def provide_feedback(
        self,
        analysis_id: int,
        was_correct: bool,
        feedback_score: Optional[float] = None
    ):
        """
        Provide feedback on analysis accuracy for learning
        
        Args:
            analysis_id: Analysis ID to provide feedback for
            was_correct: Whether the analysis was correct
            feedback_score: Optional numerical feedback score
        """
        # Update analysis history
        history_records = self.db.query(AnalysisHistory).filter(
            AnalysisHistory.analysis_id == analysis_id
        ).all()
        
        for record in history_records:
            record.was_correct = was_correct
            if feedback_score is not None:
                record.feedback_score = feedback_score
        
        # Update training data
        training_records = self.db.query(MLTrainingData).filter(
            MLTrainingData.entry_node_fingerprint.in_([r.entry_node_fingerprint for r in history_records]),
            MLTrainingData.exit_node_fingerprint.in_([r.exit_node_fingerprint for r in history_records])
        ).all()
        
        for record in training_records:
            record.was_correct = was_correct
        
        self.db.commit()
        
        # Check if we should retrain models
        total_feedback = self.db.query(func.count(MLTrainingData.id)).filter(
            MLTrainingData.was_correct.isnot(None)
        ).scalar()
        
        if total_feedback % 50 == 0:  # Retrain every 50 feedback instances
            self.train_ml_models()
