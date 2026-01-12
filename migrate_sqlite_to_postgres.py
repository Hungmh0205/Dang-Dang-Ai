"""
Migration Script: SQLite → PostgreSQL
Safely migrate existing Dang Dang memory from SQLite to PostgreSQL
"""

import sqlite3
import psycopg2
from psycopg2 import sql
import os
import shutil
from datetime import datetime
from dotenv import load_dotenv
import json

load_dotenv()

class DatabaseMigrator:
    """Migrate Dang Dang's memory from SQLite to PostgreSQL"""
    
    def __init__(self, sqlite_path="dangdang_memory.db"):
        self.sqlite_path = sqlite_path
        self.backup_path = None
        
        # PostgreSQL connection config
        self.pg_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'dangdang_db'),
            'user': os.getenv('DB_USER', 'dangdang'),
            'password': os.getenv('DB_PASSWORD', ''),
        }
    
    def backup_sqlite(self):
        """Backup SQLite database trước khi migrate"""
        if not os.path.exists(self.sqlite_path):
            print(f"⚠️  SQLite database not found: {self.sqlite_path}")
            print("   This is normal if you're starting fresh!")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = f"dangdang_memory_backup_{timestamp}.db"
        
        shutil.copy2(self.sqlite_path, self.backup_path)
        print(f"✅ SQLite backup created: {self.backup_path}")
        return True
    
    def create_postgresql_schema(self, pg_conn):
        """Tạo schema PostgreSQL (converted từ SQLite)"""
        cursor = pg_conn.cursor()
        
        print("📝 Creating PostgreSQL schema...")
        
        # Clear existing tables to avoid duplicate key errors
        print("🧹 Cleaning existing tables (if any)...")
        cursor.execute("DROP TABLE IF EXISTS schema_version CASCADE")
        cursor.execute("DROP TABLE IF EXISTS messages CASCADE")
        cursor.execute("DROP TABLE IF EXISTS episodic_memory CASCADE")
        cursor.execute("DROP TABLE IF EXISTS profile CASCADE")
        cursor.execute("DROP TABLE IF EXISTS self_image CASCADE")
        cursor.execute("DROP TABLE IF EXISTS memory_meta CASCADE")
        cursor.execute("DROP TABLE IF EXISTS bot_state CASCADE")
        pg_conn.commit()
        
        # 1. Bot state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_state (
                id INTEGER PRIMARY KEY,
                valence NUMERIC(3,2),
                energy NUMERIC(3,2),
                bond NUMERIC(3,2),
                last_reflection TEXT
            )
        """)
        
        # 2. Messages table (short-term memory)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. User profile table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                key TEXT PRIMARY KEY,
                value TEXT,
                confidence NUMERIC(3,2)
            )
        """)
        
        # 4. Episodic memory (long-term memory)
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
        
        # 5. Self-image (Dang Dang's personality traits)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS self_image (
                trait TEXT PRIMARY KEY,
                strength NUMERIC(3,2)
            )
        """)
        
        # 6. Memory metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # 7. Schema version tracking (NEW - for future migrations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        
        # Insert version 1
        cursor.execute("""
            INSERT INTO schema_version (version, description) 
            VALUES (1, 'Initial PostgreSQL migration from SQLite')
            ON CONFLICT (version) DO NOTHING
        """)
        
        # Create indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodic_importance ON episodic_memory(importance DESC, is_core DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodic_emotion ON episodic_memory(emotion_tone)")
        
        pg_conn.commit()
        print("✅ PostgreSQL schema created with indices")
    
    def migrate_data(self):
        """Main migration process"""
        print("\n🚀 Starting migration: SQLite → PostgreSQL\n")
        
        # Step 1: Backup
        has_sqlite_data = self.backup_sqlite()
        
        # Step 2: Connect to PostgreSQL
        try:
            pg_conn = psycopg2.connect(**self.pg_config)
            print("✅ Connected to PostgreSQL")
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            print("\n💡 Make sure Docker container is running:")
            print("   docker-compose up -d")
            return False
        
        # Step 3: Create schema
        self.create_postgresql_schema(pg_conn)
        
        # Step 4: Migrate data if SQLite exists
        if has_sqlite_data:
            try:
                sqlite_conn = sqlite3.connect(self.sqlite_path)
                self._migrate_table_data(sqlite_conn, pg_conn)
                sqlite_conn.close()
                print("\n✅ Data migration completed successfully!")
            except Exception as e:
                print(f"\n❌ Migration failed: {e}")
                pg_conn.rollback()
                pg_conn.close()
                return False
        else:
            print("ℹ️  No existing SQLite data to migrate. Starting fresh!")
            # Initialize default data
            self._initialize_default_data(pg_conn)
        
        pg_conn.close()
        return True
    
    def _migrate_table_data(self, sqlite_conn, pg_conn):
        """Migrate all tables from SQLite to PostgreSQL"""
        pg_cursor = pg_conn.cursor()
        
        tables_to_migrate = [
            ('bot_state', ['id', 'valence', 'energy', 'bond', 'last_reflection']),
            ('messages', ['role', 'content', 'timestamp']),  # Skip id (SERIAL)
            ('profile', ['key', 'value', 'confidence']),
            ('episodic_memory', ['content', 'importance', 'emotion_tone', 'is_core', 'timestamp']),
            ('self_image', ['trait', 'strength']),
            ('memory_meta', ['key', 'value']),
        ]
        
        for table_name, columns in tables_to_migrate:
            print(f"📦 Migrating {table_name}...", end=" ")
            
            # Read from SQLite
            sqlite_cursor = sqlite_conn.cursor()
            col_str = ', '.join(columns)
            sqlite_cursor.execute(f"SELECT {col_str} FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if rows:
                # Insert into PostgreSQL
                placeholders = ', '.join(['%s'] * len(columns))
                insert_query = f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders})"
                
                pg_cursor.executemany(insert_query, rows)
                print(f"✅ {len(rows)} rows")
            else:
                print("(empty)")
        
        pg_conn.commit()
    
    def _initialize_default_data(self, pg_conn):
        """Initialize default data cho fresh installation"""
        cursor = pg_conn.cursor()
        
        print("📝 Initializing default data...")
        
        # Default bot state
        cursor.execute("""
            INSERT INTO bot_state (id, valence, energy, bond, last_reflection)
            VALUES (1, 0.2, 0.8, 0.3, 'Hôm nay thấy hào hứng quá đi! :P')
            ON CONFLICT (id) DO NOTHING
        """)
        
        # Default personality traits
        default_traits = [
            ("Nghịch ngợm", 0.7),
            ("Hài hước", 0.8),
            ("Tinh tế", 0.6),
            ("Hay dỗi", 0.4)
        ]
        
        for trait, strength in default_traits:
            cursor.execute("""
                INSERT INTO self_image (trait, strength)
                VALUES (%s, %s)
                ON CONFLICT (trait) DO NOTHING
            """, (trait, strength))
        
        # Initialize last_decay_ts
        cursor.execute("""
            INSERT INTO memory_meta (key, value)
            VALUES ('last_decay_ts', %s)
            ON CONFLICT (key) DO NOTHING
        """, (str(datetime.now().timestamp()),))
        
        pg_conn.commit()
        print("✅ Default data initialized")
    
    def verify_migration(self):
        """Verify migration success bằng cách count rows"""
        print("\n🔍 Verifying migration...\n")
        
        try:
            pg_conn = psycopg2.connect(**self.pg_config)
            cursor = pg_conn.cursor()
            
            tables = ['bot_state', 'messages', 'profile', 'episodic_memory', 'self_image', 'memory_meta']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} rows")
            
            pg_conn.close()
            print("\n✅ Verification complete!")
            return True
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False


def main():
    """Run migration"""
    print("=" * 60)
    print("  DANG DANG AI - DATABASE MIGRATION")
    print("  SQLite → PostgreSQL")
    print("=" * 60)
    
    migrator = DatabaseMigrator()
    
    if migrator.migrate_data():
        migrator.verify_migration()
        print("\n" + "=" * 60)
        print("  🎉 MIGRATION SUCCESSFUL!")
        print("=" * 60)
        print("\n📋 Next steps:")
        print("  1. Update your .env file với DB credentials")
        print("  2. Test application: python main.py")
        print("  3. Keep SQLite backup safe (in case rollback needed)")
    else:
        print("\n" + "=" * 60)
        print("  ❌ MIGRATION FAILED")
        print("=" * 60)
        print("\n📋 Troubleshooting:")
        print("  1. Check Docker container: docker-compose ps")
        print("  2. Check logs: docker-compose logs postgres")
        print("  3. Verify .env file has correct DB credentials")


if __name__ == "__main__":
    main()
