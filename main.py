from tools.logger import Logger
from tools.NewsCrawler import NewsCrawler
from tools.DataProcessor import DataProcessor
from tools.PGVectorNewsStore import PGVectorNewsStore
from tools.SummaryGenerator import SummaryGenerator
from tools.writeReport import write_report



from pprint import pformat

def main():
    
    # initialize logger and crawler
    logger = Logger(__name__).get_logger()
    crawler = NewsCrawler(logger=logger)
    processor = DataProcessor(logger=logger)
    db_handler = PGVectorNewsStore(logger=logger)
    summary_generator = SummaryGenerator(logger=logger)
    
    startDate = "20260405"
    endDate = "20260405"
    
    results = crawler.fetch_news_by_dates(startDate=startDate, endDate=endDate)
    
    # extract data from each news result items.
    for result in results:
        info = processor.get_info_from_result(result=result)
    
        
    
    # db_handler.add_documents(documents=documents)
    # query="all the news on 2 April 2026"
    
    # query_results = db_handler.hybrid_search(query=query)
    
    # summary = summary_generator.summarize_content(
    #     query=query, 
    #     contents=query_results
    # )
    # write_report(markdown=summary)

if __name__ == "__main__":
    main()
