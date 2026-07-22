import asyncio
from pprint import pformat

from src.logger import Logger
from src.States import State
from src.NewsScraper import NewsScraper
from src.QueryParser import QueryParser
from src.PG_DBHandler import PG_DBHandler
from src.DataExtractor import DataExtractor



# main entry point.
def main():
    
    # initialize logger and crawler
    logger = Logger(__name__).get_logger()
    state = State()
    parser = QueryParser(logger=logger)
    scraper = NewsScraper(logger=logger)
    dbhandler = PG_DBHandler(logger=logger)
    extractor = DataExtractor(logger=logger)
    
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
        #     scraper.fetch_news_by_dates(state=state)
        
        # # save news to database.
        # for item in state.news_items:
        #     logger.info(f"Scraped News: \n{pformat(item.model_dump())}\n")
        #     dbhandler.insert_news(item=item)
        
        # retrieve the scraped news for data extraction.
        dbhandler.retrieve_news_for_extracting_data(state=state)
        
        # extract information from the news.
        extracted_datas = asyncio.run(extractor.extract_data_from_all_news(state=state))
        
    return

if __name__ == "__main__":
    main()
