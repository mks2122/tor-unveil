import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean, cosine
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CorrelationEngine:
    """Measures similarity between entry and exit traffic patterns using DTW"""
    
    def __init__(self):
        logger.info("CorrelationEngine initialized")
    
    def dtw_similarity(self, 
                      entry_series: np.ndarray, 
                      exit_series: np.ndarray) -> float:
        """
        Calculate DTW-based similarity between two time series
        
        Args:
            entry_series: Entry traffic time series
            exit_series: Exit traffic time series
        
        Returns:
            Normalized similarity score (0-1, where 1 is most similar)
        """
        if len(entry_series) == 0 or len(exit_series) == 0:
            return 0.0
        
        # Reshape for fastdtw
        entry_2d = entry_series.reshape(-1, 1)
        exit_2d = exit_series.reshape(-1, 1)
        
        # Calculate DTW distance
        distance, _ = fastdtw(entry_2d, exit_2d, dist=euclidean)
        
        # Normalize to 0-1 similarity score (inverse exponential)
        # Lower distance = higher similarity
        similarity = np.exp(-distance / 100)
        
        return float(similarity)
    
    def vector_similarity(self, 
                         entry_features: np.ndarray,
                         exit_features: np.ndarray) -> float:
        """
        Calculate cosine similarity between feature vectors
        
        Args:
            entry_features: Entry traffic feature vector
            exit_features: Exit traffic feature vector
        
        Returns:
            Cosine similarity score (0-1)
        """
        if len(entry_features) == 0 or len(exit_features) == 0:
            return 0.0
        
        # Cosine similarity (1 - cosine distance)
        similarity = 1 - cosine(entry_features, exit_features)
        
        # Ensure in 0-1 range
        similarity = max(0.0, min(1.0, similarity))
        
        return float(similarity)
    
    def euclidean_similarity(self,
                           entry_features: np.ndarray,
                           exit_features: np.ndarray) -> float:
        """
        Calculate Euclidean distance-based similarity
        
        Args:
            entry_features: Entry traffic feature vector
            exit_features: Exit traffic feature vector
        
        Returns:
            Similarity score (0-1)
        """
        if len(entry_features) == 0 or len(exit_features) == 0:
            return 0.0
        
        distance = euclidean(entry_features, exit_features)
        
        # Normalize to similarity (inverse exponential)
        similarity = np.exp(-distance)
        
        return float(similarity)
    
    def temporal_correlation(self,
                           entry_timestamp: Optional[datetime],
                           exit_timestamp: Optional[datetime],
                           max_window_seconds: int = 300) -> float:
        """
        Calculate temporal correlation based on timestamp proximity
        
        Args:
            entry_timestamp: Entry node observation timestamp
            exit_timestamp: Exit node observation timestamp
            max_window_seconds: Maximum time window for correlation (default 5 minutes)
        
        Returns:
            Temporal similarity score (0-1, where 1 is simultaneous)
        """
        if entry_timestamp is None or exit_timestamp is None:
            return 0.5  # Neutral score if timestamps unavailable
        
        time_delta = abs((exit_timestamp - entry_timestamp).total_seconds())
        
        if time_delta < 10:
            # Very close in time
            return 1.0
        elif time_delta < max_window_seconds:
            # Within window - exponential decay
            return np.exp(-time_delta / max_window_seconds)
        else:
            # Outside window
            return 0.1
    
    def calculate_time_delta(self,
                           entry_timestamp: Optional[datetime],
                           exit_timestamp: Optional[datetime]) -> Optional[int]:
        """
        Calculate time delta between entry and exit observations
        
        Args:
            entry_timestamp: Entry node observation timestamp
            exit_timestamp: Exit node observation timestamp
        
        Returns:
            Time delta in seconds, or None if timestamps unavailable
        """
        if entry_timestamp is None or exit_timestamp is None:
            return None
        
        return int(abs((exit_timestamp - entry_timestamp).total_seconds()))
    
    
    def correlation_score(self,
                         entry_pattern: Dict[str, Any],
                         exit_pattern: Dict[str, Any],
                         entry_features: Dict[str, Any],
                         exit_features: Dict[str, Any],
                         weights: Dict[str, float] = None,
                         entry_timestamp: Optional[datetime] = None,
                         exit_timestamp: Optional[datetime] = None) -> Tuple[float, Dict[str, float]]:
        """
        Calculate comprehensive correlation score between entry and exit patterns
        
        Args:
            entry_pattern: Entry traffic pattern
            exit_pattern: Exit traffic pattern
            entry_features: Extracted entry features
            exit_features: Extracted exit features
            weights: Weights for different similarity metrics
            entry_timestamp: Optional entry observation timestamp
            exit_timestamp: Optional exit observation timestamp
        
        Returns:
            Tuple of (overall_score, detailed_scores)
        """
        if weights is None:
            weights = {
                "dtw": 0.35,        # DTW time-series similarity
                "vector": 0.25,     # Feature vector similarity
                "euclidean": 0.15,  # Euclidean distance
                "temporal": 0.25    # Temporal correlation
            }
        
        # Extract time series for DTW
        entry_series = np.array(entry_features.get("inter_packet_delays", []))
        exit_series = np.array(exit_features.get("inter_packet_delays", []))
        
        # Extract feature vectors
        entry_vector = np.array(entry_features.get("feature_vector", []))
        exit_vector = np.array(exit_features.get("feature_vector", []))
        
        # Calculate individual similarities
        dtw_score = self.dtw_similarity(entry_series, exit_series)
        vector_score = self.vector_similarity(entry_vector, exit_vector)
        euclidean_score = self.euclidean_similarity(entry_vector, exit_vector)
        temporal_score = self.temporal_correlation(entry_timestamp, exit_timestamp)
        
        detailed_scores = {
            "dtw_similarity": dtw_score,
            "vector_similarity": vector_score,
            "euclidean_similarity": euclidean_score,
            "temporal_similarity": temporal_score
        }
        
        # Calculate weighted overall score
        overall_score = (
            weights["dtw"] * dtw_score +
            weights["vector"] * vector_score +
            weights["euclidean"] * euclidean_score +
            weights["temporal"] * temporal_score
        )
        
        logger.debug(f"Correlation scores - DTW: {dtw_score:.3f}, Vector: {vector_score:.3f}, "
                    f"Euclidean: {euclidean_score:.3f}, Temporal: {temporal_score:.3f}, Overall: {overall_score:.3f}")
        
        return overall_score, detailed_scores
    
    def batch_correlate(self,
                       entry_pattern: Dict[str, Any],
                       exit_patterns: list[Dict[str, Any]],
                       entry_features: Dict[str, Any],
                       exit_features_list: list[Dict[str, Any]]) -> list[Tuple[int, float, Dict[str, float]]]:
        """
        Correlate entry pattern with multiple exit patterns
        
        Args:
            entry_pattern: Entry traffic pattern
            exit_patterns: List of exit traffic patterns
            entry_features: Entry features
            exit_features_list: List of exit features
        
        Returns:
            List of (index, score, detailed_scores) tuples, sorted by score descending
        """
        results = []
        
        for idx, (exit_pattern, exit_features) in enumerate(zip(exit_patterns, exit_features_list)):
            score, detailed = self.correlation_score(
                entry_pattern, exit_pattern,
                entry_features, exit_features
            )
            results.append((idx, score, detailed))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Batch correlation completed for {len(exit_patterns)} patterns")
        return results
