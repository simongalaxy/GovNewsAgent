from ollama import Client  # Native Ollama client

from src.logger import Logger
from src.States import State

from typing import List, Dict
from pathlib import Path
import textwrap
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class ReportGenerator:
    def __init__(self, logger: Logger):
        # setup logger and report path.
        self.logger = logger
        self.reportpath = os.getenv("reportpath")
        
        # Ollama setup
        self.model_name = os.getenv("ollama_llm_model")
        self.client = Client()
        
        self.logger.info(f"Report Generator initiated with model - {self.model_name}")
    
    # Create log folder if it doesn't exist
        self._create_folder()
    
    
    def _create_folder(self):
        os.makedirs(self.reportpath, exist_ok=True)
    
    
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
            system_prompt = """You are an expert government news analyst and report writer.
            Your job is to synthesize multiple official news articles into a high-quality, comprehensive situational summary for senior officials.

            Core rules:
            - Be thorough and comprehensive — do not be overly concise.
            - Always preserve strict chronological order (earliest to latest).
            - Group related developments logically (by department, topic, or theme) while maintaining overall timeline.
            - Highlight key decisions, policy changes, new initiatives, statements, and outcomes.
            - Include important details, numbers, dates, and responsible agencies.
            - Avoid repetition, speculation, and commentary. Stick to facts from the articles.
            - Use clear, formal, neutral language suitable for government reporting."""

            user_prompt = f"""Below are the full texts of multiple government news articles related to the query.

            Articles (in no particular order):
            {articles}

            Please create a comprehensive **Media Summary Report** with the following requirements:

            1. **Structure**:
            - Start with a short executive overview (2-4 sentences).
            - Then organize the main body in strict chronological order (earliest events first).
            - Use clear markdown headings and sub-headings (## Date or ## Topic).
            - Group related developments when logical, but never break chronology.

            2. **Content Guidelines**:
            - Cover all significant points from the provided articles.
            - Be detailed and comprehensive rather than brief.
            - Include key facts, figures, dates, names of officials/agencies, and outcomes.
            - Show progression and evolution of the issue over time.
            - If multiple departments or topics are involved, create logical sections while keeping the overall timeline intact.

            3. **Style**:
            - Formal, objective, and professional tone.
            - Clear paragraphs. Use bullet points only for lists of actions or key outcomes when appropriate.
            - Do not omit important information just to keep it short.

            Write the complete report now."""
 
            # 4. Call Ollama directly
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.1,      # Slight increase from 0.0 helps fluency without losing facts
                    "num_ctx": 32768,        # Increase context if your model supports it (many do)
                    "num_predict": 8192,     # Significantly increase max output length
                    "top_p": 0.95,
                    "top_k": 40,
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

    