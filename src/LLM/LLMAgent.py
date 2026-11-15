import os
import instructor
from datetime import datetime
from openai import AsyncOpenAI
from pprint import pformat
from typing import List, Any, Dict, Optional

from src.Util.Settings import settings
from src.Util.logger import Logger
from src.Data.DataClasses import ParsedQuery


class LLMAgent:
    # Default class-level switch (can also be overridden when instantiating: LLMAgent(logger, use_cloud=True))
    USE_CLOUD: bool = False

    def __init__(self, logger: Logger, use_cloud: Optional[bool] = None):
        self.logger = logger
        self.use_cloud = self.USE_CLOUD if use_cloud is None else use_cloud

        # Configure model, URL, API key, and instructor mode based on provider
        if self.use_cloud:
            self.model_name = settings.ollama_cloud_model
            self.base_url = settings.ollama_base_url
            self.api_key = settings.ollama_api_key
            instructor_mode = instructor.Mode.JSON_SCHEMA
            self.logger.info(f"LLMAgent initialized in CLOUD mode [Model: {self.model_name}]")
        else:
            self.model_name = settings.local_ollama_model
            self.base_url = settings.local_ollama_url  # e.g. http://localhost:11434/v1
            self.api_key = "ollama"
            instructor_mode = instructor.Mode.JSON
            self.logger.info(f"LLMAgent initialized in LOCAL mode [Model: {self.model_name}]")

        # Raw OpenAI-compatible async client (used for Markdown generation)
        self.raw_client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        # Instructor-wrapped client (used for structured Pydantic JSON extraction)
        self.client = instructor.from_openai(
            self.raw_client,
            mode=instructor_mode,
        )

        self.original_query = None
        self.parsed_query = None
        self.extracted_datas = None

        self.summary_report_path = settings.summary_report_path
        self._create_folder()

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
        """Write the generated markdown report to a file and return the filename."""
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Media_Summary_Report-{current_timestamp}.md"
        filepath = os.path.join(self.summary_report_path, filename)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(markdown + "\n")

        self.logger.info(f"Report saved to {filepath}")
        return filename

    async def _call_llm(
        self,
        messages: list,
        response_model: Optional[type] = None,
        model: Optional[str] = None,
        num_ctx: int = 8192,
        **kwargs,
    ) -> Any:
        """Unified async caller supporting both Local Ollama and Cloud endpoints."""
        target_model = model or self.model_name

        # Only pass Ollama-specific num_ctx options when running locally
        if not self.use_cloud:
            kwargs.setdefault("extra_body", {"options": {"num_ctx": num_ctx}})

        try:
            if response_model is not None:
                return await self.client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    response_model=response_model,
                    **kwargs,
                )
            else:
                response = await self.raw_client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    **kwargs,
                )
                return response.choices.message.content
        except Exception as e:
            mode_label = "CLOUD" if self.use_cloud else "LOCAL"
            self.logger.error(f"LLM API call failed [{mode_label} | Model: {target_model}]: {e}")
            raise

    async def parse_query(self, original_query: str) -> ParsedQuery:
        self.logger.info("Start parsing information from query.")
        self.original_query = original_query
        today_str = datetime.now().strftime("%Y-%m-%d")

        system_instruction = (
            "You are a precise data extraction assistant. Your job is to extract "
            "search parameters, timeframes, organizations, and intended actions from the user's request."
        )

        user_prompt = f"""
        Current Date: {today_str}

        Extract the following keys from User Query:
        - "start_date": The beginning of the date range (format: YYYY-MM-DD). If no year is specified, assume the current year based on Current Date ({today_str}). If not mentioned, output null.
        - "end_date": The end of the date range (format: YYYY-MM-DD). If not mentioned, output null.
        - "departments": The exact name of the government department, agency, or organization mentioned. If not mentioned, output null.
        - "keywords": A list of key topics, subjects, or phrases to look for, not including the exact name of the government department, agency, or organization mentioned.
        - "actions": A list of specific operations or tasks requested by the user (e.g., 'scrape', 'summarize', 'download').

        ---
        User Query: "{original_query}"
        """

        parsed_query = await self._call_llm(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            response_model=ParsedQuery,
            num_ctx=4096,
            timeout=120.0,
            max_retries=3,
        )
        self.parsed_query = parsed_query
        self.logger.info(
            "Parsed Query:\n%s",
            pformat(parsed_query.model_dump(by_alias=True), indent=2),
        )
        return parsed_query

    async def generate_summary(self, search_results: List[dict]) -> str:
        if not search_results:
            self.logger.warning("No search results provided to summarize.")
            return ""

        self.logger.info(f"Start generating summary from {len(search_results)} search results.")
        articles = self._format_articles(rows=search_results)

        system_prompt = """
        You are an expert Media Analyst and Policy Researcher. Your task is to synthesize unstructured media coverage and news articles into a structured, highly organized media summary report.

        You must strictly organize the output using the following hierarchical structure:
        1. Department
        2. Topic

        For EACH individual topic, you must format the content in this exact order:
        - **Background Paragraph(s)**: Provide the baseline context, foundational facts, and initial trigger for the topic.
        - **Chronological History**: Present a timeline or sequence of events detailing how the topic evolved over time. Ensure dates or timeframes are explicitly noted.
        - **Government Stand**: A concise summary of the official government position, policy statements, or actions regarding this topic.
        - **Opposite Views**: A summary of criticism, public backlash, opposition party statements, or alternative viewpoints.

        CRITICAL CONSTRAINTS:
        - Do not mix the Government Stand and Opposite Views into the chronological history; they must remain at the very end of each topic section.
        - Maintain a neutral, analytical tone.
        - Do not add conversational fluff or introductory meta-commentary (e.g., "Sure, here is your summary"). Start directly with the first department.
        """

        user_prompt = f"""
        Please analyze the following raw media reports and generate a structured media summary according to your system instructions:

        1. **Content Guidelines**:
        - Cover all significant points from the provided articles.
        - Be detailed and comprehensive rather than brief; do not omit key dates, figures, or policy details.
        - Rely strictly on the provided articles without inventing external facts.

        2. **Raw Media Reports**:
        {articles}
        """

        markdown_report = await self._call_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_model=None,
            num_ctx=16384,
            timeout=300.0,
        )

        filename = self._write_report(markdown_report)
        return filename
