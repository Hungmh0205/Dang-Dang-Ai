import psycopg2
import os
from dotenv import load_dotenv
import importlib.util
import sys

# Load env vars
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'dangdang_db'),
    'user': os.getenv('DB_USER', 'dangdang'),
    'password': os.getenv('DB_PASSWORD', '')
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def run_migration_file(file_path):
    print(f"👉 Running migration: {file_path}")
    spec = importlib.util.spec_from_file_location("migration_module", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["migration_module"] = module
    spec.loader.exec_module(module)
    if hasattr(module, 'migrate'):
        success = module.migrate()
        if success:
            print(f"✅ Migration successful: {file_path}")
        else:
            print(f"❌ Migration failed: {file_path}")
            return False
    else:
        print(f"⚠️ No 'migrate' function found in {file_path}")
    return True

def reset_database():
    print("🔥 INITIATING DATABASE SELF-DESTRUCTION & REBIRTH 🔥")
    print("Warning: All data will be lost.")
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # 1. DROP EVERYTHING
        print("🧹 Dropping all tables...")
        cursor.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        conn.commit()
        print("   ✅ Tables dropped.")
        
        # 2. CREATE BASE SCHEMA (Adapted from migrate_sqlite_to_postgres.py)
        print("🏗️ Recreating Base Schema...")
        
        # Bot State
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_state (
                id INTEGER PRIMARY KEY,
                valence NUMERIC(3,2),
                energy NUMERIC(3,2),
                bond NUMERIC(3,2),
                last_reflection TEXT
            )
        """)
        # Initialize default bot state
        cursor.execute("INSERT INTO bot_state (id, valence, energy, bond) VALUES (1, 0.1, 0.8, 0.1)")

        # Messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC)")
        
        # Profile
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                key TEXT PRIMARY KEY,
                value TEXT,
                confidence NUMERIC(3,2)
            )
        """)
        
        # Episodic Memory
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                importance INTEGER,
                emotion_tone TEXT,
                is_core INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodic_importance ON episodic_memory(importance DESC, is_core DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodic_emotion ON episodic_memory(emotion_tone)")

        # Self Image
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS self_image (
                trait TEXT PRIMARY KEY,
                strength NUMERIC(3,2)
            )
        """)
        # Initialize default self image
        cursor.execute("INSERT INTO self_image (trait, strength) VALUES ('Vui vẻ', 0.8), ('Nghịch ngợm', 0.9), ('Sâu sắc', 0.5)")

        # Memory Meta
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Schema Version
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        cursor.execute("INSERT INTO schema_version (version, description) VALUES (1, 'Initial Schema')")
        
        conn.commit()
        print("   ✅ Base Schema Created.")
        cursor.close()
        conn.close()

        # 3. RUN MIGRATIONS
        print("🚀 Applying Migrations...")
        migrations = [
            "migrations/v2_1_add_sessions.py",
            "migrations/v2_2_add_proactive.py",
            "migrations/v3_0_soul_update.py",
            "migrations/v3_1_memory_decay.py",
            "migrations/v3_2_meta_cognition.py",
            "migrations/v3_3_user_patterns.py"
        ]
        
        for mig in migrations:
            if os.path.exists(mig):
                run_migration_file(mig)
            else:
                print(f"⚠️ Migration file missing: {mig}")

        print("\n✨ DATABASE RESET COMPLETE! ✨")
        print("System is fresh and ready.")

    except Exception as e:
        print(f"❌ DATABASE RESET FAILED: {e}")

if __name__ == "__main__":
    reset_database()
