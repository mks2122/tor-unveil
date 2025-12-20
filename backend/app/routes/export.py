"""
Export API Routes for TOR-Unveil
Provides endpoints for exporting forensic reports
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Literal
from datetime import datetime

from app.database import get_db
from app.models.analysis_result import AnalysisResult
from app.models.timeline_event import TimelineEvent
from app.models.analysis_history import NodeCorrelation
from app.services.export_service import ForensicExporter

router = APIRouter(prefix="/api/export", tags=["export"])
exporter = ForensicExporter()

def get_analysis_data(analysis_id: str, db: Session):
    """Helper to fetch analysis data"""
    
    # Handle 'latest' keyword
    if analysis_id.lower() == 'latest':
        results = db.query(AnalysisResult).order_by(
            AnalysisResult.id.desc()
        ).limit(10).all()
        
        if not results:
            raise HTTPException(status_code=404, detail="No analysis results found")
        
        analysis_id_int = results[0].id
    else:
        try:
            analysis_id_int = int(analysis_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid analysis_id format")
        
        results = db.query(AnalysisResult).filter(
            AnalysisResult.id == analysis_id_int
        ).all()
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id_int} not found")
    
    # Prepare analysis data from the first result's ranked_guards
    first_result = results[0]
    analysis_data = first_result.ranked_guards if first_result.ranked_guards else []
    
    # Get timeline events
    timeline_events = db.query(TimelineEvent).filter(
        TimelineEvent.analysis_id == analysis_id_int
    ).order_by(TimelineEvent.timestamp).all()
    
    # Get correlations
    correlations = db.query(NodeCorrelation).filter(
        NodeCorrelation.analysis_id == analysis_id_int
    ).all()
    
    metadata = {
        'analysis_id': analysis_id_int,
        'source_ip': results[0].source_ip if hasattr(results[0], 'source_ip') else 'N/A',
        'destination_ip': results[0].destination_ip if hasattr(results[0], 'destination_ip') else 'N/A',
        'guards_analyzed': len(analysis_data),
        'timeline_events': [e.to_dict() for e in timeline_events],
        'node_correlations': [c.to_dict() for c in correlations]
    }
    
    return analysis_data, metadata, timeline_events, correlations

@router.get("/json/{analysis_id}")
async def export_json(analysis_id: str):
    """Export analysis as JSON"""
    db: Session = next(get_db())
    
    try:
        analysis_data, metadata, timeline_events, correlations = get_analysis_data(analysis_id, db)
        
        timeline_dicts = [e.to_dict() for e in timeline_events]
        corr_dicts = [c.to_dict() for c in correlations]
        
        json_report = exporter.generate_json_report(
            analysis_data, metadata, timeline_dicts, corr_dicts
        )
        
        return Response(
            content=json_report,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=tor_unveil_analysis_{metadata['analysis_id']}.json"
            }
        )
    finally:
        db.close()

@router.get("/csv/{analysis_id}")
async def export_csv(analysis_id: str):
    """Export analysis as CSV"""
    db: Session = next(get_db())
    
    try:
        analysis_data, metadata, _, _ = get_analysis_data(analysis_id, db)
        
        csv_buffer = exporter.generate_csv_report(analysis_data, metadata)
        
        return StreamingResponse(
            iter([csv_buffer.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=tor_unveil_analysis_{metadata['analysis_id']}.csv"
            }
        )
    finally:
        db.close()

@router.get("/pdf/{analysis_id}")
async def export_pdf(analysis_id: str):
    """Export analysis as PDF"""
    db: Session = next(get_db())
    
    try:
        analysis_data, metadata, timeline_events, correlations = get_analysis_data(analysis_id, db)
        
        timeline_dicts = [e.to_dict() for e in timeline_events]
        corr_dicts = [c.to_dict() for c in correlations]
        
        pdf_buffer = exporter.generate_pdf_report(
            analysis_data, metadata, timeline_dicts, corr_dicts
        )
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=tor_unveil_forensic_report_{metadata['analysis_id']}.pdf"
            }
        )
    finally:
        db.close()

@router.get("/latest/{format}")
async def export_latest(format: Literal["json", "csv", "pdf"]):
    """Export latest analysis in specified format"""
    if format == "json":
        return await export_json("latest")
    elif format == "csv":
        return await export_csv("latest")
    elif format == "pdf":
        return await export_pdf("latest")
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use json, csv, or pdf")
