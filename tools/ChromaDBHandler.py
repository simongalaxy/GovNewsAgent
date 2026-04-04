from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_classic.retrievers import EnsembleRetriever, BM25Retriever

from tools.logger import Logger 

import os
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
        self.keyword_retriever = BM25Retriever()
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.retriever, self.keyword_retriever], 
            weights=[0.5, 0.5]
            )
        
        
        self.logger.info("ChromaDBHandler initialized with OllamaEmbeddings and Chroma vectorstore.")
        
    
    def add_documents(self, documents: list[Document]) -> None:
        count = 0
        for i, doc in enumerate(documents):
            # existing_docs = self.vectorstore.get(where={"news_id": doc.metadata["news_id"]})
            # self.logger.info(f"Checking for existing documents with news_id: {doc.metadata['news_id']}. Found {len(existing_docs)} existing documents.")
            # if not existing_docs[]:
            self.vectorstore.add_documents([doc])
            count += 1
            self.logger.info(f"Added Document with id: {doc.id} to ChromaDB.")
        
        self.logger.info(f"Total new documents added to ChromaDB: {count}")
        
        return
    
    
    def query_hybrid_search(self, query: str, top_k: int = 20) -> list[Document]:
        self.logger.info(f"Performing hybrid search for query: '{query}' with top_k={top_k}")
        results = self.ensemble_retriever.get_relevant_documents(query, top_k=top_k)
        self.logger.info(f"Hybrid search retrieved {len(results)} documents.")
        
        return results
