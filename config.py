import os
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Config:
    notion_api_version: str = "2022-06-28"
    timezone: str = "Asia/Seoul"
    categories: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = {
                "회의": ["회의", "미팅", "줌", "온라인회의", "컨퍼런스"],
                "상담": ["상담", "컨설팅", "문의", "점검", "상담예약"],
                "시공": ["시공", "공사", "설치", "작업", "철거"],
                "현장방문": ["현장", "실측", "측량", "방문"],
                "내부업무": ["내부", "테스트", "점검", "확인"]
            }

config = Config() 