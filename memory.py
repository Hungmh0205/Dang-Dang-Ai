"""
Memory Manager - PostgreSQL Version
Quản lý bộ nhớ của Dang Dang với PostgreSQL backend
Thread-safe, production-ready
"""

import time
from datetime import datetime
from db_connection import get_db_manager
from core.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        """Khởi tạo Memory Manager với PostgreSQL connection pool"""
        self.db = get_db_manager()
        self.session_mgr = SessionManager(self.db)  # NEW: Session tracking
        self.init_db()

    def init_db(self):
        """Khởi tạo cấu trúc cơ sở dữ liệu với đầy đủ các bảng chức năng và nhãn linh hồn"""
        try:
            with self.db.get_cursor(dict_cursor=False) as cursor:
                
                # 1. Bảng lưu trữ trạng thái thực thể (Mood, Energy, Bond, Reflection)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bot_state (
                        id INTEGER PRIMARY KEY,
                        valence NUMERIC(3,2),
                        energy NUMERIC(3,2), 
                        bond NUMERIC(3,2),
                        last_reflection TEXT
                    )
                """)
                
                # 2. Bảng tin nhắn (Bộ nhớ ngắn hạn - Short-term memory)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 3. Bảng hồ sơ NGƯỜI DÙNG (Dữ liệu thực tế về đối phương)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS profile (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        confidence NUMERIC(3,2)
                    )
                """)
                
                # 4. Bảng ký ức sự kiện (Episodic Memory) - Có is_core để bảo vệ ký ức cốt lõi
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

                # 5. Bảng bản ngã DANG DANG (Tự nhận thức về tính cách bản thân)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS self_image (
                        trait TEXT PRIMARY KEY,
                        strength NUMERIC(3,2)
                    )
                """)

                # 6. Bảng Meta để quản lý các thông số hệ thống
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memory_meta (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                """)

                # 7. Schema version tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """)

                # KHÔI PHỤC LINH HỒN: Khởi tạo dữ liệu mặc định cho trạng thái (Vibe nhí nhảnh của tuổi 17)
                cursor.execute("SELECT COUNT(*) FROM bot_state")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO bot_state (id, valence, energy, bond, last_reflection) 
                        VALUES (1, 0.2, 0.8, 0.3, 'Hôm nay thấy hào hứng quá đi! :P')
                    """)
                
                # KHÔI PHỤC NHÂN CÁCH GỐC: (Nghịch ngợm, Hài hước, Tinh tế, Hay dỗi)
                default_traits = [("Nghịch ngợm", 0.7), ("Hài hước", 0.8), ("Tinh tế", 0.6), ("Hay dỗi", 0.4)]
                for t, s in default_traits:
                    cursor.execute("""
                        INSERT INTO self_image (trait, strength) VALUES (%s, %s)
                        ON CONFLICT (trait) DO NOTHING
                    """, (t, s))

                # Kiểm tra và khởi tạo thời gian decay lần cuối
                cursor.execute("SELECT COUNT(*) FROM memory_meta WHERE key = 'last_decay_ts'")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO memory_meta (key, value) VALUES ('last_decay_ts', %s)
                    """, (str(time.time()),))
                
                # Create indices for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodic_importance ON episodic_memory(importance DESC, is_core DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodic_emotion ON episodic_memory(emotion_tone)")
                
            logger.info("✅ Database schema initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise

    def get_last_message_timestamp(self):
        """Lấy dấu thời gian của tin nhắn cuối cùng để tính toán khoảng lặng (Time Gap)"""
        try:
            result = self.db.execute_query(
                "SELECT timestamp FROM messages ORDER BY id DESC LIMIT 1",
                fetch_one=True
            )
            if result and result[0]:
                ts = result[0]
                # If string (from TEXT column), parse it
                if isinstance(ts, str):
                    try:
                        from datetime import datetime
                        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            # Try ISO format if simple format fails
                            return datetime.fromisoformat(ts)
                        except:
                            # Fallback if format is weird
                            logger.error(f"Could not parse timestamp string: {ts}")
                            return None
                # If already datetime (from TIMESTAMP column)
                return ts
            return None
        except Exception as e:
            logger.error(f"Error getting last message timestamp: {e}")
            return None

    def update_profile(self, key, value, confidence):
        """Cập nhật hồ sơ User với logic Identity Isolation (Overwrite ngưỡng 90%)"""
        try:
            # Check existing confidence
            existing = self.db.execute_query(
                "SELECT confidence FROM profile WHERE key = %s",
                (key,),
                fetch_one=True
            )
            
            if existing:
                old_conf = float(existing[0])
                # Chỉ overwrite nếu tin cậy mới đủ cao
                if confidence > (old_conf * 0.9):
                    self.db.execute_query(
                        "UPDATE profile SET value = %s, confidence = %s WHERE key = %s",
                        (value, confidence, key)
                    )
            else:
                self.db.execute_query(
                    "INSERT INTO profile (key, value, confidence) VALUES (%s, %s, %s)",
                    (key, value, confidence)
                )
        except Exception as e:
            logger.error(f"Error updating profile: {e}")

    def update_self_image(self, trait, strength, sensitivity=0.1):
        """Cập nhật bản ngã bằng công thức Moving Average kết hợp SensitivityIndex (Đàn hồi tâm lý)"""
        try:
            existing = self.db.execute_query(
                "SELECT strength FROM self_image WHERE trait = %s",
                (trait,),
                fetch_one=True
            )
            
            if existing:
                old_strength = float(existing[0])
                # sensitivity cao (0.7-0.8) khi có Breaking Point, mặc định 0.1
                new_strength = (old_strength * (1 - sensitivity)) + (strength * sensitivity)
                self.db.execute_query(
                    "UPDATE self_image SET strength = %s WHERE trait = %s",
                    (new_strength, trait)
                )
            else:
                self.db.execute_query(
                    "INSERT INTO self_image (trait, strength) VALUES (%s, %s)",
                    (trait, strength)
                )
        except Exception as e:
            logger.error(f"Error updating self image: {e}")

    def get_bot_state(self):
        """Lấy toàn bộ trạng thái hiện tại của Dang Dang"""
        try:
            result = self.db.execute_query(
                "SELECT valence, energy, bond, last_reflection FROM bot_state WHERE id = 1",
                fetch_one=True
            )
            if result:
                return (float(result[0]), float(result[1]), float(result[2]), result[3])
            # Return default if not found
            return (0.2, 0.8, 0.3, "Hôm nay thấy hào hứng quá đi! :P")
        except Exception as e:
            logger.error(f"Error getting bot state: {e}")
            return (0.2, 0.8, 0.3, "Hôm nay thấy hào hứng quá đi! :P")

    def update_bot_state(self, v, e, b, r=None):
        """Cập nhật chỉ số tâm lý và nhật ký nội tâm (nếu có)"""
        try:
            if r is not None:
                self.db.execute_query(
                    "UPDATE bot_state SET valence=%s, energy=%s, bond=%s, last_reflection=%s WHERE id=1",
                    (v, e, b, r)
                )
            else:
                self.db.execute_query(
                    "UPDATE bot_state SET valence=%s, energy=%s, bond=%s WHERE id=1",
                    (v, e, b)
                )
        except Exception as e:
            logger.error(f"Error updating bot state: {e}")

    def apply_bond_scar(self, penalty):
        """Áp dụng 'vết sẹo tâm lý' vào chỉ số Bond dài hạn khi có sự cố nghiêm trọng"""
        try:
            state = self.get_bot_state()
            if state:
                v, e, b, r = state
                new_bond = max(0.0, b - penalty)
                self.db.execute_query(
                    "UPDATE bot_state SET bond=%s WHERE id=1",
                    (new_bond,)
                )
        except Exception as e:
            logger.error(f"Error applying bond scar: {e}")

    def get_profile_all(self):
        """Truy xuất toàn bộ hồ sơ thực tế về đối phương"""
        try:
            results = self.db.execute_query(
                "SELECT key, value, confidence FROM profile",
                fetch_all=True
            )
            return [(r[0], r[1], float(r[2])) for r in results] if results else []
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return []

    def get_self_image(self):
        """Truy xuất danh sách các nét tính cách tự nhận thức của Dang Dang"""
        try:
            results = self.db.execute_query(
                "SELECT trait, strength FROM self_image",
                fetch_all=True
            )
            return [(r[0], float(r[1])) for r in results] if results else []
        except Exception as e:
            logger.error(f"Error getting self image: {e}")
            return []

    def get_memories_by_context(self, context_query, limit=5):
        """Ký ức liên đới: Tìm kiếm kỷ niệm dựa trên sự tương đồng và BÙ ĐẮP nếu thiếu (Semantic)"""
        try:
            # Tách từ khóa đơn giản để tìm kiếm
            keywords = [w for w in context_query.split() if len(w) > 3]
            if not keywords:
                return self.get_important_memories(limit)
            
            # Build dynamic query với ILIKE (case-insensitive)
            conditions = " OR ".join(["content ILIKE %s"] * len(keywords))
            params = [f"%{w}%" for w in keywords] + [limit]
            
            results = self.db.execute_query(
                f"""SELECT content FROM episodic_memory 
                    WHERE {conditions}
                    ORDER BY is_core DESC, importance DESC LIMIT %s""",
                tuple(params),
                fetch_all=True
            )
            
            rows = [r[0] for r in results] if results else []
            
            # Logic Bù đắp: Nếu quá ít kết quả, bổ sung bằng kỷ niệm quan trọng nhất
            if len(rows) < 2:
                additional = self.get_important_memories(limit - len(rows))
                return rows + additional
            
            return rows
        except Exception as e:
            logger.error(f"Error getting memories by context: {e}")
            return self.get_important_memories(limit)

    def get_important_memories(self, limit=5):
        """Lấy danh sách ký ức quan trọng (Ưu tiên Core Memory và độ quan trọng cao)"""
        try:
            results = self.db.execute_query(
                """SELECT content FROM episodic_memory 
                   ORDER BY is_core DESC, importance DESC, id DESC LIMIT %s""",
                (limit,),
                fetch_all=True
            )
            return [r[0] for r in results] if results else []
        except Exception as e:
            logger.error(f"Error getting important memories: {e}")
            return []

    def save_message(self, role, content, is_proactive=False, event_id=None):
        """
        Lưu trữ tin nhắn với session tracking
        
        Args:
            role: 'user' hoặc 'model'
            content: Nội dung tin nhắn
            is_proactive: True nếu là proactive message
            event_id: ID của proactive event (nếu có)
        """
        try:
            # Check if need new session
            last_msg_time = self.get_last_message_timestamp()
            
            if self.session_mgr.should_start_new_session(last_msg_time):
                session_id = self.session_mgr.start_session()
            else:
                session_id = self.session_mgr.current_session_id
            
            # Save với session context
            now = datetime.now()
            self.db.execute_query("""
                INSERT INTO messages 
                (role, content, session_id, day_date, timestamp, is_proactive, proactive_event_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (role, content, session_id, now.date(), now, is_proactive, event_id))
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")

    def get_recent_history(self, limit=10):
        """Lấy lịch sử trò chuyện gần nhất theo định dạng yêu cầu của Gemini SDK"""
        try:
            results = self.db.execute_query(
                "SELECT role, content FROM messages ORDER BY id DESC LIMIT %s",
                (limit,),
                fetch_all=True
            )
            
            if not results:
                return []
            
            history = []
            for role, content in reversed(results):
                history.append({"role": role, "parts": [{"text": content}]})
            return history
        except Exception as e:
            logger.error(f"Error getting recent history: {e}")
            return []

    def save_episode(self, content, importance, emotion_tone, is_core=0):
        """Ghi lại một kỷ niệm sự kiện vào bộ nhớ dài hạn"""
        try:
            self.db.execute_query(
                """INSERT INTO episodic_memory (content, importance, emotion_tone, is_core) 
                   VALUES (%s, %s, %s, %s)""",
                (content, importance, emotion_tone, is_core)
            )
        except Exception as e:
            logger.error(f"Error saving episode: {e}")

    def decay_memories(self):
        """Xói mòn ký ức theo thời gian vật lý, bảo vệ ký ức cốt lõi và kỷ niệm mức độ 4-5"""
        try:
            # Kiểm tra thời gian thực hiện decay lần cuối
            result = self.db.execute_query(
                "SELECT value FROM memory_meta WHERE key = 'last_decay_ts'",
                fetch_one=True
            )
            
            if not result:
                return
            
            last_decay = float(result[0])
            now = time.time()
            
            # Chỉ thực hiện decay sau mỗi 1 giờ vật lý
            if (now - last_decay) < 3600:
                return

            # Logic bảo vệ linh hồn: Chỉ giảm tầm quan trọng của ký ức thường
            self.db.execute_query(
                """UPDATE episodic_memory 
                   SET importance = importance - 1 
                   WHERE is_core = 0 AND importance > 1 AND importance < 4"""
            )
            
            # Loại bỏ hoàn toàn các ký ức đã phai mờ
            self.db.execute_query(
                "DELETE FROM episodic_memory WHERE importance <= 0 AND is_core = 0"
            )
            
            # Cập nhật dấu thời gian
            self.db.execute_query(
                "UPDATE memory_meta SET value = %s WHERE key = 'last_decay_ts'",
                (str(now),)
            )
            
            logger.info("🧹 Memory decay completed")
        except Exception as e:
            logger.error(f"Error during memory decay: {e}")