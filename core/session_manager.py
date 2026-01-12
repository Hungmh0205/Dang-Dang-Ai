"""
Session Manager - Temporal Intelligence
Manages conversation sessions với day boundaries và time awareness
"""

from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Quản lý conversation sessions
    - Detect new sessions (new day, 4+ hour gap)
    - Generate time-appropriate greetings
    - Track session metadata
    """
    
    def __init__(self, db_manager):
        """
        Initialize SessionManager
        
        Args:
            db_manager: DatabaseManager instance from db_connection
        """
        self.db = db_manager
        self.current_session_id = None
        self._load_current_session()
    
    def _load_current_session(self):
        """Load current active session if exists"""
        result = self.db.execute_query("""
            SELECT session_id FROM conversation_sessions
            WHERE end_time IS NULL
            ORDER BY start_time DESC
            LIMIT 1
        """, fetch_one=True)
        
        if result:
            self.current_session_id = result[0]
            logger.info(f"Loaded active session: {self.current_session_id}")
    
    def should_start_new_session(self, last_message_time):
        """
        Determine if should create new session
        
        Rules:
        - No previous message = YES (first time)
        - New day (date changed) = YES
        - Gap >= 4 hours = YES
        - Otherwise = NO (continue current session)
        
        Args:
            last_message_time: datetime of last message (or None)
        
        Returns:
            bool: True if should start new session
        """
        if not last_message_time:
            logger.info("No previous message - starting new session")
            return True
        
        now = datetime.now()
        
        # Check if new day
        if now.date() > last_message_time.date():
            logger.info(f"New day detected: {last_message_time.date()} → {now.date()}")
            return True
        
        # Check idle gap
        gap_hours = (now - last_message_time).total_seconds() / 3600
        if gap_hours >= 4:
            logger.info(f"Long idle detected: {gap_hours:.1f} hours")
            return True
        
        logger.debug(f"Continue current session (gap: {gap_hours:.1f}h)")
        return False
    
    def start_session(self):
        """
        Create new conversation session
        
        Returns:
            UUID: session_id of new session
        """
        now = datetime.now()
        session_type = self._get_session_type(now.hour)
        
        try:
            # End previous session if exists
            if self.current_session_id:
                self.end_session(self.current_session_id)
            
            # Create new session
            result = self.db.execute_query("""
                INSERT INTO conversation_sessions 
                (start_time, day_date, session_type)
                VALUES (%s, %s, %s)
                RETURNING session_id
            """, (now, now.date(), session_type), fetch_one=True)
            
            self.current_session_id = result[0]
            logger.info(f"New session started: {self.current_session_id} ({session_type})")
            
            return self.current_session_id
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            raise
    
    def end_session(self, session_id):
        """
        Mark session as ended và update metadata
        
        Args:
            session_id: UUID of session to end
        """
        try:
            self.db.execute_query("""
                UPDATE conversation_sessions
                SET 
                    end_time = CURRENT_TIMESTAMP,
                    message_count = (
                        SELECT COUNT(*) FROM messages 
                        WHERE session_id = %s
                    )
                WHERE session_id = %s
            """, (session_id, session_id))
            
            logger.info(f"Session ended: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
    
    def _get_session_type(self, hour):
        """
        Determine session type based on hour of day
        
        Args:
            hour: Hour (0-23)
        
        Returns:
            str: 'morning', 'afternoon', 'evening', or 'night'
        """
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 22:
            return 'evening'
        else:
            return 'night'
    
    def get_session_greeting(self, is_new_session, session_type, last_message_time=None):
        """
        Generate unique LLM-based greeting với context
        
        Args:
            is_new_session: bool - Is this a new session?
            session_type: str - Type of session
            last_message_time: datetime - Last message timestamp (optional)
        
        Returns:
            str or None: Greeting message (None if not new session)
        """
        if not is_new_session:
            return None
        
        try:
            from db_connection import get_db_manager
            import google.generativeai as genai
            import os
            
            db = get_db_manager()
            
            # Get session count
            result = db.execute_query("SELECT COUNT(*) FROM conversation_sessions", fetch_one=True)
            session_count = result[0] if result else 0
            
            # First time - simple template
            if session_count == 0:
                return "hế lôoo ^^ tớ là Dang Dang nèe, học lớp 11 đâyy. bạn tên gì thếee?"
            
            # Get bond & mood
            result = db.execute_query("SELECT valence, bond FROM bot_state ORDER BY id DESC LIMIT 1", fetch_one=True)
            if result:
                valence = float(result[0])
                bond = float(result[1])
            else:
                valence = 0.0
                bond = 0.5
            
            # Get recent conversation context (last 3 messages)
            result = db.execute_query("""
                SELECT role, content FROM messages 
                WHERE timestamp < (
                    SELECT start_time FROM conversation_sessions 
                    WHERE session_id = %s
                )
                ORDER BY timestamp DESC LIMIT 3
            """, (self.current_session_id,), fetch_all=True)
            
            recent_context = ""
            if result:
                messages = []
                for row in reversed(result):  # Show in chronological order
                    role = "User" if row[0] == "user" else "Dang Dang"
                    messages.append(f"{role}: {row[1][:80]}")  # Truncate
                recent_context = "\n".join(messages)
            
            # Time context
            time_mapping = {
                'morning': 'buổi sáng (7-12h)',
                'afternoon': 'buổi chiều (12-17h)', 
                'evening': 'buổi tối (17-22h)',
                'night': 'đêm khuya (22h-7h)'
            }
            time_desc = time_mapping.get(session_type, session_type)
            
            # Gap info
            gap_info = ""
            if last_message_time:
                gap_hours = (datetime.now() - last_message_time).total_seconds() / 3600
                if gap_hours > 24:
                    gap_info = f"Đã {int(gap_hours/24)} ngày không nói chuyện"
                elif gap_hours > 12:
                    gap_info = f"Đã {int(gap_hours)} giờ không gặp"
            
            # LLM Prompt
            prompt = f"""Bạn là Dang Dang, 17 tuổi, học sinh lớp 11 Việt Nam. Chào User một cách TỰ NHIÊN theo context:

