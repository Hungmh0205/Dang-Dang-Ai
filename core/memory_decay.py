from db_connection import get_db_manager
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MemoryDecayer:
    """
    Manages the 'Forgetting Curve' of the AI.
    Reduces importance of memories over time unless reinforced.
    """
    
    def __init__(self):
        self.db = get_db_manager()

    def run_decay_cycle(self):
        """
        Main decay process.
        Rule:
        1. Access checks: If accessed recently (3 days), NO decay.
        2. Importance checks:
           - Importance > 8 (Core): NO decay.
           - Importance > 1: Decay -1 every 7 days of inactivity.
        3. Archival:
           - Importance <= 1: Mark as 'fading' or potential for archiving.
        """
        logger.info("Starting Memory Decay Cycle...")
        
        try:
            # 1. Decay Logic
            # Decrease importance by 1 for memories not accessed in 7 days
            # AND are not 'Core' (Importance > 8)
            # AND are not locked (decay_locked = True or is_core = 1)
            
            decay_sql = """
                UPDATE episodic_memory
                SET importance = importance - 1
                WHERE last_accessed < NOW() - INTERVAL '7 days'
                  AND importance > 1
                  AND importance <= 8
                  AND (decay_locked IS FALSE OR decay_locked IS NULL)
                  AND (is_core = 0 OR is_core IS NULL)
            """
            self.db.execute_query(decay_sql)
            
            # 2. Archive/Cleanup Logic (Optional)
            # For now, we just let them sit at importance=1 (Faded)
            
            logger.info("Memory Decay Cycle Completed.")
            return True
            
        except Exception as e:
            logger.error(f"Memory Decay process failed: {e}")
            return False

    def reinforce_memory(self, memory_id):
        """
        Call this when a memory is retrieved/used.
        Resets decay clock and boosts importance.
        """
        try:
            sql = """
                UPDATE episodic_memory
                SET last_accessed = NOW(),
                    importance = LEAST(importance + 1, 10),
                    access_count = access_count + 1
                WHERE id = %s
            """
            self.db.execute_query(sql, (memory_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to reinforce memory {memory_id}: {e}")
            return False
