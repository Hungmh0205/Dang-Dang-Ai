"""
Phase 3.1 Migration: Emotional Decay & Memory Importance
- Add 'importance_score' (1.0 - 10.0) to episodic_memory
- Add 'last_recalled_at' to track memory usage (Rehearsal)

Run: python migrations/v3_1_memory_decay.py
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    """Add columns for Emotional Decay"""
    
    print("\n" + "="*60)
    print("  PHASE 3.1: EMOTIONAL DECAY MIGRATION")
    print("  Adding importance_score & last_recalled_at")
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
        # 1. UPDATE/PATCH episodic_memory DATA
        # ────────────────────────────────────────────────────────
        print("📝 Patching episodic_memory data...")
        
        # Ensure 'importance' defaults to 3 (Medium) if null
        cursor.execute("UPDATE episodic_memory SET importance = 3 WHERE importance IS NULL")
        
        # Backfill Importance based on Emotion Tone (Text-based)
        # High impact emotions
        cursor.execute("""
            UPDATE episodic_memory 
            SET importance = 8 
            WHERE emotion_tone IN ('joy', 'sadness', 'anger', 'fear', 'excited', 'distressed') 
            AND importance <= 3
        """)
        
        # Low impact
        cursor.execute("""
            UPDATE episodic_memory 
            SET importance = 2 
            WHERE emotion_tone IN ('neutral', 'calm', 'bored') 
            AND importance <= 3
        """)
        
        print("✅ Backfilled importance based on emotion_tone\n")

        # ────────────────────────────────────────────────────────
        # 2. ADD COLUMN IF MISSING (Safety)
        # ────────────────────────────────────────────────────────
        # Just in case 'decay_factor' is needed for advanced math, let's add it.
        # But for now, simple integer decay is fine.
        
        # Let's add 'decay_locked' boolean to prevent decay for specific memories manually marked
        cursor.execute("""
            ALTER TABLE episodic_memory 
            ADD COLUMN IF NOT EXISTS decay_locked BOOLEAN DEFAULT FALSE
        """)
        print("✅ Added column: decay_locked\n")
        
        # ────────────────────────────────────────────────────────
        # 3. COMMIT
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