THỜI GIAN: {time_desc}
TÌNH CẢM: {"vui" if valence > 0.3 else "buồn" if valence < -0.3 else "bình thường"}
MỐI QUAN HỆ: {"bạn thân" if bond > 0.7 else "bạn bè" if bond > 0.4 else "mới quen"}
{f"KHOẢNG CÁCH: {gap_info}" if gap_info else ""}

CUỘC TRÒ CHUYỆN GẦN NHẤT:
{recent_context if recent_context else "Chưa có cuộc trò chuyện nào"}

YÊU CẦU (BẮT BUỘC):
- TRẢ LỜI BẰNG TIẾNG VIỆT (Vietnamese only)
- Chào một cách tự nhiên, KHÔNG dùng template
- NẾU có cuộc trò chuyện trước → nhắc đến nó (VD: "hôm qua bạn nói về... thế nào rồi?")
- Phản ánh tâm trạng hiện tại
- Dùng lowercase, kéo dài chữ, typos tự nhiên (VD: "hế lôoo", "ơiii", "nhaaa")
- NGẮN GỌN (1-2 câu), đừng dài dòng

CHỈ TRẢ LỜI GREETING BẰNG TIẾNG VIỆT, KHÔNG THÊM BẤT KỲ GIẢI THÍCH NÀO:"""

            # Call Ollama (local model - no API quota)
            import ollama
            
            try:
                response = ollama.generate(
                    model='qwen2.5:3b-instruct',
                    prompt=prompt,
                    stream=False,
                    options={"temperature": 0.8, "num_predict": 100}
                )
                greeting = response['response'].strip()
                
                # Clean up (remove quotes if LLM added them)
                greeting = greeting.strip('"').strip("'")
                
                return greeting
                
            except Exception as ollama_error:
                logger.error(f"Ollama error: {ollama_error}")
                # Fallback to simple template
                return random.choice([
                    "hế lôoo ^^",
                    "ơiii bạn ơiii",
                    f"chào {time_desc} nèe"
                ])
            
        except Exception as e:
            logger.error(f"Error generating greeting: {e}")
            # Fallback
            return random.choice([
                "hế lôoo ^^",
                "ơiii bạn ơiii",
                f"chào buổi {session_type} nèe"
            ])
        """
        Generate varied, relationship-aware greeting
        
        Args:
            is_new_session: bool - Is this a new session?
            session_type: str - Type of session
            last_message_time: datetime - Last message timestamp (optional)
        
        Returns:
            str or None: Greeting message (None if not new session)
        """
        if not is_new_session:
            return None
        
        # Get relationship context
        try:
            from db_connection import get_db_manager
            db = get_db_manager()
            
            # Get total session count
            result = db.execute_query("""
                SELECT COUNT(*) FROM conversation_sessions
            """, fetch_one=True)
            session_count = result[0] if result else 0
            
            # Get bond level
            result = db.execute_query("""
                SELECT bond FROM bot_state ORDER BY id DESC LIMIT 1
            """, fetch_one=True)
            bond = float(result[0]) if result else 0.5
            
        except:
            session_count = 0
            bond = 0.5
        
        # First time ever
        if session_count == 0:
            return "hế lôoo ^^ tớ là Dang Dang nèe, học lớp 11 đâyy. bạn tên gì thếee?"
        
        # Greetings based on bond level and time
        if bond > 0.7:  # Close friends
            greetings_by_time = {
                'morning': [
                    "chào buổi sángg bạn thânn ^^",
                    "sáng rồiii, ngủ ngon khôngg hehe",
                    "ơiii dậy sớm thế bạnn",
                ],
                'afternoon': [
                    "chiều rồiii nèe",
                    "hế lôoo ^^",
                    "bạn đóoo, hôm nay thế nàoo",
                ],
                'evening': [
                    "tối rồiii bạn ơiii",
                    "ơiii buổi tối ^^",
                    "hế lôoo, hôm nay mệt khônggg",
                ],
                'night': [
                    "khuya rồiii còn thức àaa",
                    "chưa ngủ háaa",
                    "đêm rồiii nèe",
                ]
            }
        
        elif bond > 0.4:  # Regular friends
            greetings_by_time = {
                'morning': [
                    "chào buổi sángg",
                    "sáng rồiii ^^",
                    "hế lôoo bạnn",
                ],
                'afternoon': [
                    "chiều rồiii",
                    "hế lôoo",
                    "ơiii bạn",
                ],
                'evening': [
                    "tối rồiii nèe",
                    "buổi tối ^^",
                    "hế lôoo",
                ],
                'night': [
                    "đêm rồiii",
                    "khuya rồiii nhỉii",
                    "sao chưa ngủ đấyy",
                ]
            }
        
        else:  # New/distant
            greetings_by_time = {
                'morning': [
                    "chào buổi sáng nhaaa",
                    "hế lôoo ^^",
                ],
                'afternoon': [
                    "chào bạnn",
                    "hế lôoo",
                ],
                'evening': [
                    "chào bạn nhaaa",
                    "buổi tối ^^",
                ],
                'night': [
                    "hế lôoo",
                    "chào bạnn",
                ]
            }
        
        greeting = random.choice(greetings_by_time.get(session_type, ["hế lôoo"]))
        
        # Add context for long absences
        if last_message_time:
            gap_hours = (datetime.now() - last_message_time).total_seconds() / 3600
            
            if gap_hours > 24:
                days = int(gap_hours / 24)
                if bond > 0.6:
                    greeting += f"\nlâu không gặppp, nhớ bạn quáaaa ({days} ngày rồiii)"
                else:
                    greeting += f"\nlâu không nói chuyện nhỉiii"
            elif gap_hours > 12:
                if bond > 0.6:
                    greeting += "\nlâu không nói chuyệnnn"
        
        return greeting
    
    def get_yesterday_summary(self):
        """
        Get summary of yesterday if available
        
        Returns:
            str or None: Yesterday's summary
        """
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        try:
            result = self.db.execute_query("""
                SELECT emotional_summary, key_topics
                FROM daily_summaries
                WHERE summary_date = %s
            """, (yesterday,), fetch_one=True)
            
            if result and result[0]:
                summary = result[0]
                topics = result[1] if result[1] else []
                
                # Format summary
                if topics:
                    topic_str = ", ".join(topics[:3])  # Top 3 topics
                    return f"{summary} (nói về: {topic_str})"
                return summary
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get yesterday summary: {e}")
            return None
    
    def get_session_stats(self, session_id):
        """
        Get statistics for a session
        
        Args:
            session_id: UUID of session
        
        Returns:
            dict: Session statistics
        """
        try:
            result = self.db.execute_query("""
                SELECT 
                    start_time,
                    end_time,
                    session_type,
                    message_count,
                    avg_valence,
                    avg_energy
                FROM conversation_sessions
                WHERE session_id = %s
            """, (session_id,), fetch_one=True)
            
            if result:
                return {
                    'start_time': result[0],
                    'end_time': result[1],
                    'session_type': result[2],
                    'message_count': result[3],
                    'avg_valence': float(result[4]) if result[4] else None,
                    'avg_energy': float(result[5]) if result[5] else None
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return None
