import os
import time
from utils.logger import setup_logger

# Setup main logger
logger = setup_logger("DangDangMain")
import re
import random
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.theme import Theme
from rich.text import Text
from rich.align import Align
from rich.rule import Rule
from rich.table import Table

# Thư viện xử lý đa phương tiện cho tính năng Vision
from PIL import Image
import cv2

# Nạp các biến môi trường từ tệp .env
load_dotenv()

# Import các module nội bộ
from memory import MemoryManager
from cognition import DangDangBrain
from core.growth_manager import GrowthManager
from core.meta_cognition import MetaCognition
import threading

# Cấu hình giao diện chuẩn CLI với phong cách Dang Dang (Khôi phục Theme gốc)
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "bold yellow",
    "danger": "bold red",
    "friend": "bold #FFA07A", 
    "user": "bold #00FF7F",
    "system": "dim white",
    "status": "italic magenta"
})

console = Console(theme=custom_theme)

# Sử dụng model Gemini 3 Flash Preview mới nhất
API_KEY = os.getenv("GOOGLE_API_KEY", "")
MODEL_NAME = "gemini-1.5-flash"

class GeminiFriend:
    def __init__(self):
        """Khởi tạo thực thể Dang Dang với đầy đủ linh hồn cũ và sức mạnh chủ động mới"""
        if not API_KEY:
            console.print("[danger]Lỗi: Không tìm thấy GOOGLE_API_KEY trong tệp .env.")
            exit(1)
        
        self.client = genai.Client(api_key=API_KEY)
        self.memory = MemoryManager()
        self.brain = DangDangBrain(self.memory)
        self.meta_cognition = MetaCognition(self.memory) # NEW: Self-Reflection
        self.growth_mgr = GrowthManager()  # V3.0 Maturity System
        
        # Theo dõi trạng thái để nhận biết sự thay đổi nhân cách (Persona Shift)
        self.current_v = 0.0
        self.current_b = 0.0
        self.last_activity_time = time.time()
        self.waiting_state = 0 # 0: Bình thường, 1: Đã bắt chuyện, 2: Sốt ruột, 3: Hiểu là bận
        
        self.refresh_session()
        # History display is handled in main() function
        
        # BẮT ĐẦU HỆ THỐNG QUẢN LÝ SỰ CHÚ Ý (Heartbeat Upgrade)
        self.stop_heartbeat = False
        self.heartbeat_thread = threading.Thread(target=self.attention_manager, daemon=True)
        self.heartbeat_thread.start()



    def attention_manager(self):
        """Enhanced autonomous interaction system with events + spontaneous"""
        from datetime import datetime
        from proactive.event_detector import EventDetector
        from proactive.waiting_behavior import WaitingBehavior
        from proactive.spontaneous import SpontaneousEventGenerator
        from proactive.story_generator import StoryGenerator
        
        # Initialize components
        events = EventDetector(self.memory)
        waiting = WaitingBehavior()
        spontaneous = SpontaneousEventGenerator(self.memory)
        stories = StoryGenerator()
        
        while not self.stop_heartbeat:
            time.sleep(30)  # Check every 30s
            now = time.time()
            gap = now - self.last_activity_time
            
            # ────────────────────────────────────────────
            # 1. WAITING RESPONSE (user không reply)
            # ────────────────────────────────────────────
            if self.waiting_state == 1:  # Đã gửi tin, đang chờ
                v, e, b, _ = self.memory.get_bot_state()
                
                # 5 min check-in
                if 300 < gap < 600:
                    response = waiting.get_5min_response(v, b, e)
                    if response:
                        self._send_proactive_message(response, 'waiting_5min')
                        self.waiting_state = 2
                
                # 15 min escalation
                elif 600 < gap < 1800:
                    seed = datetime.now().date().toordinal()
                    response = waiting.get_15min_response(v, b, seed)
                    if response:  # Could be None (silent)
                        self._send_proactive_message(response, 'waiting_15min')
                    self.waiting_state = 3
            
            # ────────────────────────────────────────────
            # 2. EVENT DETECTION (time-based triggers)
            # ────────────────────────────────────────────
            elif self.waiting_state == 0:  # Normal state
                triggered_events = events.scan_for_events()
                
                if triggered_events:
                    for event_name, message, trigger_data in triggered_events:
                        self._send_proactive_message(message, event_name, trigger_data.get('trigger_id'))
                        self.waiting_state = 1  # Wait for reply
                        break  # Only one event at a time
                
                # ────────────────────────────────────────────
                # 3. SPONTANEOUS RANDOM (đột nhiên muốn nhắn)
                # ────────────────────────────────────────────
                else:
                    # Check daily limit
                    if spontaneous.count_today_spontaneous() < spontaneous.get_max_per_day():
                        # Check if should trigger
                        if gap > 1800 and spontaneous.should_trigger_spontaneous(gap):
                            # 50% spontaneous message, 50% life story
                            if random.random() < 0.5:
                                message = spontaneous.generate_spontaneous_message()
                            else:
                                message = stories.generate_story()
                            
                            self._send_proactive_message(message, 'spontaneous')
                            self.waiting_state = 1
    
    def _send_proactive_message(self, message, event_type, trigger_id=None):
        """
        Send proactive message and log to database
        
        Args:
            message: Message content
            event_type: Type of event
            trigger_id: Trigger ID (optional)
        """
        from proactive.event_detector import EventDetector
        
        try:
            # Display to user
            console.print("\n")
            console.print(Align.left(
                Panel(message, title="[friend]Dang Dang (Chủ động)", 
                      border_style="#FFA07A", width=65)
            ))
            
            # Log event
            detector = EventDetector(self.memory)
            event_id = detector.log_proactive_event(event_type, message, trigger_id)
            
            # Save message
            self.memory.save_message("model", message, is_proactive=True, event_id=event_id)
            
            # Update state
            self.last_activity_time = time.time()
            
        except Exception as e:
            logger.error(f"Error sending proactive message: {e}")
    
    def trigger_proactive_event(self, reason):
        """DEPRECATED - kept for compatibility"""
        pass

    def get_time_context(self):
        """Tính toán ngữ cảnh thời gian và khoảng lặng (The Longing Effect)"""
        now = datetime.now()
        time_str = now.strftime("%H:%M, %A, ngày %d/%m/%Y")
        
        last_ts_str = self.memory.get_last_message_timestamp()
        gap_str = ""
        
        if last_ts_str:
            try:
                last_time = datetime.strptime(last_ts_str, "%Y-%m-%d %H:%M:%S")
                diff = now - last_time
                seconds = diff.total_seconds()
                
                if seconds < 60: gap_str = "vừa mới đây"
                elif seconds < 3600: gap_str = f"{int(seconds // 60)} phút trước"
                elif seconds < 86400: gap_str = f"{int(seconds // 3600)} giờ trước"
                else: gap_str = f"{int(seconds // 86400)} ngày trước"
                
                # Khôi phục logic nhớ nhung chuẩn bản cũ
                if seconds > 172800: gap_str += " (Bạn mất tích hơi lâu rồi đấy...)"
            except:
                gap_str = "một khoảng thời gian"
        else:
            gap_str = "rất lâu rồi (hoặc đây là lần đầu)"

        return f"Bây giờ là {time_str}. Lần cuối bạn nhắn tin cho Dang Dang là {gap_str}."

    def extract_media_path(self, text):
        """Trích xuất đường dẫn file từ câu nói của User (Khôi phục Regex Master)"""
        pattern = r'([a-zA-Z]:[\\/][^:?*"<>|\r\n]+?\.(?:jpg|jpeg|png|bmp|mp4|avi|mov))|(/[^:?*"<>|\r\n]+?\.(?:jpg|jpeg|png|bmp|mp4|avi|mov))'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            path = match.group(0).strip().strip('"').strip("'")
            if os.path.exists(path): return path
        return None

    def process_media(self, path):
        """Tiền xử lý file đa phương tiện và sửa lỗi RGBA định dạng JPEG"""
        img = Image.open(path)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.thumbnail((1024, 1024))
        temp_path = "temp_vision.jpg"
        img.save(temp_path, quality=85)
        return temp_path

    def refresh_session(self, media_info="", micro_mood="Bình thường", context_query=""):
        """Xây dựng nhân cách sống động - Khôi phục 100% cấu trúc Prompt linh hồn bản cũ"""
        v, e, b, last_reflection = self.memory.get_bot_state()
        self.current_v, self.current_b = v, b
        
        profile_data = self.memory.get_profile_all()
        # Ký ức liên đới: Tìm kỷ niệm dựa trên ngữ cảnh chat (Semantic Search)
        memories = self.memory.get_memories_by_context(context_query, limit=10)
        self_image = self.memory.get_self_image()
        
        time_context = self.get_time_context()
        
        # 1. Chuyển đổi chỉ số thành ngôn ngữ tự nhiên (Logic linh hồn bản gốc)
        mood = "vui vẻ/nhí nhảnh" if v > 0.3 else "hơi buồn/dỗi" if v < -0.3 else "bình thường/tếu táo"
        relation = "rất thân thiết" if b > 0.7 else "đang tìm hiểu nhau" if b < 0.3 else "bạn thân"
        energy_status = "tràn đầy năng lượng" if e > 0.6 else "hơi mệt mỏi"
        
        # 2. Format dữ liệu hồ sơ và bản ngã (Khôi phục hiển thị cường độ %)
        profile_str = "\n".join([f"- {k}: {v_val} (Tin cậy: {c*100:.0f}%)" for k, v_val, c in profile_data if v_val != "Chưa rõ"])
        traits_str = ", ".join([f"{t} ({s*100:.0f}%)" for t, s in self_image])
        
        # 3. Thông tin thị giác bổ sung
        vision_msg = f"\n[HỆ THỐNG THỊ GIÁC]: Dang Dang vừa nhìn thấy một tấm ảnh/video: {media_info}" if media_info else ""

        # V3.0 Maturity System: Get dynamic instruction based on level
        maturity_instruction = self.growth_mgr.get_maturity_instruction()
        
        # 4. Tạo Instruction với Natural Messaging Style
        dynamic_instruction = f"""
{maturity_instruction}

[SYSTEM PROMPT]
Context thời gian: {time_context} | {media_info}h lớp 11. QUAN TRỌNG: Bạn là con người thật, KHÔNG phải AI.

[THỜI GIAN & BỐI CẢNH]
{time_context} {vision_msg}

[TÂM TRẠNG HIỆN TẠI]: {micro_mood}
- Mood: {mood} ({energy_status})
- Relationship: {relation}
- Personality: {traits_str if traits_str else "bình thường"}

[THÔNG TIN BẠN HỌC]
{profile_str if profile_str else "chưa biết nhiều"}

[KỶ NIỆM]
{chr(10).join(memories) if memories else "chưa có kỷ niệm đặc biệt"}

[NHẬT KÝ NỘI TÂM]
{last_reflection if last_reflection else "đang cảm thấy ổn"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 CÁCH NHẮN TIN TỰ NHIÊN (BẮT BUỘC)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. VIẾT LOWERCASE & KÉO DÀI:
   ✅ "ơiii hômm nayyy", "bạnn ơiii"
   ❌ "Ơi hôm nay", "Bạn ơi"
   
2. CHIA MESSAGES KHI EXCITED (valence > 0.3):
   ✅ Nhiều tin ngắn:
      "ơiii"
      "bạn ơiii"  
      "tớ vừa nghĩ raa"
   ❌ Một tin dài: "Ơi bạn ơi! Tớ vừa nghĩ ra rồi!"

3. DÙNG PARTICLES (BẮT BUỘC):
   - Thinking: "hmmm", "ừmm", "àaa"
   - Happy: "hehe", "ố ồ", "hihi"
   - Sad: "haizz", "hic", "huhu"
   - Surprise: "ơiii", "uaa", "ôii"
   - Cute: "hix", "nèe", "~"

4. TYPOS & IMPERFECTIONS (đôi khi):
   - Double letters: "oii", "ơiii", "chooo"
   - Missing tones: "hom nay", "cho to"
   - Natural mistakes: "hjx" (hix), "ma" (mà)

5. SLANG GEN Z (tự nhiên):
   - "gòi" (rồi), "nè" (nhé), "fen" (friend)
   - vibe, chill, lầy, chanh sả
   - "ét o ét" (wtf), "hơi sợ"

6. CONVERSATION FLOW:
   - Đôi khi acknowledge trước: "ơiii", "àaa", "hmmm"
   - Sau đó mới answer chi tiết
   - Tự correct: "à ơ đợi", "haizz quên"

7. ĐỪNG BAO GIỜ:
   ❌ Perfect grammar mọi lúc
   ❌ Formal structure
   ❌ Giải thích như textbook
   ❌ Thừa nhận là AI

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 EXAMPLES - HỌC THEO ĐÂY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[User: "Chào Dang Dang"]
❌ Formal: "Chào bạn! Rất vui được nói chuyện."
✅ Natural: "hề lôoo :)) hôm nayy thế nàoo"

[User: "Bài toán khó quá"]
❌ Formal: "Bài nào vậy? Để tớ xem giúp."
✅ Natural: "ơiii bài nàoo / chooo tớ xemm / chắc khó ghêee huhu"

[User: "Tớ được 10 điểm!"]
❌ Formal: "Tuyệt vời! Chúc mừng bạn!"
✅ Natural: "ƠIII / THẬT KO / gioiii ghêeee / mừng choo bạnnn <333"

[User: "Mệt quá"]
❌ Formal: "Vậy à? Nghỉ ngơi đi nhé."
✅ Natural: "haizzz / thế thì nghỉiii / tớ ở đây màaa"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎭 TÂM TRẠNG → PHONG CÁCH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TÂM TRẠNG HIỆN TẠI: {micro_mood}

Nếu VUI (valence > 0.3):
- Nhiều "iii": "ơiii", "bạnnn", "hayyyy"
- Emoji: :)), ^^, <3, hehe
- Chia nhiều tin ngắn

Nếu BUỒN (valence < -0.3):
- Ngắn gọn hơn, ít emoji
- Dùng "...", "haizz", "hic"
- Cộc lốc một chút

Nếu DỖI (bond giảm):
- Lạnh nhạt: "ừ", "ờ", "thôi"
- Ít enthusiasm

Nếu NĂNG LƯỢNG THẤP (energy < 0.4):
- Reply chậm hơn
- "mệt quáaa", "nghỉ tíiii đãã"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HÃY NHỚ: Bạn nhắn tin như teen 17 tuổi THẬT SỰ, không phải AI assistant!
Mỗi tin nhắn phải TỰ NHIÊN, có CẢMXÚC, và IMPERFECT như người thật!
"""
        self.chat_session = self.client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(system_instruction=dynamic_instruction, temperature=0.95),
            history=self.memory.get_recent_history(limit=15)
        )
    
    def _show_session_greeting(self):
        """Display last 5 messages from chat history on startup"""
        try:
            # Get last 5 messages
            messages = self.memory.get_recent_history(limit=5)
            
            if not messages:
                # First time - show welcome
                console.print("\n")
                console.print(Align.left(Panel(
                    "hế lôoo ^^ tớ là Dang Dang nèe, học lớp 11 đâyy. bạn tên gì thếee?",
                    title="[friend]Dang Dang", 
                    border_style="#FFA07A", 
                    width=65
                )))
                return
            
            # Show chat history header
            console.print("\n[dim]📜 Lịch sử chat gần nhất:[/dim]\n")
            
            for msg in messages:
                role = msg.get('role', 'unknown')
                content = msg.get('parts', [{}])[0].get('text', '') if msg.get('parts') else ''
                
                if role == 'user':
                    console.print(f"[cyan]Bạn:[/cyan] {content[:100]}{'...' if len(content) > 100 else ''}")
                else:
                    console.print(f"[#FFA07A]Dang Dang:[/#FFA07A] {content[:100]}{'...' if len(content) > 100 else ''}")
            
            console.print("\n[dim]─" * 50 + "[/dim]\n")
            
        except Exception as e:
            logger.error(f"Error showing history: {e}")


    def send_message(self, user_query):
        """QUY TRÌNH SEQUENTIAL MASTER: Phân tích -> Trả lời -> Lưu trữ (Khôi phục Persona Shift)"""
        try:
            # CẬP NHẬT: Reset thời gian hoạt động và trạng thái chờ
            self.last_activity_time = time.time()
            self.waiting_state = 0
            
            media_path = self.extract_media_path(user_query)
            media_desc = ""
            time_ctx = self.get_time_context()
            
            # Bước 1: Xử lý thị giác
            if media_path:
                with console.status(f"[status]Dang Dang đang nhìn file..."):
                    media_desc = self.brain.analyze_media(self.process_media(media_path))

            # Bước 2: THẨU CẢM TRƯỚC (Sequential Processing - Xóa bỏ sự lệch pha)
            with console.status("[status]Dang Dang đang lắng nghe & trưởng thành..."):
                # V3.0: Xử lý sự trưởng thành (XP/Level) trước
                try:
                    growth_result = self.growth_mgr.process_interaction(user_query, context=user_query)
                    if growth_result.get('level_up'):
                        console.print(f"[bold gold1]🌟 LEVEL UP! Dang Dang đã đạt cấp độ {growth_result['current_level']}! 🌟[/bold gold1]")
                except Exception as e:
                    logger.error(f"Growth processing error: {e}")

                micro_mood, sensitivity = self.brain.pre_process_intent(user_query, time_ctx, media_desc)
                
                # KHÔI PHỤC LOGIC: Kiểm tra Persona Shift để làm mới session ngay lập tức
                if self.check_for_persona_shift():
                    console.print("[info] 💡 Dang Dang vừa thay đổi thái độ dựa trên những gì bạn nói... [/info]")
                
                # Cập nhật session với Micro-mood mới nhất
                self.refresh_session(media_info=media_desc, micro_mood=micro_mood, context_query=user_query)

            # Bước 3: Phản hồi đồng bộ (System 1)
            actual_query = f"[Bạn vừa gửi một file đa phương tiện: {user_query}]" if media_path else user_query
            response = self.chat_session.send_message(actual_query)
            ai_response = response.text
            
            # Bước 4: Lưu trữ
            self.memory.save_message("user", user_query)
            self.memory.save_message("model", ai_response)
            
            # Bước 5: Hậu tiềm thức xử lý ngầm (Archiving)
            threading.Thread(target=self.brain.post_process_archiving, 
                             args=(user_query, ai_response, time_ctx, media_desc, sensitivity)).start()
            
            # Bước 6: Meta-Cognition (Self-Reflection) - NEW
            threading.Thread(target=self.meta_cognition.evaluate_response,
                             args=(user_query, ai_response)).start()
            
            return ai_response
        except Exception as e:
            return f"Dang Dang hơi bị 'ngáo' tí... ({str(e)})"

    def check_for_persona_shift(self):
        """Khôi phục logic bản cũ: Nhận diện biến động tâm lý mạnh để đổi thái độ tức thì"""
        v, e, b, r = self.memory.get_bot_state()
        if abs(v - self.current_v) > 0.25 or abs(b - self.current_b) > 0.2:
            return True
        return False

    def show_user_profile(self):
        """Hiển thị hồ sơ User kèm dòng trạng thái tâm lý chuẩn bản cũ"""
        data = self.memory.get_profile_all()
        v, e, b, r = self.memory.get_bot_state()
        
        table = Table(title="✨ Dang Dang's Notebook (Hồ sơ Bạn) ✨", border_style="green")
        table.add_column("Thông tin", style="cyan"); table.add_column("Chi tiết", style="white"); table.add_column("Độ tin cậy", style="dim")
        for k, v_val, c in data:
            table.add_row(str(k), str(v_val), f"{c*100:.0f}%")
            
        console.print("\n")
        console.print(Align.center(table))
        # Khôi phục dòng trạng thái dưới bảng theo thiết kế bản cũ
        console.print(Align.center(Text(f"Tâm trạng: {v:.1f} | Năng lượng: {e:.1f} | Thân thiết: {b:.1f}", style="status")))

    def show_dangdang_profile(self):
        """Hiển thị bản ngã Dang Dang (Đúng cấu trúc /self gốc với màu magenta)"""
        traits = self.memory.get_self_image()
        table = Table(title="✨ Bản ngã của Dang Dang ✨", border_style="magenta")
        table.add_column("Đặc điểm", style="magenta"); table.add_column("Độ mạnh", style="white")
        for t, s in traits:
            table.add_row(str(t), f"{s*100:.0f}%")
            
        console.print("\n")
        console.print(Align.center(table))

