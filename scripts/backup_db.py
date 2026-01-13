import os
import subprocess
import time
from datetime import datetime
from dotenv import load_dotenv
import glob

# Setup logging manually since this is a standalone script
def log(msg):
    print(f"[{datetime.now()}] {msg}")

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'dangdang_db')
DB_USER = os.getenv('DB_USER', 'dangdang')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

BACKUP_DIR = "backups"
MAX_BACKUPS = 7  # Keep last 7 backups

def backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{DB_NAME}_backup_{timestamp}.sql"
    filepath = os.path.join(BACKUP_DIR, filename)
    
    log(f"Starting backup for {DB_NAME}...")
    
    # Set password env var for pg_dump
    os.environ['PGPASSWORD'] = DB_PASSWORD
    
    # Find pg_dump
    pg_dump_cmd = 'pg_dump'
    
    # Check if pg_dump is in PATH
    from shutil import which
    if not which('pg_dump'):
        # Try common paths
        common_paths = [
            r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
            r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
            r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
            r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe"
        ]
        for path in common_paths:
            if os.path.exists(path):
                pg_dump_cmd = f'"{path}"' # Quote for spaces
                log(f"Found pg_dump at: {path}")
                # We need to use list for subprocess if not shell=True, but with spaces and quotes it gets tricky
                # Safest is to use the clean path string in list
                pg_dump_cmd = path
                break
        
        if pg_dump_cmd == 'pg_dump':
            log("⚠️ pg_dump not found in PATH or common locations. Backup might fail.")

    # Construct command
    cmd = [
        pg_dump_cmd,
        '-h', DB_HOST,
        '-p', DB_PORT,
        '-U', DB_USER,
        '-F', 'c', # Custom format
        '-b', 
        '-v', 
        '-f', filepath,
        DB_NAME
    ]
    
    try:
        subprocess.run(cmd, check=True)
        log(f"✅ Backup successful: {filepath}")
        cleanup_old_backups()
    except subprocess.CalledProcessError as e:
        log(f"❌ Backup failed: {e}")
    except FileNotFoundError:
        log("❌ pg_dump not found. Please ensure PostgreSQL bin directory is in your PATH.")

def cleanup_old_backups():
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "*.sql")), key=os.path.getmtime, reverse=True)
    
    if len(files) > MAX_BACKUPS:
        log(f"Cleaning up old backups (Keeping latest {MAX_BACKUPS})...")
        for f in files[MAX_BACKUPS:]:
            try:
                os.remove(f)
                log(f"Deleted old backup: {f}")
            except Exception as e:
                log(f"Failed to delete {f}: {e}")

if __name__ == "__main__":
    backup()
