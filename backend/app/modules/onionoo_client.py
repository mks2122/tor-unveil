import requests
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings

logger = logging.getLogger(__name__)

class OnionooClient:
    """Client for Onionoo API with caching layer"""
    
    def __init__(self, db: Session):
        self.db = db
        self.api_url = settings.TOR_ONIONOO_API
        self.cache_ttl = timedelta(seconds=settings.ONIONOO_CACHE_TTL_SECONDS)
        self.timeout = settings.ONIONOO_REQUEST_TIMEOUT
        self.max_retries = settings.ONIONOO_MAX_RETRIES
        
    def get_relay_by_fingerprint(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """Get relay details by fingerprint with caching"""
        if settings.ENABLE_RELAY_CACHE:
            cached = self._get_from_cache(fingerprint=fingerprint, cache_type="details")
            if cached:
                logger.debug(f"Cache hit for fingerprint {fingerprint}")
                return cached
        
        # Fetch from API
        try:
            url = f"{self.api_url}/details"
            params = {"lookup": fingerprint}
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            relays = data.get("relays", [])
            
            if relays:
                relay_data = relays[0]
                if settings.ENABLE_RELAY_CACHE:
                    self._save_to_cache(
                        fingerprint=fingerprint,
                        cache_type="details",
                        cache_data=relay_data
                    )
                return relay_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch relay {fingerprint}: {e}")
            return None
    
    def get_relay_by_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get relay details by IP address (for exit node identification)"""
        if settings.ENABLE_RELAY_CACHE:
            cached = self._get_from_cache(ip_address=ip_address, cache_type="ip_lookup")
            if cached:
                logger.debug(f"Cache hit for IP {ip_address}")
                return cached
        
        # Fetch from API
        try:
            url = f"{self.api_url}/details"
            params = {"search": ip_address}
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            relays = data.get("relays", [])
            
            # Find relay matching the IP
            for relay in relays:
                or_addresses = relay.get("or_addresses", [])
                for addr in or_addresses:
                    if ip_address in addr:
                        if settings.ENABLE_RELAY_CACHE:
                            self._save_to_cache(
                                ip_address=ip_address,
                                cache_type="ip_lookup",
                                cache_data=relay
                            )
                        return relay
            
            logger.warning(f"No relay found for IP {ip_address}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch relay by IP {ip_address}: {e}")
            return None
    
    def _get_from_cache(self, fingerprint: str = None, ip_address: str = None, 
                       cache_type: str = "details") -> Optional[Dict[str, Any]]:
        """Get cached relay data"""
        try:
            query = text("""
                SELECT cache_data 
                FROM relay_cache 
                WHERE cache_type = :cache_type 
                AND expires_at > :now
                AND (fingerprint = :fingerprint OR ip_address = :ip_address)
                ORDER BY fetched_at DESC 
                LIMIT 1
            """)
            
            result = self.db.execute(
                query,
                {
                    "cache_type": cache_type,
                    "now": datetime.utcnow(),
                    "fingerprint": fingerprint,
                    "ip_address": ip_address
                }
            ).fetchone()
            
            if result:
                return result[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Cache read error: {e}")
            return None
    
    def _save_to_cache(self, cache_type: str, cache_data: Dict[str, Any],
                      fingerprint: str = None, ip_address: str = None):
        """Save relay data to cache"""
        try:
            expires_at = datetime.utcnow() + self.cache_ttl
            
            query = text("""
                INSERT INTO relay_cache 
                (fingerprint, ip_address, cache_type, cache_data, fetched_at, expires_at)
                VALUES (:fingerprint, :ip_address, :cache_type, :cache_data, :fetched_at, :expires_at)
            """)
            
            self.db.execute(
                query,
                {
                    "fingerprint": fingerprint,
                    "ip_address": ip_address,
                    "cache_type": cache_type,
                    "cache_data": json.dumps(cache_data),
                    "fetched_at": datetime.utcnow(),
                    "expires_at": expires_at
                }
            )
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Cache write error: {e}")
            self.db.rollback()
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        try:
            query = text("DELETE FROM relay_cache WHERE expires_at < :now")
            result = self.db.execute(query, {"now": datetime.utcnow()})
            self.db.commit()
            logger.info(f"Cleaned up {result.rowcount} expired cache entries")
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            self.db.rollback()
