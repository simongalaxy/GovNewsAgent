from pydantic import BaseModel, Field, model_validator
from datetime import date
from typing import List, Optional



class ParsedQuery(BaseModel):
    start_date: str | None = Field(description="start date in the query")
    end_date: str | None = Field(description="end date in the query")
    keywords: List[str] | None = Field(description="keywords to search")
    query_text: str = Field(description="The primary intent of the user query")
    
    @model_validator(mode="after")
    def fill_end_date(self):
        if self.end_date is None:
            self.end_date = self.start_date
        return self
    
    
class NewsItem(BaseModel):
    news_id: str
    published_date: date
    title: str
    content: str
    url: str
    embeddings: List[float]
    
