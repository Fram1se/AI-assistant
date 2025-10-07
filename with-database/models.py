from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    created_at: datetime
    last_activity: datetime
    search_count: int = 0

@dataclass
class SearchQuery:
    id: int
    user_id: int
    query_text: str
    query_type: str  # 'general', 'difference', 'history'
    result_count: int
    created_at: datetime

@dataclass
class SearchResult:
    id: int
    query_id: int
    source: str  # 'wikipedia_ru', 'wikipedia_en', 'duckduckgo'
    title: str
    summary: str
    url: str
    created_at: datetime