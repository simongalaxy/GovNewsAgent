from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig, MemoryAdaptiveDispatcher, CrawlResult
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

from tools.DataProcessor import generate_date_urls, consolidate_news_urls
from tools.logger import Logger

from pprint import pformat
import asyncio, json, re, os
from typing import List

   
class NewsCrawler:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.browser_config = BrowserConfig(
            headless=True,
            text_mode=True,
            light_mode=True
        )
        self.dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=75,
            check_interval=1,
            max_session_permit=3
        )
        self.crawl_config_datePage = CrawlerRunConfig(
            scraping_strategy=LXMLWebScrapingStrategy(),
            exclude_all_images=True,
            exclude_external_links=True,
            exclude_social_media_domains=True,
            target_elements=['div[class="leftBody"]'],
            cache_mode=CacheMode.BYPASS
        )
        self.crawl_config_newsPage = CrawlerRunConfig(
            scraping_strategy=LXMLWebScrapingStrategy(),
            exclude_all_images=True,
            exclude_external_links=True,
            exclude_social_media_domains=True,
            target_elements=['span[id="pressrelease"]'],
            cache_mode=CacheMode.BYPASS,
        )


    # crawling functions.
    async def _crawl_pages(self, urls: list[str], config: CrawlerRunConfig) -> List[CrawlResult]:
        async with AsyncWebCrawler(
            config=self.browser_config,
            max_concurrency=3, 
            headless=True, 
            disable_images=True, 
            disable_css=True, 
            disable_scripts=True, 
            disable_pdf=True, 
            disable_video=True, 
            disable_audio=True, 
            extraction_mode="light"
            ) as crawler:
            
            results = await crawler.arun_many(
                urls=urls,
                config=config,
                dispatcher=self.dispatcher
            )
    
        return results
 

    def fetch_news_by_dates(self, startDate: str, endDate: str) -> List[CrawlResult]:
        """To fetch news items from the government press release website by specified date range, and return the crawl results as a list of CrawlResult objects.

        Args:
            startDate (str): in the format of "YYYYMMDD", e.g. "20260405"
            endDate (str):  in the format of "YYYYMMDD", e.g. "20260405"

        Returns:
            List[CrawlResult]: in the format of a list of CrawlResult objects, where each object contains the metadata and markdown content of a news item. The metadata includes the title, date, and url of the news item.
        """
        
        urls = generate_date_urls(startDate=startDate, endDate=endDate, logger=self.logger)
    
        # crawl page links of press release.
        results = asyncio.run(self._crawl_pages(urls=urls, config=self.crawl_config_datePage))
        
        news_links = consolidate_news_urls(results=results, logger=self.logger)
        
        # get the data dictionaries from press releases and save results to chromadb.
        results = asyncio.run(self._crawl_pages(urls=news_links, config=self.crawl_config_newsPage))
        
        # log the crawling results for debugging and verification.
        self.logger.info(f"Crawling completed. Total news items retrieved: {len(results)}")
        for idx, result in enumerate(results, start=1):
            self.logger.info(f"News Item {idx}:")
            self.logger.info(f"Title: {result.metadata["title"]}") 
            self.logger.info(f"Content: \n%s", result.markdown)
            self.logger.info("-" * 50)
        
        return results
    
    