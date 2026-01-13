"""
Daily Consolidation System
Tự động tóm tắt và consolidate memories mỗi ngày
"""

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


from core.sentiment_arbiter import SentimentArbiter
from core.pattern_detector import PatternDetector

# ...

class DailyConsolidator:
    # ...
    def __init__(self, memory_manager):
        """
        Initialize DailyConsolidator
        
        Args:
            memory_manager: MemoryManager instance
        """
        self.memory = memory_manager
        self.db = memory_manager.db
        self.arbiter = SentimentArbiter()
        self.pattern_detector = PatternDetector(memory_manager)
    
    def consolidate_day(self, target_date):
        """
        Generate summary cho một ngày cụ thể
        """
        try:
            logger.info(f"Consolidating memories for {target_date}")
            
            # 1. Gather data
            messages = self._get_messages_for_date(target_date)
            
            if not messages:
                logger.info(f"No messages for {target_date}, skipping")
                return False
            
            # 2. Generate Summary using LLM (Qwen)
            summary_text = self.arbiter.summarize_day(messages)
            
            # 3. Save Summary to Daily Summaries Table (Analytic view)
            # Use fallback values for now or expand analysis later
            logger.debug(f"Saving summary params: {target_date}, {len(messages)}, {summary_text[:20]}...")
            self.db.execute_query("""
                INSERT INTO daily_summaries 
                (summary_date, total_messages, emotional_summary, generated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (summary_date) DO UPDATE SET
                    emotional_summary = EXCLUDED.emotional_summary,
                    total_messages = EXCLUDED.total_messages
            """, (target_date, len(messages), summary_text))

            # 4. MEMORY REPLACEMENT LOGIC
            # Save Summary as Episodic Memory
            summary_content = f"[CONSOLIDATED {target_date}] {summary_text}"
            self.memory.save_episode(
                content=summary_content, 
                importance=5, # Medium-High importance for daily summaries
                emotion_tone='neutral', # Neutral container
                is_core=0
            ) 
            
            # 5. Archive old fragments (Optional/Per request)
            # Mark raw episodic memories of that day as archived (importance=0)
            # Excluding 'Core Memories' (importance >= 8) and newly created summary
            self.db.execute_query("""
                UPDATE episodic_memory 
                SET importance = 0
                WHERE day_date = %s 
                  AND importance < 8 
                  AND content != %s 
                  AND is_core = 0
            """, (target_date, summary_content))
            
            # 6. PATTERN DETECTION (Weekly or Daily check)
            # We run it daily, looking back 7 days
            try:
                self.pattern_detector.detect_patterns(lookback_days=7)
            except Exception as e:
                logger.error(f"Pattern detection step failed: {e}")
            
            logger.info(f"✅ Consolidated {target_date}: {summary_text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to consolidate {target_date}: {e}")
            return False
    
    def _get_sessions_for_date(self, date):
        """Get all sessions for a date"""
        try:
            result = self.db.execute_query("""
                SELECT session_id, session_type, message_count
                FROM conversation_sessions
                WHERE day_date = %s
                ORDER BY start_time
            """, (date,), fetch_all=True)
            
            sessions = []
            if result:
                for row in result:
                    sessions.append({
                        'session_id': row[0],
                        'type': row[1],
                        'message_count': row[2]
                    })
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting sessions: {e}")
            return []
    
    def _get_messages_for_date(self, date):
        """Get all messages for a date"""
        try:
            result = self.db.execute_query("""
                SELECT role, content
                FROM messages
                WHERE day_date = %s
                ORDER BY timestamp
            """, (date,), fetch_all=True)
            
            messages = []
            if result:
                for row in result:
                    messages.append({
                        'role': row[0],
                        'content': row[1]
                    })
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def _analyze_emotional_trend(self, date):
        """
        Analyze emotional trend for the day
        Currently uses simple averaging, future: LLM analysis
        """
        try:
            # Get bot state history for the day (if tracked)
            # For now, get current state as proxy
            v, e, b, _ = self.memory.get_bot_state()
            
            return {
                'valence': v,
                'energy': e,
                'bond': b
            }
            
        except Exception as e:
            logger.error(f"Error analyzing emotions: {e}")
            return {'valence': 0, 'energy': 0, 'bond': 0}
    
    def _extract_topics(self, messages):
        """
        Extract key topics from messages
        Simple keyword frequency for now
        """
        try:
            # Combine all user messages
            user_messages = [m['content'] for m in messages if m['role'] == 'user']
            text = " ".join(user_messages)
            
            if not text:
                return []
            
            # Simple word frequency (Vietnamese-aware would be better)
            words = text.lower().split()
            
            # Filter short words and common ones
            stopwords = {'là', 'của', 'và', 'có', 'không', 'thì', 'cho', 'nè', 
                        'nhé', 'đi', 'à', 'ơi', 'vậy', 'thế', 'này', 'đó'}
            
            word_freq = {}
            for word in words:
                # Remove punctuation
                word = word.strip('.,!?:;()[]{}')
                
                if len(word) > 2 and word not in stopwords:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top 5 keywords
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return [word for word, freq in top_words]
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []
    
    def _get_memorable_moments(self, date):
        """Get memorable moments from episodic memory"""
        try:
            result = self.db.execute_query("""
                SELECT content
                FROM episodic_memory
                WHERE day_date = %s
                  AND importance >= 3
                ORDER BY importance DESC
                LIMIT 3
            """, (date,), fetch_all=True)
            
            moments = []
            if result:
                for row in result:
                    moments.append(row[0])
            
            return moments
            
        except Exception as e:
            logger.error(f"Error getting memorable moments: {e}")
            return []
    
    def _generate_summary(self, sessions, emotions, topics):
        """
        Generate human-readable summary
        """
        try:
            # Session summary
            session_types = [s['type'] for s in sessions]
            session_str = ", ".join(set(session_types)) if session_types else "không rõ"
            
            # Emotional summary
            v = emotions['valence']
            if v > 0.3:
                mood_str = "vui vẻ"
            elif v < -0.3:
                mood_str = "hơi buồn"
            else:
                mood_str = "bình thường"
            
            # Topics summary
            topic_str = ", ".join(topics[:3]) if topics else "nhiều thứ"
            
            # Combine
            summary = f"Đã chat {len(sessions)} lần ({session_str}), tâm trạng {mood_str}. Nói về {topic_str}."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Hôm đó có nói chuyện."
    
    def should_consolidate_yesterday(self):
        """
        Check if yesterday needs consolidation
        
        Returns:
            bool: True if should consolidate
        """
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        try:
            # Check if already consolidated
            result = self.db.execute_query("""
                SELECT COUNT(*) FROM daily_summaries
                WHERE summary_date = %s
            """, (yesterday,), fetch_one=True)
            
            already_done = result[0] > 0 if result else False
            
            # If not done, check if there are messages from yesterday
            if not already_done:
                result = self.db.execute_query("""
                    SELECT COUNT(*) FROM messages
                    WHERE day_date = %s
                """, (yesterday,), fetch_one=True)
                
                has_messages = result[0] > 0 if result else False
                return has_messages
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking consolidation status: {e}")
            return False
