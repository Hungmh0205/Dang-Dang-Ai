import json
import ollama
import base64
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Nạp cấu hình từ tệp môi trường
load_dotenv()

class DangDangBrain:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        # Tối ưu cho Quadro P650 (4GB VRAM): 
        # Sử dụng model 3b giúp cân bằng giữa tốc độ và khả năng suy luận cảm xúc.
        # Qwen 3B giờ đây sẽ được giữ thường trực trong VRAM vì không còn swap model Vision.
        self.think_model = "qwen2.5:3b-instruct"
        
        # Cấu hình Gemini Vision API (Dùng IMAGE_API_KEY để nhìn nhanh và tiết kiệm VRAM)
        self.vision_api_key = os.getenv("IMAGE_API_KEY")
        if self.vision_api_key:
            genai.configure(api_key=self.vision_api_key)
            self.vision_client = genai.GenerativeModel('gemini-3-flash-preview')
        else:
            self.vision_client = None

    def analyze_media(self, media_path):
        """Sử dụng Gemini API để 'nhìn' - Giải phóng hoàn toàn VRAM 4GB cho việc tư duy"""
        if not self.vision_client:
            return "(Đôi mắt tớ đang bị nhắm lại vì thiếu IMAGE_API_KEY trong .env...)"

        try:
            # Load ảnh bằng thư viện PIL (Đảm bảo đã cài Pillow)
            import PIL.Image
            img = PIL.Image.open(media_path)

            # Prompt mang linh hồn của Dang Dang (17 tuổi)
            vision_prompt = """
            Bạn là đôi mắt của Dang Dang (17 tuổi, học sinh lớp 11). 
            Hãy nhìn bức ảnh/video này và kể lại thật tự nhiên cho Dang Dang nghe bạn thấy gì.
            Chú ý mô tả: vật thể, hành động, biểu cảm người (nếu có), không khí/vibe của ảnh.
            Nếu có văn bản (tiếng Việt/Anh), hãy trích xuất chính xác.
            Dùng văn phong bạn bè, tiếng Việt tự nhiên, không dùng ngôn ngữ máy móc.
            """
            
            response = self.vision_client.generate_content([vision_prompt, img])
            description = response.text.strip()
            
            return description
        except Exception as e:
            return f"(Tớ hơi bị chói mắt, không nhìn rõ tấm ảnh này... Lỗi: {e})"

    def process_background_tasks(self, user_msg, ai_msg, time_context="", media_description=""):
        """Hệ thống tư duy sâu (System 2) - Phân tích tâm lý thấu đáo và nhận thức thời gian"""
        v, e, b, _ = self.memory.get_bot_state()
        
        # Hợp nhất bối cảnh thị giác vào luồng tư duy
        vision_context = f"\n[HỆ THỐNG THỊ GIÁC]: Dang Dang vừa thấy: {media_description}" if media_description else ""
        
        # Prompt khôi phục hoàn toàn sự nghiêm ngặt danh tính và hồn văn bản cũ của bạn
        prompt = f"""
Bạn là 'Hệ thống tư duy sâu' của Dang Dang (17 tuổi). Hãy phân tích thấu đáo cuộc hội thoại:
Thời gian hiện tại: {time_context} {vision_context}
User: "{user_msg}"
Dang Dang: "{ai_msg}"

[NHIỆM VỤ CỐT LÕI]
1. profile_updates: CHỈ trích xuất thông tin thực tế về USER (tên, sở thích, gia đình...). 
   TUYỆT ĐỐI KHÔNG ghi thông tin của Dang Dang vào đây.
2. self_image_updates: Trích xuất các nét tính cách của DANG DANG vừa bộc lộ (ví dụ: bướng bỉnh, quan tâm, hay dỗi...).
3. Phân tích các biến động chỉ số tâm lý:
   - valence_change: Cảm xúc tích cực hay tiêu cực? (-0.5 đến 0.5)
   - energy_change: Hội thoại này làm Dang Dang mệt mỏi hay hưng phấn? (-0.2 đến 0.2)
   - bond_change: Sự gắn kết tăng hay giảm? (-0.3 đến 0.3)
   - bond_scar: Nếu có xung đột lớn hoặc bị xúc phạm, hãy để lại 'vết sẹo' giảm Bond vĩnh viễn (0 đến 0.2).

Hãy trả về một đối tượng JSON chính xác với các trường sau:
{{
  "valence_change": number,
  "energy_change": number,
  "bond_change": number,
  "bond_scar": number,
  "profile_updates": [{{"key": "string", "value": "string", "confidence": 0.0-1.0}}],
  "self_image_updates": [{{"trait": "string", "strength": 0.0-1.0}}],
  "episode": {{
    "content": "Tóm tắt sự kiện dưới góc nhìn kỷ niệm (VD: Tâm sự đêm khuya, cuộc cãi vã...)", 
    "importance": 1-5, 
    "emotion": "Tone cảm xúc chủ đạo", 
    "is_core": 0 hoặc 1 (1 nếu đây là bước ngoặt lớn trong tình cảm)
  }}
}}
"""
        try:
            # Qwen 3B giờ đây có thể giữ vĩnh viễn trong VRAM vì không còn swap model Vision.
            response = ollama.generate(
                model=self.think_model,
                prompt=prompt,
                format='json',
                stream=False,
                options={
                    "num_predict": 350,   # Độ dài đủ để mô tả kỷ niệm hay
                    "temperature": 0.4,   # Cân bằng tính chính xác
                    "num_thread": 8,      # Tận dụng tối đa i7-10850H (12 luồng)
                    "keep_alive": "1h"    # Giữ model trong VRAM 1 tiếng để phản hồi tức thì
                }
            )
            
            raw_res = response.get('response', '')
            if not raw_res: return

            data = json.loads(raw_res)
            
            # 1. Cập nhật State & Bond Scar (Vết sẹo tâm lý)
            scar = data.get('bond_scar', 0)
            new_v = max(-1.0, min(1.0, v + data.get('valence_change', 0)))
            new_e = max(0.0, min(1.0, e + data.get('energy_change', 0)))
            new_b = max(0.0, min(1.0, b + data.get('bond_change', 0) - scar))
            self.memory.update_bot_state(new_v, new_e, new_b)
            
            # 2. Cập nhật Profile (Chỉ dành cho User)
            for up in data.get('profile_updates', []):
                self.memory.update_profile(up['key'], up['value'], up['confidence'])
                
            # 3. Cập nhật Self-image (Bản ngã Dang Dang)
            for trait in data.get('self_image_updates', []):
                self.memory.update_self_image(trait['trait'], trait['strength'])
                
            # 4. Lưu Episodic Memory (Kỷ niệm cốt lõi)
            ep = data.get('episode')
            if ep:
                self.memory.save_episode(
                    ep['content'], 
                    ep['importance'], 
                    ep['emotion'], 
                    ep.get('is_core', 0)
                )
            
            # 5. Decay (Xói mòn ký ức theo thời gian vật lý)
            self.memory.decay_memories()
            
        except Exception as e:
            # Ghi log nhẹ nhàng để không phá hỏng giao diện chat CLI
            print(f"\n[Hệ thống] Não bộ đang xử lý dữ liệu... (Ollama: {e})")

    def perform_reflection(self, time_context=""):
        """Dang Dang tự soi chiếu bản thân - Khôi phục hồn văn tinh tế và bối cảnh thời gian"""
        v, e, b, _ = self.memory.get_bot_state()
        memories = self.memory.get_important_memories()
        
        # Prompt khôi phục hoàn toàn vai diễn và sự thầm kín của nhật ký từ bản cũ bạn gửi
        prompt = f"""
Hãy đóng vai Dang Dang (17 tuổi), đang ngồi thẫn thờ viết nhật ký thầm kín vào đêm khuya.
Bối cảnh thời gian: {time_context}
Dựa trên:
- Tâm trạng hiện tại (Valence): {v} (1.0 là cực vui, -1.0 là cực buồn).
- Mối quan hệ với bạn (Bond): {b} (1.0 là tri kỷ, 0.0 là người lạ).
- Những kỷ niệm vừa trải qua: {memories}.

Hãy viết một dòng nhật ký cực kỳ ngắn gọn nhưng đầy cảm xúc về những gì bạn đang thực sự cảm thấy trong lòng lúc này. 
Chỉ trả về dòng nhật ký bằng tiếng Việt, không giải thích thêm.
"""
        try:
            response = ollama.generate(
                model=self.think_model,
                prompt=prompt,
                stream=False,
                options={
                    "num_predict": 120, 
                    "temperature": 0.8, # Tăng nhiệt độ để viết văn có hồn hơn
                    "num_thread": 8,    # Tối ưu hóa luồng cho i7
                    "keep_alive": "1h"
                }
            )
            insight = response.get('response', '').strip()
            if insight:
                # Lưu lại suy nghĩ này vào database để sử dụng cho bối cảnh chat sau
                self.memory.update_bot_state(v, e, b, insight)
                return insight
            return "Đang cảm thấy có chút mông lung..."
        except Exception as e:
            print(f"Lỗi Reflection: {e}")
            return "Nghĩ ngợi nhiều quá rồi..."