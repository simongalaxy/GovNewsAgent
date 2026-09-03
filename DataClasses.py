from pydantic import BaseModel, Field
from datetime import date
from typing import List


class ParsedQuery(BaseModel):
    start_date: str = Field(description="The beginning date, ISO date format YYYY-MM-DD")
    end_date: str | None = Field(description="The ending date, ISO date format YYYY-MM-DD")
    departments: List[str] | None = Field(description="Name of Department or Bureau")
    keywords: List[str] | None = Field(description="keywords for searching")
    action: List[str] | None = Field(description="action to do in the query")


class ExtractedData(BaseModel):
    id: str = Field(description="ID of the press release")
    subject_department: str = Field(description="Subject Department/Bureau issued this press release")
    summary: str = Field(description="Summary of Press Release with maximum 800 words. All specific keywords and names should be kept.")

    
class NewsItem(BaseModel): # to store the news items that are relevant to the user query.
    id: str = Field(description="ID of the press release")
    published_date: date = Field(description="Date published the press release")
    title: str = Field(description="title of the press release")
    content: str = Field(description="Raw Content of the press release")
    url: str = Field(description="url of the press release")
   
    


    
    
