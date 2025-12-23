import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """Extracts comparable features from traffic patterns"""
    
    @staticmethod
    def extract_features(pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract feature vector from traffic pattern
        
        Args:
            pattern: Traffic pattern dictionary with timestamps and packet_sizes
        
        Returns:
            Dictionary of extracted features
        """
        timestamps = pattern.get("timestamps", [])
        packet_sizes = pattern.get("packet_sizes", [])
        
        if not timestamps or len(timestamps) < 2:
            logger.warning("Insufficient data for feature extraction")
            return {
                "inter_packet_delays": [],
                "burst_durations": [],
                "packet_volumes": [],
                "feature_vector": []
            }
        
        # Calculate inter-packet delays
        inter_packet_delays = [
            timestamps[i+1] - timestamps[i] 
            for i in range(len(timestamps) - 1)
        ]
        
        # Adaptive burst threshold based on traffic characteristics
        # Use median delay * 3 as threshold, with bounds [0.2s, 1.0s]
        if inter_packet_delays:
            median_delay = np.median(inter_packet_delays)
            burst_threshold = np.clip(median_delay * 3, 0.2, 1.0)
        else:
            burst_threshold = 0.5  # Unified default threshold
        
        burst_boundaries = [0]
        for i, delay in enumerate(inter_packet_delays):
            if delay > burst_threshold:
                burst_boundaries.append(i + 1)
        burst_boundaries.append(len(timestamps))
        
        # Calculate burst durations and volumes
        burst_durations = []
        packet_volumes = []
        
        for i in range(len(burst_boundaries) - 1):
            start_idx = burst_boundaries[i]
            end_idx = burst_boundaries[i + 1]
            
            if end_idx > start_idx:
                duration = timestamps[end_idx - 1] - timestamps[start_idx]
                burst_durations.append(duration)
                
                volume = sum(packet_sizes[start_idx:end_idx])
                packet_volumes.append(volume)
        
        # Compute statistical features
        features = {
            # Timing features
            "mean_inter_packet_delay": float(np.mean(inter_packet_delays)) if inter_packet_delays else 0.0,
            "std_inter_packet_delay": float(np.std(inter_packet_delays)) if inter_packet_delays else 0.0,
            "median_inter_packet_delay": float(np.median(inter_packet_delays)) if inter_packet_delays else 0.0,
            "jitter_variance": float(np.var(inter_packet_delays)) if inter_packet_delays else 0.0,
            "delay_skewness": float(np.percentile(inter_packet_delays, 75) - np.percentile(inter_packet_delays, 25)) if len(inter_packet_delays) > 4 else 0.0,
            
            # Burst features
            "num_bursts": len(burst_durations),
            "mean_burst_duration": float(np.mean(burst_durations)) if burst_durations else 0.0,
            "std_burst_duration": float(np.std(burst_durations)) if burst_durations else 0.0,
            
            # Volume features
            "total_packets": len(timestamps),
            "total_bytes": sum(packet_sizes),
            "mean_packet_size": float(np.mean(packet_sizes)) if packet_sizes else 0.0,
            "std_packet_size": float(np.std(packet_sizes)) if packet_sizes else 0.0,
            "mean_burst_volume": float(np.mean(packet_volumes)) if packet_volumes else 0.0,
            
            # Pattern features
            "burst_density": len(burst_durations) / len(timestamps) if len(timestamps) > 0 else 0.0,
            
            # Overall timing
            "total_duration": timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0.0,
            "packet_rate": len(timestamps) / (timestamps[-1] - timestamps[0]) if len(timestamps) > 1 and timestamps[-1] != timestamps[0] else 0.0,
        }
        
        # Create normalized feature vector for similarity comparison (expanded from 7 to 12 features)
        feature_vector = [
            features["mean_inter_packet_delay"],
            features["std_inter_packet_delay"],
            features["median_inter_packet_delay"],
            features["jitter_variance"],
            features["delay_skewness"],
            features["mean_burst_duration"],
            features["std_burst_duration"],
            features["mean_packet_size"],
            features["std_packet_size"],
            features["packet_rate"],
            float(features["num_bursts"]),
            features["burst_density"],
        ]
        
        # Store raw arrays for DTW if needed
        features["inter_packet_delays"] = inter_packet_delays
        features["burst_durations"] = burst_durations
        features["packet_volumes"] = packet_volumes
        features["feature_vector"] = feature_vector
        
        logger.debug(f"Extracted features: {len(feature_vector)} dimensions")
        return features
    
    @staticmethod
    def normalize_features(features: Dict[str, Any]) -> np.ndarray:
        """
        Normalize feature vector to 0-1 range
        
        Args:
            features: Feature dictionary from extract_features
        
        Returns:
            Normalized feature vector as numpy array
        """
        feature_vector = np.array(features.get("feature_vector", []))
        
        if len(feature_vector) == 0:
            return feature_vector
        
        # Min-max normalization
        min_val = np.min(feature_vector)
        max_val = np.max(feature_vector)
        
        if max_val - min_val == 0:
            return np.zeros_like(feature_vector)
        
        normalized = (feature_vector - min_val) / (max_val - min_val)
        return normalized
    
    @staticmethod
    def extract_timestamp_series(pattern: Dict[str, Any]) -> np.ndarray:
        """
        Extract timestamp series for DTW comparison
        
        Args:
            pattern: Traffic pattern dictionary
        
        Returns:
            Numpy array of inter-packet delays
        """
        timestamps = pattern.get("timestamps", [])
        
        if len(timestamps) < 2:
            return np.array([])
        
        inter_packet_delays = [
            timestamps[i+1] - timestamps[i]
            for i in range(len(timestamps) - 1)
        ]
        
        return np.array(inter_packet_delays)
