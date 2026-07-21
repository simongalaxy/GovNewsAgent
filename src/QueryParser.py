import instructor
from openai import OpenAI

from src.Settings import settings
from src.logger import Logger
from src.States import ParsedQuery

class QueryParser:
    def __init__(self, logger: Logger):
        # initiate logger.
        self.logger=logger
        
        # cloud ollama llm settings.
        self.model_name = settings.ollama_cloud_model
        self.base_url = settings.ollama_base_url
        self.api_key = settings.ollama_api_key
        self.client = instructor.from_openai(
            OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            ),
            mode=instructor.Mode.JSON_SCHEMA,
        )
    
    
    def parse_query(self, query: str) -> ParsedQuery:
        self.logger.info("Start parsing information from query.")
        
        system_instruction = (
            "You are a strict data extraction AI. Extract the requested fields "
            "as a flat JSON object matching the requested schema layout. "
            "Convert any relative or explicit dates to YYYY-MM-DD format."
        )

        user_prompt = f"""
        Extract entities from the user query.
        
        User Query: "{query}"
        
        Filtering Rules:
        - Do not include action verbs (like 'news', 'summarize', 'scrape', 'all') in keywords.
        - Put entities like 'Department of Health' into the departments array.
        """
        
        resp = self.client.create( 
            model=self.model_name, 
            messages=[ 
                { "role": "system", "content": system_instruction },
                { "role": "user", "content": user_prompt } 
            ], 
            max_retries=3,
            timeout=15.0, 
            response_model=ParsedQuery, 
        ) 

        parsed_query_json = resp.model_dump_json(indent=2)
        self.logger.info(f"Parsed Query: \n%s", parsed_query_json)
        
        return resp