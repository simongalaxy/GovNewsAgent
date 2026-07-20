from pydantic import BaseModel, Field, model_validator
from datetime import date
from typing import List, Optional

class ParsedQuery(BaseModel):
    start_date: str = Field(description="The beginning date, ISO date format YYYY-MM-DD")
    end_date: str | None = Field(description="The ending date, ISO date format YYYY-MM-DD")
    keywords: List[str] | None = Field(description="List of search terms or core topics")
    departments: List[str] | None = Field(description="Government branches, bureaux or departments")

    
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
    query_results: List[dict] = []
    markdown: str = None
    

    
    
