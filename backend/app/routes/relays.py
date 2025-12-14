from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.relay_service import RelayService
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class RelayResponse(BaseModel):
    fingerprint: str
    nickname: str
    relay_type: str
    bandwidth: Optional[float]
    uptime: Optional[int]
    country: Optional[str]
    country_name: Optional[str]
    
    class Config:
        from_attributes = True

class RelayStatsResponse(BaseModel):
    total: int
    guard: int
    exit: int
    middle: int

@router.post("/refresh")
async def refresh_relays(db: Session = Depends(get_db)):
    """Refresh relay metadata from configured data source"""
    try:
        relay_service = RelayService(db)
        relays = relay_service.refresh_relays()
        
        return {
            "message": "Relays refreshed successfully",
            "count": len(relays),
            "source": relays[0].data_source if relays else "none"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[RelayResponse])
async def get_all_relays(
    relay_type: Optional[str] = None,
    country: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all relays with optional filtering"""
    relay_service = RelayService(db)
    
    if relay_type == "guard":
        relays = relay_service.get_guard_relays()
    elif relay_type == "exit":
        relays = relay_service.get_exit_relays()
    elif country:
        relays = relay_service.get_relays_by_country(country)
    else:
        relays = relay_service.get_all_relays()
    
    # Apply limit
    relays = relays[:limit]
    
    return relays

@router.get("/stats", response_model=RelayStatsResponse)
async def get_relay_stats(db: Session = Depends(get_db)):
    """Get relay statistics"""
    relay_service = RelayService(db)
    stats = relay_service.get_relay_count()
    return stats

@router.get("/guards", response_model=List[RelayResponse])
async def get_guard_relays(limit: int = 100, db: Session = Depends(get_db)):
    """Get all guard relays"""
    relay_service = RelayService(db)
    relays = relay_service.get_guard_relays()[:limit]
    return relays

@router.get("/{fingerprint}", response_model=RelayResponse)
async def get_relay(fingerprint: str, db: Session = Depends(get_db)):
    """Get specific relay by fingerprint"""
    relay_service = RelayService(db)
    relay = relay_service.get_relay_by_fingerprint(fingerprint)
    
    if not relay:
        raise HTTPException(status_code=404, detail="Relay not found")
    
    return relay
