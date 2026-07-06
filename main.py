import asyncio
from pprint import pformat

from src.logger import Logger
from src.States import State
from src.NewsFetcher import NewsFetcher
from src.QueryParser import QueryParser




# main entry point.
def main():
    
    # initialize logger and crawler
    logger = Logger(__name__).get_logger()
    state = State()
    parser = QueryParser(logger=logger)
    fetcher = NewsFetcher(logger=logger)

    
    while True:
        user_query = input("Enter the query to the Gov News or type 'q' for exit:")
        logger.info(f"User Query: {user_query}")
        if user_query.lower() == "q":
            break
        
        # save the original query and its embeddings into state.
        state.original_query = user_query
        logger.info(f"Original query stored in state: {state.original_query}")
        
        # parse the user query.
        state.parsed_query = parser.parse_query(query=user_query)
        
        # crawl all relevant news based on parsed_query.
        if state.parsed_query.start_date is not None:
            fetcher.fetch_news_by_dates(state=state)
        
        
        
    return

if __name__ == "__main__":
    main()
