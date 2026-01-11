import google.generativeai as genai
from dotenv import load_dotenv
import PIL.Image
import os
load_dotenv()
# 1. Cấu hình API Key
GOOGLE_API_KEY = os.getenv("IMAGE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def test_gemini_vision(image_path):
    try:
        # 2. Chọn model (Gemini 1.5 Flash là bản nhanh và free tốt nhất hiện nay)
        model = genai.GenerativeModel('gemini-3-flash-preview')

        # 3. Load ảnh bằng thư viện PIL
        if not os.path.exists(image_path):
            print(f"Lỗi: Không tìm thấy file {image_path}")
            return

        img = PIL.Image.open(image_path)

        # 4. Gửi yêu cầu phân tích
        print(f"Đang phân tích ảnh: {image_path}...")
        response = model.generate_content([
            "Mô tả chi tiết hình ảnh này bằng tiếng Việt. Nếu có chữ, hãy trích xuất văn bản đó.",
            img
        ])

        # 5. In kết quả
        print("\n" + "="*30)
        print("KẾT QUẢ TỪ GEMINI:")
        print(response.text)
        print("="*30)

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    # Thay tên file ảnh bạn muốn test vào đây
    image_file = "test.jpg"
    test_gemini_vision(image_file)
