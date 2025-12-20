from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.modules.traffic_generator import TrafficGenerator
from app.modules.feature_extractor import FeatureExtractor
from app.modules.tor_client import TorHttpClient
from typing import Dict, Any, Optional

router = APIRouter()

class TrafficGenerationRequest(BaseModel):
    num_bursts: int = 10
    random_seed: int = 42
    pattern_type: str = "entry"  # 'entry' or 'exit'
    source_location: Optional[Dict[str, Any]] = None

class TrafficGenerationResponse(BaseModel):
    pattern: Dict[str, Any]
    features: Dict[str, Any]

class TorFetchRequest(BaseModel):
    url: str
    proxy_url: str = "socks5h://127.0.0.1:9050"
    timeout: int = 20
    max_bytes: int = 4096
    headers: Optional[Dict[str, str]] = None

class TorFetchResponse(BaseModel):
    url: str
    status_code: int
    elapsed_ms: float
    headers: Dict[str, Any]
    text_preview: str
    preview_truncated: bool

class CorrelatedTrafficRequest(BaseModel):
    num_bursts: int = 10
    random_seed: int = 42
    time_jitter: float = 0.2
    entry_location: Optional[Dict[str, Any]] = None
    exit_location: Optional[Dict[str, Any]] = None

@router.post("/generate", response_model=TrafficGenerationResponse)
async def generate_traffic(request: TrafficGenerationRequest):
    """Generate synthetic traffic pattern"""
    generator = TrafficGenerator(seed=request.random_seed)
    
    if request.pattern_type == "entry":
        pattern = generator.generate_entry_pattern(
            num_bursts=request.num_bursts,
            source_location=request.source_location
        )
    else:
        pattern = generator.generate_exit_pattern(
            num_bursts=request.num_bursts,
            source_location=request.source_location
        )
    
    # Extract features
    extractor = FeatureExtractor()
    features = extractor.extract_features(pattern)
    
    return {
        "pattern": pattern,
        "features": features
    }

@router.post("/tor-fetch", response_model=TorFetchResponse)
async def tor_fetch(request: TorFetchRequest):
    """Perform a real HTTP GET routed through a Tor SOCKS proxy."""
    client = TorHttpClient(proxy_url=request.proxy_url, timeout=request.timeout)
    try:
        result = client.get(
            url=request.url,
            headers=request.headers,
            max_bytes=request.max_bytes,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return result

@router.post("/generate-correlated")
async def generate_correlated_traffic(request: CorrelatedTrafficRequest):
    """Generate correlated entry and exit traffic patterns"""
    generator = TrafficGenerator(seed=request.random_seed)
    
    entry_pattern, exit_pattern = generator.generate_correlated_patterns(
        num_bursts=request.num_bursts,
        time_jitter=request.time_jitter,
        entry_location=request.entry_location,
        exit_location=request.exit_location
    )
    
    # Extract features
    extractor = FeatureExtractor()
    entry_features = extractor.extract_features(entry_pattern)
    exit_features = extractor.extract_features(exit_pattern)
    
    return {
        "entry": {
            "pattern": entry_pattern,
            "features": entry_features
        },
        "exit": {
            "pattern": exit_pattern,
            "features": exit_features
        }
    }
