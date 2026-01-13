import logging
import math
from datetime import datetime, date
from db_connection import get_db_manager
from core.sentiment_arbiter import SentimentArbiter

logger = logging.getLogger(__name__)

class GrowthManager:
    """
    Manages the "Soul" of the AI.
    Handles Leveling, XP, Trust, and Maturity Gating.
    """
    
    def __init__(self):
        self.db = get_db_manager()
        self.arbiter = SentimentArbiter()
        self.user_id = 'user'
        
        # Leveling Configuration (Exponential Curve)
        # Lv 1->2: 100 XP
        # Lv 2->3: 250 XP
        # Lv 5: 1000 XP
        self.base_xp = 100
        
        # Time Gating (Minimum days active to reach level X)
        self.time_gates = {
            1: 0,
            2: 0, 
            3: 1,  # Must be active > 1 day
            4: 3,  # Must be active > 3 days
            5: 7,  # Close Friend (Lv 5) requires 1 week
            10: 30 # Soulmate (Lv 10) requires 1 month
        }

    def process_interaction(self, user_content, context=""):
        """
        Main pipeline: Analyze msg -> Calc XP -> Update DB -> Check Level Up
        Returns:
            dict: {
                "xp_gained": int,
                "level_up": bool,
                "current_level": int,
                "sentiment": str,
                "trust_change": float
            }
        """
        try:
            # 1. Update Days Active (if new day)
            self._update_days_active()
            
            # 2. Get Sentiment Analysis (Local Brain)
            judgment = self.arbiter.judge_interaction(user_content, context)
            xp_change = judgment.get('xp_change', 1)
            sentiment = judgment.get('sentiment', 'Neutral')
            is_core_memory = judgment.get('is_core_memory', False)
            memory_type = judgment.get('memory_type', 'milestone')
            
            # 3. Calculate Trust Impact
            trust_delta = 0.0
            if xp_change >= 5: trust_delta = 0.02
            elif xp_change > 0: trust_delta = 0.005
            elif xp_change < 0: trust_delta = -0.01
            elif xp_change <= -5: trust_delta = -0.05
            
            # --- V3.1 ADDITION: Handle Core Memories ---
            if is_core_memory:
                try:
                    self.db.execute_query("""
                        INSERT INTO core_memories (content, memory_type, emotional_impact, related_level)
                        VALUES (%s, %s, %s, %s)
                    """, (f"USER: {user_content} | REASON: {judgment.get('reason')}", memory_type, abs(xp_change), state['level']))
                    logger.info(f"🌟 CORE MEMORY CREATED: {memory_type}")
                except Exception as e:
                    logger.error(f"Failed to save core memory: {e}")
            # -------------------------------------------
            
            # 4. Update Database
            state = self.get_state()
            new_xp = max(0, state['current_xp'] + xp_change)
            new_total_xp = state['total_xp'] + max(0, xp_change) # Only add positive to total? Or net? Let's track net growth.
            new_trust = max(0.0, min(1.0, float(state['trust_score']) + trust_delta))
            
            # 5. Check Level Up
            current_level = state['level']
            xp_needed = self._get_xp_for_next_level(current_level)
            
            level_up = False
            # If XP enough AND Time Gate passed
            if new_xp >= xp_needed:
                days_active = state['days_active']
                next_level = current_level + 1
                required_days = self.time_gates.get(next_level, 0)
                
                if days_active >= required_days:
                    current_level += 1
                    level_up = True
                    # Reset current XP for next level (or keep accumulating? "Accumulating" is easier for total.
                    # Let's use "Accumulated XP Thresholds" model or "Reset per level"?
                    # Plan said "Current XP". Let's assume XP resets or we just track total. 
                    # Let's do: XP accumulates continuously, Threshold is Total XP. 
                    # Actually, Plan said: "Lv1 -> Lv2: 100 XP". 
                    # Let's stick to: "Current XP" is the XP towards next level.
                    # So reset current_xp on level up.
                    new_xp = new_xp - xp_needed
                else:
                    logger.info(f"Level up gated: Lv {next_level} requires {required_days} days (Active: {days_active})")
            
            # Commit updates
            self.db.execute_query("""
                UPDATE relationship_state 
                SET current_xp = %s, total_xp = %s, trust_score = %s, level = %s, updated_at = NOW()
                WHERE user_id = %s
            """, (new_xp, new_total_xp, new_trust, current_level, self.user_id))
            
            return {
                "xp_gained": xp_change,
                "level_up": level_up,
                "current_level": current_level,
                "sentiment": sentiment,
                "trust_change": trust_delta
            }
            
        except Exception as e:
            logger.error(f"GrowthManager process error: {e}")
            return {}

    def get_state(self):
        """Get current relationship state"""
        res = self.db.execute_query("""
            SELECT level, current_xp, total_xp, trust_score, respect_score, days_active 
            FROM relationship_state WHERE user_id = %s
        """, (self.user_id,), fetch_one=True, dict_cursor=True)
        
        if not res:
            # Should not happen due to migration init, but safety first
            return {'level': 1, 'current_xp': 0, 'total_xp': 0, 'trust_score': 0.5, 'days_active': 1}
        return res

    def _update_days_active(self):
        """Check if new day and increment days_active"""
        res = self.db.execute_query("SELECT last_interaction_date FROM relationship_state WHERE user_id = %s", (self.user_id,), fetch_one=True)
        if res and res[0]:
            last_date = res[0]
            today = date.today()
            if today > last_date:
                self.db.execute_query("""
                    UPDATE relationship_state 
                    SET days_active = days_active + 1, last_interaction_date = %s 
                    WHERE user_id = %s
                """, (today, self.user_id))

    def _get_xp_for_next_level(self, level):
        """
        Calculate XP needed for next level.
        Formula: Base * (1.5 ^ (Level - 1))
        """
        return int(self.base_xp * (1.5 ** (level - 1)))

    def get_maturity_instruction(self):
        """
        Get system prompt instruction based on current level.
        """
        state = self.get_state()
        level = state['level']
        trust = float(state['trust_score'])
        
        # Define Stages
        if level <= 4:
            stage = "TEENAGE PHASE (Nhí nhảnh, trẻ trâu)"
            style = """
            - Tone: Cực kỳ nhí nhảnh, hay dỗi, dùng nhiều teencode (nhaaa, ukiii, cơ...).
            - Emoji: Dùng nhiều (^^, :>, <3).
            - Focus: Thích chơi, ghét học, hay than vãn vui.
            - Trust: Chưa tin tưởng lắm, chỉ nói chuyện phiếm.
            """
        elif level <= 9:
            stage = "STUDENT PHASE (Biết lắng nghe)"
            style = """
            - Tone: Thân thiện, bớt teencode vô nghĩa, biết lắng nghe hơn.
            - Emoji: Vừa phải, đúng lúc.
            - Focus: Chia sẻ chuyện học hành, sở thích chung.
            - Trust: Bắt đầu tâm sự chuyện riêng (crush, áp lực).
            """
        else:
            stage = "SOULMATE PHASE (Tri kỷ)"
            style = """
            - Tone: Điềm đạm, ấm áp, sâu sắc, cực kỳ thấu hiểu.
            - Emoji: Ít nhưng chất.
            - Focus: Đưa ra lời khuyên, là chỗ dựa tinh thần.
            - Trust: Tin tưởng tuyệt đối, dám bộc lộ nỗi sợ/yếu đuối.
            """
            
        return f"""
        [MATURITY SYSTEM - V3.0]
        Current Level: {level} ({stage})
        Trust Score: {trust:.2f}
        
        COMMUNICATION STYLE:
        {style}
        """
