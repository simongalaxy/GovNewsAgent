from tools.logger import Logger
from tools.NewsCrawler import NewsCrawler
from tools.DataProcessor import DataProcessor
from tools.PGVectorNewsStore import PGVectorNewsStore
from tools.SummaryGenerator import SummaryGenerator
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
    summary_generator = SummaryGenerator(logger=logger)
    parser = QueryParser(logger=logger)
    
    while True:
        user_query = input("Enter the query to the Gov News or type 'q' for exit:")
        logger.info(f"User Query: {user_query}")
        if user_query.lower() == "q":
            break
        
        # parse the user query.
        parsed_query = parser.parse_query(query=user_query)

        # crawl all relevant news based on parsed_query.
        results = crawler.fetch_news_by_dates(startDate=startDate, endDate=endDate)
    
    # # extract data from each news result items and then save data to pgvector.
    # for result in results:
    #     newsItem = processor.get_info_from_result(result=result)
    #     db_handler.upsert_news(
    #         news_id=newsItem["news_id"],
    #         published_date=newsItem["published_date"],
    #         title=newsItem["title"],
    #         content=newsItem["content"],
    #         url=newsItem["url"],
    #         embedding=newsItem["embeddings"]
    #     )
    
    # query to pgvector.
    # query="all the news on  30 March 2026"
    # query_results = db_handler.hybrid_search(query=query)
    
    # summary = summary_generator.summarize_content(
    #     query=query, 
    #     contents=query_results
    # )
    # write_report(markdown=summary)
    
    return

if __name__ == "__main__":
    main()
