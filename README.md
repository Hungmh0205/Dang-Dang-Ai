# 🤖 Dang Dang AI - Living Entity Chatbot

Một AI companion với nhân cách sống động, cảm xúc, và bộ nhớ dài hạn. Dang Dang là học sinh lớp 11, 17 tuổi, nhí nhảnh và tinh tế.

## ✨ Features

### 🧠 Advanced Memory System
- **Episodic Memory**: Ghi nhớ các sự kiện quan trọng với emotion và importance
- **Memory Decay**: Ký ức phai mờ theo thời gian (nhưng core memories được bảo vệ)
- **Semantic Search**: Tìm ký ức liên quan dựa trên context
- **Self-Image**: Tự nhận thức về tính cách bản thân

### 💖 Emotional Intelligence  
- **VAB Model**: Valence (tâm trạng), Energy (năng lượng), Bond (gắn kết)
- **Persona Shift**: Thay đổi thái độ dựa trên cảm xúc
- **Breaking Point**: Nhận biết và phản ứng với biến cố mạnh
- **Self-Reflection**: Tự suy ngẫm và viết nhật ký

### 🎯 Proactive Behavior
- **Attention Manager**: Tự động bắt chuyện khi user im lặng lâu
- **Time Awareness**: Nhận biết và phản ứng với thời gian (đêm khuya, lâu không gặp...)
- **Waiting States**: Phản ứng khi bị ngó lơ (5 phút, 15 phút...)

### 👁️ Vision Support
- Analyze ảnh/video với Gemini Vision
- Bình luận hóm hỉnh và tinh tế

### 🛢️ Production-Grade Database
- **PostgreSQL** với Docker
- Thread-safe connection pooling
- Automatic backup và migration
- Transaction rollback support

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker Desktop
- Google Gemini API Key

### Installation

1. **Clone và setup:**
```bash
cd Dang-Dang-AI
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env và thêm API keys + database password
```

3. **Start PostgreSQL:**
```bash
docker-compose up -d
```

4. **Run migration:**
```bash
python migrate_sqlite_to_postgres.py
```

5. **Run application:**
```bash
python main.py
```

📖 **Detailed setup guide**: See [SETUP_POSTGRES.md](SETUP_POSTGRES.md)

---

## 📂 Project Structure

```
├── main.py                          # Main application entry point
├── memory.py                        # Memory management (PostgreSQL)
├── cognition.py                     # Brain/cognition system
├── db_connection.py                 # Database connection pooling
├── docker-compose.yml               # PostgreSQL container config
├── migrate_sqlite_to_postgres.py   # Migration script
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
└── SETUP_POSTGRES.md               # Setup guide
```

---

## 🎮 Usage

### Basic Commands

```bash
# Normal conversation
❯ Hey Dang Dang!

# View user profile (what Dang Dang knows about you)
❯ /profile

# View Dang Dang's personality
❯ /self

# View Dang Dang's reflection/diary
❯ /reflect

# Exit
❯ thoát
```

### Send Images
```bash
❯ Nhìn xem này: C:\Users\...\image.jpg
```

---

## 🧪 Testing

### Health Check
```bash
# Test database connection
python -c "from memory import MemoryManager; m = MemoryManager(); print('✅ OK')"

# Check bot state
python -c "from memory import MemoryManager; m = MemoryManager(); print(m.get_bot_state())"
```

### Docker Commands
```bash
# View logs
docker-compose logs -f postgres

# Restart database
docker-compose restart

# Stop everything
docker-compose down
```

---

## 🗺️ Roadmap

### Phase 1: ✅ Critical Fixes (Completed)
- [x] PostgreSQL migration với Docker
- [x] Thread-safe connection pooling
- [x] Migration script với backup

### Phase 2: 🚧 Infrastructure (In Progress)
- [ ] Structured logging system
- [ ] Database versioning/migrations
- [ ] Identity guard (protection từ manipulation)

### Phase 3: 📅 Advanced Features (Planned)
- [ ] Emotion-based memory decay
- [ ] Memory consolidation
- [ ] Meta-cognition system
- [ ] pgvector cho semantic search

---

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Database**: PostgreSQL 16 (via Docker)
- **AI Models**: 
  - Google Gemini 3 Flash (chat)
  - Qwen 2.5 3B (local cognition via Ollama)
  - Gemini Vision (image analysis)
- **Libraries**:
  - `psycopg2` - PostgreSQL adapter
  - `google-genai` - Gemini SDK
  - `ollama` - Local LLM
  - `rich` - CLI interface
  - `Pillow`, `opencv` - Image processing

---

## 📝 Configuration

### Environment Variables (.env)

```bash
# API Keys
GOOGLE_API_KEY=your_gemini_api_key
IMAGE_API_KEY=your_vision_api_key

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dangdang_db
DB_USER=dangdang
DB_PASSWORD=your_secure_password
```

---

## 🤝 Contributing

Ideas for improvement:
1. Add unit tests
2. Implement guardrail system
3. Add voice support (TTS/STT)
4. Multi-user support
5. Web interface

---

## 📜 License

MIT License - Feel free to use and modify!

---

## 🙏 Acknowledgments

- Google Gemini API
- PostgreSQL Team
- Ollama Community
- Rich CLI Library

---

## 📧 Support

Nếu gặp issues, check [SETUP_POSTGRES.md](SETUP_POSTGRES.md) troubleshooting section trước!

---

**Made with ❤️ by hungmh0205**
