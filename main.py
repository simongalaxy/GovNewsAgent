from tools.logger import Logger
from tools.States import State
from tools.NewsCrawler import NewsCrawler
from tools.QueryParser import QueryParser
from tools.DataProcessor import DataProcessor
from tools.PGVectorNewsStore import PGVectorNewsStore


from pprint import pformat

# main entry point.
def main():
    
    # initialize logger and crawler
    logger = Logger(__name__).get_logger()
    state = State()
    parser = QueryParser(logger=logger)
    crawler = NewsCrawler(logger=logger)
    processor = DataProcessor(logger=logger)
    db_handler = PGVectorNewsStore(logger=logger)
    
    while True:
        user_query = input("Enter the query to the Gov News or type 'q' for exit:")
        logger.info(f"User Query: {user_query}")
        if user_query.lower() == "q":
            break
        
        # parse the user query.
        parser.parse_query(query=user_query, state=state)

        # crawl all relevant news based on parsed_query.
        crawler.fetch_news_by_dates(state=state)
    
        # extract data from each news result items and then save data to pgvector.
        state.news_items = [processor.get_info_from_result(result=result) for result in state.news_page_results]
        
        # save news items to pgvector.
        for news_item in state.news_items:
            db_handler.upsert_news(item=news_item)
            
        # # query to pgvector.
        # query_results = db_handler.hybrid_search(parsed_query=parsed_query)
        
        # # show the query results:
        # for i, result in enumerate(query_results, start=1):
        #     logger.info(f"Record No. {i}: \n%s", pformat(result, indent=4))
        
        # summary = summary_generator.summarize_content(
        #     query=query, 
        #     contents=query_results
        # )
        # write_report(markdown=summary)
    
    return

if __name__ == "__main__":
    main()
