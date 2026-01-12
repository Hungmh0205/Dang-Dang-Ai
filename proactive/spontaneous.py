"""
Spontaneous Event Generator
"Đột nhiên muốn nhắn" - True randomness for human-like behavior
"""

import random
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SpontaneousEventGenerator:
    """Generate truly random spontaneous events"""
    
    def __init__(self, memory_manager):
        """
        Initialize SpontaneousEventGenerator
        
        Args:
            memory_manager: MemoryManager instance
        """
        self.memory = memory_manager
    
    def should_trigger_spontaneous(self, idle_time_seconds):
        """
        Decide if should send random message
        Uses personality factor based on time of day
        
        Args:
            idle_time_seconds: Seconds since last activity
        
        Returns:
            bool: True if should trigger
        """
        hour = datetime.now().hour
        
        # Personality factor by hour (Dang Dang active times)
        activity_factor = self._get_activity_factor(hour)
        
        # Base probability adjusted by idle time
        if idle_time_seconds < 1800:  # < 30 min
            base_prob = 0.05
        elif idle_time_seconds < 3600:  # 30min - 1h
            base_prob = 0.15
        elif idle_time_seconds < 7200:  # 1-2 hours
            base_prob = 0.3
        else:  # > 2 hours
            base_prob = 0.5
        
        # Final probability
        final_prob = base_prob * activity_factor
        
        return random.random() < final_prob
    
    def _get_activity_factor(self, hour):
        """
        Get activity factor for hour
        Dang Dang more active during certain times
        
        Args:
            hour: Hour (0-23)
        
        Returns:
            float: Activity factor (0.1 - 1.0)
        """
        # Morning (6-9): Low activity (sleeping/school)
        if 6 <= hour < 9:
            return 0.2
        
        # School time (9-15): Very low
        elif 9 <= hour < 15:
            return 0.1
        
        # After school (15-18): HIGH activity
        elif 15 <= hour < 18:
            return 0.8
        
        # Evening (18-21): Medium-high
        elif 18 <= hour < 21:
            return 0.6
        
        # Late evening (21-23): Medium
        elif 21 <= hour < 23:
            return 0.5
        
        # Night (23-2): Very low
        elif hour >= 23 or hour < 2:
            return 0.1
        
        # Early morning (2-6): Almost never
        else:
            return 0.05
    
    def generate_spontaneous_message(self):
        """
        Generate truly random message
        
        Returns:
            str: Random message
        """
        categories = {
            'just_hi': 0.3,
            'random_thought': 0.25,
            'random_question': 0.2,
            'impulse': 0.15,
            'feeling': 0.1
        }
        
        choice = random.choices(
            list(categories.keys()),
            weights=list(categories.values())
        )[0]
        
        return self._generate_by_category(choice)
    
    def _generate_by_category(self, category):
        """Generate message by category"""
        
        if category == 'just_hi':
            # Just saying hi
            messages = [
                "hề lôoo",
                "bạnn ơiii",
                "ơiii",
                "hehe",
                "bạn đó ^^",
                "này bạnnn"
            ]
        
        elif category == 'random_thought':
            # Random thoughts
            thoughts = [
                "tớ đang nghĩ về {thing}",
                "à mà",
                "quên nói",
                "tớ thích {thing} áaa",
                "bạn có sợ {thing} khôngg",
                "tại sao {question} nhỉiii"
            ]
            
            things = ["trời", "bài tập", "phim", "nhạc", "game", "tương lai"]
            questions = ["con người ta sống", "phải học nhiều thế", "lại phải đi học"]
            
            template = random.choice(thoughts)
            template = template.replace("{thing}", random.choice(things))
            template = template.replace("{question}", random.choice(questions))
            messages = [template]
        
        elif category == 'random_question':
            # Random questions
            messages = [
                "bạn thích mưa không??",
                "nếu được chọn bạn sẽ làm gì??",
                "bạn nghĩ sao về tình yêuu??",
                "bạn có tin vào số phận khôngg",
                "bạn muốn trở thành ai??",
            ]
        
        elif category == 'impulse':
            # Impulse messages (excited)
            messages = [
                "ƠIII",
                "BẠN ƠI",
                "!!!",
                "heheee",
                "uaaaaa",
                "ố ồ",
            ]
        
        else:  # feeling
            # Expressing feelings
            messages = [
                "haizzz",
                "buồn quáaaa",
                "vui ghêêê",
                "chán lắmmm",
                "mệt quáaaa",
                "hạnh phúc ^^",
            ]
        
        return random.choice(messages)
    
    def get_max_per_day(self):
        """
        Get max spontaneous messages per day
        Should be limited to avoid spam
        
        Returns:
            int: Max messages (default 3)
        """
        return 3
    
    def count_today_spontaneous(self):
        """
        Count spontaneous messages sent today
        
        Returns:
            int: Count
        """
        try:
            today = datetime.now().date()
            
            result = self.memory.db.execute_query("""
                SELECT COUNT(*) FROM proactive_events
                WHERE event_type = 'spontaneous'
                  AND DATE(sent_time) = %s
            """, (today,), fetch_one=True)
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error counting spontaneous: {e}")
            return 0
