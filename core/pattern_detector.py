import json
import ollama
import logging
from db_connection import get_db_manager

logger = logging.getLogger(__name__)

class PatternDetector:
    """
    Phát hiện các mô hình hành vi (Pattern Detection) của User.
    - Tìm kiếm thói quen, sở thích, hoặc tâm trạng lặp đi lặp lại.
    - Lưu vào bảng user_patterns.
    """
    
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.db = memory_manager.db
        self.model = "qwen2.5:3b-instruct"

    def detect_patterns(self, lookback_days=7):
        """
        Scan recent daily summaries or messages to find patterns.
        Args:
            lookback_days: How far back to look.
        Returns:
            list: Detected patterns.
        """
        try:
            # 1. Gather Data: Get recent daily summaries (consolidated memories)
            # We use episodic_memory where content starts with [CONSOLIDATED]
            # or just raw messages if needed. Let's use CONSOLIDATED ones for efficiency.
            
            res = self.db.execute_query(
                """SELECT day_date, content FROM episodic_memory 
                   WHERE content LIKE %s 
                   ORDER BY day_date DESC LIMIT %s""",
                ('[CONSOLIDATED%', lookback_days),
                fetch_all=True
            )
            
            if not res or len(res) < 2:
                # Not enough data to find patterns
                return []
            
            # Format context for LLM
            history_text = "\n".join([f"- {r[0]}: {r[1]}" for r in res])
            
            prompt = f"""
You are a Behavioral Analyst. Analyze these daily summaries of a User.
Identify recurring PATTERNS (Habits, Emotional Triggers, Routine).

HISTORY:
{history_text}

TASK:
Find 1-2 distinct patterns.
Example: "User often acts tired on Mondays", "User loves talking about technology late at night".
Format: JSON.

Output:
{{
  "patterns": [
    {{
      "type": "habit",
      "description": "User tends to...",
      "confidence": 0.8
    }}
  ]
}}
"""
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ], options={"temperature": 0.2})
            
            content = response['message']['content']
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            data = json.loads(content)
            patterns = data.get('patterns', [])
            
            # Save to DB
            saved_patterns = []
            for p in patterns:
                if self._save_pattern(p):
                    saved_patterns.append(p)
            
            return saved_patterns

        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
            return []

    def _save_pattern(self, pattern):
        """Save a detected pattern to DB if it doesn't duplicate recent ones"""
        try:
            desc = pattern.get('description')
            p_type = pattern.get('type', 'general')
            conf = pattern.get('confidence', 0.5)
            
            # Check for existing similar pattern (naive string match for now)
            # Ideally use semantic similarity, but basic string check helps prevent spam.
            exists = self.db.execute_query(
                "SELECT id FROM user_patterns WHERE description = %s",
                (desc,), fetch_one=True
            )
            
            if exists:
                # Update frequency/confidence instead of inserting
                self.db.execute_query(
                    "UPDATE user_patterns SET frequency = frequency + 1, confidence_score = %s, detected_at = NOW() WHERE id = %s",
                    (conf, exists[0])
                )
                return True
            else:
                self.db.execute_query(
                    """INSERT INTO user_patterns (pattern_type, description, confidence_score) 
                       VALUES (%s, %s, %s)""",
                    (p_type, desc, conf)
                )
                logger.info(f"🧩 New Pattern Detected: {desc}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save pattern: {e}")
            return False
