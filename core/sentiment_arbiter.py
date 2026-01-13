import ollama
import logging
import json

logger = logging.getLogger(__name__)

class SentimentArbiter:
    """
    Qwen-based Local Brain for analyzing relationship depth.
    Determines XP gain/loss based on interaction quality.
    """
    
    def __init__(self, model_name="qwen2.5:3b-instruct"):
        self.model = model_name

    def judge_interaction(self, user_content, context=""):
        """
        Analyze user message to determine XP adjustment.
        
        Returns:
            dict: {
                "xp_change": int, (-5 to 10)
                "reason": str,
                "sentiment": str
            }
        """
        try:
            prompt = f"""You are the Sentiment Arbiter. Analyze the USER's message to Dang Dang (AI).
Determine the quality of interaction for Relationship Growth (XP) and detect Emotional Milestones.

CONTEXT: {context}
USER MESSAGE: "{user_content}"

RULES FOR XP:
- High Quality (+5 to +10): Deep sharing, emotional vulnerability, sincere advice, comforting, very funny.
- Medium (+2 to +4): Nice compliment, meaningful question, continued conversation.
- Neutral (+1): Casual greeting, short reply (ok, uh huh), phatic communication.
- Negative (-1 to -5): Rude, dismissive, trolling, insults, spam.

RULES FOR MILESTONES (Core Memories):
- True if: User shares a major secret, successful comfort after sadness, deep realization, or first "I love you".
- False if: Normal conversation.

OUTPUT JSON ONLY:
{{
    "xp_change": <number -5 to 10>,
    "sentiment": "<Positive/Neutral/Negative>",
    "is_core_memory": <true/false>,
    "memory_type": "<milestone/bonding/conflict/null>",
    "reason": "<Short explanation>"
}}
"""
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            result_text = response['message']['content'].strip()
            
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                 result_text = result_text.split("```")[1].split("```")[0].strip()
                 
            return json.loads(result_text)
            
        except Exception as e:
            logger.error(f"Sentiment Arbiter failed: {e}")
            # Fallback based on length
            length = len(user_content.split())
            xp = 2 if length > 10 else 1
            return {"xp_change": xp, "sentiment": "Neutral", "is_core_memory": False, "reason": "Fallback logic"}

    def summarize_day(self, messages):
        """
        Summarize a list of messages into a coherent daily narrative.
        Args:
            messages: list of dict {'role': 'user/model', 'content': '...'}
        Returns:
            str: Summary text
        """
        try:
            if not messages:
                return "Không có hoạt động nào."

            # Format conversation for LLM
            conversation_text = ""
            for msg in messages:
                role = "USER" if msg['role'] == 'user' else "DANG DANG"
                conversation_text += f"{role}: {msg['content']}\n"
            
            prompt = f"""You are a Memory Consolidator. Summarize the following conversation from today into a single, concise paragraph (Vietnamese).
Focus on: Key events, user's mood, and important facts shared. Ignore small talk.

CONVERSATION:
{conversation_text}

SUMMARY (Vietnamese):"""

            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            return response['message']['content'].strip()

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return "Không thể tóm tắt do lỗi hệ thống."
