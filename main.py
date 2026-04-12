from tools.logger import Logger
from tools.NewsCrawler import NewsCrawler
from tools.DataProcessor import DataProcessor
from tools.PGVectorNewsStore import PGVectorNewsStore
from tools.LLMSummarizer import LLMSummarizer
from tools.writeReport import write_report
from tools.QueryParser import QueryParser


from pprint import pformat

# main entry point.
def main():
    
    # initialize logger and crawler
    logger = Logger(__name__).get_logger()
    crawler = NewsCrawler(logger=logger)
    processor = DataProcessor(logger=logger)
    db_handler = PGVectorNewsStore(logger=logger)
    summarizer = LLMSummarizer(logger=logger)
    parser = QueryParser(logger=logger)
    
    while True:
        user_query = input("Enter the query to the Gov News or type 'q' for exit:")
        logger.info(f"User Query: {user_query}")
        if user_query.lower() == "q":
            break
        
        # parse the user query.
        parsed_query = parser.parse_query(query=user_query)

        # crawl all relevant news based on parsed_query.
        results = crawler.fetch_news_by_dates(
            startDate=parsed_query.start_date, 
            endDate=parsed_query.end_date
        )
    
        # extract data from each news result items and then save data to pgvector.
        for result in results:
            newsItem = processor.get_info_from_result(result=result)
            db_handler.upsert_news(item=newsItem)
    
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
