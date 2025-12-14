from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.modules.traffic_generator import TrafficGenerator
from app.modules.feature_extractor import FeatureExtractor
from typing import Dict, Any

router = APIRouter()

class TrafficGenerationRequest(BaseModel):
    num_bursts: int = 10
    random_seed: int = 42
    pattern_type: str = "entry"  # 'entry' or 'exit'

class TrafficGenerationResponse(BaseModel):
    pattern: Dict[str, Any]
    features: Dict[str, Any]

@router.post("/generate", response_model=TrafficGenerationResponse)
async def generate_traffic(request: TrafficGenerationRequest):
    """Generate synthetic traffic pattern"""
    generator = TrafficGenerator(seed=request.random_seed)
    
    if request.pattern_type == "entry":
        pattern = generator.generate_entry_pattern(num_bursts=request.num_bursts)
    else:
        pattern = generator.generate_exit_pattern(num_bursts=request.num_bursts)
    
    # Extract features
    extractor = FeatureExtractor()
    features = extractor.extract_features(pattern)
    
    return {
        "pattern": pattern,
        "features": features
    }

@router.post("/generate-correlated")
async def generate_correlated_traffic(
    num_bursts: int = 10,
    random_seed: int = 42,
    time_jitter: float = 0.2
):
    """Generate correlated entry and exit traffic patterns"""
    generator = TrafficGenerator(seed=random_seed)
    
    entry_pattern, exit_pattern = generator.generate_correlated_patterns(
        num_bursts=num_bursts,
        time_jitter=time_jitter
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
