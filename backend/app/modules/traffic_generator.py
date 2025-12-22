import numpy as np
import random
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TrafficGenerator:
    """Generates synthetic Tor-like traffic patterns"""
    
    # Location-based traffic profiles (latency in ms, jitter factor)
    LOCATION_PROFILES = {
        "United States": {"base_latency": 20, "jitter_factor": 0.15, "packet_variance": 0.10},
        "United Kingdom": {"base_latency": 35, "jitter_factor": 0.18, "packet_variance": 0.12},
        "Germany": {"base_latency": 40, "jitter_factor": 0.20, "packet_variance": 0.12},
        "France": {"base_latency": 38, "jitter_factor": 0.19, "packet_variance": 0.11},
        "Netherlands": {"base_latency": 32, "jitter_factor": 0.17, "packet_variance": 0.11},
        "Canada": {"base_latency": 25, "jitter_factor": 0.16, "packet_variance": 0.10},
        "Australia": {"base_latency": 180, "jitter_factor": 0.30, "packet_variance": 0.18},
        "Japan": {"base_latency": 120, "jitter_factor": 0.25, "packet_variance": 0.15},
        "Singapore": {"base_latency": 150, "jitter_factor": 0.28, "packet_variance": 0.16},
        "Brazil": {"base_latency": 140, "jitter_factor": 0.28, "packet_variance": 0.17},
        "Russia": {"base_latency": 90, "jitter_factor": 0.25, "packet_variance": 0.16},
        "India": {"base_latency": 160, "jitter_factor": 0.30, "packet_variance": 0.18},
        "default": {"base_latency": 50, "jitter_factor": 0.20, "packet_variance": 0.12}
    }
    
    def __init__(self, seed: int = 42, location: Optional[str] = None):
        """
        Initialize traffic generator with random seed and optional location
        
        Args:
            seed: Random seed for reproducibility
            location: Country/location for traffic characteristics
        """
        self.seed = seed
        self.location = location
        random.seed(seed)
        np.random.seed(seed)
        
        # Get location profile
        self.location_profile = self.LOCATION_PROFILES.get(
            location, self.LOCATION_PROFILES["default"]
        )
        
        logger.info(f"TrafficGenerator initialized with seed {seed}, location: {location}")
        logger.info(f"Using profile: {self.location_profile}")
    
    def generate_burst(self, 
                       burst_size_range: Tuple[int, int] = (5, 20),
                       inter_packet_delay_range: Tuple[float, float] = (0.01, 0.1)) -> Tuple[List[float], List[int]]:
        """
        Generate a single traffic burst with location-based characteristics
        
        Args:
            burst_size_range: Min and max packets in burst
            inter_packet_delay_range: Min and max delay between packets (seconds)
        
        Returns:
            Tuple of (timestamps, packet_sizes)
        """
        burst_size = random.randint(*burst_size_range)
        timestamps = []
        packet_sizes = []
        
        # Apply location-based latency
        base_latency_seconds = self.location_profile["base_latency"] / 1000.0
        jitter_factor = self.location_profile["jitter_factor"]
        packet_variance = self.location_profile["packet_variance"]
        
        current_time = 0.0
        for i in range(burst_size):
            timestamps.append(current_time)
            
            # Tor cells are typically 512 bytes, with location-based variance
            base_size = 512
            size_variation = int(base_size * packet_variance * random.uniform(-1, 1))
            packet_size = base_size + size_variation
            packet_size = max(400, min(600, packet_size))  # Keep within bounds
            packet_sizes.append(packet_size)
            
            # Add delay with location-based jitter
            base_delay = random.uniform(*inter_packet_delay_range)
            location_jitter = base_latency_seconds * jitter_factor * random.uniform(-1, 1)
            delay = base_delay + location_jitter
            delay = max(0.001, delay)  # Ensure positive delay
            current_time += delay
        
        return timestamps, packet_sizes
    
    def generate_pattern(self,
                        num_bursts: int = 10,
                        burst_size_range: Tuple[int, int] = (5, 20),
                        inter_burst_delay_range: Tuple[float, float] = (0.5, 2.0),
                        inter_packet_delay_range: Tuple[float, float] = (0.01, 0.1)) -> Dict[str, Any]:
        """
        Generate a complete traffic pattern with multiple bursts
        
        Args:
            num_bursts: Number of traffic bursts
            burst_size_range: Min and max packets per burst
            inter_burst_delay_range: Min and max delay between bursts (seconds)
            inter_packet_delay_range: Min and max delay between packets (seconds)
        
        Returns:
            Dictionary with timestamps, packet_sizes, and metadata
        """
        all_timestamps = []
        all_packet_sizes = []
        current_offset = 0.0
        
        for burst_num in range(num_bursts):
            burst_timestamps, burst_sizes = self.generate_burst(
                burst_size_range, inter_packet_delay_range
            )
            
            # Offset timestamps by current position
            offset_timestamps = [t + current_offset for t in burst_timestamps]
            all_timestamps.extend(offset_timestamps)
            all_packet_sizes.extend(burst_sizes)
            
            # Add delay before next burst
            if burst_num < num_bursts - 1:
                inter_burst_delay = random.uniform(*inter_burst_delay_range)
                current_offset = offset_timestamps[-1] + inter_burst_delay
        
        return {
            "timestamps": all_timestamps,
            "packet_sizes": all_packet_sizes,
            "num_bursts": num_bursts,
            "total_packets": len(all_timestamps),
            "total_bytes": sum(all_packet_sizes),
            "duration": all_timestamps[-1] if all_timestamps else 0.0,
            "location": self.location,
            "location_profile": self.location_profile,
            "generation_params": {
                "num_bursts": num_bursts,
                "burst_size_range": burst_size_range,
                "inter_burst_delay_range": inter_burst_delay_range,
                "inter_packet_delay_range": inter_packet_delay_range,
                "seed": self.seed,
                "location": self.location
            }
        }
    
    def generate_entry_pattern(self, **kwargs) -> Dict[str, Any]:
        """Generate entry-side traffic pattern"""
        pattern = self.generate_pattern(**kwargs)
        pattern["pattern_type"] = "entry"
        logger.info(f"Generated entry pattern with {pattern['total_packets']} packets")
        return pattern
    
    def generate_exit_pattern(self, **kwargs) -> Dict[str, Any]:
        """Generate exit-side traffic pattern"""
        # Exit patterns may have slightly different characteristics
        pattern = self.generate_pattern(**kwargs)
        pattern["pattern_type"] = "exit"
        logger.info(f"Generated exit pattern with {pattern['total_packets']} packets")
        return pattern
    
    def generate_correlated_patterns(self, 
                                     num_bursts: int = 10,
                                     time_jitter: float = 0.2) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate correlated entry and exit patterns
        
        Args:
            num_bursts: Number of bursts in pattern
            time_jitter: Amount of random time shift to add (0-1, where 1 = full randomization)
        
        Returns:
            Tuple of (entry_pattern, exit_pattern)
        """
        # Generate base entry pattern
        entry_pattern = self.generate_entry_pattern(num_bursts=num_bursts)
        
        # Create correlated exit pattern with some jitter
        exit_timestamps = []
        for ts in entry_pattern["timestamps"]:
            # Add random jitter
            jitter = random.uniform(-time_jitter, time_jitter)
            exit_timestamps.append(ts + jitter)
        
        exit_pattern = {
            "timestamps": exit_timestamps,
            "packet_sizes": entry_pattern["packet_sizes"].copy(),
            "num_bursts": num_bursts,
            "total_packets": len(exit_timestamps),
            "total_bytes": sum(entry_pattern["packet_sizes"]),
            "duration": exit_timestamps[-1] if exit_timestamps else 0.0,
            "pattern_type": "exit",
            "generation_params": {
                **entry_pattern["generation_params"],
                "time_jitter": time_jitter
            }
        }
        
        logger.info(f"Generated correlated patterns with {time_jitter} jitter")
        return entry_pattern, exit_pattern
