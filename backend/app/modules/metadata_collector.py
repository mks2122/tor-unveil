import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MetadataCollector:
    """Collects Tor relay metadata from Onionoo API"""
    
    def __init__(self, api_url: str = "https://onionoo.torproject.org"):
        self.api_url = api_url
        self.details_endpoint = f"{api_url}/details"
        
    def fetch_all_relays(self) -> List[Dict[str, Any]]:
        """Fetch all relay details from Onionoo API"""
        try:
            logger.info("Fetching relay metadata from Onionoo API...")
            response = requests.get(self.details_endpoint, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            relays = data.get("relays", [])
            
            logger.info(f"Successfully fetched {len(relays)} relays")
            return relays
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch relay metadata: {e}")
            raise
    
    def fetch_guard_relays(self) -> List[Dict[str, Any]]:
        """Fetch only guard relays"""
        try:
            logger.info("Fetching guard relay metadata...")
            params = {"flag": "Guard"}
            response = requests.get(self.details_endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            relays = data.get("relays", [])
            
            logger.info(f"Successfully fetched {len(relays)} guard relays")
            return relays
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch guard relays: {e}")
            raise
    
    def fetch_exit_relays(self) -> List[Dict[str, Any]]:
        """Fetch only exit relays"""
        try:
            logger.info("Fetching exit relay metadata...")
            params = {"flag": "Exit"}
            response = requests.get(self.details_endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            relays = data.get("relays", [])
            
            logger.info(f"Successfully fetched {len(relays)} exit relays")
            return relays
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch exit relays: {e}")
            raise
    
    def parse_relay_data(self, relay_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw relay data into structured format"""
        flags = relay_data.get("flags", [])
        
        # Determine relay type
        is_guard = "Guard" in flags
        is_exit = "Exit" in flags
        
        if is_guard and is_exit:
            relay_type = "guard"  # Prioritize guard
        elif is_guard:
            relay_type = "guard"
        elif is_exit:
            relay_type = "exit"
        else:
            relay_type = "middle"
        
        # Calculate uptime
        first_seen = relay_data.get("first_seen")
        last_seen = relay_data.get("last_seen")
        uptime = 0
        if first_seen and last_seen:
            try:
                first = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
                last = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
                uptime = int((last - first).total_seconds())
            except:
                pass
        
        return {
            "fingerprint": relay_data.get("fingerprint"),
            "nickname": relay_data.get("nickname", "Unknown"),
            "is_guard": is_guard,
            "is_exit": is_exit,
            "is_middle": relay_type == "middle",
            "relay_type": relay_type,
            "bandwidth": relay_data.get("observed_bandwidth", 0),
            "uptime": uptime,
            "country": relay_data.get("country", ""),
            "country_name": relay_data.get("country_name", ""),
            "region": relay_data.get("region_name", ""),
            "city": relay_data.get("city_name", ""),
            "or_addresses": relay_data.get("or_addresses", []),
            "exit_policy": relay_data.get("exit_policy", []),
            "first_seen": first_seen,
            "last_seen": last_seen,
            "consensus_weight": relay_data.get("consensus_weight", 0),
            "guard_probability": relay_data.get("guard_probability", 0.0),
            "middle_probability": relay_data.get("middle_probability", 0.0),
            "exit_probability": relay_data.get("exit_probability", 0.0),
        }
    
    def fetch_and_parse_relays(self, relay_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch and parse relays based on type"""
        if relay_type == "guard":
            raw_relays = self.fetch_guard_relays()
        elif relay_type == "exit":
            raw_relays = self.fetch_exit_relays()
        else:
            raw_relays = self.fetch_all_relays()
        
        parsed_relays = [self.parse_relay_data(relay) for relay in raw_relays]
        return parsed_relays
