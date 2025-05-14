import logging
from utils import config, ValidationError

logger = logging.getLogger(__name__)

def classify_category(text: str) -> str:
    """명령어에 포함된 단어를 기반으로 일정의 카테고리를 분류"""
    if not isinstance(text, str):
        raise ValidationError("text must be a string")

    text = text.lower()
    for category, keywords in config.categories.items():
        if any(keyword.lower() in text for keyword in keywords):
            logger.info(f"Classified category: {category}")
            return category

    logger.info("No category matched, returning '미정'")
    return "미정"
