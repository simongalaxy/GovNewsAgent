from ollama import Client  # Native Ollama client

from tools.logger import Logger
from tools.States import State

from typing import List, Dict
from pathlib import Path
import textwrap
from datetime import datetime
import os
from dotenv import load_dotenv


load_dotenv()


class ReportGenerator:
    def __init__(self, logger: Logger):
        # setup logger.
        self.logger = logger
        
        # Ollama setup
        self.model_name = os.getenv("ollama_llm_model")
        self.client = Client()
        
        self.logger.info(f"Report Generator initiated with model - {self.model_name}")
    
    
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
    
    
    def _write_report(self, markdown: str) -> str:
        """Write the generated markdown report to a text file with a timestamped filename, and return the filename."""
        
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # generate filename by daily press release url.
        filename = f"Media_Summary_Report-{current_timestamp}.md"
        filepath = "./reports/"
        
        # generate report in text file.
        with open(os.path.join(filepath, filename), "w", encoding="utf-8") as file:
            file.write(markdown + "\n")
            
        return filename
    
    
    def generate_report(self, state: State) -> None:
        
        try: 
            
            # check whether query_results is not None.
            if not state.query_results:
                warning = "No relevant articles were found for this query and date range."
                self.logger.info(f"Warning: {warning}")
                return warning
                
            # prepare the documents from search results in pgvector.
            articles = self._format_articles(state.query_results)

            # 3. Strong system + user prompt
            system_prompt = "You are a government news summarizer."

            user_prompt = f"""Below are multiple government news articles. Each article has a date, title, and content.

            Articles:
            {articles}

            Your tasks:
            1. Group information by department or topic where possible.
            2. Preserve chronology (earliest to latest).
            3. Be concise but complete, focusing only on information relevant to the query.
            4. Avoid repetition and speculation.

            Write the final summary in clear paragraphs in a markdown format.
            """
 
            # 4. Call Ollama directly
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.0,      # Very important for factual report
                    "num_ctx": 16384,
                    "num_predict": 4096,     # Allow long report
                }
            )

            report_text = response['message']['content']
            state.markdown = report_text
            self.logger.info("#"*50)
            self.logger.info("Report generated: \n%s", report_text)
            self.logger.info("#"*50)
            self._write_report(markdown=report_text)
        
        except Exception as e:
            self.logger.error(f"Failed to generate report for '{state.original_query}': {e}")
            raise
        
        return

    