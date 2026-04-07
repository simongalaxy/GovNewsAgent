import psycopg
from psycopg.rows import dict_row
from typing import List, Tuple
import numpy as np

import os
from dotenv import load_dotenv
from sympy import content
load_dotenv()

from tools.logger import Logger


class PGVectorNewsStore:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.username = os.getenv("username")
        self.password = os.getenv("password")
        self.host = os.getenv("host")
        self.port = os.getenv("port")
        self.db_name = os.getenv("db_name")
        self.conn_str = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        self.embedding_dim = 1536
        

        with psycopg.connect(self.conn_str) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id SERIAL PRIMARY KEY,
                    news_id TEXT UNIQUE,
                    published_date DATE,
                    title TEXT,
                    content TEXT,
                    url TEXT,
                    embedding VECTOR(%s),
                    tsv TSVECTOR
                );
            """, (self.embedding_dim,))

            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_tsv ON news USING GIN(tsv);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_embedding ON news USING ivfflat (embedding vector_l2_ops);")
            conn.commit()

    # ---------------------------------------------------------
    # Insert or update a news article
    # ---------------------------------------------------------
    def upsert_news(
        self,
        news_id: str,
        published_date: str,
        title: str,
        content: str,
        url: str,
        embedding: List[float]
    ):
        
        """Insert a news article into the database, or update it if it already exists."""
        
        with psycopg.connect(self.conn_str) as conn:
            conn.execute("""
                INSERT INTO news (news_id, published_date, title, content, url, embedding, tsv)
                VALUES (%s, %s, %s, %s, %s, %s, to_tsvector('english', %s))
                ON CONFLICT (news_id)
                DO UPDATE SET
                    published_date = EXCLUDED.published_date,
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    url = EXCLUDED.url,
                    embedding = EXCLUDED.embedding,
                    tsv = EXCLUDED.tsv;
            """, (news_id, published_date, title, content, url, embedding, content))
            conn.commit()

    # ---------------------------------------------------------
    # Hybrid search: keyword + semantic + date filter
    # ---------------------------------------------------------
    def hybrid_search(
        self,
        query_text: str,
        query_embedding: List[float],
        start_date: str,
        end_date: str,
        limit: int = 30
    ) -> List[dict]:

        """Perform a hybrid search combining keyword relevance, vector similarity, and date filtering."""
        
        with psycopg.connect(self.conn_str, row_factory=dict_row) as conn:
            rows = conn.execute("""
                SELECT
                    id,
                    news_id,
                    published_date,
                    title,
                    content,
                    url,
                    -- BM25-like score
                    ts_rank(tsv, plainto_tsquery('english', %s)) AS keyword_score,
                    -- Vector similarity (smaller distance = better)
                    (embedding <-> %s) AS vector_distance,
                    -- Hybrid score (higher = better)
                    (
                        0.4 * ts_rank(tsv, plainto_tsquery('english', %s)) +
                        0.6 * (1 - (embedding <-> %s))
                    ) AS hybrid_score
                FROM News
                WHERE published_date BETWEEN %s AND %s
                ORDER BY hybrid_score DESC
                LIMIT %s;
            """, (
                query_text,
                query_embedding,
                query_text,
                query_embedding,
                start_date,
                end_date,
                limit
            )).fetchall()

            return rows
