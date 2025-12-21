from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.modules.traffic_generator import TrafficGenerator
from app.modules.feature_extractor import FeatureExtractor
from app.services.analysis_service import AnalysisService
from app.database import get_db
from typing import Dict, Any, List

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

class RealtimeTrafficRequest(BaseModel):
    client_logs: List[Dict[str, Any]]
    server_logs: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

@router.post("/ingest-realtime")
async def ingest_realtime_traffic(request: RealtimeTrafficRequest, db: Session = Depends(get_db)):
    """
    Ingest real-time traffic from honeypot and automatically analyze
    
    This endpoint receives traffic logs from the honeypot server and immediately
    runs correlation analysis to identify the probable guard node.
    """
    try:
        analysis_service = AnalysisService(db)
        
        # Run real-time analysis
        result = analysis_service.run_realtime_analysis(
            client_logs=request.client_logs,
            server_logs=request.server_logs,
            metadata=request.metadata
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/status")
async def get_traffic_status():
    """Get traffic analysis status and configuration"""
    from app.config import settings
    
    return {
        "analysis_mode": settings.ANALYSIS_MODE,
        "cache_enabled": settings.ENABLE_RELAY_CACHE,
        "cache_ttl_seconds": settings.ONIONOO_CACHE_TTL_SECONDS,
        "expected_real_accuracy": settings.EXPECTED_REAL_ACCURACY,
        "auto_analyze": settings.REAL_TRAFFIC_AUTO_ANALYZE
    }

@router.get("/realtime-analyses")
async def get_realtime_analyses(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent real-time traffic analyses from honeypot"""
    try:
        analysis_service = AnalysisService(db)
        results = analysis_service.get_realtime_analyses(limit=limit)
        return {
            "count": len(results),
            "analyses": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analyses: {str(e)}")

