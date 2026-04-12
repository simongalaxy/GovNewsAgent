from langchain_ollama import OllamaEmbeddings
from datetime import datetime
from crawl4ai import CrawlResult
from typing import List
import numpy as np

from pprint import pformat
import os
from dotenv import load_dotenv
from sympy import content
load_dotenv()

from tools.logger import Logger
from tools.States import NewsItem


class DataProcessor:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.model = os.getenv("ollama_embedding_model")
        self.embeddings = OllamaEmbeddings(model=self.model)

    def _embed_text(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)
    
    
    def _to_postgres_date(self, date_str: str) -> str:
        # Parse the natural-language date
        dt = datetime.strptime(date_str, "%B %d, %Y")
        # Format into PostgreSQL date format
        return dt.strftime("%Y-%m-%d")


    def get_info_from_result(self, result: CrawlResult) -> NewsItem:
        url = result.url
        content = result.markdown
        news_id = url.split("/")[-1].split(".")[0]  # Extract news_id from URL
        title = result.metadata["title"]
        date_str = content.split("\n")[-4].split(", ", 1)[-1].strip()
        
        item = NewsItem(
            news_id=news_id,
            published_date= self._to_postgres_date(date_str=date_str),
            title=title,
            content=content,
            url=url,
            embeddings=self._embed_text(text=content)
        )
        
        self.logger.info(f"Extracted info from result: /n%s", pformat(item.model_dump(exclude={"embeddings"}), indent=4))
        
        return item