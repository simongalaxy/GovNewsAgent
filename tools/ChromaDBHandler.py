from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

from tools.logger import Logger 

import os
from typing import Optional, List
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
        Add documents to Chroma and prepare BM25 retriever for hybrid search.
        """
        for i, doc in enumerate(documents, start=1):
            self.vectorstore.add_documents([doc])
            self.logger.info(f"added document {i}/{len(documents)} with id: {doc.id} and title: {doc.metadata['title']}")    
        
        # create BM25 retriever and ensemble retriever after adding documents.
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        
        # create ensemble retriever with equal weights for both retrievers.
        self.ensemble_retriever = EnsembleRetriever(retrievers=[self.retriever, self.bm25_retriever], weights=[0.5, 0.5])
           
        return
    
    
    def hybrid_search(self, query: str) -> List[Document]:
        """
        Perform hybrid search (Ollama vector + BM25) and return relevant documents.
        """
        if not self.ensemble_retriever:
            self.logger.warning("Ensemble retriever not initialized. Please add documents before performing hybrid search.")
        
        return self.ensemble_retriever.invoke(query)
