import asyncio
from pprint import pformat

from src.Util.logger import Logger
from src.Data.DataClasses import NewsItem, ParsedQuery
from src.LLM.LLMAgent import LLMAgent
from src.WebScraper.NewsScraper import NewsScraper
from src.Database.PG_DBHandler import PG_DBHandler



# main entry point.
async def main():
    
    # initialize classes.
    logger = Logger(__name__).get_logger()
    scraper = NewsScraper(logger=logger)
    agent = LLMAgent(logger=logger)
    dbhandler = PG_DBHandler(logger=logger)
    
    # initialize query loop.
    while True:
        original_query = input("Enter the query to the Gov News or type 'q' for exit:")
        logger.info(f"User Query stored in state: {original_query}")
        if original_query.lower() == "q":
            break
        
        # parse the user query.
        parsed_query = await agent.parse_query(original_query=original_query)
        
        # scenriario: "scrape", "search", "summarize"

        # Scrape all relevant news based on parsed_query.
        if parsed_query.start_date is not None and "scrape" in parsed_query.actions:
            async for news_batch in scraper.scrape_by_duration(parsed_query):
                # 拿到一天的資料，立刻寫入資料庫
                for item in news_batch:
                    dbhandler.upsert_news(item=item)
                logger.info(f"Main Pipeline: Saved {len(news_batch)} items to DB.")

        # Search and retrieve the scraped news for data extraction.
        if "search" in parsed_query.actions:
            search_results = dbhandler.query_full_text_search(parsed_query=parsed_query)
            export_to_excel = input("Do you want to export the search results to Excel? (y/n): ")
            if export_to_excel.lower() == 'y':
                dbhandler.export_to_excel(search_results=search_results, parsed_query=parsed_query)
                logger.info("Main Pipeline: Exported search results to Excel.")
                
        # Summarize the retrieved news articles.
        if "summarize" in parsed_query.actions:
            if search_results:
                logger.info(f"Main Pipeline: Retrieved {len(search_results)} items from DB for data extraction.")
                # Generate summary in markdown format.
                summary = await agent.generate_summary(search_results=search_results, parsed_query=parsed_query)
            else:
                logger.info("Main Pipeline: No relevant articles found in DB for the given query.")
        
    return

if __name__ == "__main__":
    asyncio.run(main())
