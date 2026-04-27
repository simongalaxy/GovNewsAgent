from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from typing import List, Dict

from tools.logger import Logger
from typing import List

import os
from dotenv import load_dotenv
load_dotenv()


class LLMSummarizer:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.model = ChatOllama(
            model=os.getenv("ollama_llm_model"),
            temperature=0.2
        )
        self.prompt_template = PromptTemplate(
            input_variables=["query", "content"],
            template="""
            You are a government news summarizer.

            User query:
            {query}

            Below are multiple government news articles. Each article has a date, title, and content.

            Articles:
            {articles}

            Your tasks:
            1. Group information by department or topic where possible.
            2. Preserve chronology (earliest to latest).
            3. Be concise but complete, focusing only on information relevant to the query.
            4. Avoid repetition and speculation.

            Write the final summary in clear paragraphs in a markdown format.
            """
        )
        self.logger.info("SummaryGenerator initialized")
    
    
    def _format_articles(self, rows: List[Dict]) -> str:
        """Turn DB rows into a readable block for the LLM."""
        parts = []
        for r in rows:
            parts.append(
                f"Date: {r.get('published_date')}\n"
                f"Title: {r.get('title')}\n"
                f"Content:\n{r.get('content')}\n"
                "-----"
            )
        return "\n\n".join(parts)
    
    
    def summarize_content(self, query: str, rows: List[Dict]) -> str:
        
        if not rows:
            warning = "No relevant articles were found for this query and date range."
            self.logger.info(f"Warning: {warning}")
            return warning
            
        # prepare the documents from search results in pgvector.
        articles_block = self._format_articles(rows)
        prompt_str = self.prompt_template.format(query=query, articles=articles_block)

        # ChatOllama accepts a plain string as a single user message
        summary = self.model.invoke(prompt_str)
        self.logger.info("Summary generated: \n%s", summary.content)
        # result is usually a ChatMessage; get the content
        
        return summary.content
    
