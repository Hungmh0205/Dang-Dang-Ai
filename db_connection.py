"""
PostgreSQL Connection Pool Manager
Thread-safe database connection handling với automatic retry và health checks
"""

import psycopg2
from psycopg2 import pool, extras, OperationalError, InterfaceError
from contextlib import contextmanager
import time
import os
from dotenv import load_dotenv
import logging

# Setup logging
logger = logging.getLogger(__name__)

load_dotenv()

class DatabaseManager:
    """
    Production-grade PostgreSQL connection pool manager
    - Thread-safe connection pooling
    - Automatic connection retry với exponential backoff
    - Health checking
    - Transaction management với auto-rollback
    """
    
    def __init__(self, min_conn=2, max_conn=10):
        """
        Initialize connection pool
        
        Args:
            min_conn: Minimum number of connections to maintain
            max_conn: Maximum number of connections allowed
        """
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'dangdang_db'),
            'user': os.getenv('DB_USER', 'dangdang'),
            'password': os.getenv('DB_PASSWORD', ''),
        }
        
        self.min_conn = min_conn
        self.max_conn = max_conn
        self.pool = None
        
        # Initialize pool với retry
        self._initialize_pool()
    
    def _initialize_pool(self, max_retries=5):
        """Initialize connection pool với retry logic"""
        for attempt in range(max_retries):
            try:
                self.pool = psycopg2.pool.ThreadedConnectionPool(
                    self.min_conn,
                    self.max_conn,
                    **self.db_config
                )
                logger.info(f"✅ PostgreSQL connection pool initialized (min={self.min_conn}, max={self.max_conn})")
                return
            except OperationalError as e:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"⚠️ Database connection failed (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s...")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Failed to initialize database pool after {max_retries} attempts: {e}")
                    raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager để lấy connection từ pool
        Automatically releases connection về pool sau khi xong
        
        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
        """
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        except (OperationalError, InterfaceError) as e:
            logger.error(f"❌ Database connection error: {e}")
            if conn:
                self.pool.putconn(conn, close=True)
            raise
        finally:
            if conn:
                self.pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, commit=True, dict_cursor=True):
        """
        Context manager để lấy cursor với auto-commit/rollback
        
        Args:
            commit: Tự động commit nếu True, rollback nếu exception
            dict_cursor: Use RealDictCursor (dict) vs regular (tuple)
        
        Usage:
            with db.get_cursor() as cursor:
                cursor.execute("INSERT INTO users VALUES (%s, %s)", (name, email))
        """
        with self.get_connection() as conn:
            if dict_cursor:
                cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
            else:
                cursor = conn.cursor()  # Regular tuple cursor
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ Transaction rolled back due to error: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False, dict_cursor=False):
        """
        Execute query với automatic error handling
        
        Args:
            query: SQL query string
            params: Query parameters (tuple or dict)
            fetch_one: Return single row
            fetch_all: Return all rows
            dict_cursor: Return rows as dictionaries (True) or tuples (False)
        """
        try:
            # Always use tuple cursor for simplicity by default, unless requested
            with self.get_cursor(dict_cursor=dict_cursor) as cursor:
                cursor.execute(query, params)
                
                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"❌ Query execution failed: {query[:100]}... | Error: {e}")
            raise
    
    def execute_many(self, query, params_list):
        """
        Execute batch insert/update với single transaction
        
        Args:
            query: SQL query với placeholders
            params_list: List of parameter tuples
        
        Returns:
            Number of rows affected
        """
        try:
            with self.get_cursor(dict_cursor=False) as cursor:
                cursor.executemany(query, params_list)
                return cursor.rowcount
        except Exception as e:
            logger.error(f"❌ Batch execution failed: {e}")
            raise
    
    def health_check(self):
        """
        Check database connection health
        
        Returns:
            (bool, str): (is_healthy, message)
        """
        try:
            with self.get_cursor(commit=False, dict_cursor=False) as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    return True, "✅ Database connection healthy"
                return False, "❌ Unexpected health check result"
        except Exception as e:
            return False, f"❌ Health check failed: {e}"
    
    def close_all_connections(self):
        """Đóng tất cả connections trong pool - call khi shutdown"""
        if self.pool:
            self.pool.closeall()
            logger.info("🔒 All database connections closed")
    
    def __enter__(self):
        """Support for 'with' statement"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting 'with' block"""
        self.close_all_connections()


# Singleton instance for global usage
_db_manager = None

def get_db_manager():
    """
    Get singleton DatabaseManager instance
    
    Returns:
        DatabaseManager: Global database manager
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
