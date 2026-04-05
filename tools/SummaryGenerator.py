from langchain_ollama.chat_models import ChatOllama
from langchain_classic.chains.summarize import load_summarize_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

from tools.logger import Logger
from typing import List

import os
from dotenv import load_dotenv
load_dotenv()


class SummaryGenerator:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.model = ChatOllama(
            model=os.getenv("ollama_llm_model"),
            temperature=0.7
        )
        self.prompt_template = PromptTemplate(
            input_variables=["query", "content"],
            template="""
            You are a helpful assistant for summarizing news content.
            Given the following news content and a query, provide a concise summary that addresses the query.
            
            Your tasks:
            1. Read the provided news content carefully.
            2. Categorize the news content by department.
            3. For each category, summarize the news content no more than 1000 words in a clear, concise and chronological manner, ensuring that the summary directly addresses the query.
        
            Query: 
            {query}
            
            Content:
            {content}
            
            Summary:
            """
        )
        self.chain = load_summarize_chain(
            llm=self.model, 
            chain_type="map_reduce", 
            map_prompt=self.prompt_template,
            verbose=True
        )
        self.logger.info("SummaryGenerator initialized")
    
    
    def summarize_content(self, query: str, query_results: List[Document]) -> str:
        # Extract the content from the query results
        contents = [doc.page_content for doc in query_results]
        
        # Combine the contents into a single string for summarization
        combined_content = "\n".join(contents)
        
        # Generate a summary using the language model
        summary = self.chain.invoke({"content": combined_content, "query": query})
        self.logger.info("Summary generated: \n%s", summary)
        
        
        return summary