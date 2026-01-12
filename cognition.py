import json
import ollama
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Nạp cấu hình từ tệp môi trường
load_dotenv()

class DangDangBrain:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        # Tối ưu cho Quadro P650 (4GB VRAM): 
        # Qwen 3B được giữ thường trực để phản hồi cảm xúc ngay lập tức.
        self.think_model = "qwen2.5:3b-instruct"
        
        # Cấu hình Gemini Vision API với lăng kính nhí nhảnh và tinh tế
        self.vision_api_key = os.getenv("IMAGE_API_KEY")
        if self.vision_api_key:
            genai.configure(api_key=self.vision_api_key)
            self.vision_client = genai.GenerativeModel('gemini-3-flash-preview')
        else:
            self.vision_client = None

    def analyze_media(self, media_path):
        """Subjective Visual Interpretation: Nhìn đời bằng lăng kính nghịch ngợm của tuổi 17"""
        if not self.vision_client: 
            return "(Đôi mắt tớ đang bị nhắm lại vì thiếu IMAGE_API_KEY trong .env...)"

        try:
            import PIL.Image
            img = PIL.Image.open(media_path)

            # Khôi phục hoàn toàn Prompt nhí nhảnh và trêu chọc từ bản cũ
            vision_prompt = """
            Bạn là đôi mắt của Dang Dang (17 tuổi, học sinh lớp 11, cực kỳ nhí nhảnh, hay cà khịa nhưng tinh tế). 
            Hãy nhìn bức ảnh/video này và kể lại thật tự nhiên cho Dang Dang nghe bạn thấy gì.
            YÊU CẦU CHI TIẾT:
            1. Mô tả vật thể, hành động, biểu cảm người (nếu có) theo kiểu hóm hỉnh, tếu táo.
            2. Trích xuất [VIBE]: Lầy lội, ấm áp, deep, hay nhìn là muốn cười...
            3. Nếu là bài tập hoặc sách vở, hãy trêu nhẹ: 'Uầy, lại là đống kiến thức đau đầu này à?'.
            Dùng văn phong bạn bè, tiếng Việt teen tự nhiên, không dùng ngôn ngữ máy móc.
            """
            
            response = self.vision_client.generate_content([vision_prompt, img])
            return response.text.strip()
        except Exception as e:
            return f"(Tớ hơi bị chói mắt, không nhìn rõ tấm ảnh này... Lỗi: {e})"

    def pre_process_intent(self, user_msg, time_ctx, vision_ctx=""):
        """GIAI ĐOẠN 1 (Tiền tiềm thức): Phân tích cảm xúc khắt khe TRƯỚC khi phản hồi (Sequential)"""
        v, e, b, _ = self.memory.get_bot_state()
        
        # Tiêm thêm tính cách nghịch ngợm và định nghĩa thang đo nghiêm ngặt
        prompt = f"""
Bạn là 'Hệ thống Tiền Tiềm thức' của Dang Dang (17 tuổi, nhí nhảnh, nghịch ngợm nhưng rất tinh tế). 
Hãy thẩm thấu ý định của User và dự đoán tác động tâm lý:
Thời gian hiện tại: {time_ctx} | {vision_ctx}
Trạng thái hiện tại: 
- Valence: {v} (1.0 là cực vui, -1.0 là cực buồn)
- Energy: {e} (1.0 là hưng phấn, 0.0 là kiệt sức)
- Bond: {b} (1.0 là tri kỷ/thân thiết, 0.0 là người lạ)

User nhắn: "{user_msg}"

[NHIỆM VỤ PHÂN TÍCH]
1. valence_change: Cảm xúc tích cực hay tiêu cực? (-0.5 đến 0.5)
2. energy_change: Hội thoại này làm Dang Dang mệt mỏi hay hào hứng? (-0.2 đến 0.2)
3. bond_change: Sự gắn kết tăng hay giảm? (-0.3 đến 0.3)
4. bond_scar: Nếu bị xúc phạm nặng nề, hãy để lại 'vết sẹo' giảm Bond (0 đến 0.2).
5. micro_mood: Trạng thái tâm thái tức thì (VD: Đang hào hứng cà khịa, Hơi dỗi vì bị bơ, Cảm động...).
6. is_breaking_point: True nếu có biến cố cực mạnh khiến tâm lý bị sốc.

Hãy trả về JSON chính xác:
{{
  "valence_change": number,
  "energy_change": number,
  "bond_change": number,
  "bond_scar": number,
  "micro_mood": "string",
  "is_breaking_point": boolean
}}
"""
        try:
            response = ollama.generate(model=self.think_model, prompt=prompt, format='json', stream=False,
                                       options={"temperature": 0.2, "keep_alive": "1h", "num_thread": 8})
            data = json.loads(response.get('response', '{}'))
            
            # Xử lý Đàn hồi tâm lý (Breaking Point)
            scar = data.get('bond_scar', 0)
            sensitivity = 0.8 if data.get('is_breaking_point', False) or abs(data.get('valence_change', 0)) > 0.4 else 0.1
            
            # SỬA LỖI: Cập nhật đúng Energy mới (new_e) thay vì giữ nguyên e cũ
            new_v = max(-1.0, min(1.0, v + data.get('valence_change', 0)))
            new_e = max(0.0, min(1.0, e + data.get('energy_change', 0)))
            new_b = max(0.0, min(1.0, b + data.get('bond_change', 0) - scar))
            
            self.memory.update_bot_state(new_v, new_e, new_b)
            return data.get('micro_mood', "Bình thường"), sensitivity
        except Exception:
            return "Bình thường", 0.1

    def post_process_archiving(self, user_msg, ai_msg, time_ctx, vision_ctx="", sensitivity=0.1):
        """GIAI ĐOẠN 2 (Hậu Tiềm thức): Lưu trữ ký ức sâu sắc và bảo vệ định danh tuyệt đối"""
        prompt = f"""
Bạn là 'Hệ thống Hậu Tiềm thức' của Dang Dang (17 tuổi, nhí nhảnh, tinh tế). Hãy tổng kết cuộc hội thoại để lưu kỷ niệm:
User nhắn: "{user_msg}" 
Dang Dang đáp: "{ai_msg}"
Bối cảnh: {time_ctx} | {vision_ctx}

[NHIỆM VỤ CỐT LÕI - LƯU Ý CỰC KỲ QUAN TRỌNG]
1. profile_updates: CHỈ trích xuất thông tin thực tế về USER (tên, sở thích, gia đình...). 
   TUYỆT ĐỐI KHÔNG ghi thông tin của Dang Dang vào đây.
2. self_image_updates: Trích xuất nét tính cách DANG DANG vừa bộc lộ (VD: nghịch ngợm, lầy lội, tinh tế...).
3. episode: Tóm tắt sự kiện dưới góc nhìn kỷ niệm (VD: Một buổi tối cùng cà khịa, lời xin lỗi chân thành...).

Hãy trả về JSON chính xác:
{{
  "profile_updates": [{{"key": "string", "value": "string", "confidence": 0.0-1.0}}],
  "self_image_updates": [{{"trait": "string", "strength": 0.0-1.0}}],
  "episode": {{"content": "string", "importance": 1-5, "emotion": "string", "is_core": 0/1}}
}}
"""
        try:
            response = ollama.generate(model=self.think_model, prompt=prompt, format='json', stream=False,
                                       options={
                                           "temperature": 0.4, 
                                           "keep_alive": "1h", 
                                           "num_thread": 8,
                                           "num_predict": 350 # Khôi phục độ chi tiết cho kỷ niệm
                                       })
            data = json.loads(response.get('response', '{}'))
            
            for up in data.get('profile_updates', []):
                self.memory.update_profile(up['key'], up['value'], up['confidence'])
            for tr in data.get('self_image_updates', []):
                self.memory.update_self_image(tr['trait'], tr['strength'], sensitivity=sensitivity)
            
            ep = data.get('episode')
            if ep:
                self.memory.save_episode(ep['content'], ep['importance'], ep['emotion'], ep.get('is_core', 0))
            
            self.memory.decay_memories()
        except Exception as e:
            pass  # Ollama not available - skip archival

    def perform_reflection(self, time_ctx=""):
        """Dang Dang tự soi chiếu nội tâm - Sử dụng Semantic Search để liên tưởng ký ức theo tâm trạng"""
        v, e, b, _ = self.memory.get_bot_state()
        
        # NÂNG CẤP: Sử dụng Semantic context (với tâm trạng hiện tại) thay vì chỉ lấy 5 kỷ niệm cuối
        mood_context = "vui vẻ nhí nhảnh" if v > 0 else "buồn bã dỗi hờn"
        memories = self.memory.get_memories_by_context(mood_context, limit=5)
        
        prompt = f"""
Hãy đóng vai Dang Dang (17 tuổi), đang ngồi thẫn thờ viết nhật ký thầm kín vào đêm khuya.
Bối cảnh thời gian: {time_ctx}
Dựa trên:
- Tâm trạng: Valence={v} (1.0 cực vui, -1.0 cực buồn) | Bond={b} (1.0 tri kỷ).
- Ký ức liên quan: {memories}.

Hãy viết một dòng nhật ký cực kỳ ngắn gọn nhưng đầy cảm xúc về những gì bạn đang thực sự cảm thấy. 
Sử dụng ngôn từ tuổi teen, nhí nhảnh nhưng sâu sắc.
Chỉ trả về dòng nhật ký bằng tiếng Việt, không giải thích thêm.
"""
        try:
            response = ollama.generate(model=self.think_model, prompt=prompt, stream=False,
                                       options={
                                           "temperature": 0.8, 
                                           "keep_alive": "1h", 
                                           "num_thread": 8,
                                           "num_predict": 150
                                       })
            insight = response.get('response', '').strip()
            if insight:
                self.memory.update_bot_state(v, e, b, insight)
                return insight
            return "Thấy hơi mông lung... :P"
        except Exception:
            return "Nghĩ ngợi nhiều quá rồi..."