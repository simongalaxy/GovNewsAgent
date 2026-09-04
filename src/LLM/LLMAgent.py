import os
import json
import asyncio
import instructor
from openai import AsyncOpenAI
from pprint import pformat
from typing import List, Any, Dict
from pathlib import Path
import textwrap


from src.Util.Settings import settings
from src.Util.logger import Logger
from src.Data.DataClasses import ParsedQuery


class LLMAgent:
    def __init__(self, logger: Logger):
        # initiate logger.
        self.logger=logger
        
        # cloud ollama llm settings.
        self.model_name = settings.ollama_cloud_model
        self.base_url = settings.ollama_base_url
        self.api_key = settings.ollama_api_key
        self.client = instructor.from_openai(
            AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            ),
            mode=instructor.Mode.JSON_SCHEMA,  # Forces JSON extraction compatible with Ollama
        )

        # local state variables to hold the original query, parsed query, extracted data, and summary.
        self.original_query = None
        self.parsed_query = None
        self.extracted_datas = None
        self.summary = None

        # summary report path settings.
        self.summary_report_path = settings.summary_report_path

        # Create log folder if it doesn't exist
        self._create_folder()
        
    # methods for report generation.
    def _create_folder(self):
        os.makedirs(self.summary_report_path, exist_ok=True)
    
    
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
        
        # generate report in text file.
        with open(os.path.join(self.summary_report_path, filename), "w", encoding="utf-8") as file:
            file.write(markdown + "\n")
            
        return filename


    # 💡 抽離出的共用底層非同步方法
    async def _call_llm(self, model: str, messages: list, response_model: type, **kwargs) -> Any:
        """統一管理所有對 Ollama 的非同步請求與異常處理"""
        try:
            return await self.client.create(
                model=model,
                messages=messages,
                response_model=response_model,
                **kwargs
            )
        except Exception as e:
            self.logger.error(f"LLM API call failed [Model: {model}]: {e}")
            raise e
    

    async def parse_query(self, original_query: str) -> ParsedQuery:
        self.logger.info("Start parsing information from query.")
        
        system_instruction = (
            "You are a precise data extraction assistant. Your job is to extract search parameters, timeframes, organizations, and intended actions from the user's request."
        )

        user_prompt = f"""
        Extract the following keys from User Query:
        - "start_date": The beginning of the date range (format: YYYY-MM-DD). If no year is specified, assume the current or contextually appropriate year. If not mentioned, output null.
        - "end_date": The end of the date range (format: YYYY-MM-DD). If not mentioned, output null.
        - "departments": The exact name of the government department, agency, or organization mentioned. If not mentioned, output null.
        - "keywords": A list of key topics, subjects, or phrases to look for, not including the exact name of the government department, agency, or organization mentioned.
        - "actions": A list of specific operations or tasks requested by the user (e.g., 'scrape', 'summarize', 'download').

        Strictly return ONLY the raw JSON object. Do not include markdown formatting, code blocks, or conversational filler.

        ---
        User Query: "{original_query}"

        """

        # 乾淨地呼叫抽離後的非同步方法
        parsed_query = await self._call_llm(
            model=self.model_name,
            messages=[
                { "role": "system", "content": system_instruction },
                { "role": "user", "content": user_prompt }
            ],
            response_model=ParsedQuery,
            timeout=15.0,
            max_retries=3
        )
        self.logger.info(f"Parsed Query: \n%s", pformat(parsed_query.model_dump(by_alias=True), indent=2))
        
        return parsed_query


    async def generate_summary(self, search_results: List[dict], parsed_query: ParsedQuery) -> None:
        self.logger.info("Start generating summary from search results.")
        
        # prepare the documents from search results in pgvector.
        articles = self._format_articles(rows=search_results)

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

        summary = await self._call_llm(
            model=self.model_name,
            messages=[
                { "role": "system", "content": system_prompt },
                { "role": "user", "content": user_prompt }
            ],
            response_model=str,
            timeout=15.0,
            max_retries=3
        )
        self._write_report(markdown=summary)
        self.logger.info("#"*50)
        self.logger.info(f"Generated Summary: \n%s", summary)
        self.logger.info("#"*50)

        return