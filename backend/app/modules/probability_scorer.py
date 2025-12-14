import numpy as np
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class ProbabilityScorer:
    """Estimates likelihood of guard nodes being entry points"""
    
    def __init__(self, 
                 similarity_weight: float = 0.6,
                 bandwidth_weight: float = 0.2,
                 uptime_weight: float = 0.1,
                 consensus_weight: float = 0.1):
        """
        Initialize probability scorer with weights
        
        Args:
            similarity_weight: Weight for correlation similarity score
            bandwidth_weight: Weight for relay bandwidth
            uptime_weight: Weight for relay uptime
            consensus_weight: Weight for consensus weight
        """
        self.similarity_weight = similarity_weight
        self.bandwidth_weight = bandwidth_weight
        self.uptime_weight = uptime_weight
        self.consensus_weight = consensus_weight
        
        # Normalize weights to sum to 1
        total = similarity_weight + bandwidth_weight + uptime_weight + consensus_weight
        self.similarity_weight /= total
        self.bandwidth_weight /= total
        self.uptime_weight /= total
        self.consensus_weight /= total
        
        logger.info(f"ProbabilityScorer initialized with weights: "
                   f"similarity={self.similarity_weight:.2f}, "
                   f"bandwidth={self.bandwidth_weight:.2f}, "
                   f"uptime={self.uptime_weight:.2f}, "
                   f"consensus={self.consensus_weight:.2f}")
    
    def normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range"""
        if max_val == min_val:
            return 0.5
        return (value - min_val) / (max_val - min_val)
    
    def calculate_relay_score(self,
                             similarity_score: float,
                             relay_metadata: Dict[str, Any],
                             all_relays_metadata: List[Dict[str, Any]]) -> Tuple[float, Dict[str, float]]:
        """
        Calculate probability score for a single relay
        
        Args:
            similarity_score: Correlation similarity score
            relay_metadata: Metadata for the relay being scored
            all_relays_metadata: Metadata for all relays (for normalization)
        
        Returns:
            Tuple of (probability_score, component_scores)
        """
        # Extract relay metrics
        bandwidth = relay_metadata.get("bandwidth", 0)
        uptime = relay_metadata.get("uptime", 0)
        consensus_weight = relay_metadata.get("consensus_weight", 0)
        
        # Get ranges for normalization
        bandwidths = [r.get("bandwidth", 0) for r in all_relays_metadata]
        uptimes = [r.get("uptime", 0) for r in all_relays_metadata]
        consensus_weights = [r.get("consensus_weight", 0) for r in all_relays_metadata]
        
        # Normalize metrics
        norm_bandwidth = self.normalize_value(
            bandwidth,
            min(bandwidths) if bandwidths else 0,
            max(bandwidths) if bandwidths else 1
        )
        
        norm_uptime = self.normalize_value(
            uptime,
            min(uptimes) if uptimes else 0,
            max(uptimes) if uptimes else 1
        )
        
        norm_consensus = self.normalize_value(
            consensus_weight,
            min(consensus_weights) if consensus_weights else 0,
            max(consensus_weights) if consensus_weights else 1
        )
        
        # Calculate weighted probability score
        probability_score = (
            self.similarity_weight * similarity_score +
            self.bandwidth_weight * norm_bandwidth +
            self.uptime_weight * norm_uptime +
            self.consensus_weight * norm_consensus
        )
        
        component_scores = {
            "similarity": similarity_score,
            "normalized_bandwidth": norm_bandwidth,
            "normalized_uptime": norm_uptime,
            "normalized_consensus": norm_consensus,
            "weighted_similarity": self.similarity_weight * similarity_score,
            "weighted_bandwidth": self.bandwidth_weight * norm_bandwidth,
            "weighted_uptime": self.uptime_weight * norm_uptime,
            "weighted_consensus": self.consensus_weight * norm_consensus
        }
        
        return probability_score, component_scores
    
    def rank_guards(self,
                   guard_relays: List[Dict[str, Any]],
                   similarity_scores: Dict[str, float],
                   top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Rank guard nodes by probability score
        
        Args:
            guard_relays: List of guard relay metadata
            similarity_scores: Dictionary mapping fingerprint to similarity score
            top_n: Number of top results to return
        
        Returns:
            List of ranked guard nodes with probability scores
        """
        ranked_results = []
        
        for relay in guard_relays:
            fingerprint = relay.get("fingerprint")
            similarity = similarity_scores.get(fingerprint, 0.0)
            
            prob_score, components = self.calculate_relay_score(
                similarity, relay, guard_relays
            )
            
            ranked_results.append({
                "fingerprint": fingerprint,
                "nickname": relay.get("nickname", "Unknown"),
                "probability_score": prob_score,
                "confidence_score": prob_score * 100,  # Convert to percentage
                "similarity_score": similarity,
                "bandwidth": relay.get("bandwidth", 0),
                "uptime": relay.get("uptime", 0),
                "country": relay.get("country", ""),
                "country_name": relay.get("country_name", ""),
                "consensus_weight": relay.get("consensus_weight", 0),
                "component_scores": components,
                "relay_metadata": relay
            })
        
        # Sort by probability score descending
        ranked_results.sort(key=lambda x: x["probability_score"], reverse=True)
        
        # Return top N
        top_results = ranked_results[:top_n]
        
        logger.info(f"Ranked {len(guard_relays)} guards, returning top {len(top_results)}")
        return top_results
    
    def calculate_statistics(self, ranked_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics for ranked results
        
        Args:
            ranked_results: List of ranked guard nodes
        
        Returns:
            Dictionary of statistics
        """
        if not ranked_results:
            return {
                "count": 0,
                "avg_confidence": 0.0,
                "max_confidence": 0.0,
                "min_confidence": 0.0
            }
        
        confidence_scores = [r["confidence_score"] for r in ranked_results]
        
        return {
            "count": len(ranked_results),
            "avg_confidence": np.mean(confidence_scores),
            "max_confidence": np.max(confidence_scores),
            "min_confidence": np.min(confidence_scores),
            "std_confidence": np.std(confidence_scores),
            "median_confidence": np.median(confidence_scores)
        }
