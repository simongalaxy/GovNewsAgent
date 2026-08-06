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
        state.original_query = input("Enter the query to the Gov News or type 'q' for exit:")
        logger.info(f"User Query stored in state: {state.original_query}")
        if state.original_query.lower() == "q":
            break
        
        # parse the user query.
        parser.parse_query(state=state)
        
        # crawl all relevant news based on parsed_query.
        if state.parsed_query.start_date is not None:
            scraper.fetch_news_by_dates(state=state)
        
        # show summary of scraped news items by date.
        for date, news_urls in zip(state.dates, state.news_urls):
            logger.info(f"Date Page - {date}: {len(news_urls)} news.")
        logger.info("\n")
        
        # extract information from the news.
        asyncio.run(extractor.extract_data_from_all_news(state=state))
        
        # # save news to database.
        logger.info(f"Start saving total {len(state.news_items)} to database.")
        for item in state.news_items:
            # logger.info(f"Scraped News: \n{pformat(item.model_dump())}\n")
            dbhandler.insert_news(item=item)
        
        
        # retrieve the scraped news for data extraction.
        # dbhandler.retrieve_news_for_extracting_data(state=state)
        
       
        
    return

if __name__ == "__main__":
    main()
