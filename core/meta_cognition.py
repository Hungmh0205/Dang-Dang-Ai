import json
import ollama
import logging
from db_connection import get_db_manager

logger = logging.getLogger(__name__)

class MetaCognition:
    """
    Tự soi chiếu và đánh giá chất lượng phản hồi sau mỗi tin nhắn.
    - Relevance: Có đúng trọng tâm không?
    - Creativity: Có sáng tạo/thú vị không?
    - Personality: Có đúng chất Dang Dang không?
    """
    
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.db = memory_manager.db
        # Use simple model for critique
        self.model = "qwen2.5:3b-instruct"

    def evaluate_response(self, user_msg, ai_msg):
        """
        Evaluate the AI's response to the user.
        Args:
            user_msg: The user's input
            ai_msg: The AI's response
        Returns:
            dict: Scores and critique
        """
        prompt = f"""
You are a Critical Judge. Evaluate this AI response.
Identity: Dang Dang (17-year-old student, witty, playful, subtle, Vietnamese).

User: "{user_msg}"
AI: "{ai_msg}"

TASK: Rate on 1-5 scale (5 is best).
1. Relevance: Direct answer or relevant continuation?
2. Creativity: Interesting phrasing? Not generic?
3. Personality: Is it playful/witty like a teen? (1=Robot, 5=Soulful Teen)

Return JSON only:
{{
  "relevance": 1-5,
  "creativity": 1-5,
  "personality": 1-5,
  "critique": "Short critique in Vietnamese (max 10 words)"
}}
"""
        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ], options={"temperature": 0.1})
            
            content = response['message']['content']
            # Clean json block if needed
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            scores = json.loads(content)
            
            # Save to DB
            self._save_evaluation(scores)
            
            return scores
            
        except Exception as e:
            logger.error(f"Meta-Cognition evaluation failed: {e}")
            return None

    def _save_evaluation(self, scores):
        """Save scores to DB"""
        try:
            # We don't have message_id easily available here unless passed down. 
            # Ideally we pass message_id. For now, we'll retrieve the last AI message ID.
            
            # Get last AI message ID
            res = self.db.execute_query(
                "SELECT id FROM messages WHERE role = 'model' ORDER BY id DESC LIMIT 1",
                fetch_one=True
            )
            
            message_id = res[0] if res else None
            
            if message_id:
                self.db.execute_query("""
                    INSERT INTO response_quality 
                    (message_id, relevance_score, creativity_score, personality_score, critique)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    message_id,
                    scores.get('relevance', 3),
                    scores.get('creativity', 3),
                    scores.get('personality', 3),
                    scores.get('critique', '')
                ))
                logger.info(f"🧠 Reflection: P{scores.get('personality')}/5 - {scores.get('critique')}")
                
        except Exception as e:
            logger.error(f"Failed to save evaluation: {e}")
