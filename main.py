import asyncio

from tools.logger import Logger
from tools.States import State
from tools.NewsFetcher import NewsFetcher
from tools.QueryParser import QueryParser
from tools.ContentEmbedder import ContentEmbedder
# from tools.PGVectorNewsStore import PGVectorNewsStore


from pprint import pformat

# main entry point.
def main():
    
    # initialize logger and crawler
    logger = Logger(__name__).get_logger()
    state = State()
    parser = QueryParser(logger=logger)
    fetcher = NewsFetcher(logger=logger)
    embedder = ContentEmbedder(logger=logger)
    # db_handler = PGVectorNewsStore(logger=logger)
    
    while True:
        user_query = input("Enter the query to the Gov News or type 'q' for exit:")
        logger.info(f"User Query: {user_query}")
        if user_query.lower() == "q":
            break
        
        # parse the user query.
        state.oringinal_query = user_query
        logger.info(f"Original query stored in state: {state.oringinal_query}")
        
        state.parsed_query = parser.parse_query(query=user_query)
        
        # crawl all relevant news based on parsed_query.
        fetcher.fetch_news_by_dates(state=state)
    
        # # generate embedding and then save news items to pgvector.
        for item in state.news_items:
            embedder.embed_text(item=item)
            # db_handler.upsert_news(item=news_item)
            
        # # query to pgvector.
        # query_results = db_handler.hybrid_search(parsed_query=state.parsed_query)
        
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
