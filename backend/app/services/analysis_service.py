from sqlalchemy.orm import Session
from app.models.analysis_result import AnalysisResult
from app.models.timeline_event import TimelineEvent
from app.models.analysis_history import NodeCorrelation
from app.services.relay_service import RelayService
from app.modules.traffic_generator import TrafficGenerator
from app.modules.feature_extractor import FeatureExtractor
from app.modules.correlation_engine import CorrelationEngine
from app.modules.probability_scorer import ProbabilityScorer
from app.modules.iterative_learner import IterativeLearner
from app.modules.onionoo_client import OnionooClient
from app.modules.traffic_parser import TrafficParser
from typing import Dict, Any, List
from datetime import datetime
import logging
import time
import uuid
import numpy as np

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for orchestrating traffic analysis and guard node identification"""
    
    def __init__(self, db: Session):
        self.db = db
        self.relay_service = RelayService(db)
        self.feature_extractor = FeatureExtractor()
        self.correlation_engine = CorrelationEngine()
        self.learner = IterativeLearner(db)
        self.onionoo_client = OnionooClient(db)
        self.traffic_parser = TrafficParser()
    
    def run_analysis(self,
                    simulation_count: int = 100,
                    top_n: int = 10,
                    random_seed: int = 42,
                    guard_location: str = None) -> Dict[str, Any]:
        """
        Run complete analysis to identify probable guard nodes
        
        Args:
            simulation_count: Number of traffic simulations to run
            top_n: Number of top guard nodes to return
            random_seed: Random seed for reproducibility
            guard_location: Country/location of the simulated guard node
        
        Returns:
            Dictionary with analysis results
        """
        start_time = time.time()
        analysis_id = str(uuid.uuid4())
        
        logger.info(f"Starting analysis {analysis_id} with {simulation_count} simulations, location: {guard_location}")
        
        try:
            # Step 1: Get guard relays
            guard_relays = self.relay_service.get_guard_relays()
            if not guard_relays:
                logger.warning("No guard relays found, attempting to refresh")
                self.relay_service.refresh_relays()
                guard_relays = self.relay_service.get_guard_relays()

            if not guard_relays:
                raise ValueError("No guard relays available for analysis")
            
            # Filter by location if specified
            if guard_location:
                # Normalize location for comparison (case-insensitive)
                location_normalized = guard_location.strip().lower()
                location_relays = [
                    r for r in guard_relays 
                    if (r.country_name and r.country_name.lower() == location_normalized) or
                       (r.country and r.country.lower() == location_normalized)
                ]
                if location_relays:
                    logger.info(f"Filtered to {len(location_relays)} relays in {guard_location}")
                else:
                    logger.warning(f"No relays found in {guard_location}, using all guard relays")
                    location_relays = guard_relays
            else:
                location_relays = guard_relays

            logger.info(f"Analyzing {len(guard_relays)} guard relays ({len(location_relays)} match location)")

            # Step 2: Generate synthetic traffic patterns with location-based characteristics
            traffic_gen = TrafficGenerator(seed=random_seed, location=guard_location)

            similarity_scores = {}
            analysis_db_id = None
            last_detailed = {}
            last_entry_timestamp = None
            last_exit_timestamp = None
            
            # Will add timeline events after we have analysis_id
            timeline_events_queue = []

            # Use location_relays for simulation (prioritize matching location)
            relays_to_simulate = location_relays if location_relays else guard_relays

            for i in range(min(simulation_count, len(relays_to_simulate))):
                # Generate correlated patterns
                entry_pattern, exit_pattern = traffic_gen.generate_correlated_patterns(
                    num_bursts=10,
                    time_jitter=0.2
                )

                # Extract features
                entry_features = self.feature_extractor.extract_features(entry_pattern)
                exit_features = self.feature_extractor.extract_features(exit_pattern)

                # Correlate with a guard relay from the location-filtered list
                guard_relay = relays_to_simulate[i % len(relays_to_simulate)]

                # Calculate correlation score with location matching
                # Note: For simulated mode, we don't need adaptive normalization (patterns are synthetic)
                score, detailed = self.correlation_engine.correlation_score(
                    entry_pattern, exit_pattern,
                    entry_features, exit_features,
                    relay_country=guard_relay.country_name or guard_relay.country,
                    expected_location=guard_location
                )

                last_detailed = detailed

                # Store similarity score for this guard
                fingerprint = guard_relay.fingerprint
                if fingerprint not in similarity_scores:
                    similarity_scores[fingerprint] = []
                similarity_scores[fingerprint].append(score)
                
                # Queue timeline events for later (after we have analysis_id)
                if i % 20 == 0:  # Record every 20th simulation
                    timeline_events_queue.append({
                        'type': 'traffic_generated',
                        'fingerprint': fingerprint,
                        'metadata': {
                            'simulation_num': i + 1,
                            'correlation_score': float(score),
                            'country': guard_relay.country
                        }
                    })

            # Average similarity scores for each guard
            avg_similarity_scores = {
                fp: sum(scores) / len(scores)
                for fp, scores in similarity_scores.items()
            }
            
            # Timeline: correlation analysis phase
            self._create_timeline_event(
                analysis_db_id,
                'correlation_analysis',
                None,
                {'unique_guards_analyzed': len(avg_similarity_scores)}
            )

            # Step 3: Score and rank guards with rebalanced weights
            scorer = ProbabilityScorer()  # Uses new rebalanced default weights

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
            
            # Timeline: scoring phase completed  
            if analysis_db_id:
                self._create_timeline_event(
                    analysis_db_id,
                    'scoring_completed',
                    None,
                    {'total_scored': len(ranked_guards), 'top_n': top_n}
                )

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
            self.db.refresh(result)
            analysis_db_id = result.id
            
            logger.info(f"Analysis saved with DB ID: {analysis_db_id}")
            
            # Timeline: analysis started (now that we have an ID)
            self._create_timeline_event(
                analysis_db_id,
                'analysis_started',
                None,
                {'simulation_count': simulation_count, 'top_n': top_n, 'random_seed': random_seed}
            )
            
            # Add timeline event for data collection phase
            self._create_timeline_event(
                analysis_db_id,
                'data_collection_started',
                None,
                {'guard_count': len(guard_relays)}
            )
            
            # Process queued timeline events from simulation loop
            for event in timeline_events_queue:
                self._create_timeline_event(
                    analysis_db_id,
                    event['type'],
                    event['fingerprint'],
                    event['metadata']
                )

            # Apply iterative learning to top result
            if ranked_guards and last_detailed:
                top_guard = ranked_guards[0]
                feature_vector = {
                    'dtw_score': last_detailed.get('dtw_similarity', 0),
                    'vector_score': last_detailed.get('vector_similarity', 0),
                    'euclidean_score': last_detailed.get('euclidean_similarity', 0),
                    'temporal_score': last_detailed.get('temporal_similarity', 0),
                    'combined_score': avg_similarity_scores.get(top_guard['fingerprint'], 0)
                }

                improved_confidence = self.learner.hybrid_confidence_score(
                    top_guard['fingerprint'],
                    'EXIT_NODE',  # Placeholder
                    top_guard['confidence_score'],
                    feature_vector
                )

                self.learner.record_analysis(
                    analysis_db_id,
                    top_guard['fingerprint'],
                    'EXIT_NODE',
                    improved_confidence,
                    feature_vector
                )

                self._record_node_correlation(
                    analysis_db_id,
                    top_guard['fingerprint'],
                    'EXIT_NODE',
                    avg_similarity_scores.get(top_guard['fingerprint'], 0),
                    self.correlation_engine.calculate_time_delta(last_entry_timestamp, last_exit_timestamp),
                    last_detailed.get('dtw_similarity', 0)
                )

                self._create_timeline_event(
                    analysis_db_id,
                    'entry_observed',
                    top_guard['fingerprint'],
                    {'confidence': improved_confidence, 'country': top_guard.get('country')}
                )

            # Timeline: analysis completed
            self._create_timeline_event(
                analysis_db_id,
                'analysis_completed',
                None,
                {'execution_time': execution_time, 'guards_analyzed': len(guard_relays)}
            )

            logger.info(f"Analysis {analysis_id} completed in {execution_time:.2f}s")
            
            logger.info(f"Returning analysis_db_id: {analysis_db_id}")

            return {
                "analysis_id": analysis_id,
                "analysis_db_id": analysis_db_id,
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

    def _create_timeline_event(self, analysis_id: int, event_type: str,
                               node_fingerprint: str = None, metadata: dict = None):
        """Create a timeline event for analysis tracking"""
        try:
            event = TimelineEvent(
                analysis_id=analysis_id or 0,
                event_type=event_type,
                timestamp=datetime.utcnow(),
                node_fingerprint=node_fingerprint,
                event_metadata=metadata
            )
            self.db.add(event)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to create timeline event: {e}")

    def _record_node_correlation(self, analysis_id: int, entry_fp: str, exit_fp: str,
                                 correlation_score: float, time_delta: int = None,
                                 traffic_similarity: float = None):
        """Record node correlation for forensic analysis"""
        try:
            corr = NodeCorrelation(
                analysis_id=analysis_id,
                entry_fingerprint=entry_fp,
                exit_fingerprint=exit_fp,
                correlation_score=correlation_score,
                time_delta_seconds=time_delta,
                traffic_pattern_similarity=traffic_similarity
            )
            self.db.add(corr)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to record node correlation: {e}")

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

    def run_realtime_analysis(self, client_logs: List[Dict], server_logs: List[Dict], 
                             metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze real-time traffic from honeypot
        
        Args:
            client_logs: Client-side timing logs
            server_logs: Server-side request logs
            metadata: Additional session metadata
            
        Returns:
            Analysis results with guard node identification
        """
        start_time = time.time()
        analysis_id = str(uuid.uuid4())
        
        logger.info(f"Starting real-time analysis {analysis_id}")
        
        try:
            # Validate minimum packet threshold
            min_packets = 50  # Minimum required for statistical significance
            if len(client_logs) < min_packets:
                raise ValueError(
                    f"Insufficient traffic data: {len(client_logs)} packets (minimum {min_packets} required). "
                    "Please capture more traffic before analysis."
                )
            
            # Parse real traffic logs into patterns
            entry_pattern, exit_pattern, parsed_metadata = self.traffic_parser.parse_realtime_request({
                "client_logs": client_logs,
                "server_logs": server_logs,
                "metadata": metadata or {}
            })
            
            # Get exit node info from IP
            exit_ip = parsed_metadata.get("exit_ip")
            exit_node = None
            exit_fingerprint = None
            exit_country = None
            
            if exit_ip:
                logger.info(f"Looking up exit node for IP: {exit_ip}")
                exit_node = self.onionoo_client.get_relay_by_ip(exit_ip)
                if exit_node:
                    exit_fingerprint = exit_node.get("fingerprint")
                    exit_country = exit_node.get("country", "Unknown")
                    exit_nickname = exit_node.get("nickname", "Unknown")
                    logger.info(f"Exit node found: {exit_nickname} ({exit_fingerprint[:16]}...) in {exit_country}")
                else:
                    logger.warning(f"No exit node found for IP: {exit_ip} - geographic scoring will be neutral")
            else:
                logger.warning("No exit IP provided in request - geographic scoring will be neutral")
            
            # Extract features
            entry_features = self.feature_extractor.extract_features(entry_pattern)
            exit_features = self.feature_extractor.extract_features(exit_pattern)
            
            # Get guard relays
            guard_relays = self.relay_service.get_guard_relays()
            if not guard_relays:
                raise ValueError("No guard relays available for analysis")
            
            logger.info(f"Correlating against {len(guard_relays)} guard relays")
            
            # Log bandwidth distribution by country
            country_bw = {}
            for guard in guard_relays:
                country = guard.country or "Unknown"
                bw = guard.bandwidth or 0
                if country not in country_bw:
                    country_bw[country] = []
                country_bw[country].append(bw)
            
            # Show top 5 countries by average bandwidth
            avg_bw = {c: sum(bws)/len(bws)/1e6 for c, bws in country_bw.items() if len(bws) > 5}
            top_bw_countries = sorted(avg_bw.items(), key=lambda x: x[1], reverse=True)[:5]
            logger.info(f"Top 5 countries by avg bandwidth: {[(c, f'{bw:.1f}MB') for c, bw in top_bw_countries]}")
            
            # Build relay metadata list for normalization
            all_relays_metadata = []
            for guard in guard_relays:
                all_relays_metadata.append({
                    "fingerprint": guard.fingerprint,
                    "nickname": guard.nickname,
                    "bandwidth": guard.bandwidth or 0,
                    "uptime": guard.uptime or 0,
                    "consensus_weight": guard.consensus_weight or 0,
                    "country": guard.country,
                    "country_name": guard.country_name
                })
            
            # Phase 1: Collect all DTW distances for adaptive normalization
            from fastdtw import fastdtw
            from scipy.spatial.distance import euclidean
            
            entry_series = np.array(entry_features.get("inter_packet_delays", []))
            all_dtw_distances = []
            
            if len(entry_series) > 0:
                for guard in guard_relays:
                    # Quick DTW distance calculation
                    exit_series = np.array(exit_features.get("inter_packet_delays", []))
                    if len(exit_series) > 0:
                        entry_2d = entry_series.reshape(-1, 1)
                        exit_2d = exit_series.reshape(-1, 1)
                        distance, _ = fastdtw(entry_2d, exit_2d, dist=euclidean)
                        all_dtw_distances.append(distance)
            
            logger.info(f"Collected {len(all_dtw_distances)} DTW distances for adaptive normalization")
            
            # Create scorer instance with rebalanced weights
            scorer = ProbabilityScorer()
            
            # Phase 2: Correlate patterns with each guard using adaptive normalization
            guard_scores = []
            for guard in guard_relays:
                # Use correlation engine with adaptive DTW normalization
                score, detailed = self.correlation_engine.correlation_score(
                    entry_pattern, exit_pattern,
                    entry_features, exit_features,
                    relay_country=guard.country or guard.country_name,
                    all_dtw_distances=all_dtw_distances  # Pass for adaptive normalization
                )
                
                # Calculate geographic score based on exit node location
                # Default to neutral - only adjust if we have strong evidence
                geographic_score = 0.5  # Neutral for all guards by default
                
                # Only apply geographic hints if exit node is known AND in specific country
                # Keep the adjustment very subtle to avoid country bias
                if exit_node:
                    exit_country = exit_node.get("country", "")
                    guard_country = guard.country or ""
                    
                    if exit_country and guard_country:
                        if exit_country.lower() == guard_country.lower():
                            geographic_score = 0.55  # Very subtle boost (was 0.6)
                        # Don't penalize other countries - keep neutral
                    
                    # Log for first few guards to debug
                    if len(guard_scores) < 3:
                        logger.debug(f"Guard {guard.nickname} ({guard_country}): "
                                   f"exit_country={exit_country}, geo_score={geographic_score:.2f}")
                
                # Build relay metadata for this guard
                relay_metadata = {
                    "fingerprint": guard.fingerprint,
                    "nickname": guard.nickname,
                    "bandwidth": guard.bandwidth or 0,
                    "uptime": guard.uptime or 0,
                    "consensus_weight": guard.consensus_weight or 0,
                    "country": guard.country
                }
                
                # Score guard node with geographic factor
                prob_score, components = scorer.calculate_relay_score(
                    score,
                    relay_metadata,
                    all_relays_metadata,
                    geographic_score=geographic_score
                )
                
                guard_scores.append({
                    "fingerprint": guard.fingerprint,
                    "nickname": guard.nickname,
                    "probability": prob_score,
                    "correlation_score": score,
                    "bandwidth": guard.bandwidth,
                    "country": guard.country,
                    "components": components  # Add component scores for debugging
                })
            
            # Sort by probability
            guard_scores.sort(key=lambda x: x["probability"], reverse=True)
            top_guards = guard_scores[:10]
            
            # Log detailed analysis for top 5 guards
            logger.info("="*60)
            logger.info("TOP 5 GUARD ANALYSIS BREAKDOWN:")
            for i, g in enumerate(top_guards[:5], 1):
                comp = guard_scores[guard_scores.index(g)].get("components", {})
                logger.info(f"#{i}: {g['nickname']} ({g['country']}) - {g['probability']*100:.2f}%")
                logger.info(f"  Correlation: {g.get('correlation_score', 0):.4f} (weighted: {comp.get('weighted_similarity', 0):.4f})")
                logger.info(f"  Bandwidth: {comp.get('raw_bandwidth', 0)/1e6:.1f}MB (norm: {comp.get('normalized_bandwidth', 0):.3f}, weighted: {comp.get('weighted_bandwidth', 0):.4f})")
                logger.info(f"  Consensus: {comp.get('raw_consensus', 0):.6f} (norm: {comp.get('normalized_consensus', 0):.3f}, weighted: {comp.get('weighted_consensus', 0):.4f})")
                logger.info(f"  Geographic: {comp.get('geographic_score', 0):.3f} (weighted: {comp.get('weighted_geographic', 0):.4f})")
            
            # Log country distribution in top 10
            country_counts = {}
            for g in top_guards:
                country = g.get("country", "Unknown")
                country_counts[country] = country_counts.get(country, 0) + 1
            logger.info(f"Country distribution in top 10: {country_counts}")
            logger.info("="*60)
            
            execution_time = time.time() - start_time
            
            result = {
                "analysis_id": analysis_id,
                "mode": "real",
                "ranked_guards": top_guards,
                "exit_node": {
                    "ip": exit_ip,
                    "fingerprint": exit_fingerprint,
                    "details": exit_node
                } if exit_node else None,
                "statistics": {
                    "total_guards_analyzed": len(guard_relays),
                    "entry_packets": entry_pattern["total_packets"],
                    "exit_packets": exit_pattern["total_packets"],
                    "traffic_duration": entry_pattern["duration"],
                    "top_guard_probability": top_guards[0]["probability"] if top_guards else 0
                },
                "patterns": {
                    "entry": entry_pattern,
                    "exit": exit_pattern
                },
                "execution_time": execution_time,
                "metadata": parsed_metadata
            }
            
            # Store real-time analysis result in database
            self._store_realtime_result(result)
            
            logger.info(f"Real-time analysis complete. Top guard: {top_guards[0]['fingerprint'] if top_guards else 'None'} "
                       f"({top_guards[0]['probability']:.2%} probability)")
            
            return result
            
        except Exception as e:
            logger.error(f"Real-time analysis failed: {e}")
            raise
    
    def _store_realtime_result(self, result: Dict[str, Any]):
        """Store real-time analysis result for dashboard display"""
        try:
            from sqlalchemy import text
            import json
            
            query = text("""
                INSERT INTO traffic_uploads 
                (upload_id, filename, parsed_entry_patterns, parsed_exit_patterns, 
                 exit_node_fingerprint, exit_node_ip, metadata, status)
                VALUES (:upload_id, :filename, :entry_patterns, :exit_patterns,
                        :exit_fingerprint, :exit_ip, :metadata, 'analyzed')
            """)
            
            self.db.execute(
                query,
                {
                    "upload_id": result["analysis_id"],
                    "filename": "realtime_capture",
                    "entry_patterns": json.dumps(result.get("patterns", {}).get("entry", {})),
                    "exit_patterns": json.dumps(result.get("patterns", {}).get("exit", {})),
                    "exit_fingerprint": result.get("exit_node", {}).get("fingerprint") if result.get("exit_node") else None,
                    "exit_ip": result.get("exit_node", {}).get("ip") if result.get("exit_node") else None,
                    "metadata": json.dumps({
                        "ranked_guards": result.get("ranked_guards", []),
                        "statistics": result.get("statistics", {}),
                        "execution_time": result.get("execution_time"),
                        "mode": "real"
                    })
                }
            )
            self.db.commit()
            logger.info(f"Stored real-time analysis result: {result['analysis_id']}")
        except Exception as e:
            logger.error(f"Failed to store real-time result: {e}")
            self.db.rollback()
    
    def get_realtime_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent real-time analysis results with IST timestamps"""
        try:
            from sqlalchemy import text
            import json
            from datetime import timedelta
            
            query = text("""
                SELECT upload_id, filename, exit_node_fingerprint, exit_node_ip, 
                       metadata, upload_timestamp, status
                FROM traffic_uploads
                WHERE status = 'analyzed'
                ORDER BY upload_timestamp DESC
                LIMIT :limit
            """)
            
            results = self.db.execute(query, {"limit": limit}).fetchall()
            
            analyses = []
            for row in results:
                metadata = row[4] if isinstance(row[4], dict) else json.loads(row[4]) if row[4] else {}
                
                # Convert UTC to IST (UTC+5:30)
                utc_time = row[5]
                ist_time = None
                if utc_time:
                    ist_time = utc_time + timedelta(hours=5, minutes=30)
                
                analyses.append({
                    "analysis_id": row[0],
                    "mode": "real",
                    "exit_fingerprint": row[2],
                    "exit_ip": row[3],
                    "ranked_guards": metadata.get("ranked_guards", []),
                    "statistics": metadata.get("statistics", {}),
                    "execution_time": metadata.get("execution_time"),
                    "created_at": ist_time.isoformat() if ist_time else None,
                    "created_at_ist": ist_time.strftime("%Y-%m-%d %H:%M:%S IST") if ist_time else None,
                    "status": row[6]
                })
            
            return analyses
        except Exception as e:
            logger.error(f"Failed to get real-time analyses: {e}")
            return []

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
