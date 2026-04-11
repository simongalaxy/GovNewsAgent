from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional, Dict, Any



class ParsedQuery(BaseModel):
    start_date: date | None = Field(description="start date in the query")
    end_date: date | None = Field(description="end date in the query")
    keywords: List[str] | None = Field(description="keywords to search")
    query_text: str = Field(description="The primary intent of the user query")
    

class NewsItem(BaseModel):
    news_id: str
    published_date: date
    title: str
    content: str
    url: str
    embeddings: List[float]
    
