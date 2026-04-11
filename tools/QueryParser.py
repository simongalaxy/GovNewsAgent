from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from logger import Logger
from tools.States import ParsedQuery

from devtools import debug
import os
from dotenv import load_dotenv
load_dotenv()


class QueryParser:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.model = os.getenv("ollama_llm_model")
        self.llm = ChatOllama(
            model=self.model,
            temperature=0,
        )
        self.parser = PydanticOutputParser(pydantic_object=ParsedQuery)
        self.prompt = PromptTemplate(
            template="Extract info from this query.\n {format_instructions} \n {query} \n",
            input_variables=["query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        self.chain = self.prompt | self.llm | self.parser
        self.logger.info("QueryParser initialized")
    
    def parse_query(self, query: str) -> ParsedQuery:
        parsed_query = self.chain.invoke({"query": query})
        self.logger.info(f"Parsed Query: \n%s", debug(parsed_query))
        # debug(parsed_query)
        
        return parsed_query


## testing
# parser = QueryParser()
# query = "make a summary from the Centre of Food Safety and the Police by topics and by dates in chronical order for the news from 1 April 2026 to 30 April 2026"
# parsed_query = parser.parse_query(query=query)