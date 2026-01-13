"""
Phase 3.2 Migration: Meta-Cognition & Response Quality
- Add 'response_quality' table to track self-reflection scores.

Run: python migrations/v3_2_meta_cognition.py
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    """Add response_quality table"""
    
    print("\n" + "="*60)
    print("  PHASE 3.2: META-COGNITION MIGRATION")
    print("  Adding response_quality table")
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
        # 1. CREATE response_quality TABLE
        # ────────────────────────────────────────────────────────
        print("📝 Creating response_quality table...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS response_quality (
                id SERIAL PRIMARY KEY,
                message_id INTEGER, -- FK to messages table (model response)
                relevance_score INTEGER, -- 1-5
                creativity_score INTEGER, -- 1-5
                personality_score INTEGER, -- 1-5 (How much like Dang Dang?)
                critique TEXT, -- Short text critique
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_msg ON response_quality(message_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_time ON response_quality(timestamp DESC)")
        
        print("✅ Table created: response_quality\n")
        
        # ────────────────────────────────────────────────────────
        # 2. COMMIT
        # ────────────────────────────────────────────────────────
        conn.commit()
        
        print("="*60)
        print("  ✅ MIGRATION SUCCESSFUL!")
        print("="*60)
        
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
