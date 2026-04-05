from asyncio.log import logger

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

from tools.logger import Logger

import os
from typing import Optional, List
from pprint import pformat
from dotenv import load_dotenv
load_dotenv()

class ChromaDBHandler:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.embeddings = OllamaEmbeddings(model=os.getenv("ollama_embedding_model"))
        self.vectorstore = Chroma(
            collection_name=os.getenv("collection_name"), 
            embedding_function=self.embeddings,
            persist_directory=os.getenv("chromadb_path")
        )
        self.retriever = self.vectorstore.as_retriever()
        self.bm25_retriever: Optional[BM25Retriever] = None  # Initialize as None, will be set when documents are added
        self.hybrid_retriever: Optional[EnsembleRetriever] = None  # Initialize as None, will be set when
        
        self.logger.info("ChromaDBHandler initialized with OllamaEmbeddings and Chroma vectorstore.")
        
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the Chroma vectorstore, and create BM25 retriever after adding documents.
        """
        for i, doc in enumerate(documents, start=1):
            self.vectorstore.add_documents([doc])
            self.logger.info(f"added document {i}/{len(documents)} with id: {doc.id} and title: {doc.metadata['title']}")    
        
        return
    
    
    def hybrid_search(self, query: str) -> List[Document]:
        """
        Perform hybrid search (Ollama vector + BM25) and return relevant documents.
        """
        self.logger.info(f"Performing hybrid search for query: {query}")
        
        # create BM25 retriever and ensemble retriever after adding documents.
        all_documents = self.vectorstore.get()
        docs = [Document(page_content=doc, metadata=meta) for doc, meta in zip(all_documents["documents"], all_documents["metadatas"])]
        self.logger.info(f"Total documents retrieved from vectorstore for BM25 retriever: {len(docs)}")
        self.bm25_retriever = BM25Retriever.from_documents(documents=docs)
        
        # create ensemble retriever with equal weights for both retrievers.
        self.ensemble_retriever = EnsembleRetriever(retrievers=[self.retriever, self.bm25_retriever], weights=[0.5, 0.5])
        if not self.ensemble_retriever:
            self.logger.warning("Ensemble retriever not initialized. Please add documents before performing hybrid search.")
        
        query_results = self.ensemble_retriever.invoke(query)
        
        # print out the retrieved results for debugging and verification.
        self.logger.info(f"Query results retrieved: {len(query_results)}")       
        
        # get all the news_id from the query results.
        news_ids = [doc.metadata["news_id"] for doc in query_results]
        self.logger.info(f"News IDs retrieved from query results: {news_ids}")
        
        # get all the documents from the vectorstore and filter out the documents with the retrieved news_ids.
        filtered_docs = self.vectorstore.get(
            include=["documents", "metadatas"],
            where={"news_id": {"$in": news_ids}}
            )
        self.logger.info(f"Total documents retrieved from vectorstore for filtering: {len(filtered_docs['documents'])}")
        self.logger.info(f"filtered_docs: \n%s", pformat(filtered_docs["documents"]))
        
        return filtered_docs["documents"]