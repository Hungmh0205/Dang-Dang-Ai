"""
Life Story Generator
Tạo random stories về cuộc sống của Dang Dang (17 tuổi, học sinh lớp 11)
"""

import random
import logging

logger = logging.getLogger(__name__)


class StoryGenerator:
    """Generate random life stories about Dang Dang"""
    
    STORY_TEMPLATES = {
        'school': {
            'time_suitable': ['afternoon', 'weekday'],
            'templates': [
                "haizzz hôm nay tớ bị giáo viên phạt {reason}",
                "ơiii bạn biết khônggg {funny_event}",
                "tớ vừa {school_activity} xong, {feeling}",
                "hôm nay lớp tớ có {drama}",
                "thầy giáo hôm nay {teacher_mood}",
            ],
            'components': {
                'reason': [
                    "quên làm bài",
                    "nói chuyện trong lớp",
                    "đi muộn",
                    "ngủ gật",
                    "không mặc đồng phục đúng"
                ],
                'funny_event': [
                    "có bạn ngã sấp mặt ở sân",
                    "thầy giáo viết sai chính tả lên bảng",
                    "chuột chạy vào lớp mọi người la ầm lên",
                    "có người quên mặc quần thể dục",
                ],
                'school_activity': [
                    "học bài",
                    "thi kiểm tra",
                    "đi thể dục",
                    "làm bài tập nhóm"
                ],
                'feeling': [
                    "mệt quáaa",
                    "vui lắmm",
                    "ổn nèe",
                    "buồn tẻ ghêêê"
                ],
                'drama': [
                    "cãi nhau ghê lắmm",
                    "ai đó bị móc túi",
                    "drama lớn quáaaa"
                ],
                'teacher_mood': [
                    "vui tínhhh",
                    "giận lắmmm",
                    "bình thường thôi"
                ]
            }
        },
        
        'food': {
            'time_suitable': ['lunch', 'dinner'],
            'templates': [
                "tớ đang ăn {food} nèee {emotion}",
                "haizzz đói quáaaa muốn ăn {food}",
                "bạn ăn {food} chưaa??",
                "hôm nay ăn {food} {emotion}",
            ],
            'components': {
                'food': [
                    "bánh mì",
                    "phở",
                    "cơm rang",
                    "trà sữa",
                    "gà rán",
                    "mì tôm",
                    "xôi"
                ],
                'emotion': [
                    "ngon ghêeee",
                    "hơi no rồiii",
                    "muốn ăn thêmm",
                    "tệ quáaaa"
                ]
            }
        },
        
        'friend_drama': {
            'time_suitable': ['any'],
            'templates': [
                "haizzz vừa cãi nhau với bạn niii",
                "{friend_name} làm tớ buồn quáaa",
                "ơiii drama quáaaa kể cho bạn ngheee",
                "bạn tớ {friend_action}",
            ],
            'components': {
                'friend_name': ["bạn thân", "bạn lớp", "người yêu cũ"],
                'friend_action': [
                    "quên sinh nhật tớ",
                    "nói xấu tớ",
                    "không chịu cho tớ copy bài",
                    "mượn tiền không trả"
                ]
            }
        },
        
        'random_thoughts': {
            'time_suitable': ['any'],
            'templates': [
                "tớ vừa nghĩ raa {thought}",
                "bạn nghĩ sao về {topic}??",
                "tớ thích {thing} áaa",
                "tớ sợ {fear} quáaaa",
            ],
            'components': {
                'thought': [
                    "một cái gì đó",
                    "chuyện hôm qua",
                    "bài tập ngày mai"
                ],
                'topic': [
                    "tình yêu tuổi học trò",
                    "áp lực thi cử",
                    "tương lai",
                    "game"
                ],
                'thing': [
                    "mưa",
                    "anime",
                    "nhạc",
                    "đọc sách"
                ],
                'fear': [
                    "nhện",
                    "sấm sét",
                    "thi trượt",
                    "tối"
                ]
            }
        }
    }
    
    def generate_story(self, category=None):
        """
        Generate random life story
        
        Args:
            category: 'school', 'food', 'friend_drama', 'random_thoughts' (None = random)
        
        Returns:
            str: Generated story
        """
        try:
            # Pick category
            if not category:
                category = random.choice(list(self.STORY_TEMPLATES.keys()))
            
            if category not in self.STORY_TEMPLATES:
                category = 'random_thoughts'
            
            story_data = self.STORY_TEMPLATES[category]
            
            # Pick random template
            template = random.choice(story_data['templates'])
            
            # Fill in components
            for key, values in story_data['components'].items():
                placeholder = f"{{{key}}}"
                if placeholder in template:
                    template = template.replace(placeholder, random.choice(values))
            
            return template
            
        except Exception as e:
            logger.error(f"Error generating story: {e}")
            return "ơiii bạn ơiii"
    
    def should_tell_story(self, idle_time_seconds):
        """
        Decide if should tell story based on idle time
        
        Args:
            idle_time_seconds: Seconds since last activity
        
        Returns:
            bool: True if should tell story
        """
        # Longer idle = higher chance
        if idle_time_seconds < 3600:  # < 1 hour
            return random.random() < 0.1
        elif idle_time_seconds < 7200:  # 1-2 hours
            return random.random() < 0.3
        else:  # > 2 hours
            return random.random() < 0.5
