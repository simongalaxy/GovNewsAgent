from pydantic import BaseModel, Field, model_validator
from datetime import date
from typing import List, Optional, Literal

class ParsedQuery(BaseModel):
    start_date: str = Field(description="The beginning date, ISO date format YYYY-MM-DD")
    end_date: str | None = Field(description="The ending date, ISO date format YYYY-MM-DD")
    keywords: List[str] | None = Field(description="List of search terms or core topics")
    departments: List[str] | None = Field(description="Government branches, bureaux or departments")

    
class NewsItem(BaseModel): # to store the news items that are relevant to the user query.
    id: str = Field(description="ID of the press release")
    title: str = Field(description="title of the press release")
    content: str = Field(description="Raw Content of the press release")
    url: str = Field(description="url of the press release")
    published_date: date = Field(description="Date published the press release")
    
class ExtractedData(BaseModel):
    id: str | None = Field(description="ID of the press release")
    subject_department: str = Field(description="Subject Department/Bureau issued this press release")
    summary: str = Field(description="Summary of Press Release")
    category: str = Field(description="Category of Press Release, e.g. Security, Education, Health, Welfare, Public Goverance")
    keywords: list[str] = Field(description="Maximun 5 keywords of the press release, keep original wordings")
    content_type: Literal["Press Release", "Speech", "Response to Query"]

class State(BaseModel): # to store the overall state of the system, including the parsed query and the news items.
    original_query: str = None
    parsed_query: ParsedQuery = None
    news_items: List[NewsItem] = []
    retrieved_items: List[dict] = []
    extracted_items: List[ExtractedData] = []
    search_results: List[dict] = []
    markdown: str = None
    

    
    
