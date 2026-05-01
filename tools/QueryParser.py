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
        self.model_name = os.getenv("ollama_extraction_model")
        if self.model_name is None:
            raise ValueError("Environment variable 'ollama_extraction_model' must be set")

    def parse_query(self, query: str) -> ParsedQuery: 
        prompt = f"""Extract the following information from the user query. 
        Content: {query}
        """
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": query}],
                format=ParsedQuery.model_json_schema(),
                options={"temperature": 0.0}
            )
            response_content = ParsedQuery.model_validate_json(response.message.content)
            self.logger.info("Parsed Query: \n%s", pformat(response_content, indent=4))
            return response_content
            
        except (json.JSONDecodeError, ValidationError) as e:
            self.logger.error(f"Failed to parse LLM response: {e}")