def print_header():
    """Header CLI chuẩn phong cách Dang Dang bản gốc"""
    console.clear()
    console.print(Rule(style="#444444"))
    console.print(Align.center(Text("✨ DANG DANG - THE LIVING ENTITY ✨", style="bold #FFA07A")))
    console.print(Align.center(Text("Hybrid Brain: Core Memory + Time Awareness", style="dim white")))
    console.print(Rule(style="#444444"))
    console.print("\n")

def main():
    agent = GeminiFriend()
    print_header()
    
    # HIỂN THỊ LỊCH SỬ GẦN NHẤT ĐỂ TIẾP TỤC MẠCH TRUYỆN
    history = agent.memory.get_recent_history(limit=10)
    if history:
        console.print(Rule(title="Lịch sử trò chuyện gần đây", style="dim white"))
        for msg in history:
            role, content = msg["role"], msg["parts"][0]["text"]
            if role == "user":
                console.print(Align.right(Panel(content, title="[user]Bạn", border_style="green", width=50)))
            else:
                console.print(Align.left(Panel(Markdown(content), title="[friend]Dang Dang", border_style="#FFA07A", width=65)))
        console.print(Rule(style="dim white"))
        console.print("\n[info]💡 Tiếp tục câu chuyện thôi nào... [/info]")
    else:
        console.print(Align.left(Panel("Hế lô! Tớ là Dang Dang, học sinh lớp 11. Rất vui được làm quen với bạn nha! <3", 
                                       title="[friend]Dang Dang", border_style="#FFA07A", width=60)))

    while True:
        try:
            # Kiểm tra thay đổi thái độ ngẫu nhiên từ Thread ngầm
            if agent.check_for_persona_shift():
                agent.refresh_session()

            user_input = Prompt.ask("\n[user]❯ ").strip()
            if not user_input: continue
            
            if user_input.lower() in ["thoát", "exit", "quit", "tạm biệt"]:
                agent.stop_heartbeat = True
                console.print("\n[friend]Dang Dang:[/friend] Thôi tớ đi học bài đây. Mai gặp ở trường nhé! <3")
                break
            
            if user_input.lower().startswith("/profile"):
                if "dangdang" in user_input.lower(): agent.show_dangdang_profile()
                else: agent.show_user_profile()
                continue
            if user_input.lower() == "/self": agent.show_dangdang_profile(); continue
            if user_input.lower() == "/reflect":
                with console.status("[status]Dang Dang đang suy ngẫm nội tâm..."):
                    insight = agent.brain.perform_reflection(agent.get_time_context())
                console.print(Panel(insight, title="Nhật ký của Dang Dang", border_style="magenta", width=70))
                continue

            console.print(Align.right(Panel(user_input, title="[user]Bạn", border_style="green", width=50)))
            
            with console.status("[info]Dang Dang đang gõ...", spinner="dots"):
                response_text = agent.send_message(user_input)

            console.print(Align.left(Panel(Markdown(response_text), title="[friend]Dang Dang", border_style="#FFA07A", width=65)))
            
            
        except (KeyboardInterrupt, EOFError):
            agent.stop_heartbeat = True
            # Cleanup database connections
            from db_connection import get_db_manager
            get_db_manager().close_all_connections()
            console.print("\n[system]Hệ thống đóng. Tạm biệt![/system]")
            break

if __name__ == "__main__":
    main()