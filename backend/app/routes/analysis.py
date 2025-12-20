from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analysis_service import AnalysisService
from app.models.timeline_event import TimelineEvent
from pydantic import BaseModel
from typing import Dict, Any, List

router = APIRouter()

class AnalysisRequest(BaseModel):
    simulation_count: int = 100
    top_n: int = 10
    random_seed: int = 42

class AnalysisResponse(BaseModel):
    analysis_id: str
    analysis_db_id: int = None
    ranked_guards: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    configuration: Dict[str, Any]
    execution_time: float

@router.post("/run", response_model=AnalysisResponse)
async def run_analysis(request: AnalysisRequest, db: Session = Depends(get_db)):
    """
    Run complete traffic analysis to identify probable guard nodes
    
    This endpoint:
    1. Retrieves guard relays from the database
    2. Generates synthetic traffic patterns
    3. Correlates entry/exit patterns
    4. Scores and ranks guard nodes
    5. Returns ranked results with confidence scores
    """
    try:
        analysis_service = AnalysisService(db)
        result = analysis_service.run_analysis(
            simulation_count=request.simulation_count,
            top_n=request.top_n,
            random_seed=request.random_seed
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{analysis_id}")
async def get_analysis_result(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieve a previous analysis result by ID"""
    analysis_service = AnalysisService(db)
    result = analysis_service.get_analysis_result(analysis_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return result

@router.get("/")
async def get_recent_analyses(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent analysis results"""
    analysis_service = AnalysisService(db)
    results = analysis_service.get_recent_analyses(limit=limit)
    return results

@router.get("/timeline/{analysis_id}")
async def get_timeline_events(analysis_id: int, db: Session = Depends(get_db)):
    """Get timeline events for an analysis"""
    events = db.query(TimelineEvent).filter(
        TimelineEvent.analysis_id == analysis_id
    ).order_by(TimelineEvent.timestamp).all()
    
    return {
        "analysis_id": analysis_id,
        "events": [e.to_dict() for e in events]
    }
