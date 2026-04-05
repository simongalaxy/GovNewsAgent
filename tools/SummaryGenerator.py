from langchain_ollama.chat_models import ChatOllama
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
            2. Classify all news content by organization.
            3. For each organization, summarize each news content in one paragraph with no more than 1000 words with subheadings using the name of organization, and then present each paragraphs by the order of their publication dates.
                If there are multiple news content from the same organization, summarize each news content in one paragraph with no more than 1000 words, and then present each paragraphs by the topic.
            4. Ensure that the summary directly addresses the query.
            5. Your output should be in markdown format with clear subheadings.
        
            Query: 
            {query}
            
            Content:
            {content}
            
            Summary:
            """
        )
        self.logger.info("SummaryGenerator initialized")
    
    
    def summarize_content(self, query: str, contents: List[str]) -> str:
       
        # Combine the contents into a single string for summarization
        combined_content = "\n".join(contents)
        
        # Format the prompt with the query and combined content
        formatted_prompt = self.prompt_template.format(query=query, content=combined_content)
        self.logger.info("Formatted prompt for summarization: \n%s", formatted_prompt)
        
        # Generate a summary using the language model
        summary = self.model.invoke(formatted_prompt)
        self.logger.info("Summary generated: \n%s", summary.content)
        
        return summary.content