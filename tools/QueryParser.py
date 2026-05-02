import json
import ollama
from pydantic import ValidationError
from pprint import pformat

from tools.States import ParsedQuery, State

import os
from dotenv import load_dotenv
load_dotenv()

class QueryParser:
    def __init__(self, logger):
        self.logger = logger
        model_name = os.getenv("ollama_extraction_model")
        if model_name is None:
            raise ValueError("Environment variable 'ollama_extraction_model' must be set")
        self.model_name = model_name

    def parse_query(self, query: str) -> ParsedQuery: 
        prompt = f"""
        Extract the dates and keywords from the user query. 
        
        Content: 
        {query}
        
        You MUST output ONLY valid JSON that matches this schema:

        {{
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "departments": ["string"]
        }}

        Rules:
        - Convert all dates to ISO format.
        - "Police" must be normalized to "Hong Kong Police Force".
        - "Department of Health" stays as-is.
        - Departments NEVER belong to dates.
        - If multiple departments are mentioned, list all of them.
        
        """
        
        try:
            response = ollama.chat(
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
            self.logger.info("Parsed Query: \n%s", pformat(parsed_content, indent=4))
            return parsed_content
            
        except (json.JSONDecodeError, ValidationError) as e:
            self.logger.error(f"Failed to parse LLM response: {e}")
            raise