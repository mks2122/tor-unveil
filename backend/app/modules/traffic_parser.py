import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class TrafficParser:
    """Parse real traffic logs into pattern format compatible with analysis engine"""
    
    def __init__(self):
        pass
    
    def parse_json_log(self, log_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Parse JSON traffic log into entry and exit patterns
        
        Args:
            log_data: Dictionary containing traffic log data
            
        Returns:
            Tuple of (entry_pattern, exit_pattern, metadata)
        """
        try:
            # Validate format
            if "version" not in log_data:
                raise ValueError("Invalid log format: missing version")
            
            metadata = log_data.get("metadata", {})
            entry_traffic = log_data.get("entry_traffic", {})
            exit_traffic = log_data.get("exit_traffic", {})
            
            # Parse entry pattern
            entry_pattern = self._parse_traffic_data(entry_traffic, "entry")
            
            # Parse exit pattern
            exit_pattern = self._parse_traffic_data(exit_traffic, "exit")
            
            logger.info(f"Parsed log: {len(entry_pattern['timestamps'])} entry packets, "
                       f"{len(exit_pattern['timestamps'])} exit packets")
            
            return entry_pattern, exit_pattern, metadata
            
        except Exception as e:
            logger.error(f"Failed to parse JSON log: {e}")
            raise
    
    def _parse_traffic_data(self, traffic_data: Dict[str, Any], pattern_type: str) -> Dict[str, Any]:
        """Parse traffic data into pattern format"""
        timestamps = traffic_data.get("timestamps", [])
        packet_sizes = traffic_data.get("packet_sizes", [])
        
        if not timestamps or not packet_sizes:
            raise ValueError(f"Invalid {pattern_type} traffic data: empty timestamps or packet_sizes")
        
        if len(timestamps) != len(packet_sizes):
            raise ValueError(f"Timestamp and packet_size arrays must have same length")
        
        # Normalize timestamps to relative time (start at 0)
        if timestamps:
            base_time = min(timestamps)
            relative_timestamps = [t - base_time for t in timestamps]
        else:
            relative_timestamps = []
        
        # Calculate statistics
        total_packets = len(packet_sizes)
        total_bytes = sum(packet_sizes)
        duration = relative_timestamps[-1] if relative_timestamps else 0.0
        
        # Detect bursts using unified threshold (matches feature_extractor default)
        bursts = self._detect_bursts(relative_timestamps, threshold=0.5)
        
        pattern = {
            "timestamps": relative_timestamps,
            "packet_sizes": packet_sizes,
            "pattern_type": pattern_type,
            "total_packets": total_packets,
            "total_bytes": total_bytes,
            "duration": duration,
            "num_bursts": len(bursts),
            "source": "real"
        }
        
        return pattern
    
    def _detect_bursts(self, timestamps: List[float], threshold: float = 0.5) -> List[Tuple[int, int]]:
        """
        Detect traffic bursts based on inter-packet delay threshold
        
        Args:
            timestamps: List of packet timestamps
            threshold: Gap in seconds to separate bursts
            
        Returns:
            List of (start_idx, end_idx) for each burst
        """
        if not timestamps:
            return []
        
        bursts = []
        burst_start = 0
        
        for i in range(1, len(timestamps)):
            gap = timestamps[i] - timestamps[i-1]
            if gap > threshold:
                # End of burst
                bursts.append((burst_start, i-1))
                burst_start = i
        
        # Add final burst
        bursts.append((burst_start, len(timestamps)-1))
        
        return bursts
    
    def parse_realtime_request(self, request_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Parse real-time traffic capture from honeypot
        
        Expected format:
        {
            "client_logs": [{"timestamp": 0.0, "size": 512, "direction": "outgoing"}, ...],
            "server_logs": [{"timestamp": "2025-12-21T10:00:00.123Z", "exit_ip": "1.2.3.4", "size": 512}, ...],
            "metadata": {"session_id": "abc123", "user_agent": "..."}
        }
        """
        try:
            client_logs = request_data.get("client_logs", [])
            server_logs = request_data.get("server_logs", [])
            metadata = request_data.get("metadata", {})
            
            # Parse client-side (entry) traffic
            entry_timestamps = []
            entry_sizes = []
            for log in client_logs:
                entry_timestamps.append(float(log.get("timestamp", 0)))
                entry_sizes.append(int(log.get("size", 512)))
            
            # Parse server-side (exit) traffic
            exit_timestamps = []
            exit_sizes = []
            exit_ip = None
            
            for log in server_logs:
                # Convert ISO timestamp to relative seconds
                ts_str = log.get("timestamp")
                if ts_str:
                    dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    # Use first timestamp as base
                    if not exit_timestamps:
                        base_dt = dt
                    exit_timestamps.append((dt - base_dt).total_seconds() if exit_timestamps else 0.0)
                else:
                    exit_timestamps.append(0.0)
                
                exit_sizes.append(int(log.get("size", 512)))
                if not exit_ip and "exit_ip" in log:
                    exit_ip = log["exit_ip"]
            
            # Create patterns
            entry_pattern = self._parse_traffic_data(
                {"timestamps": entry_timestamps, "packet_sizes": entry_sizes},
                "entry"
            )
            
            exit_pattern = self._parse_traffic_data(
                {"timestamps": exit_timestamps, "packet_sizes": exit_sizes},
                "exit"
            )
            
            # Add exit IP to metadata
            if exit_ip:
                metadata["exit_ip"] = exit_ip
            
            return entry_pattern, exit_pattern, metadata
            
        except Exception as e:
            logger.error(f"Failed to parse realtime request: {e}")
            raise
    
    def validate_log_format(self, log_data: Dict[str, Any]) -> bool:
        """Validate that log data has required fields"""
        required_fields = ["version", "metadata", "entry_traffic", "exit_traffic"]
        
        for field in required_fields:
            if field not in log_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate traffic data structure
        for traffic_type in ["entry_traffic", "exit_traffic"]:
            traffic = log_data.get(traffic_type, {})
            if "timestamps" not in traffic or "packet_sizes" not in traffic:
                logger.error(f"Invalid {traffic_type}: missing timestamps or packet_sizes")
                return False
        
        return True
