"""
Phase 1 Migration: Add Temporal Intelligence Tables
- conversation_sessions: Track chat sessions
- daily_summaries: Store daily memory consolidations

Run: python migrations/v2_1_add_sessions.py
"""

import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def migrate():
    """Create new tables for temporal intelligence"""
    
    print("\n" + "="*60)
    print("  PHASE 1: TEMPORAL INTELLIGENCE MIGRATION")
    print("  Adding session tracking & daily summaries")
    print("="*60 + "\n")
    
    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'dangdang_db'),
            user=os.getenv('DB_USER', 'dangdang'),
            password=os.getenv('DB_PASSWORD', '')
        )
        print("✅ Connected to PostgreSQL\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}\n")
        print("💡 Fix: Check if Docker container is running:")
        print("   docker-compose ps")
        print("   docker-compose restart")
        return False
    
    cursor = conn.cursor()
    
    try:
        # ────────────────────────────────────────────────────────
        # 1. CREATE conversation_sessions TABLE
        # ────────────────────────────────────────────────────────
        print("📝 Creating conversation_sessions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_sessions (
                session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                day_date DATE NOT NULL,
                session_type TEXT,  -- 'morning', 'afternoon', 'evening', 'night'
                message_count INTEGER DEFAULT 0,
                avg_valence NUMERIC(3,2),
                avg_energy NUMERIC(3,2),
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_date ON conversation_sessions(day_date DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_type ON conversation_sessions(session_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON conversation_sessions(start_time DESC)")
        
        print("✅ conversation_sessions table created with indices\n")
        
        # ────────────────────────────────────────────────────────
        # 2. CREATE daily_summaries TABLE
        # ────────────────────────────────────────────────────────
        print("📝 Creating daily_summaries table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summaries (
                summary_date DATE PRIMARY KEY,
                session_count INTEGER,
                total_messages INTEGER,
                emotional_summary TEXT,
                key_topics TEXT[],
                memorable_moments TEXT[],
                valence_avg NUMERIC(3,2),
                energy_avg NUMERIC(3,2),
                bond_avg NUMERIC(3,2),
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                consolidation_method TEXT DEFAULT 'rule_based'
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_summaries_date ON daily_summaries(summary_date DESC)")
        
        print("✅ daily_summaries table created\n")
        
        # ────────────────────────────────────────────────────────
        # 3. UPDATE messages TABLE
        # ────────────────────────────────────────────────────────
        print("📝 Updating messages table with session columns...")
        cursor.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS session_id UUID")
        cursor.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS day_date DATE")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(day_date DESC)")
        
        print("✅ messages table updated\n")
        
        # ────────────────────────────────────────────────────────
        # 4. UPDATE episodic_memory TABLE
        # ────────────────────────────────────────────────────────
        print("📝 Updating episodic_memory table...")
        cursor.execute("ALTER TABLE episodic_memory ADD COLUMN IF NOT EXISTS session_id UUID")
        cursor.execute("ALTER TABLE episodic_memory ADD COLUMN IF NOT EXISTS day_date DATE")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodic_session ON episodic_memory(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodic_date ON episodic_memory(day_date DESC)")
        
        print("✅ episodic_memory table updated\n")
        
        # ────────────────────────────────────────────────────────
        # 5. BACKFILL day_date FOR EXISTING RECORDS
        # ────────────────────────────────────────────────────────
        print("📝 Backfilling day_date for existing records...")
        
        # Update messages
        cursor.execute("""
            UPDATE messages 
            SET day_date = DATE(timestamp) 
            WHERE day_date IS NULL AND timestamp IS NOT NULL
        """)
        updated_messages = cursor.rowcount
        
        # Update episodic_memory
        cursor.execute("""
            UPDATE episodic_memory 
            SET day_date = DATE(timestamp) 
            WHERE day_date IS NULL AND timestamp IS NOT NULL
        """)
        updated_episodes = cursor.rowcount
        
        print(f"✅ Backfilled {updated_messages} messages and {updated_episodes} episodes\n")
        
        # ────────────────────────────────────────────────────────
        # 6. COMMIT ALL CHANGES
        # ────────────────────────────────────────────────────────
        conn.commit()
        
        print("="*60)
        print("  ✅ MIGRATION SUCCESSFUL!")
        print("="*60)
        print("\n📊 Summary:")
        print("  - conversation_sessions table created")
        print("  - daily_summaries table created")
        print("  - messages table updated with session tracking")
        print("  - episodic_memory table updated")
        print(f"  - {updated_messages} messages backfilled")
        print(f"  - {updated_episodes} episodes backfilled")
        print("\n🎯 Next: Implement SessionManager class")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
    
    finally:
        cursor.close()
        conn.close()


def verify():
    """Verify migration success"""
    print("\n🔍 Verifying migration...\n")
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'dangdang_db'),
            user=os.getenv('DB_USER', 'dangdang'),
            password=os.getenv('DB_PASSWORD', '')
        )
        cursor = conn.cursor()
        
        # Check tables exist
        tables = ['conversation_sessions', 'daily_summaries']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table}: {count} rows")
        
        # Check new columns
        cursor.execute("SELECT COUNT(*) FROM messages WHERE day_date IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"  ✅ messages.day_date: {count} rows filled")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Verification complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    if migrate():
        verify()
    else:
        print("\n💡 Troubleshooting:")
        print("  1. Ensure PostgreSQL is running: docker-compose ps")
        print("  2. Check .env file has correct credentials")
        print("  3. Try restarting: docker-compose restart")
