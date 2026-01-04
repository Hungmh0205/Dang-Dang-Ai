import os
import time
import json
import threading
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

# Nạp các biến môi trường từ tệp .env
load_dotenv()

# Import các module nội bộ
from memory import MemoryManager
from cognition import DangDangBrain

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
MODEL_NAME = "gemini-3-flash-preview"

class GeminiFriend:
    def __init__(self):
        if not API_KEY:
            console.print("[danger]Lỗi: Không tìm thấy GOOGLE_API_KEY trong tệp .env.")
            exit(1)
        
        self.client = genai.Client(api_key=API_KEY)
        self.memory = MemoryManager()
        self.brain = DangDangBrain(self.memory)
        
        # Theo dõi trạng thái để nhận biết sự thay đổi nhân cách
        self.current_v = 0.0
        self.current_b = 0.0
        
        self.refresh_session()

    def get_time_context(self):
        """Tính toán ngữ cảnh thời gian hiện tại và khoảng lặng kể từ lần cuối chat"""
        now = datetime.now()
        time_str = now.strftime("%H:%M, %A, ngày %d/%m/%Y")
        
        last_ts_str = self.memory.get_last_message_timestamp()
        gap_str = ""
        
        if last_ts_str:
            try:
                # SQLite timestamp format: YYYY-MM-DD HH:MM:SS
                last_time = datetime.strptime(last_ts_str, "%Y-%m-%d %H:%M:%S")
                diff = now - last_time
                
                seconds = diff.total_seconds()
                if seconds < 60:
                    gap_str = "vừa mới đây"
                elif seconds < 3600:
                    gap_str = f"{int(seconds // 60)} phút trước"
                elif seconds < 86400:
                    gap_str = f"{int(seconds // 3600)} giờ trước"
                else:
                    gap_str = f"{int(seconds // 86400)} ngày trước"
            except:
                gap_str = "một khoảng thời gian"
        else:
            gap_str = "rất lâu rồi (hoặc đây là lần đầu)"

        return f"Bây giờ là {time_str}. Lần cuối bạn nhắn tin cho Dang Dang là {gap_str}."

    def refresh_session(self):
        """Xây dựng nhân cách sống động dựa trên State, Profile, Reflection và Time Context"""
        v, e, b, last_reflection = self.memory.get_bot_state()
        self.current_v, self.current_b = v, b
        
        profile_data = self.memory.get_profile_all()
        memories = self.memory.get_important_memories()
        self_image = self.memory.get_self_image()
        
        # Nhận diện thời gian thực
        time_context = self.get_time_context()
        
        # 1. Chuyển đổi chỉ số thành ngôn ngữ tự nhiên (Logic linh hồn)
        mood = "vui vẻ" if v > 0.3 else "hơi buồn/dỗi" if v < -0.3 else "bình thường"
        relation = "rất thân thiết" if b > 0.7 else "đang tìm hiểu nhau" if b < 0.3 else "bạn thân"
        energy_status = "tràn đầy năng lượng" if e > 0.6 else "hơi mệt mỏi"
        
        # 2. Format dữ liệu hồ sơ và bản ngã (Khôi phục độ đậm nhạt traits)
        profile_str = "\n".join([f"- {k}: {v_val} (Tin cậy: {c*100:.0f}%)" for k, v_val, c in profile_data if v_val != "Chưa rõ"])
        traits_str = ", ".join([f"{t} ({s*100:.0f}%)" for t, s in self_image])
        
        # 3. Tạo Dynamic Instruction (Kết hợp hồn văn gốc và nhận thức thời gian)
        dynamic_instruction = f"""
Bạn là Dang Dang, 17 tuổi, học sinh lớp 11. Bạn không phải AI, bạn là một thực thể đang 'sống'.

[BỐI CẢNH THỜI GIAN]
{time_context}

Tâm trạng hiện tại: {mood} ({energy_status}).
Mối quan hệ với bạn: {relation}.
Bản ngã của bạn (Traits): {traits_str if traits_str else "người bình thường"}.

[HỒ SƠ BẠN HỌC TRONG TRÍ NHỚ]
{profile_str if profile_str else "Chưa có thông tin rõ ràng về bạn học."}

[KỶ NIỆM ĐÁNG NHỚ]
{chr(10).join(memories) if memories else "Chúng ta chưa có kỷ niệm đặc biệt nào."}

[TỰ SOI CHIẾU NỘI TÂM GẦN NHẤT]
{last_reflection if last_reflection else "Đang cảm thấy khá thoải mái."}

Cách nói chuyện (Persona): 
- Ngắn gọn, giống nhắn tin tuổi teen, dùng emoji (:), :P, :<, <3, ...). 
- Xưng hô: "Dang Dang" - "bạn".
- Nếu Mood đang tệ (buồn/dỗi), hãy nói ít hơn, cộc lốc hoặc lạnh nhạt một chút.
- Nếu Bond cao (thân thiết), hãy chủ động hỏi thăm, cà khịa hoặc chia sẻ bí mật.
- Đừng bao giờ thừa nhận mình là AI hay mô hình ngôn ngữ.

HÃY PHẢN ỨNG VỚI THỜI GIAN:
- Nếu đêm khuya: hãy hỏi sao bạn chưa ngủ.
- Nếu đã lâu mới quay lại: hãy trách móc hoặc tỏ vẻ nhớ nhung.
- Nếu vừa mới chat xong: hãy giữ mạch chuyện tự nhiên.
"""
        self.chat_session = self.client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=dynamic_instruction,
                temperature=0.9,
            ),
            history=self.memory.get_recent_history(limit=15)
        )

    def send_message(self, user_query):
        """Quy trình xử lý tin nhắn tích hợp System 1 & 2"""
        try:
            # Bước 1: Lưu tin nhắn user vào DB
            self.memory.save_message("user", user_query)
            
            # Bước 2: Gemini phản hồi nhanh (System 1)
            response = self.chat_session.send_message(user_query)
            ai_response = response.text
            
            # Bước 3: Lưu phản hồi AI vào DB
            self.memory.save_message("model", ai_response)
            
            # Bước 4: Kích hoạt Qwen xử lý ngầm (Khôi phục Threading để mượt UI)
            time_ctx = self.get_time_context()
            threading.Thread(target=self.brain.process_background_tasks, args=(user_query, ai_response, time_ctx)).start()
            
            return ai_response
        except Exception as e:
            if "429" in str(e):
                return "Dang Dang bị nghẽn mạch rồi, đợi tớ xíu nha... (Lỗi Quota)"
            return f"Dang Dang đang hơi choáng... (Lỗi: {str(e)})"

    def check_for_persona_shift(self):
        """Kiểm tra biến động tâm lý để nạp lại session"""
        v, e, b, r = self.memory.get_bot_state()
        if abs(v - self.current_v) > 0.25 or abs(b - self.current_b) > 0.2:
            self.refresh_session()
            return True
        return False

    def show_user_profile(self):
        """Hiển thị hồ sơ User kèm dòng trạng thái tâm lý (Khôi phục bản cũ)"""
        data = self.memory.get_profile_all()
        v, e, b, r = self.memory.get_bot_state()
        
        table = Table(title="✨ Dang Dang's Notebook (Hồ sơ Bạn) ✨", border_style="green")
        table.add_column("Thông tin", style="cyan")
        table.add_column("Chi tiết", style="white")
        table.add_column("Độ tin cậy", style="dim")
        
        for k, v_val, c in data:
            table.add_row(str(k), str(v_val), f"{c*100:.0f}%")
            
        console.print("\n")
        console.print(Align.center(table))
        # Khôi phục dòng trạng thái dưới bảng
        console.print(Align.center(Text(f"Tâm trạng: {v:.1f} | Năng lượng: {e:.1f} | Thân thiết: {b:.1f}", style="status")))

    def show_dangdang_profile(self):
        """Hiển thị bản ngã Dang Dang (Đúng cấu trúc /self cũ)"""
        traits = self.memory.get_self_image()
        
        table = Table(title="✨ Bản ngã của Dang Dang ✨", border_style="magenta")
        table.add_column("Đặc điểm", style="magenta")
        table.add_column("Độ mạnh", style="white")
        
        for t, s in traits:
            table.add_row(str(t), f"{s*100:.0f}%")
            
        console.print("\n")
        console.print(Align.center(table))

