import asyncio

from tools.logger import Logger
from tools.States import State
from tools.NewsFetcher import NewsFetcher
from tools.QueryParser import QueryParser
from tools.ContentEmbedder import ContentEmbedder
from tools.PGVectorNewsStore import PGVectorNewsStore
from tools.ReportGenerator import ReportGenerator


from pprint import pformat

# main entry point.
def main():
    
    # initialize logger and crawler
    logger = Logger(__name__).get_logger()
    state = State()
    parser = QueryParser(logger=logger)
    fetcher = NewsFetcher(logger=logger)
    embedder = ContentEmbedder(logger=logger)
    db_handler = PGVectorNewsStore(logger=logger)
    generator = ReportGenerator(logger=logger)
    
    while True:
        user_query = input("Enter the query to the Gov News or type 'q' for exit:")
        logger.info(f"User Query: {user_query}")
        if user_query.lower() == "q":
            break
        
        # save the original query and its embeddings into state.
        state.original_query = user_query
        logger.info(f"Original query stored in state: {state.original_query}")
        state.query_embeddings = embedder.embed_query_text(query=user_query)
        
        # parse the user query.
        state.parsed_query = parser.parse_query(query=user_query)
        
        # crawl all relevant news based on parsed_query.
        fetcher.fetch_news_by_dates(state=state)
    
        # generate embedding and then save news items to pgvector.
        for item in state.news_items:
            embedder.embed_news(item=item)
            db_handler.upsert_news(item=item)
            
        # query to pgvector.
        state.query_results = db_handler.search_news(state=state)
        
        # show the query results:
        # for i, result in enumerate(state.query_results, start=1):
        #     logger.info(f"Record No. {i}: \n%s", pformat(result, indent=4))
        
        generator.generate_report(state=state)

        # log all records in state.
        logger.info("#"*50)
        logger.info(f"State Summary:")
        logger.info("Original Query: \n%s", state.original_query)
        logger.info("Parsed Query: \n%s", pformat(state.parsed_query.model_dump(by_alias=True), indent=4))
        logger.info(f"No. of News items: {len(state.news_items)}")
        logger.info(f"No. of Query results: {len(state.query_results)}")
        logger.info("Report Generated: \n%s", state.markdown)
        logger.info("#"*50)
        
    return

if __name__ == "__main__":
    main()
