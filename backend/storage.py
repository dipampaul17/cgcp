"""
DuckDB Storage Layer for Claude Governance Control Plane
Provides persistent storage for events, policies, and metrics
"""

import duckdb
from typing import Optional


def init_db(db_path: str = 'governance.db') -> duckdb.DuckDBPyConnection:
    """
    Initialize DuckDB database with required tables
    """
    conn = duckdb.connect(db_path)
    
    # Create events table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id VARCHAR PRIMARY KEY,
            timestamp TIMESTAMP,
            user_id VARCHAR,
            org_id VARCHAR,
            surface VARCHAR,
            tier VARCHAR,
            prompt TEXT,
            completion TEXT,
            risk_scores JSON,
            tags JSON,
            model_version VARCHAR,
            action VARCHAR,
            asl_triggered BOOLEAN DEFAULT FALSE
        )
    """)
    
    # Create policy actions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS policy_actions (
            action_id VARCHAR PRIMARY KEY,
            event_id VARCHAR REFERENCES events(event_id),
            action VARCHAR,
            asl_level INTEGER,
            policy_version VARCHAR,
            reason TEXT,
            timestamp TIMESTAMP
        )
    """)
    
    # Create policy history table for audit trail
    conn.execute("""
        CREATE TABLE IF NOT EXISTS policy_history (
            change_id VARCHAR PRIMARY KEY,
            category VARCHAR,
            tier VARCHAR,
            old_threshold DOUBLE,
            new_threshold DOUBLE,
            changed_by VARCHAR,
            timestamp TIMESTAMP
        )
    """)
    
    # Create metrics table for time-series data
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            metric_id VARCHAR PRIMARY KEY,
            timestamp TIMESTAMP,
            metric_type VARCHAR,
            metric_value JSON
        )
    """)
    
    return conn


class StorageManager:
    """Manages database connections and operations"""
    
    def __init__(self, db_path: str = 'governance.db'):
        self.db_path = db_path
        self.conn = init_db(db_path)
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close() 