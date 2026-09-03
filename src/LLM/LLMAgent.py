import os
import json
import asyncio
import instructor
from openai import AsyncOpenAI
from pprint import pformat
from typing import List, Any

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
        self.original_query = None
        self.parsed_query = None
        self.extracted_datas = None
        self.summary = None


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
            "You are a strict data extraction AI. Extract the requested fields "
            "as a flat JSON object matching the requested schema layout. "
            "Convert any relative or explicit dates to YYYY-MM-DD format."
        )

        user_prompt = f"""
        Extract entities from the user query.
        
        User Query: "{original_query}"
        
        Filtering Rules:
        - Do not include action verbs (like 'news', 'summarize', 'scrape', 'all') in keywords.
        - Put entities like 'Department of Health' into the departments array.
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


    async def generate_summary(self, search_results: List[dict], parsed_query: ParsedQuery) -> str:
        self.logger.info("Start generating summary from search results.")
        
        system_instruction = (
            "You are a strict summarization AI. Generate a concise summary "
            "in markdown format based on the provided search results."
        )

        user_prompt = f"""
        Generate a summary based on the following search results.
        
        Search Results: {json.dumps(search_results, indent=2)}
        
        Summary Rules:
        - Focus on the most relevant information.
        - Use bullet points for clarity.
        - Include any important dates or events mentioned.
        """

        summary = await self._call_llm(
            model=self.model_name,
            messages=[
                { "role": "system", "content": system_instruction },
                { "role": "user", "content": user_prompt }
            ],
            response_model=str,
            timeout=15.0,
            max_retries=3
        )
        
        self.logger.info(f"Generated Summary: \n%s", summary)
        
        return summary