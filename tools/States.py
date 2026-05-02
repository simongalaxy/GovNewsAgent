from pydantic import BaseModel, Field, model_validator
from crawl4ai import CrawlResult
from datetime import date
from typing import List, Optional

class ParsedQuery(BaseModel):
    start_date: str | None = Field(description="ISO date string, e.g. '2026-04-01'")
    end_date: str | None = Field(description="ISO date string, e.g. '2026-04-02'")
    keywords: List[str] | None = Field(default=None, description="free-text keywords")
    departments: List[str] | None = Field(default=None, description="HK government departments")

    
class NewsItem(BaseModel): # to store the news items that are relevant to the user query.
    news_id: str
    published_date: date
    title: str
    content: str
    url: str
    embeddings: List[float] = []


class State(BaseModel): # to store the overall state of the system, including the parsed query and the news items.
    original_query: str = None
    query_embeddings: List[float] | None = None
    parsed_query: ParsedQuery = None
    news_items: List[NewsItem] = []
    
    
