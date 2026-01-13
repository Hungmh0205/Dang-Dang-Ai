"""
Phase 3.3 Migration: User Pattern Detection
- Add 'user_patterns' table to store detected habits and behavioral trends.

Run: python migrations/v3_3_user_patterns.py
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    """Add user_patterns table"""
    
    print("\n" + "="*60)
    print("  PHASE 3.3: PATTERN DETECTION MIGRATION")
    print("  Adding user_patterns table")
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
        # 1. CREATE user_patterns TABLE
        # ────────────────────────────────────────────────────────
        print("📝 Creating user_patterns table...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_patterns (
                id SERIAL PRIMARY KEY,
                pattern_type VARCHAR(50), -- 'habit', 'emotional', 'preference'
                description TEXT NOT NULL, -- "User thường than mệt vào thứ 2"
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confidence_score FLOAT DEFAULT 0.5, -- 0.0 to 1.0
                frequency INTEGER DEFAULT 1 -- Số lần xuất hiện/quan sát
            )
        """)
        
        # Add constraint to avoid duplicate descriptions overlapping too much
        # (Though text matching is hard, we rely on ID for now)
        
        print("✅ Table created: user_patterns\n")
        
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
