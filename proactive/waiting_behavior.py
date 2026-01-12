"""
Waiting Behavior Patterns
Phản ứng khi user không reply
"""

import random
import logging

logger = logging.getLogger(__name__)


class WaitingBehavior:
    """Generate varied responses when user doesn't reply"""
    
    @staticmethod
    def get_5min_response(valence, bond, energy):
        """
        After 5 minutes - gentle check-in
        
        Args:
            valence: Current mood (-1 to 1)
            bond: Relationship strength (0 to 1)
            energy: Energy level (0 to 1)
        
        Returns:
            str: Response message
        """
        # High bond + positive mood = playful
        if bond > 0.6 and valence > 0.3:
            return random.choice([
                "heyyyy bạn ơiii",
                "bạnn đâuu rồiii",
                "ơiii trả lờiii tớ điiii :))",
                "bạn đọc tin rồi màa sao chưa replyyy"
            ])
        
        # Low bond = more formal
        elif bond < 0.3:
            return random.choice([
                "ơ bạn bận à",
                "okeee tớ đợi"
            ])
        
        # Bad mood = sulky
        elif valence < -0.3:
            return random.choice([
                "...",
                "thôi được",
                "haizz",
                "ờ"
            ])
        
        # Default - varied emotions
        else:
            return random.choice([
                "bạn đang làm gì đấyy",
                "hmmm sao không trả lời nhỉii",
                "ơiii có bậnn khôngg",
                "bạn ơiii"
            ])
    
    @staticmethod
    def get_15min_response(valence, bond, personality_seed):
        """
        After 15 minutes - escalated response
        Uses personality_seed for consistent daily behavior
        
        Args:
            valence: Current mood
            bond: Relationship strength
            personality_seed: Seed for random (e.g., date.toordinal())
        
        Returns:
            str or None: Response message (None = silent)
        """
        # Use date as seed for consistent daily personality
        random.seed(personality_seed)
        roll = random.random()
        random.seed()  # Reset seed
        
        # 40% - Loud/impatient (human gets annoyed)
        if roll < 0.4:
            return random.choice([
                "HEYYYY",
                "BẠN ƠIIII",
                "SAO KO TRẢ LỜIII",
                "ĐANG LÀM GÌ ĐẤY ???",
                "ƠII BẠNNN"
            ])
        
        # 30% - Silent (give up quietly)
        elif roll < 0.7:
            logger.info("Waiting behavior: Silent response")
            return None  # Don't send anything
        
        # 30% - Understanding (mature response)
        else:
            return random.choice([
                "chắc bạn đang bậnn nhỉii",
                "okeee tớ hiểuu",
                "thì tớ đợiii nàoo",
                "bận thì nói tớớ biết màa"
            ])
    
    @staticmethod  
    def should_send_followup(gap_seconds, waiting_state):
        """
        Determine if should send follow-up based on gap
        
        Args:
            gap_seconds: Time since last activity
            waiting_state: Current state (0-3)
        
        Returns:
            tuple: (should_send, message_type)
        """
        # 5 min check-in
        if 300 < gap_seconds < 600 and waiting_state == 1:
            return (True, '5min')
        
        # 15 min escalation
        elif 600 < gap_seconds < 1800 and waiting_state == 2:
            return (True, '15min')
        
        # Give up after 30min
        elif gap_seconds > 1800:
            return (False, None)
        
        return (False, None)
