"""
Reset Database Script
Clears all data from the governance database for clean demo runs
"""

import duckdb
import os


def reset_database(db_path: str = "governance.db"):
    """Reset the governance database by dropping and recreating all tables"""
    
    print("🗑️  Resetting governance database...")
    
    try:
        # Connect to database
        conn = duckdb.connect(db_path)
        
        # Drop existing tables in correct order (handle foreign key constraints)
        tables = ['policy_actions', 'policy_history', 'metrics', 'events']  # events last due to FK
        for table in tables:
            try:
                conn.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"  ✓ Dropped table: {table}")
            except Exception as e:
                print(f"  ⚠️  Could not drop {table}: {e}")
        
        # Recreate tables
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
        print("  ✓ Created events table")
        
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
        print("  ✓ Created policy_actions table")
        
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
        print("  ✓ Created policy_history table")
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                metric_id VARCHAR PRIMARY KEY,
                timestamp TIMESTAMP,
                metric_type VARCHAR,
                metric_value JSON
            )
        """)
        print("  ✓ Created metrics table")
        
        # Verify
        result = conn.execute("SELECT COUNT(*) FROM events").fetchone()
        print(f"\n✅ Database reset complete. Events table has {result[0]} records.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # Also remove any WAL files
    if os.path.exists("governance.db.wal"):
        try:
            os.remove("governance.db.wal")
            print("  ✓ Removed WAL file")
        except:
            pass
    
    reset_database() 