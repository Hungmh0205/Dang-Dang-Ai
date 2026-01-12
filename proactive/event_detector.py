"""
Event Detector System
Scan và trigger proactive events based on rules
"""

from datetime import datetime, time as dt_time
import random
import logging

logger = logging.getLogger(__name__)


class EventDetector:
    """
    Detect và trigger proactive events
    - Scan event_triggers table
    - Check conditions (time, cooldown, probability)
    - Return events to fire
    """
    
    def __init__(self, memory_manager):
        """
        Initialize EventDetector
        
        Args:
            memory_manager: MemoryManager instance
        """
        self.memory = memory_manager
        self.db = memory_manager.db
    
    def scan_for_events(self):
        """
        Main scanning method - return list of events to fire
        
        Returns:
            list: [(event_name, message, trigger_data), ...]
        """
        events_to_fire = []
        
        try:
            # Get all enabled triggers
            triggers = self._get_active_triggers()
            
            if not triggers:
                return []
            
            # Check each trigger
            for trigger in triggers:
                if self._should_trigger(trigger):
                    message = self._select_message(trigger)
                    
                    if message:
                        events_to_fire.append((
                            trigger['trigger_name'],
                            message,
                            trigger
                        ))
                        
                        # Mark as triggered
                        self._mark_triggered(trigger['trigger_id'])
                        
                        # Only one event at a time
                        break
            
            return events_to_fire
            
        except Exception as e:
            logger.error(f"Error scanning for events: {e}")
            return []
    
    def _get_active_triggers(self):
        """Get all enabled triggers from database"""
        try:
            result = self.db.execute_query("""
                SELECT 
                    trigger_id, trigger_name, trigger_type,
                    time_range_start, time_range_end,
                    max_per_day, cooldown_hours, last_triggered,
                    base_probability, message_templates, priority
                FROM event_triggers
                WHERE enabled = TRUE
                ORDER BY priority DESC
            """, fetch_all=True)
            
            if not result:
                return []
            
            triggers = []
            for row in result:
                triggers.append({
                    'trigger_id': row[0],
                    'trigger_name': row[1],
                    'trigger_type': row[2],
                    'time_range_start': row[3],
                    'time_range_end': row[4],
                    'max_per_day': row[5],
                    'cooldown_hours': row[6],
                    'last_triggered': row[7],
                    'base_probability': float(row[8]) if row[8] else 1.0,
                    'message_templates': row[9],
                    'priority': row[10]
                })
            
            return triggers
            
        except Exception as e:
            logger.error(f"Error getting triggers: {e}")
            return []
    
    def _should_trigger(self, trigger):
        """
        Check if trigger should fire
        
        Args:
            trigger: Trigger dict
        
        Returns:
            bool: True if should trigger
        """
        try:
            # 1. Cooldown check
            if not self._cooldown_passed(trigger):
                return False
            
            # 2. Daily limit check
            if not self._within_daily_limit(trigger):
                return False
            
            # 3. Time range check (for time_based)
            if trigger['trigger_type'] == 'time_based':
                if not self._in_time_range(trigger):
                    return False
            
            # 4. Probability check
            if random.random() > trigger['base_probability']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking trigger conditions: {e}")
            return False
    
    def _cooldown_passed(self, trigger):
        """Check if cooldown period has passed"""
        if not trigger['last_triggered']:
            return True
        
        now = datetime.now()
        last = trigger['last_triggered']
        hours_passed = (now - last).total_seconds() / 3600
        
        return hours_passed >= trigger['cooldown_hours']
    
    def _within_daily_limit(self, trigger):
        """Check if within max triggers per day"""
        try:
            today = datetime.now().date()
            
            result = self.db.execute_query("""
                SELECT COUNT(*) FROM proactive_events
                WHERE event_type = %s
                  AND DATE(sent_time) = %s
            """, (trigger['trigger_name'], today), fetch_one=True)
            
            count = result[0] if result else 0
            return count < trigger['max_per_day']
            
        except Exception as e:
            logger.error(f"Error checking daily limit: {e}")
            return True  # Allow on error
    
    def _in_time_range(self, trigger):
        """
        Check if current time is in trigger's time range
        Handles overnight ranges (e.g., 23:00-02:00)
        """
        start = trigger['time_range_start']
        end = trigger['time_range_end']
        
        if not start or not end:
            return True
        
        now_time = datetime.now().time()
        
        # Normal range (e.g., 07:00-09:00)
        if start <= end:
            return start <= now_time <= end
        
        # Overnight range (e.g., 23:00-02:00)
        else:
            return now_time >= start or now_time <= end
    
    def _select_message(self, trigger):
        """Randomly select message from templates"""
        templates = trigger['message_templates']
        
        if not templates:
            return None
        
        return random.choice(templates)
    
    def _mark_triggered(self, trigger_id):
        """Update last_triggered timestamp"""
        try:
            self.db.execute_query("""
                UPDATE event_triggers
                SET last_triggered = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE trigger_id = %s
            """, (trigger_id,))
            
        except Exception as e:
            logger.error(f"Error marking trigger: {e}")
    
    def log_proactive_event(self, event_type, message, trigger_id=None):
        """
        Log a proactive event to database
        
        Args:
            event_type: Event type name
            message: Message content
            trigger_id: Trigger ID (if from trigger)
        
        Returns:
            int: event_id
        """
        try:
            # Get current state
            v, e, b, _ = self.memory.get_bot_state()
            session_id = self.memory.session_mgr.current_session_id
            
            # Insert event
            result = self.db.execute_query("""
                INSERT INTO proactive_events 
                (event_type, trigger_id, trigger_time, sent_time, 
                 message_content, session_id,
                 valence_at_send, energy_at_send, bond_at_send)
                VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                        %s, %s, %s, %s, %s)
                RETURNING event_id
            """, (event_type, trigger_id, message, session_id, v, e, b),
            fetch_one=True)
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error logging proactive event: {e}")
            return None
