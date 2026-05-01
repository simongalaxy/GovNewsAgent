from pydantic import BaseModel, Field, model_validator
from crawl4ai import CrawlResult
from datetime import date
from typing import List, Optional

class ParsedQuery(BaseModel): # to store the parsed information from user query.
    start_date: str | None = Field(description="start date")
    end_date: str | None = Field(description="end date")
    keywords: List[str] | None = Field(description="keywords to search, e.g. Department of Health, Programme")
    
    
class NewsItem(BaseModel): # to store the news items that are relevant to the user query.
    news_id: str
    published_date: date
    title: str
    content: str
    url: str
    embeddings: List[float] = []


class State(BaseModel): # to store the overall state of the system, including the parsed query and the news items.
    oringinal_query: str = None
    parsed_query: ParsedQuery = None
    news_items: List[NewsItem] = []
    
    