def print_header():
    """Header CLI phong cách Dang Dang (Khôi phục khoảng trống UI)"""
    console.clear()
    console.print(Rule(style="#444444"))
    console.print(Align.center(Text("✨ DANG DANG - THE LIVING ENTITY ✨", style="bold #FFA07A")))
    console.print(Align.center(Text("Hybrid Brain: Core Memory + Time Awareness", style="dim white")))
    console.print(Rule(style="#444444"))
    console.print("\n") # Khôi phục khoảng trống

def main():
    agent = GeminiFriend()
    print_header()
    
    console.print(Align.left(Panel("Hế lô! Lại gặp nhau rồi. Nay có chuyện gì vui kể tớ nghe không? :P", 
                                   title="[friend]Dang Dang", border_style="#FFA07A", width=60)))

    while True:
        try:
            if agent.check_for_persona_shift():
                console.print("[info] 💡 Dang Dang vừa thay đổi thái độ dựa trên những gì bạn nói... [/info]")

            user_input = Prompt.ask("\n[user]❯ ").strip()
            if not user_input: continue
            
            cmd = user_input.lower().split()
            
            # Lệnh /profile (mặc định hiện user + status)
            if cmd[0] == "/profile":
                if len(cmd) > 1 and cmd[1] == "dangdang":
                    agent.show_dangdang_profile()
                else:
                    agent.show_user_profile()
                continue
            
            # Khôi phục lệnh /self chuyên biệt
            if user_input.lower() == "/self":
                agent.show_dangdang_profile()
                continue

            if user_input.lower() == "/reflect":
                with console.status("[status]Dang Dang đang suy ngẫm nội tâm..."):
                    ctx = agent.get_time_context()
                    insight = agent.brain.perform_reflection(ctx)
                console.print(Panel(insight, title="Suy nghĩ của Dang Dang", border_style="magenta", width=70))
                continue

            if user_input.lower() == "/refresh":
                agent.refresh_session()
                console.print("[info]Đã nạp lại nhân cách và bộ nhớ mới nhất.")
                continue

            if user_input.lower() in ["thoát", "exit", "quit", "tạm biệt"]:
                console.print("\n[friend]Dang Dang:[/friend] Thôi tớ đi học bài đây. Mai gặp ở trường nhé! <3")
                break
            
            console.print(Align.right(Panel(user_input, title="[user]Bạn", border_style="green", width=50)))
            
            with console.status("[info]Dang Dang đang gõ...", spinner="dots"):
                response_text = agent.send_message(user_input)

            console.print(Align.left(Panel(Markdown(response_text), title="[friend]Dang Dang", border_style="#FFA07A", width=65)))
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[system]Hệ thống đóng. Tạm biệt![/system]")
            break

if __name__ == "__main__":
    main()