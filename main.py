import asyncio
from pprint import pformat

from src.logger import Logger
from src.States import State
from src.NewsFetcher import NewsFetcher
from src.QueryParser import QueryParser
from src.PG_DBHandler import PG_DBHandler
from src.NewsExtractor import NewsExtractor



# main entry point.
def main():
    
    # initialize logger and crawler
    logger = Logger(__name__).get_logger()
    state = State()
    parser = QueryParser(logger=logger)
    fetcher = NewsFetcher(logger=logger)
    dbhandler = PG_DBHandler(logger=logger)
    extractor = NewsExtractor(logger=logger)
    
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
        
        # # crawl all relevant news based on parsed_query.
        # if state.parsed_query.start_date is not None:
        #     fetcher.fetch_news_by_dates(state=state)
        
        # # save news to database.
        # for item in state.news_items:
        #     logger.info(f"Scraped News: \n{pformat(item.model_dump())}\n")
        #     dbhandler.insert_news(item=item)
        
        # retrieve the scraped news for data extraction.
        results = dbhandler.retrieve_news_for_extracting_data(state=state)
        logger.info(f"Total no. of news retrieved from period {state.parsed_query.start_date} to {state.parsed_query.end_date}: {len(results)}")
        # logger.info(f"First news retrieved: \n%s", pformat(dict(results[3]), indent=2))
        
        # extract information from the news.
        results = asyncio.run(extractor.extract_data_from_all_news(result))
        
    return

if __name__ == "__main__":
    main()
