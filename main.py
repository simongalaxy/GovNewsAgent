from tools.NewsCrawler import NewsCrawler
from tools.logger import Logger
from tools.DocumentGenerator import DocumentGenerator
from tools.ChromaDBHandler import ChromaDBHandler


def main():
    
    # initialize logger and crawler
    logger = Logger(__name__).get_logger()
    crawler = NewsCrawler(logger=logger)
    document_generator = DocumentGenerator(logger=logger)
    db_handler = ChromaDBHandler(logger=logger)
    
    startDate = "20260331"
    endDate = "20260404"
    
    results = crawler.fetch_news_by_dates(startDate=startDate, endDate=endDate)
    logger.info(f"Crawling completed. Total news items retrieved: {len(results)}")
    for idx, result in enumerate(results, start=1):
        logger.info(f"News Item {idx}: \n title: {result.metadata["title"]} \n content: {result.markdown}")    

    documents = document_generator._generate_documents(crawl_results=results)
    logger.info(f"Document generation completed. Total documents created: {len(documents)}")
    
    db_handler.add_documents(documents=documents)
    
    query_results = db_handler.hybrid_search(query="What are the key points of the news items published between April 3, 2026 and April 4, 2026?")
    logger.info(f"Query results retrieved: {len(query_results)}")
    for idx, doc in enumerate(query_results, start=1):
        logger.info(f"Query Result {idx}: \n id: {doc.id} \n content: {doc.page_content} \n metadata: {doc.metadata}")
    
    
if __name__ == "__main__":
    main()
