import numpy as np
import random
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class TrafficGenerator:
    """Generates synthetic Tor-like traffic patterns"""
    
    def __init__(self, seed: int = 42):
        """
        Initialize traffic generator with random seed
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        logger.info(f"TrafficGenerator initialized with seed {seed}")
    
    def generate_burst(self, 
                       burst_size_range: Tuple[int, int] = (5, 20),
                       inter_packet_delay_range: Tuple[float, float] = (0.01, 0.1)) -> Tuple[List[float], List[int]]:
        """
        Generate a single traffic burst
        
        Args:
            burst_size_range: Min and max packets in burst
            inter_packet_delay_range: Min and max delay between packets (seconds)
        
        Returns:
            Tuple of (timestamps, packet_sizes)
        """
        burst_size = random.randint(*burst_size_range)
        timestamps = []
        packet_sizes = []
        
        current_time = 0.0
        for i in range(burst_size):
            timestamps.append(current_time)
            # Tor cells are typically 512 bytes
            packet_size = random.randint(400, 600)
            packet_sizes.append(packet_size)
            
            # Add delay to next packet
            delay = random.uniform(*inter_packet_delay_range)
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
            "generation_params": {
                "num_bursts": num_bursts,
                "burst_size_range": burst_size_range,
                "inter_burst_delay_range": inter_burst_delay_range,
                "inter_packet_delay_range": inter_packet_delay_range,
                "seed": self.seed
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
