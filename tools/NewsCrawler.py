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
        urls = generate_date_urls(startDate=startDate, endDate=endDate, logger=self.logger)
    
        # crawl page links of press release.
        results = asyncio.run(self._crawl_pages(urls=urls, config=self.crawl_config_datePage))
        
        news_links = consolidate_news_urls(results=results, logger=self.logger)
        
        # get the data dictionaries from press releases and save results to chromadb.
        results = asyncio.run(self._crawl_pages(urls=news_links, config=self.crawl_config_newsPage))
        
        return results
    
    