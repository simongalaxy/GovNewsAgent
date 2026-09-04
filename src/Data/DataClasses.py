from pydantic import BaseModel, Field
from datetime import date
from typing import List


class ParsedQuery(BaseModel):
    start_date: str = Field(description="The beginning date, ISO date format YYYY-MM-DD")
    end_date: str | None = Field(description="The ending date, ISO date format YYYY-MM-DD")
    departments: List[str] | None = Field(description="The exact name of the government department, agency, or organization mentioned")
    keywords: List[str] | None = Field(description="A list of core topics, subjects, or phrases the user wants to search for")
    actions: List[str] | None = Field(description="A list of specific operations or tasks requested by the user (e.g., 'scrape', 'summarize', 'download')")


# class SummaryReport(BaseModel):
#     markdown_content: str = Field(description="The complete generated markdown text summary report.")
    
class NewsItem(BaseModel): # to store the news items that are relevant to the user query.
    id: str = Field(description="ID of the press release")
    title: str = Field(description="title of the press release")
    content: str = Field(description="Raw Content of the press release")
    url: str = Field(description="url of the press release")
    published_date: date = Field(description="Date published the press release")
   
    


    
    
