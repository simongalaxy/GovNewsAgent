from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider
from dataclasses import dataclass

from crawl4ai import CrawlResult
import asyncio
from pprint import pformat
from typing import List

from src.logger import Logger
from src.Settings import settings
from src.DataClass import JobInfo, ExtractedJobInfo


@dataclass
class Instruction:
    content: str

class JobExtractor:
    def __init__(self, logger):
        self.logger = logger
        self.model_name = settings.ollama_extraction_model
        self.base_url = settings.ollama_base_url
        self.api_key = settings.ollama_api_key
        self.prompt = """You are an expert job‑ad analyst. Extract and infer information with high precision.

        TASKS:
        1. Extract explicit information exactly as written.
        2. Get the company name from the context. If company name is missing, just state None.
        3. Read the job ad and output one industry label only. No Explanation (e.g., “fintech company”, “global bank”, “AI startup”). 
        4. Extract core responsibilities explicitly mentioned in the job ad.
        5. Extract core working experiences explicitly mentioned in the job ad.
        6. Extract technical skills (e.g. python, SQL, AWS) explicitly mentioned in the job ad.
        7. Extract soft skills (e.g. communication, teamwork, problem-solving) explicitly mentioned in the job ad.
        8. Summarize the job in structured JSON.
        """
        
        self.model = OllamaModel(
            model_name=self.model_name,
            provider=OllamaProvider(
                base_url=self.base_url,
                api_key=self.api_key
            )
        )
        # Use NativeOutput wrapper for the output dataclass
        # Adjust argument names to match Agent constructor
        self.extract_agent = Agent(
            model=self.model,
            system_prompt=self.prompt,
            output_type=ExtractedJobInfo,
            model_settings=ModelSettings(
                temperature=0.0,
                max_tokens=2048,
            )
        )
        
    async def _summarize_job_info(self, result: CrawlResult, keyword: str) -> JobInfo:
        url = result.url
        job_id = url.split("/")[-1].split("?")[0]
        content = result.markdown
        
        try:
            # extract job info by LLm.{{
            response = await self.extract_agent.run(f"Job Content: \n{content}")
            extracted = response.output
            
            job_info = JobInfo(
                id=job_id,
                url=url,
                content=content,
                keyword=keyword,
                job_info=extracted
            )
            
            self.logger.info("Successfully extracted job: \n%s", pformat(job_info.model_dump(), indent=4))
            self.logger.info("#"*50)
        
            return job_info

        except Exception as e:
            self.logger.error(f"Failed to extract job {job_id}: {e}")
            # Fallback: return basic info so the pipeline doesn't crash
            return JobInfo(
                id=job_id,
                url=url,
                content=content,
                keyword=keyword,
                job_info=ExtractedJobInfo(
                    job_title=None,
                    company=None,
                    responsibilities=None,
                    qualifications=None,
                    experiences=None,
                    technical_skills=None,
                    soft_skills=None,
                    salary=None,
                    working_location=None,
                    industry=None,
                )
            )

            
    async def summarize_all_jobs(self, results: List[CrawlResult], keyword: str) -> List[JobInfo]:
        self.logger.info(f"Starting extraction for {len(results)} jobs...")

        semaphore = asyncio.Semaphore(4)   # Tune this (3~6) based on your GPU/RAM

        async def bounded_extract(result: CrawlResult):
            async with semaphore:
                return await self._summarize_job_info(result, keyword)

        tasks = [bounded_extract(result) for result in results]
        job_infos = await asyncio.gather(*tasks, return_exceptions=True)

        # Remove any exceptions
        successful = [j for j in job_infos if not isinstance(j, Exception)]
        self.logger.info(f"Extraction completed. {len(successful)}/{len(results)} jobs succeeded.")

        return successful