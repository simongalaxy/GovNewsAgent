from pprint import pformat

import aiohttp
import asyncio
from bs4 import BeautifulSoup
import markdown
from typing import List, Any
from datetime import datetime, timedelta

from tools.logger import Logger
from tools.States import State, NewsItem


class NewsFetcher:
    def __init__(self, logger):
        self.logger = logger
        self.base_url = "http://www.info.gov.hk"
    
    
    # function to generate links based on the date range.
    def _generate_date_urls(self, startDate: str, endDate: str) -> list[str]:
        # transform the dates from string to datetime format.
        start_date = datetime.strptime(startDate, "%Y-%m-%d")
        if endDate == "":
            end_date = start_date
        else:
            end_date = datetime.strptime(endDate, "%Y-%m-%d")
        self.logger.info(f"Start date: {start_date}, End Date: {end_date}")
        
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)
        
        self.logger.info(f"Generated date range from {startDate} to {endDate}: {dates}")
        
        urls = [f"{self.base_url}/gia/general/{date[:-2]}/{date[-2:]}.htm" for date in dates]
        self.logger.info(f"Generated {len(urls)} date URLs:")
        
        for i, url in enumerate(urls, start=1):
            self.logger.info(f"No. {i}: {url}")
        self.logger.info("-"*50)
        
        return urls
    
    
    # functions to parse links and content from poges.
    def _parse_links(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        content = soup.find('div', class_='leftBody')
        urls = [f"{self.base_url}{a['href']}" for a in content.find_all('a', href=True)]
        self.logger.info(f"Parsed {len(urls)} news URLs from date page.")
        for i, url in enumerate(urls, start=1):
            self.logger.info(f"No. {i} - data type: {type(url)}: {url}")
        self.logger.info("-"*50)
        
        return urls


    # convert date to postgres date format.
    def _convert_to_postgres_date(self, date_str: str) -> str:
        # Parse the natural-language date
        dt = datetime.strptime(date_str, "%B %d, %Y")
        # Format into PostgreSQL date format
        return dt.strftime("%Y-%m-%d")


    # function to parse the news page and extract the content, title, date, url and news_id.
    def _parse_news(self, html: str, url: str) -> NewsItem:
        soup = BeautifulSoup(html, 'html.parser')

        news_id = url.split("/")[-1].split(".")[0]
        date = soup.find('div', class_='mB15 f15').get_text().split("\n")[0].split(", ", 1)[-1].strip()
        published_date = self._convert_to_postgres_date(date_str=date)
        title = soup.find('span', id='PRHeadlineSpan').get_text(strip=True)
        content = markdown.markdown(soup.find('span', id='pressrelease').get_text(strip=True))
        
        item = NewsItem(
            news_id=news_id,
            published_date=published_date,
            title=title,
            content=content,
            url=str(url)
        )
        self.logger.info("Fetched news item: \n%s", pformat(item.model_dump(), indent=4))
        
        return item

    
    # fetch date pages.
    async def _fetch_date_page(self, url: str) -> List[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        html = await response.text()
                        return self._parse_links(html=html)
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return []    
    
    
    # fetch news pages.
    async def _fetch_news_page(self, url: str) -> NewsItem:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                item = self._parse_news(html=html, url=url)
        
        return item
    
    
    async def _fetch_all_pages(self, urls: List[str], fetch_function) -> List[Any]:
        tasks = [fetch_function(url) for url in urls]
        return await asyncio.gather(*tasks)
        
        
    # main function to fetch news based on the date range.
    def fetch_news_by_dates(self, state: State) -> None:
        
        # Generate the urls by date range.
        urls = self._generate_date_urls(
            startDate=state.parsed_query.start_date, 
            endDate=state.parsed_query.end_date
        )
        
        # fetch news URLs from each date page asynchronously.
        news_urls = asyncio.run(self._fetch_all_pages(urls=urls, fetch_function=self._fetch_date_page))
        self.logger.info(f"Total {len(news_urls)} news URLs fetched from date pages.")
        
        for i, url in enumerate(news_urls, start=1):
            self.logger.info(f"No. {i} - data type: {type(url)}: {url}")
        self.logger.info("-"*50)
        
        # fetch news items from each news page asynchronously.
        all_items = []
        for i, urls in enumerate(news_urls, start=1):
            if len(urls) > 0:
                self.logger.info(f"Fetching news page {i}/{len(news_urls)}: {url}")
                news_items = asyncio.run(self._fetch_all_pages(urls=urls, fetch_function=self._fetch_news_page))
                all_items.extend(news_items)

        self.logger.info(f"Total {len(all_items)} news items were fetched from {len(urls)} date pages.")
        state.news_items = all_items
        
        return