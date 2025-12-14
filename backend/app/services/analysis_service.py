from sqlalchemy.orm import Session
from app.models.analysis_result import AnalysisResult
from app.services.relay_service import RelayService
from app.modules.traffic_generator import TrafficGenerator
from app.modules.feature_extractor import FeatureExtractor
from app.modules.correlation_engine import CorrelationEngine
from app.modules.probability_scorer import ProbabilityScorer
from typing import Dict, Any, List
import logging
import time
import uuid

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for orchestrating traffic analysis and guard node identification"""
    
    def __init__(self, db: Session):
        self.db = db
        self.relay_service = RelayService(db)
        self.feature_extractor = FeatureExtractor()
        self.correlation_engine = CorrelationEngine()
    
    def run_analysis(self,
                    simulation_count: int = 100,
                    top_n: int = 10,
                    random_seed: int = 42) -> Dict[str, Any]:
        """
        Run complete analysis to identify probable guard nodes
        
        Args:
            simulation_count: Number of traffic simulations to run
            top_n: Number of top guard nodes to return
            random_seed: Random seed for reproducibility
        
        Returns:
            Dictionary with analysis results
        """
        start_time = time.time()
        analysis_id = str(uuid.uuid4())
        
        logger.info(f"Starting analysis {analysis_id} with {simulation_count} simulations")
        
        try:
            # Step 1: Get guard relays
            guard_relays = self.relay_service.get_guard_relays()
            if not guard_relays:
                logger.warning("No guard relays found, attempting to refresh")
                self.relay_service.refresh_relays()
                guard_relays = self.relay_service.get_guard_relays()
            
            if not guard_relays:
                raise ValueError("No guard relays available for analysis")
            
            logger.info(f"Analyzing {len(guard_relays)} guard relays")
            
            # Step 2: Generate synthetic traffic patterns
            traffic_gen = TrafficGenerator(seed=random_seed)
            
            # Generate correlated entry/exit patterns
            similarity_scores = {}
            
            for i in range(min(simulation_count, len(guard_relays))):
                # Generate correlated patterns
                entry_pattern, exit_pattern = traffic_gen.generate_correlated_patterns(
                    num_bursts=10,
                    time_jitter=0.2
                )
                
                # Extract features
                entry_features = self.feature_extractor.extract_features(entry_pattern)
                exit_features = self.feature_extractor.extract_features(exit_pattern)
                
                # Correlate with a guard relay
                guard_relay = guard_relays[i % len(guard_relays)]
                
                # Calculate correlation score
                score, detailed = self.correlation_engine.correlation_score(
                    entry_pattern, exit_pattern,
                    entry_features, exit_features
                )
                
                # Store similarity score for this guard
                fingerprint = guard_relay.fingerprint
                if fingerprint not in similarity_scores:
                    similarity_scores[fingerprint] = []
                similarity_scores[fingerprint].append(score)
            
            # Average similarity scores for each guard
            avg_similarity_scores = {
                fp: sum(scores) / len(scores)
                for fp, scores in similarity_scores.items()
            }
            
            # Step 3: Score and rank guards
            scorer = ProbabilityScorer(
                similarity_weight=0.6,
                bandwidth_weight=0.2,
                uptime_weight=0.1,
                consensus_weight=0.1
            )
            
            # Convert guard relays to dictionaries
            guard_relay_dicts = [
                {
                    "fingerprint": r.fingerprint,
                    "nickname": r.nickname,
                    "bandwidth": r.bandwidth or 0,
                    "uptime": r.uptime or 0,
                    "country": r.country,
                    "country_name": r.country_name,
                    "consensus_weight": r.consensus_weight or 0,
                }
                for r in guard_relays
            ]
            
            ranked_guards = scorer.rank_guards(
                guard_relay_dicts,
                avg_similarity_scores,
                top_n=top_n
            )
            
            # Calculate statistics
            stats = scorer.calculate_statistics(ranked_guards)
            
            execution_time = time.time() - start_time
            
            # Store results
            result = AnalysisResult(
                analysis_id=analysis_id,
                top_n=top_n,
                simulation_count=simulation_count,
                random_seed=random_seed,
                ranked_guards=ranked_guards,
                correlation_scores=avg_similarity_scores,
                total_guards_analyzed=len(guard_relays),
                avg_confidence_score=stats["avg_confidence"],
                execution_time_seconds=execution_time
            )
            
            self.db.add(result)
            self.db.commit()
            
            logger.info(f"Analysis {analysis_id} completed in {execution_time:.2f}s")
            
            return {
                "analysis_id": analysis_id,
                "ranked_guards": ranked_guards,
                "statistics": stats,
                "configuration": {
                    "simulation_count": simulation_count,
                    "top_n": top_n,
                    "random_seed": random_seed,
                    "total_guards_analyzed": len(guard_relays)
                },
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.db.rollback()
            raise
    
    def get_analysis_result(self, analysis_id: str) -> Dict[str, Any]:
        """Retrieve a previous analysis result"""
        result = self.db.query(AnalysisResult).filter(
            AnalysisResult.analysis_id == analysis_id
        ).first()
        
        if not result:
            return None
        
        return {
            "analysis_id": result.analysis_id,
            "ranked_guards": result.ranked_guards,
            "configuration": {
                "simulation_count": result.simulation_count,
                "top_n": result.top_n,
                "random_seed": result.random_seed,
                "total_guards_analyzed": result.total_guards_analyzed
            },
            "avg_confidence_score": result.avg_confidence_score,
            "execution_time": result.execution_time_seconds,
            "created_at": result.created_at.isoformat() if result.created_at else None
        }
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analysis results"""
        results = self.db.query(AnalysisResult).order_by(
            AnalysisResult.created_at.desc()
        ).limit(limit).all()
        
        return [
            {
                "analysis_id": r.analysis_id,
                "top_n": r.top_n,
                "simulation_count": r.simulation_count,
                "avg_confidence_score": r.avg_confidence_score,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in results
        ]
