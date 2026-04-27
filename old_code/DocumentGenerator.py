from langchain_core.documents import Document
from crawl4ai import CrawlResult
from langchain_text_splitters import RecursiveCharacterTextSplitter

from tools.DataProcessor import date_to_unix, transform_text_to_time
from tools.logger import Logger
from typing import List

from pprint import pformat

class DocumentGenerator:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=0,
            separators=["\n\n", "\n", " ", ""]
            )
        self.logger.info("DocumentGenerator initialized with RecursiveCharacterTextSplitter.")
    
    
    def _split_text(self, content: str) -> List[str]:
        all_chunks = self.text_splitter.split_text(content)
        self.logger.info(f"Split content into {len(all_chunks)} chunks.")
        
        for i, split in enumerate(all_chunks, start=1):
            self.logger.info(f"Chunk {i}: \n{split}")
        self.logger.info("-" * 50)
        
        return all_chunks
    
    
    def generate_documents(self, crawl_results: List[CrawlResult]) -> List[Document]:
        """Generating documents from crawlresults.

        Args:
            crawl_results (List[CrawlResult]): a list of CrawlResults, where each CrawlResult contains the metadata and markdown content of a news item. The metadata includes the title, date, and url of the news item.

        Returns:
            List[Document]: List of Documents, where each Document corresponds to a chunk of a news item, and contains the metadata (news_id, title, published_date, published_time, url, chunk_index, total_chunks) and the page_content (the text content of the chunk).
        """
        
        documents = []
        for result in crawl_results:
            # get the information from result.
            url = result.url
            content = result.markdown
            news_id = url.split("/")[-1].split(".")[0]  # Extract news_id from URL
            title = result.metadata["title"]
            date_str = content.split("\n")[-4].split(", ", 1)[-1].strip()  # Extract date string from markdown
            # time_str = content.split("\n")[-3].split(" ")[-2].strip()  # Extract time string from markdown
            chunks = self._split_text(content=content)
            
            self.logger.info(f"Processing news item: {title}")
            
            # prepare metadata and create Document objects for each chunk.
            for i, chunk in enumerate(chunks):
                doc = Document(
                    id=f"{news_id}#chunk={i}",
                    page_content=chunk,
                    metadata={
                        "news_id": news_id,
                        "title": title,
                        "published_date": date_to_unix(date_str),
                        "url": url,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                )
                self.logger.info(f"Created Document for chunk {i} of news item - {title}")
                self.logger.info(f"Metadata for chunk {i}: \n%s", pformat(doc.metadata, indent=4))
                self.logger.info(f"Chunk content: {chunk}")
                self.logger.info("-" * 50)
                documents.append(doc)
        
        self.logger.info(f"Document generation completed. Total documents created: {len(documents)}")
        
        return documents
        
    
    