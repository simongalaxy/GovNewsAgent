from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig, MemoryAdaptiveDispatcher, CrawlResult
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

from datetime import datetime, timedelta
from pprint import pformat
import asyncio, re
from typing import List

from tools.logger import Logger
from tools.States import State

class NewsCrawler:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.browser_config = BrowserConfig(
            headless=True,
            text_mode=True,
            light_mode=True
        )
        self.dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=70,
            check_interval=1,
            max_session_permit=4
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

    
    # data processing functions.
    def _generate_date_range(self, startDate: str, endDate: str) -> list[str]:
        # transform the dates from string to datetime format.
        start_date = datetime.strptime(startDate, "%d %B %Y")
        if endDate == "":
            end_date = start_date
        else:
            end_date = datetime.strptime(endDate, "%d %B %Y")
        
        self.logger.info(f"Start date: {start_date}, End Date: {end_date}")
        
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)
        
        self.logger.info(f"Generated date range from {startDate} to {endDate}: {dates}")
        
        return dates


    def _generate_date_urls(self, startDate: str, endDate: str) -> list[str]:
        dates = self._generate_date_range(startDate=startDate, endDate=endDate)
        urls = [f"https://www.info.gov.hk/gia/general/{date[:-2]}/{date[-2:]}.htm" for date in dates]
        self.logger.info(f"Generated {len(urls)} date URLs: {urls}")
        
        return urls


    def _consolidate_news_urls(self, results: List[CrawlResult]) -> list[str]:
        news_links = []
        for result in results:
            links = result.links.get("internal", [])
            for link in links:
                if re.search(pattern=r"P.*\.htm", string=link["href"]):
                        news_links.append(link["href"])
        
        self.logger.info(f"Extracted {len(news_links)} news URLs from crawl results.")
        self.logger.info(f"Consolidated news URLs: {news_links}")
        
        return news_links


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
 

    def fetch_news_by_dates(self, state: State) -> None:
        """To fetch news items from the government press release website by specified date range, and return the crawl results as a list of CrawlResult objects.

        Args:
            startDate (str): in the format of "YYYYMMDD", e.g. "20260405"
            endDate (str):  in the format of "YYYYMMDD", e.g. "20260405"

        Returns:
            List[CrawlResult]: in the format of a list of CrawlResult objects, where each object contains the metadata and markdown content of a news item. The metadata includes the title, date, and url of the news item.
        """
        
        urls = self._generate_date_urls(startDate=state.parsed_query.start_date, endDate=state.parsed_query.end_date)
    
        # crawl page links of press release.
        date_page_results = asyncio.run(self._crawl_pages(urls=urls, config=self.crawl_config_datePage))
        
        news_links = self._consolidate_news_urls(results=date_page_results)
        
        # get the data dictionaries from press releases and save results to chromadb.
        state.news_page_results = asyncio.run(self._crawl_pages(urls=news_links, config=self.crawl_config_newsPage))
        
        # log the crawling results for debugging and verification.
        self.logger.info(f"Crawling completed. Total news items retrieved: {len(state.news_page_results)}")
        for idx, result in enumerate(state.news_page_results, start=1):
            self.logger.info(f"News Item {idx}:")
            self.logger.info(f"Title: {result.metadata["title"]}") 
            self.logger.info(f"Content: \n%s", result.markdown)
            self.logger.info("-" * 50)
        
        return
    
    