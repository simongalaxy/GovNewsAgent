import ollama
import os
from typing import List
from dotenv import load_dotenv
load_dotenv()


from tools.logger import Logger
from tools.States import NewsItem


class ContentEmbedder:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.model = os.getenv("ollama_embedding_model")


    def embed_news(self, item: NewsItem) -> None:
        response = ollama.embed(
            model=self.model, 
            input=item.content
            )
        item.embeddings = response["embeddings"]
        self.logger.info(f"{item.title} - embeddings generated. Length: {len(response["embeddings"][0])}")
    
        return
   
   
    def embed_query_text(self, query: str) -> List[float]:
        response = ollama.embed(
            model=self.model, 
            input=query
            )
        embeddings = response["embeddings"]
        self.logger.info(f"query embeddings generated. Length: {len(response["embeddings"][0])}")
    
        return embeddings

