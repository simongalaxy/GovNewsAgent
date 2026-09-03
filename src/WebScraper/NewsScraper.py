import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from typing import List, Any, AsyncGenerator
from datetime import datetime, timedelta
from pprint import pformat

from src.Util.logger import Logger
from src.Data.DataClasses import NewsItem, ParsedQuery


class NewsScraper:
    def __init__(self, logger):
        self.logger = logger
        self.base_url = "https://www.info.gov.hk"  # 💡 建議改為 https 避免被 redirect
        self.dates = []
        self.date_urls = []
        self.total_news_pages = 0
    
    # 產生日期連結
    def _generate_date_urls(self, parsed_query: ParsedQuery) -> None:
        # Pydantic 物件如果本來就是 datetime/date 型態則不需 strptime，這裡假設傳入的是字串
        start_date = datetime.strptime(str(parsed_query.start_date), "%Y-%m-%d")
        if not parsed_query.end_date:
            end_date = start_date
        else:
            end_date = datetime.strptime(str(parsed_query.end_date), "%Y-%m-%d")
            
        self.logger.info(f"Start date: {start_date.date()}, End Date: {end_date.date()}")
        
        self.dates = []
        current = start_date
        while current <= end_date:
            self.dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)
            
        # 建立格式如: https://info.gov.hk/gia/general/202512/01.htm
        self.date_urls = [f"{self.base_url}/gia/general/{date[:-2]}/{date[-2:]}.htm" for date in self.dates]
        self.logger.info(f"Generated {len(self.date_urls)} date URLs.")

    # 解析日期頁面中的新聞連結
    def _parse_links(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        content = soup.find('div', class_='leftBody')
        
        # 💡 安全檢查：如果這天沒有任何新聞稿，content 會是 None
        if not content:
            return []
            
        urls = [f"{self.base_url}{a['href']}" for a in content.find_all('a', href=True) if '/gia/general/' in a['href']]
        return urls

    # 將英文日期轉換成 Postgres 格式
    def _convert_to_postgres_date(self, date_str: str) -> str:
        try:
            # 範例："December 31, 2025"
            dt = datetime.strptime(date_str.strip(), "%B %d, %Y")
            return dt.strftime("%Y-%m-%d")
        except Exception as e:
            self.logger.error(f"Failed to parse date string '{date_str}': {e}")
            return datetime.now().strftime("%Y-%m-%d") # 降級處理

    # 解析單篇新聞稿內文
    def _parse_news(self, html: str, url: str) -> NewsItem:
        soup = BeautifulSoup(html, 'html.parser')

        news_id = url.split("/")[-1].split(".")[0]
        
        # 💡 強健的日期選取邏輯
        date_element = soup.find('div', class_='mB15 f15')
        if date_element:
            # 處理可能包含 "Issued at HKT..." 的複雜字串，只拿前半段日期
            raw_date = date_element.get_text().split("\n")[0].split(" (")[0].strip()
            if "," in raw_date:
                # 排除星期幾，只拿 "December 31, 2025"
                date_str = raw_date.split(", ", 1)[-1].strip()
            else:
                date_str = raw_date
            published_date = self._convert_to_postgres_date(date_str=date_str)
        else:
            published_date = datetime.now().strftime("%Y-%m-%d")

        # 💡 安全選取 Title
        title_element = soup.find('span', id='PRHeadlineSpan')
        title = title_element.get_text(strip=True) if title_element else "No Title"
        
        # 💡 安全選取 Content
        content_element = soup.find('span', id='pressrelease')
        content = content_element.get_text(strip=True).replace("\u200b", "") if content_element else ""
        
        return NewsItem(
            id=news_id,
            published_date=published_date,
            title=title,
            content=content,
            url=str(url)
        )

    # 非同步抓取日期頁面 (共用 session)
    async def _fetch_date_page(self, session: aiohttp.ClientSession, url: str) -> List[str]:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch date page {url}: Status {response.status}")
                    return []
                html = await response.text()
                return self._parse_links(html=html)
        except Exception as e:
            self.logger.error(f"Error fetching date page {url}: {e}")
            return []

    # 非同步抓取新聞內文頁面 (共用 session)
    async def _fetch_news_page(self, session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore) -> Any:
        async with semaphore:  # 💡 限制最大並行數，防止被政府網站封鎖
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
                    return self._parse_news(html=html, url=url)
            except Exception as e:
                self.logger.error(f"Error fetching news page {url}: {e}")
                return None

    # 🚀 終極優化：主爬蟲管線方法 (改為非同步 Generator 模式)
    async def scrape_by_duration(self, parsed_query: ParsedQuery) -> AsyncGenerator[List[NewsItem], None]:
        """
        根據時間區間爬取新聞稿，每次爬完『一天』的新聞就立刻 yield 回傳給外層（main.py）寫入資料庫。
        """
        self._generate_date_urls(parsed_query=parsed_query)
        
        # 設定並行限制，保護網頁不崩潰
        semaphore = asyncio.Semaphore(5) 
        
        # 💡 建立全域唯一的 ClientSession
        async with aiohttp.ClientSession() as session:
            
            # 遍歷每一個日期網頁
            for date_str, date_url in zip(self.dates, self.date_urls):
                self.logger.info(f"Processing date: {date_str} -> {date_url}")
                
                # 1. 抓取這天的所有新聞超連結
                news_urls = await self._fetch_date_page(session, date_url)
                if not news_urls:
                    self.logger.info(f"No news releases found on {date_str}.")
                    continue
                
                self.logger.info(f"Found {len(news_urls)} news pages on {date_str}. Fetching contents...")
                
                # 2. 並行抓取這天內的所有新聞內文
                tasks = [self._fetch_news_page(session, url, semaphore) for url in news_urls]
                raw_results = await asyncio.gather(*tasks)
                
                # 過濾失敗的項目
                day_news_items = [item for item in raw_results if isinstance(item, NewsItem)]
                
                self.total_news_pages += len(day_news_items)
                self.logger.info(f"Successfully scraped {len(day_news_items)} items for date {date_str}.")
                
                # 3. 💡 關鍵：立刻回傳這一批數據給外層，記憶體隨即釋放
                yield day_news_items

        self.logger.info(f"All done! Total {self.total_news_pages} news items processed.")
