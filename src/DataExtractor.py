import os
import json
import asyncio
import instructor
from openai import AsyncOpenAI
# from openai import OpenAI
from pprint import pformat


from src.logger import Logger
from src.Settings import settings
from src.States import State, NewsItem


class DataExtractor:
    def __init__(self, logger: Logger):
        # logger setting.
        self.logger = logger
        
        # Explicitly declare the remote host address
        self.model_name = settings.ollama_cloud_model
        self.base_url = settings.ollama_base_url
        self.api_key = settings.ollama_api_key
        self.client = instructor.from_openai(
            AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            ),
            mode=instructor.Mode.JSON_SCHEMA,  # Forces JSON extraction compatible with Ollama
        )


    async def _extract_data(self, item: dict):
        combined_content = f"Title: {item.get("title")}\nContent:\n{item.get("content")}"
        self.logger.info(f"Content to be extracted: \n%s", combined_content)
        
        resp = await self.client.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": f"Extract the information from the content: \n{combined_content}",
                }
            ],
            response_model=NewsItem,
        )

        metadata = resp.model_dump_json(indent=2)
        self.logger.info(f"News item: \n%s", pformat(metadata, indent=2))

        return metadata
    
        
    async def extract_data_from_all_news(self, state: State):
        
        self.logger.info(f"Start extracting data from press releases.")
        
        semaphore = asyncio.Semaphore(4) # Tune this (3~6) based on your GPU/RAM
        
        async def bounded_extract(item: dict):
            async with semaphore:
                return await self._extract_data(item=item)

        tasks = [bounded_extract(item=item) for item in state.retrieved_items]
        news_infos = await asyncio.gather(*tasks, return_exceptions=True)

        # Remove any exceptions
        successful = [j for j in news_infos if not isinstance(j, Exception)]
        self.logger.info(f"Extraction completed. {len(successful)}/{len(state.retrieved_items)} press release succeeded.")
        
        if successful:
            self.logger.info(f"Sample Extracted Item: \n%s", successful[0])
        
        return successful
        

#   def generate_summary(self, news_list: List[News]):

#     # 1. 準備摘要內容：初始化字串
#     content = "Contents:\n\n"

#     # 2. 遍歷新聞列表，先將所有內容完整組合（注意：三引號內不要額外加 \n）
#     for news in news_list:
#         meta_dict = json.loads(news.metadata)
#         content += f"""Date: {meta_dict.get('published_date_time')}
#                       Title: {meta_dict.get('title')}
#                       Department: {meta_dict.get('subject_department')}
#                       Summary: {",".join(meta_dict.get('summary'))}

#                       """

#     # 3. 檢查組合後的內容（移到迴圈外，只印出一次）
#     print(f"Combined Content for LLM summarization: \n{content}\n\n")

#     resp = self.client.create(
#         model=self.model,
#         messages=[
#             {
#                 "role": "user",
#                 "content": f"Summarize the following content not less than 800 words by departments in chronological order: \n{content}",
#             }
#         ],
#         response_model=Summary,
#     )

#     print(f"Summary: \n{resp.model_dump_json(indent=2)}")
#     return