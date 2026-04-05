from tools.NewsCrawler import NewsCrawler
from tools.logger import Logger
from tools.DocumentGenerator import DocumentGenerator
from tools.ChromaDBHandler import ChromaDBHandler
from tools.SummaryGenerator import SummaryGenerator

from pprint import pformat

def main():
    
    # initialize logger and crawler
    logger = Logger(__name__).get_logger()
    crawler = NewsCrawler(logger=logger)
    document_generator = DocumentGenerator(logger=logger)
    db_handler = ChromaDBHandler(logger=logger)
    summary_generator = SummaryGenerator(logger=logger)
    
    # startDate = "20260405"
    # endDate = "20260405"
    
    # results = crawler.fetch_news_by_dates(startDate=startDate, endDate=endDate)
    
    # documents = document_generator.generate_documents(crawl_results=results)
    
    # db_handler.add_documents(documents=documents)
    query="News relating to Center for Food Safety on 31 March, 2026"
    
    query_results = db_handler.hybrid_search(query=query)
    
    summary = summary_generator.summarize_content(
        query=query, 
        query_results=query_results
    )


if __name__ == "__main__":
    main()
