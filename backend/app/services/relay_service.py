from sqlalchemy.orm import Session
from app.models.relay import Relay
from app.modules.metadata_collector import MetadataCollector
from app.config import settings
from typing import List, Optional
import logging
import json

logger = logging.getLogger(__name__)

class RelayService:
    """Service for managing Tor relay data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.collector = MetadataCollector(settings.TOR_ONIONOO_API)
    
    def load_sample_data(self) -> List[Relay]:
        """Load sample relay data from seed file"""
        try:
            with open("/app/../database/seeds/sample_relays.json", "r") as f:
                sample_data = json.load(f)
            
            relays = []
            for relay_data in sample_data:
                relay = Relay(**relay_data, data_source="sample")
                self.db.add(relay)
                relays.append(relay)
            
            self.db.commit()
            logger.info(f"Loaded {len(relays)} sample relays")
            return relays
            
        except FileNotFoundError:
            logger.warning("Sample data file not found")
            return []
        except Exception as e:
            logger.error(f"Error loading sample data: {e}")
            self.db.rollback()
            return []
    
    def fetch_live_data(self, relay_type: Optional[str] = None) -> List[Relay]:
        """Fetch live relay data from Tor Onionoo API"""
        try:
            parsed_relays = self.collector.fetch_and_parse_relays(relay_type)
            
            relays = []
            for relay_data in parsed_relays:
                # Check if relay already exists
                existing = self.db.query(Relay).filter(
                    Relay.fingerprint == relay_data["fingerprint"]
                ).first()
                
                if existing:
                    # Update existing relay
                    for key, value in relay_data.items():
                        setattr(existing, key, value)
                    existing.data_source = "live"
                    relay = existing
                else:
                    # Create new relay
                    relay = Relay(**relay_data, data_source="live")
                    self.db.add(relay)
                
                relays.append(relay)
            
            self.db.commit()
            logger.info(f"Fetched {len(relays)} live relays")
            return relays
            
        except Exception as e:
            logger.error(f"Error fetching live data: {e}")
            self.db.rollback()
            raise
    
    def refresh_relays(self) -> List[Relay]:
        """Refresh relay data based on configuration"""
        data_source = settings.DATA_SOURCE
        
        if data_source == "sample":
            # Check if sample data already loaded
            count = self.db.query(Relay).filter(Relay.data_source == "sample").count()
            if count > 0:
                logger.info("Sample data already loaded")
                return self.get_all_relays()
            return self.load_sample_data()
        
        elif data_source == "live":
            return self.fetch_live_data()
        
        elif data_source == "both":
            # Try live first, fallback to sample
            try:
                return self.fetch_live_data()
            except Exception as e:
                logger.warning(f"Live fetch failed, loading sample data: {e}")
                return self.load_sample_data()
        
        return []
    
    def get_all_relays(self) -> List[Relay]:
        """Get all relays from database"""
        return self.db.query(Relay).all()
    
    def get_guard_relays(self) -> List[Relay]:
        """Get all guard relays"""
        return self.db.query(Relay).filter(Relay.relay_type == "guard").all()
    
    def get_exit_relays(self) -> List[Relay]:
        """Get all exit relays"""
        return self.db.query(Relay).filter(Relay.relay_type == "exit").all()
    
    def get_relay_by_fingerprint(self, fingerprint: str) -> Optional[Relay]:
        """Get relay by fingerprint"""
        return self.db.query(Relay).filter(Relay.fingerprint == fingerprint).first()
    
    def get_relays_by_country(self, country_code: str) -> List[Relay]:
        """Get relays by country code"""
        return self.db.query(Relay).filter(Relay.country == country_code).all()
    
    def get_relay_count(self) -> dict:
        """Get count of relays by type"""
        return {
            "total": self.db.query(Relay).count(),
            "guard": self.db.query(Relay).filter(Relay.relay_type == "guard").count(),
            "exit": self.db.query(Relay).filter(Relay.relay_type == "exit").count(),
            "middle": self.db.query(Relay).filter(Relay.relay_type == "middle").count(),
        }
