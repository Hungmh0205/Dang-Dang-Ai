"""
Phase 3 (V3.0) Migration: The Soul Update
- relationship_state: Tracks Level, XP, Trust, Respect, and Days Active
- core_memories: Tracks significant emotional events for milestones

Run: python migrations/v3_0_soul_update.py
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    """Create Soul Update tables"""
    
    print("\n" + "="*60)
    print("  PHASE 3: THE SOUL UPDATE (V3.0) MIGRATION")
    print("  Adding relationship state & core memories")
    print("="*60 + "\n")
    
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
        print(f"❌ Connection failed: {e}")
        return False
    
    cursor = conn.cursor()
    
    try:
        # ────────────────────────────────────────────────────────
        # 1. CREATE relationship_state TABLE
        # ────────────────────────────────────────────────────────
        print("📝 Creating relationship_state table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationship_state (
                id SERIAL PRIMARY KEY,
                user_id TEXT UNIQUE DEFAULT 'user',
                
                -- Growth Stats
                level INTEGER DEFAULT 1,
                current_xp INTEGER DEFAULT 0,
                total_xp INTEGER DEFAULT 0,
                
                -- Relationship Meters (0.0 - 1.0)
                trust_score NUMERIC(3,2) DEFAULT 0.5,
                respect_score NUMERIC(3,2) DEFAULT 0.5,
                
                -- Time Gating
                days_active INTEGER DEFAULT 1,
                last_interaction_date DATE DEFAULT CURRENT_DATE,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default row if not exists
        cursor.execute("""
            INSERT INTO relationship_state (user_id) 
            VALUES ('user') 
            ON CONFLICT (user_id) DO NOTHING
        """)
        
        print("✅ relationship_state table created & initialized\n")
        
        # ────────────────────────────────────────────────────────
        # 2. CREATE core_memories TABLE (Emotional Milestones)
        # ────────────────────────────────────────────────────────
        print("📝 Creating core_memories table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS core_memories (
                memory_id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                
                -- Metadata
                memory_type TEXT, -- 'milestone', 'bonding', 'conflict', 'realization'
                emotional_impact INTEGER DEFAULT 5, -- 1-10 scale
                
                -- Context
                related_level INTEGER, -- Level when this happened
                session_id UUID,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_core_memories_type ON core_memories(memory_type)")
        
        print("✅ core_memories table created\n")
        
        # ────────────────────────────────────────────────────────
        # 3. COMMIT
        # ────────────────────────────────────────────────────────
        conn.commit()
        
        print("="*60)
        print("  ✅ MIGRATION SUCCESSFUL!")
        print("="*60)
        print("\n📊 Summary:")
        print("  - relationship_state table created (with default user)")
        print("  - core_memories table created")
        print("\n🎯 Next: Implement Core Logic (GrowthManager & SentimentArbiter)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
    
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    migrate()
