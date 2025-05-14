from utils import get_logger
import re
from datetime import datetime, timedelta

logger = get_logger(__name__)

class Parser:
    def __init__(self):
        self.date_patterns = [
            (r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', '%Y년 %m월 %d일'),
            (r'(\d{1,2})월\s*(\d{1,2})일', '%m월 %d일'),
            (r'(\d{1,2})일', '%d일'),
            (r'내일', 'tomorrow'),
            (r'모레', 'day_after_tomorrow'),
            (r'다음주', 'next_week')
        ]
        
        self.time_patterns = [
            (r'(\d{1,2})시\s*(\d{1,2})분', '%H시 %M분'),
            (r'(\d{1,2})시', '%H시'),
            (r'오전\s*(\d{1,2})시', 'AM %H시'),
            (r'오후\s*(\d{1,2})시', 'PM %H시')
        ]

    def parse_date(self, text: str) -> datetime:
        """Parse date from text"""
        try:
            current_date = datetime.now()
            
            for pattern, format_str in self.date_patterns:
                match = re.search(pattern, text)
                if match:
                    if format_str == 'tomorrow':
                        return current_date + timedelta(days=1)
                    elif format_str == 'day_after_tomorrow':
                        return current_date + timedelta(days=2)
                    elif format_str == 'next_week':
                        return current_date + timedelta(days=7)
                    else:
                        try:
                            return datetime.strptime(match.group(0), format_str)
                        except ValueError:
                            continue
            
            logger.warning(f"No date pattern matched in text: {text}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date: {str(e)}")
            return None

    def parse_time(self, text: str) -> datetime:
        """Parse time from text"""
        try:
            current_time = datetime.now()
            
            for pattern, format_str in self.time_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        time_str = match.group(0)
                        if 'AM' in format_str:
                            hour = int(re.search(r'(\d{1,2})', time_str).group(1))
                            if hour == 12:
                                hour = 0
                        elif 'PM' in format_str:
                            hour = int(re.search(r'(\d{1,2})', time_str).group(1))
                            if hour != 12:
                                hour += 12
                        else:
                            hour = int(re.search(r'(\d{1,2})', time_str).group(1))
                        
                        minute = 0
                        minute_match = re.search(r'(\d{1,2})분', time_str)
                        if minute_match:
                            minute = int(minute_match.group(1))
                        
                        return current_time.replace(hour=hour, minute=minute)
                    except ValueError:
                        continue
            
            logger.warning(f"No time pattern matched in text: {text}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing time: {str(e)}")
            return None

    def parse_datetime(self, text: str) -> tuple:
        """Parse both date and time from text"""
        try:
            date = self.parse_date(text)
            time = self.parse_time(text)
            
            if date and time:
                return (
                    date.replace(hour=time.hour, minute=time.minute),
                    date.replace(hour=time.hour, minute=time.minute) + timedelta(hours=1)
                )
            elif date:
                return (
                    date,
                    date + timedelta(hours=1)
                )
            elif time:
                return (
                    time,
                    time + timedelta(hours=1)
                )
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error parsing datetime: {str(e)}")
            return None, None

    def extract_task_name(self, text: str) -> str:
        """Extract task name from text"""
        try:
            # Remove date and time patterns
            for pattern, _ in self.date_patterns + self.time_patterns:
                text = re.sub(pattern, '', text)
            
            # Clean up the text
            text = text.strip()
            text = re.sub(r'\s+', ' ', text)
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting task name: {str(e)}")
            return text 