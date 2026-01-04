import sqlite3
import json
import time
from datetime import datetime

class MemoryManager:
    def __init__(self, db_path="dangdang_memory.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Khởi tạo cấu trúc cơ sở dữ liệu với đầy đủ các bảng chức năng"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Bảng lưu trữ trạng thái thực thể (Mood, Energy, Bond, Reflection)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_state (
                    id INTEGER PRIMARY KEY,
                    valence REAL,
                    energy REAL,
                    bond REAL,
                    last_reflection TEXT
                )
            """)
            
            # 2. Bảng tin nhắn (Bộ nhớ ngắn hạn - Short-term memory)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 3. Bảng hồ sơ NGƯỜI DÙNG (Dữ liệu thực tế về đối phương)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profile (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    confidence REAL
                )
            """)
            
            # 4. Bảng ký ức sự kiện (Episodic Memory) - Có is_core để bảo vệ ký ức cốt lõi
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    importance INTEGER,
                    emotion_tone TEXT,
                    is_core INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 5. Bảng bản ngã DANG DANG (Tự nhận thức về tính cách bản thân)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS self_image (
                    trait TEXT PRIMARY KEY,
                    strength REAL
                )
            """)

            # 6. Bảng Meta để quản lý các thông số hệ thống như thời gian Decay
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Kiểm tra và khởi tạo dữ liệu mặc định cho trạng thái
            cursor.execute("SELECT COUNT(*) FROM bot_state")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO bot_state VALUES (1, 0.0, 0.5, 0.2, '')")
            
            # Kiểm tra và khởi tạo thời gian decay lần cuối
            cursor.execute("SELECT COUNT(*) FROM memory_meta WHERE key = 'last_decay_ts'")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO memory_meta VALUES ('last_decay_ts', ?)", (str(time.time()),))
            
            conn.commit()

    def get_last_message_timestamp(self):
        """Lấy dấu thời gian của tin nhắn cuối cùng để tính toán khoảng lặng (Time Gap)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp FROM messages ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return row[0]
            return None

    def update_profile(self, key, value, confidence):
        """Cập nhật hồ sơ User với logic kiểm soát niềm tin (Identity Isolation)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT confidence FROM profile WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            if row:
                old_conf = row[0]
                # Chỉ overwrite nếu tin cậy mới đủ cao để lung lay niềm tin cũ (ngưỡng 90%)
                if confidence > (old_conf * 0.9):
                    cursor.execute("UPDATE profile SET value = ?, confidence = ? WHERE key = ?", 
                                 (value, confidence, key))
            else:
                # Đảm bảo đúng trật tự: key, value, confidence
                cursor.execute("INSERT INTO profile (key, value, confidence) VALUES (?, ?, ?)", 
                             (key, value, confidence))
            conn.commit()

    def update_self_image(self, trait, strength):
        """Cập nhật bản ngã bằng công thức Moving Average để tính cách không đổi đột ngột"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT strength FROM self_image WHERE trait = ?", (trait,))
            row = cursor.fetchone()
            
            if row:
                old_strength = row[0]
                # Công thức: 90% tính cách cũ + 10% tác động mới
                new_strength = (old_strength * 0.9) + (strength * 0.1)
                cursor.execute("UPDATE self_image SET strength = ? WHERE trait = ?", (new_strength, trait))
            else:
                cursor.execute("INSERT INTO self_image (trait, strength) VALUES (?, ?)", (trait, strength))
            conn.commit()

    def get_bot_state(self):
        """Lấy toàn bộ trạng thái hiện tại của Dang Dang"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT valence, energy, bond, last_reflection FROM bot_state WHERE id = 1")
            return cursor.fetchone()

    def update_bot_state(self, v, e, b, r=None):
        """Cập nhật chỉ số tâm lý và nhật ký nội tâm (nếu có)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if r is not None:
                cursor.execute("UPDATE bot_state SET valence=?, energy=?, bond=?, last_reflection=? WHERE id=1", 
                             (v, e, b, r))
            else:
                cursor.execute("UPDATE bot_state SET valence=?, energy=?, bond=? WHERE id=1", (v, e, b))
            conn.commit()

    def apply_bond_scar(self, penalty):
        """Áp dụng 'vết sẹo tâm lý' vào chỉ số Bond dài hạn khi có sự cố nghiêm trọng"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            state = self.get_bot_state()
            if state:
                v, e, b, r = state
                new_bond = max(0.0, b - penalty)
                cursor.execute("UPDATE bot_state SET bond=? WHERE id=1", (new_bond,))
            conn.commit()

    def get_profile_all(self):
        """Truy xuất toàn bộ hồ sơ về người dùng"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value, confidence FROM profile")
            return cursor.fetchall()

    def get_self_image(self):
        """Truy xuất danh sách các nét tính cách của Dang Dang"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT trait, strength FROM self_image")
            return cursor.fetchall()

    def get_important_memories(self, limit=5):
        """Lấy danh sách ký ức quan trọng (Ưu tiên Core Memory và độ quan trọng cao)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT content FROM episodic_memory 
                ORDER BY is_core DESC, importance DESC, id DESC LIMIT ?
            """, (limit,))
            return [row[0] for row in cursor.fetchall()]

    def save_message(self, role, content):
        """Lưu trữ tin nhắn vào bộ nhớ ngắn hạn"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))
            conn.commit()

    def get_recent_history(self, limit=10):
        """Lấy lịch sử trò chuyện gần nhất theo định dạng yêu cầu của Gemini SDK"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            history = []
            for role, content in reversed(rows):
                history.append({"role": role, "parts": [{"text": content}]})
            return history

    def save_episode(self, content, importance, emotion_tone, is_core=0):
        """Ghi lại một kỷ niệm sự kiện vào bộ nhớ dài hạn"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO episodic_memory (content, importance, emotion_tone, is_core) 
                VALUES (?, ?, ?, ?)
            """, (content, importance, emotion_tone, is_core))
            conn.commit()

    def decay_memories(self):
        """Xói mòn ký ức theo thời gian vật lý, bảo vệ ký ức cốt lõi và kỷ niệm mức độ 4-5"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Kiểm tra thời gian thực hiện decay lần cuối (An toàn hơn với Null Check)
            cursor.execute("SELECT value FROM memory_meta WHERE key = 'last_decay_ts'")
            last_decay_row = cursor.fetchone()
            if not last_decay_row:
                return

            last_decay = float(last_decay_row[0])
            now = time.time()
            
            # Chỉ thực hiện decay sau mỗi 1 giờ vật lý
            if (now - last_decay) < 3600:
                return

            # Logic: Chỉ giảm tầm quan trọng của các ký ức thông thường (không phải Core)
            # và các ký ức có độ quan trọng thấp (< 4). Ký ức mức 4 và 5 được bảo vệ.
            cursor.execute("""
                UPDATE episodic_memory 
                SET importance = importance - 1 
                WHERE is_core = 0 AND importance > 1 AND importance < 4
            """)
            
            # Loại bỏ hoàn toàn các ký ức đã phai mờ (importance về 0)
            cursor.execute("DELETE FROM episodic_memory WHERE importance <= 0 AND is_core = 0")
            
            # Cập nhật dấu thời gian thực hiện decay mới nhất
            cursor.execute("UPDATE memory_meta SET value = ? WHERE key = 'last_decay_ts'", (str(now),))
            conn.commit()