import json
from ollama import Client
from pydantic import ValidationError
from pprint import pformat

from src.States import ParsedQuery, State
from src.Settings import settings

class QueryParser:
    def __init__(self, logger):
        # setup logger.
        self.logger = logger
        
        # ollama setup.
        self.model_name = settings.ollama_extraction_model
        self.client = Client()

    def parse_query(self, query: str) -> ParsedQuery: 
        prompt = f"""
        Extract the dates and keywords from the user query. 
        
        Content: 
        {query}
        
        You MUST output ONLY valid JSON that matches this schema:

        {{
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "keywords": ["string"]
        }}

        Rules:
        - Convert all dates to ISO format.
        - Record all keywords except "summarize", "scrape", "all", "news".
        """
        
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                        }
                    ],
                format="json",
                options={"temperature": 0.0}
            )
            
            raw = response["message"]["content"]
            parsed_content = ParsedQuery.model_validate_json(raw)
            self.logger.info("Parsed Query: \n%s", pformat(parsed_content.model_dump(by_alias=True), indent=4))
            
            return parsed_content
            
        except (json.JSONDecodeError, ValidationError) as e:
            self.logger.error(f"Failed to parse LLM response: {e}")
            raise