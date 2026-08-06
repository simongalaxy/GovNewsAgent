import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Any
from datetime import datetime, timedelta
from pprint import pformat

from src.logger import Logger
from src.States import State, NewsItem


class NewsScraper:
    def __init__(self, logger):
        self.logger = logger
        self.base_url = "http://www.info.gov.hk"
    
    
    # function to generate links based on the date range.
    # def _generate_date_urls(self, startDate: str, endDate: str) -> list[str]:
    def _generate_date_urls(self, state: State) -> None:
        # transform the dates from string to datetime format.
        start_date = datetime.strptime(state.parsed_query.start_date, "%Y-%m-%d")
        if state.parsed_query.end_date == "":
            end_date = start_date
        else:
            end_date = datetime.strptime(state.parsed_query.end_date, "%Y-%m-%d")
        self.logger.info(f"Start date: {start_date}, End Date: {end_date}")
        
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)
        state.dates = dates
        self.logger.info(f"Generated date range from {state.parsed_query.start_date} to {state.parsed_query.end_date}: {state.dates}")
        
        state.date_urls = [f"{self.base_url}/gia/general/{date[:-2]}/{date[-2:]}.htm" for date in dates]
        self.logger.info(f"Generated {len(state.date_urls)} date URLs:")
        
        for i, url in enumerate(state.date_urls, start=1):
            self.logger.info(f"No. {i}: {url}\n")
        self.logger.info("-"*50)
        
        return
    
    
    # functions to parse links and content from poges.
    def _parse_links(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        content = soup.find('div', class_='leftBody')
        urls = [f"{self.base_url}{a['href']}" for a in content.find_all('a', href=True)]
        self.logger.info(f"Parsed {len(urls)} news URLs from date page.")
        
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

        # get the metadata relating to the news.
        news_id = url.split("/")[-1].split(".")[0]
        date = soup.find('div', class_='mB15 f15').get_text().split("\n")[0].split(", ", 1)[-1].strip()
        published_date = self._convert_to_postgres_date(date_str=date)
        title = soup.find('span', id='PRHeadlineSpan').get_text(strip=True)
        content = soup.find('span', id='pressrelease').get_text(strip=True).replace("<p>", "").replace("</p>", "").replace("\u200b", "")
        
        item = NewsItem(
            id=news_id,
            published_date=published_date,
            title=title,
            content=content,
            url=str(url),
            extracted_data=None
        )
        # self.logger.info("Fetched news item: \n%s", pformat(item.model_dump(by_alias=True), indent=4))
        
        return item

    
    # fetch date pages.
    async def _fetch_date_page(self, url: str) -> List[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                    html = await response.text()
                    return self._parse_links(html=html)

    
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
        # state.date_urls = self._generate_date_urls(
        #     startDate=state.parsed_query.start_date, 
        #     endDate=state.parsed_query.end_date
        # )
        
        self._generate_date_urls(state=state)
        
        # fetch news URLs from each date page asynchronously.
        state.news_urls = asyncio.run(self._fetch_all_pages(urls=state.date_urls, fetch_function=self._fetch_date_page))
        self.logger.info(f"Total {len(state.news_urls)} news URLs fetched from {len(state.date_urls)} date pages.")
        
        # fetch news items from each news page asynchronously.
        all_items = []
        for i, urls in enumerate(state.news_urls, start=1):
            self.logger.info(f"Fetching news page {i}/{len(state.news_urls)}: {urls}")
            news_items = asyncio.run(self._fetch_all_pages(urls=urls, fetch_function=self._fetch_news_page))
            all_items.extend(news_items)
        
        state.news_items = all_items
        self.logger.info(f"Total {len(state.news_items)} news items were fetched and saved to State.")
        self.logger.info(f"Sample news item saved in State: \n%s", pformat(state.news_items[0].model_dump(by_alias=True), indent=4))
        
        return
    
    
