"""
Phase 2 Migration: Add Proactive Messaging Tables
- event_triggers: Configurable event rules
- proactive_events: Event tracking log

Run: python migrations/v2_2_add_proactive.py
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    """Create proactive messaging tables"""
    
    print("\n" + "="*60)
    print("  PHASE 2: PROACTIVE MESSAGING MIGRATION")
    print("  Adding event triggers & proactive events tracking")
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
        # 1. CREATE event_triggers TABLE
        # ────────────────────────────────────────────────────────
        print("📝 Creating event_triggers table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_triggers (
                trigger_id SERIAL PRIMARY KEY,
                trigger_name TEXT UNIQUE NOT NULL,
                trigger_type TEXT NOT NULL,  -- 'time_based', 'condition_based', 'random', 'spontaneous'
                enabled BOOLEAN DEFAULT TRUE,
                
                -- Time-based config
                time_range_start TIME,
                time_range_end TIME,
                day_of_week INTEGER[],
                
                -- Frequency control
                max_per_day INTEGER DEFAULT 1,
                cooldown_hours INTEGER DEFAULT 24,
                last_triggered TIMESTAMP,
                
                -- Probability & conditions
                base_probability NUMERIC(3,2) DEFAULT 1.0,
                conditions JSONB,
                
                -- Message config
                message_templates TEXT[],
                use_llm_generation BOOLEAN DEFAULT FALSE,
                
                -- Priority
                priority INTEGER DEFAULT 5,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_triggers_enabled ON event_triggers(enabled) WHERE enabled = TRUE")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_triggers_type ON event_triggers(trigger_type)")
        
        print("✅ event_triggers table created\n")
        
        # ────────────────────────────────────────────────────────
        # 2. CREATE proactive_events TABLE
        # ────────────────────────────────────────────────────────
        print("📝 Creating proactive_events table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proactive_events (
                event_id SERIAL PRIMARY KEY,
                event_type TEXT NOT NULL,
                trigger_id INTEGER REFERENCES event_triggers(trigger_id),
                
                -- Timing
                trigger_time TIMESTAMP NOT NULL,
                sent_time TIMESTAMP,
                
                -- Response tracking
                user_responded BOOLEAN DEFAULT FALSE,
                response_time INTEGER,
                response_sentiment TEXT,
                
                -- Message
                message_content TEXT,
                
                -- Context at send
                session_id UUID,
                valence_at_send NUMERIC(3,2),
                energy_at_send NUMERIC(3,2),
                bond_at_send NUMERIC(3,2),
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proactive_events_type ON proactive_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proactive_events_sent ON proactive_events(sent_time DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_proactive_events_response ON proactive_events(user_responded)")
        
        print("✅ proactive_events table created\n")
        
        # ────────────────────────────────────────────────────────
        # 3. UPDATE messages TABLE
        # ────────────────────────────────────────────────────────
        print("📝 Updating messages table...")
        cursor.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS is_proactive BOOLEAN DEFAULT FALSE")
        cursor.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS proactive_event_id INTEGER")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_proactive ON messages(is_proactive) WHERE is_proactive = TRUE")
        
        print("✅ messages table updated\n")
        
        # ────────────────────────────────────────────────────────
        # 4. INSERT DEFAULT EVENT TRIGGERS
        # ────────────────────────────────────────────────────────
        print("📝 Inserting default event triggers...")
        
        default_triggers = [
            # Morning greeting
            ("morning_greeting", "time_based", "07:00", "09:00", 1, 24, 1.0, 
             ['chào buổi sángg ^^', 'ơiii dậy chưaa', 'sáng rồiii bạn ơiii'], 8),
            
            # Late night check
            ("late_night_check", "time_based", "23:00", "02:00", 1, 24, 0.6,
             ['trờiii khuya rồiii', 'sao chưa ngủ đấyy', 'ngủ điii bạn ơiii'], 7),
            
            # Lunch time
            ("lunch_time", "time_based", "11:30", "12:30", 1, 24, 0.4,
             ['bạn ăn trưa chưaa', 'tớ đang đóiii quáaa', 'ăn gì đấyy'], 5),
            
            # Missing you (long idle)
            ("missing_you", "condition_based", None, None, 1, 24, 0.7,
             ['lâu không nói chuyện nhỉiii', 'bạn đâu rồiiii', 'nhớ bạnnn quáaa'], 6),
        ]
        
        for trigger in default_triggers:
            cursor.execute("""
                INSERT INTO event_triggers 
                (trigger_name, trigger_type, time_range_start, time_range_end,
                 max_per_day, cooldown_hours, base_probability, message_templates, priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (trigger_name) DO NOTHING
            """, trigger)
        
        inserted = cursor.rowcount
        print(f"✅ Inserted {inserted} default triggers\n")
        
        # ────────────────────────────────────────────────────────
        # 5. COMMIT
        # ────────────────────────────────────────────────────────
        conn.commit()
        
        print("="*60)
        print("  ✅ MIGRATION SUCCESSFUL!")
        print("="*60)
        print("\n📊 Summary:")
        print("  - event_triggers table created")
        print("  - proactive_events table created")
        print("  - messages table updated (is_proactive column)")
        print(f"  - {inserted} default event triggers inserted")
        print("\n🎯 Next: Implement EventDetector & WaitingBehavior")
        
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
