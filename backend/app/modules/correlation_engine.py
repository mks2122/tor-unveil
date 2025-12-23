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
                      exit_series: np.ndarray,
                      all_distances: list = None) -> float:
        """
        Calculate DTW-based similarity between two time series
        
        Args:
            entry_series: Entry traffic time series
            exit_series: Exit traffic time series
            all_distances: List of all DTW distances for adaptive normalization
        
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
        
        # Adaptive normalization based on data distribution
        # Use median of all distances if available, otherwise use reasonable default
        if all_distances and len(all_distances) > 0:
            median_distance = np.median(all_distances)
            normalization_factor = max(median_distance, 50)  # Minimum 50 to avoid over-sensitivity
        else:
            # Fallback: use max of (distance/2, 50) for single comparison
            normalization_factor = max(distance / 2, 50)
        
        # Normalize to 0-1 similarity score (inverse exponential)
        # Lower distance = higher similarity
        similarity = np.exp(-distance / normalization_factor)
        
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
                           entry_pattern: Dict[str, Any],
                           exit_pattern: Dict[str, Any],
                           max_window_seconds: int = 300) -> float:
        """
        Calculate temporal correlation based on packet timing alignment
        
        Args:
            entry_pattern: Entry traffic pattern with timestamps
            exit_pattern: Exit traffic pattern with timestamps
            max_window_seconds: Maximum time window for correlation (default 5 minutes)
        
        Returns:
            Temporal similarity score (0-1, where 1 is well-aligned)
        """
        entry_timestamps = entry_pattern.get("timestamps", [])
        exit_timestamps = exit_pattern.get("timestamps", [])
        
        if len(entry_timestamps) < 2 or len(exit_timestamps) < 2:
            return 0.5  # Neutral score if insufficient data
        
        # Calculate average packet timing offset
        # Use first few packets to estimate timing shift
        num_samples = min(10, len(entry_timestamps), len(exit_timestamps))
        
        # Normalize both to start at 0
        entry_relative = [t - entry_timestamps[0] for t in entry_timestamps[:num_samples]]
        exit_relative = [t - exit_timestamps[0] for t in exit_timestamps[:num_samples]]
        
        # Calculate timing alignment using cross-correlation of inter-packet delays
        entry_delays = np.diff(entry_relative)
        exit_delays = np.diff(exit_relative)
        
        if len(entry_delays) == 0 or len(exit_delays) == 0:
            return 0.5
        
        # Need at least 3 points for meaningful correlation
        min_len = min(len(entry_delays), len(exit_delays))
        if min_len < 3:
            return 0.5
        
        # Check if delays have variance (avoid divide by zero)
        entry_std = np.std(entry_delays[:min_len])
        exit_std = np.std(exit_delays[:min_len])
        
        if entry_std < 1e-10 or exit_std < 1e-10:
            # No variance - delays are constant, check if they're similar
            entry_mean = np.mean(entry_delays[:min_len])
            exit_mean = np.mean(exit_delays[:min_len])
            diff_ratio = abs(entry_mean - exit_mean) / max(entry_mean, exit_mean, 0.01)
            return 1.0 - min(diff_ratio, 1.0)
        
        # Safe correlation calculation
        try:
            correlation = np.corrcoef(entry_delays[:min_len], exit_delays[:min_len])[0, 1]
            
            # Handle NaN (can occur if std dev is 0)
            if np.isnan(correlation) or np.isinf(correlation):
                return 0.5
            
            # Convert correlation to 0-1 similarity score
            similarity = (correlation + 1) / 2  # Map [-1, 1] to [0, 1]
            return float(np.clip(similarity, 0.0, 1.0))
        except:
            return 0.5
    
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
                         exit_timestamp: Optional[datetime] = None,
                         relay_country: Optional[str] = None,
                         expected_location: Optional[str] = None,
                         all_dtw_distances: list = None) -> Tuple[float, Dict[str, float]]:
        """
        Calculate comprehensive correlation score between entry and exit patterns
        
        Args:
            entry_pattern: Entry traffic pattern
            exit_pattern: Exit traffic pattern
            entry_features: Extracted entry features
            exit_features: Extracted exit features
            weights: Weights for different similarity metrics
            entry_timestamp: Optional entry observation timestamp (deprecated)
            exit_timestamp: Optional exit observation timestamp (deprecated)
            relay_country: Country of the relay being evaluated
            expected_location: Expected location from traffic generation
            all_dtw_distances: List of all DTW distances for adaptive normalization
        
        Returns:
            Tuple of (overall_score, detailed_scores)
        """
        if weights is None:
            weights = {
                "dtw": 0.25,        # DTW time-series similarity (reduced from 0.30)
                "vector": 0.20,     # Feature vector similarity
                "euclidean": 0.15,  # Euclidean distance
                "temporal": 0.15,   # Temporal correlation (reduced from 0.20)
                "location": 0.25    # Location matching bonus (increased from 0.15)
            }
        
        # Extract time series for DTW
        entry_series = np.array(entry_features.get("inter_packet_delays", []))
        exit_series = np.array(exit_features.get("inter_packet_delays", []))
        
        # Extract feature vectors
        entry_vector = np.array(entry_features.get("feature_vector", []))
        exit_vector = np.array(exit_features.get("feature_vector", []))
        
        # Calculate individual similarities
        dtw_score = self.dtw_similarity(entry_series, exit_series, all_dtw_distances)
        vector_score = self.vector_similarity(entry_vector, exit_vector)
        euclidean_score = self.euclidean_similarity(entry_vector, exit_vector)
        temporal_score = self.temporal_correlation(entry_pattern, exit_pattern)
        
        # Calculate location matching score
        location_score = self._location_matching_score(
            entry_pattern.get("location"),
            relay_country,
            expected_location
        )
        
        detailed_scores = {
            "dtw_similarity": dtw_score,
            "vector_similarity": vector_score,
            "euclidean_similarity": euclidean_score,
            "temporal_similarity": temporal_score,
            "location_match": location_score
        }
        
        # Calculate weighted overall score
        overall_score = (
            weights["dtw"] * dtw_score +
            weights["vector"] * vector_score +
            weights["euclidean"] * euclidean_score +
            weights["temporal"] * temporal_score +
            weights["location"] * location_score
        )
        
        logger.debug(f"Correlation scores - DTW: {dtw_score:.3f}, Vector: {vector_score:.3f}, "
                    f"Euclidean: {euclidean_score:.3f}, Temporal: {temporal_score:.3f}, "
                    f"Location: {location_score:.3f}, Overall: {overall_score:.3f}")
        
        return overall_score, detailed_scores
    
    def _location_matching_score(self,
                                 pattern_location: Optional[str],
                                 relay_country: Optional[str],
                                 expected_location: Optional[str]) -> float:
        """
        Calculate location matching score
        
        Args:
            pattern_location: Location from generated traffic pattern
            relay_country: Country of the relay being evaluated
            expected_location: Expected location from analysis request
        
        Returns:
            Location match score (0-1, where 1 is perfect match)
        """
        # If no location info, return neutral score
        if not expected_location or not relay_country:
            return 0.5
        
        # Normalize for case-insensitive comparison
        expected_normalized = expected_location.strip().lower()
        relay_normalized = relay_country.strip().lower()
        
        # Check if relay country matches expected location
        if relay_normalized == expected_normalized:
            return 1.0
        
        # Check if pattern location matches relay (should be the same as expected if generated correctly)
        if pattern_location:
            pattern_normalized = pattern_location.strip().lower()
            if pattern_normalized == relay_normalized:
                return 1.0
        
        # No match - return low score
        return 0.1
    
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
