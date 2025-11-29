"""
Mapping Write Detector
Monitors for unauthorized writes to mapping resources
Runs as a background job to detect violations and alert admins
"""

import os
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class MappingDetector:
    """
    Detects unauthorized writes to mapping resources.
    
    Monitors:
    1. OrchestratorAudit table for mapping_write_blocked events
    2. File modification times on mapping CSV files
    3. Database table row counts for mapping tables
    """
    
    def __init__(self, database_url: str = None, data_dir: str = "data"):
        self.database_url = database_url or os.getenv("DATABASE_URL", "sqlite:///./terminology.db")
        self.data_dir = Path(data_dir)
        self.engine = create_engine(self.database_url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Baseline file modification times
        self.baseline_mtimes: Dict[str, float] = {}
        self.baseline_row_counts: Dict[str, int] = {}
        
        # Initialize baselines
        self._initialize_baselines()
    
    def _initialize_baselines(self):
        """Initialize baseline modification times and row counts"""
        # File baselines
        mapping_files = [
            self.data_dir / "namaste.csv",
            self.data_dir / "icd11_codes.csv",
            self.data_dir / "faiss_index.bin",
            self.data_dir / "reranker.joblib"
        ]
        
        for file_path in mapping_files:
            if file_path.exists():
                self.baseline_mtimes[str(file_path)] = file_path.stat().st_mtime
                logger.info(f"Baseline mtime for {file_path.name}: {datetime.fromtimestamp(file_path.stat().st_mtime)}")
        
        # Database table baselines
        try:
            session = self.SessionLocal()
            
            mapping_tables = ['ayush_terms', 'mapping_candidates', 'icd_codes']
            for table in mapping_tables:
                try:
                    result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    self.baseline_row_counts[table] = count
                    logger.info(f"Baseline row count for {table}: {count}")
                except Exception as e:
                    logger.warning(f"Could not get baseline for table {table}: {str(e)}")
            
            session.close()
        except Exception as e:
            logger.error(f"Error initializing database baselines: {str(e)}")
    
    def check_audit_logs(self, since_minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Check OrchestratorAudit for mapping_write_blocked events
        
        Args:
            since_minutes: Check logs from last N minutes
            
        Returns:
            List of blocked write events
        """
        try:
            session = self.SessionLocal()
            
            since_time = datetime.utcnow() - timedelta(minutes=since_minutes)
            
            query = text("""
                SELECT id, action, actor, resource_target, payload_summary, timestamp, error_message
                FROM orchestrator_audit
                WHERE action = 'mapping_write_blocked'
                AND timestamp >= :since_time
                ORDER BY timestamp DESC
            """)
            
            results = session.execute(query, {"since_time": since_time}).fetchall()
            session.close()
            
            events = []
            for row in results:
                events.append({
                    'id': row[0],
                    'action': row[1],
                    'actor': row[2],
                    'resource_target': row[3],
                    'payload_summary': row[4],
                    'timestamp': row[5],
                    'error_message': row[6]
                })
            
            if events:
                logger.warning(f"Found {len(events)} mapping write blocked events in last {since_minutes} minutes")
            
            return events
            
        except Exception as e:
            logger.error(f"Error checking audit logs: {str(e)}")
            return []
    
    def check_file_modifications(self) -> List[Dict[str, Any]]:
        """
        Check if mapping files have been modified since baseline
        
        Returns:
            List of modified files
        """
        violations = []
        
        for file_path_str, baseline_mtime in self.baseline_mtimes.items():
            file_path = Path(file_path_str)
            
            if not file_path.exists():
                logger.warning(f"Mapping file missing: {file_path}")
                violations.append({
                    'type': 'file_missing',
                    'file': str(file_path),
                    'baseline_mtime': baseline_mtime
                })
                continue
            
            current_mtime = file_path.stat().st_mtime
            
            if current_mtime > baseline_mtime:
                logger.critical(f"MAPPING FILE MODIFIED: {file_path}")
                logger.critical(f"  Baseline: {datetime.fromtimestamp(baseline_mtime)}")
                logger.critical(f"  Current:  {datetime.fromtimestamp(current_mtime)}")
                
                violations.append({
                    'type': 'file_modified',
                    'file': str(file_path),
                    'baseline_mtime': baseline_mtime,
                    'current_mtime': current_mtime,
                    'baseline_time': datetime.fromtimestamp(baseline_mtime).isoformat(),
                    'current_time': datetime.fromtimestamp(current_mtime).isoformat()
                })
        
        return violations
    
    def check_table_row_counts(self) -> List[Dict[str, Any]]:
        """
        Check if mapping table row counts have changed
        
        Returns:
            List of tables with changed row counts
        """
        violations = []
        
        try:
            session = self.SessionLocal()
            
            for table, baseline_count in self.baseline_row_counts.items():
                try:
                    result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    current_count = result.scalar()
                    
                    if current_count != baseline_count:
                        logger.critical(f"MAPPING TABLE ROW COUNT CHANGED: {table}")
                        logger.critical(f"  Baseline: {baseline_count}")
                        logger.critical(f"  Current:  {current_count}")
                        
                        violations.append({
                            'type': 'table_row_count_changed',
                            'table': table,
                            'baseline_count': baseline_count,
                            'current_count': current_count,
                            'delta': current_count - baseline_count
                        })
                except Exception as e:
                    logger.error(f"Error checking table {table}: {str(e)}")
            
            session.close()
        except Exception as e:
            logger.error(f"Error checking table row counts: {str(e)}")
        
        return violations
    
    def run_detection(self) -> Dict[str, Any]:
        """
        Run full detection sweep
        
        Returns:
            Dict with detection results
        """
        logger.info("Running mapping write detection sweep...")
        
        # Check all violation types
        audit_events = self.check_audit_logs(since_minutes=5)
        file_violations = self.check_file_modifications()
        table_violations = self.check_table_row_counts()
        
        total_violations = len(audit_events) + len(file_violations) + len(table_violations)
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_violations': total_violations,
            'audit_events': audit_events,
            'file_violations': file_violations,
            'table_violations': table_violations,
            'status': 'VIOLATION_DETECTED' if total_violations > 0 else 'OK'
        }
        
        if total_violations > 0:
            logger.critical(f"MAPPING VIOLATION DETECTED: {total_violations} violations found")
            self._send_alert(results)
        else:
            logger.info("✓ No mapping violations detected")
        
        return results
    
    def _send_alert(self, results: Dict[str, Any]):
        """
        Send alert to admin (placeholder for email/Slack integration)
        
        Args:
            results: Detection results
        """
        logger.critical("=" * 80)
        logger.critical("MAPPING WRITE VIOLATION ALERT")
        logger.critical("=" * 80)
        logger.critical(f"Total violations: {results['total_violations']}")
        logger.critical(f"Audit events: {len(results['audit_events'])}")
        logger.critical(f"File violations: {len(results['file_violations'])}")
        logger.critical(f"Table violations: {len(results['table_violations'])}")
        logger.critical("=" * 80)
        
        # TODO: Implement actual notification (email, Slack, PagerDuty, etc.)
        # For now, just log critically
    
    def reset_baselines(self):
        """Reset baselines to current state (admin only)"""
        logger.warning("Resetting mapping detector baselines...")
        self._initialize_baselines()
        logger.info("Baselines reset complete")


def run_detector_job():
    """
    Run detector as a standalone job (can be called by cron)
    """
    detector = MappingDetector()
    results = detector.run_detection()
    
    # Exit with error code if violations detected
    if results['total_violations'] > 0:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    # Run detector when executed directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_detector_job()
