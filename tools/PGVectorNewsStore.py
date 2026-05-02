import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from typing import List, Tuple
import numpy as np

import os
from dotenv import load_dotenv
load_dotenv()

from tools.logger import Logger
from tools.States import NewsItem, ParsedQuery


class PGVectorNewsStore:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.username = os.getenv("username")
        self.password = os.getenv("password")
        self.host = os.getenv("host")
        self.port = os.getenv("port")
        self.db_name = os.getenv("db_name")
        self.conn_str = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        self.embedding_dim = 1024
        

        with psycopg.connect(self.conn_str) as conn:
            register_vector(conn)
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS news (
                    id SERIAL PRIMARY KEY,
                    news_id TEXT UNIQUE NOT NULL,
                    published_date DATE,
                    title TEXT,
                    content TEXT,
                    url TEXT,
                    embedding VECTOR({self.embedding_dim}),
                    tsv TSVECTOR
                );
            """) # type: ignore

            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_date ON news (published_date);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_tsv ON news USING GIN(tsv);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_embedding ON news USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);")
            conn.commit()

    # ---------------------------------------------------------
    # Insert or update a news article
    # ---------------------------------------------------------
    def upsert_news(self, item: NewsItem):
        
        """Insert a news article into the database, or update it if it already exists."""
        
        with psycopg.connect(self.conn_str) as conn:
            register_vector(conn)
            conn.execute("""
                INSERT INTO news (news_id, published_date, title, content, url, embedding, tsv)
                VALUES (%s, %s, %s, %s, %s, %s, to_tsvector('english', %s))
                ON CONFLICT (news_id) DO UPDATE SET
                    published_date = EXCLUDED.published_date,
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    url = EXCLUDED.url,
                    embedding = EXCLUDED.embedding,
                    tsv = EXCLUDED.tsv;
            """, (item.news_id, item.published_date, item.title, item.content, item.url, item.embeddings, item.content))
            conn.commit()

    # ---------------------------------------------------------
    # Hybrid search: keyword + semantic + date filter
    # ---------------------------------------------------------
    def hybrid_search(self, parsed_query: ParsedQuery) -> List[dict]:

        """Perform a hybrid search combining keyword relevance, vector similarity, and date filtering."""
        
        sql, params = self._build_news_query(parsed=parsed_query)

        cur.execute(sql, params)
        rows = cur.fetchall()
        
        return rows

    #  Build a dynamic SQL query string based on the values present in ParsedQuery, Returns (sql_string, params_list).
    def _build_news_query(parsed: ParsedQuery) -> tuple[str, list]:
   
        base = """
            SELECT
                id,
                title,
                content,
                published_at,
                departments,
                ts_rank(content_tsv, plainto_tsquery('english', %s)) AS keyword_score,
                (embedding <-> %s) AS vector_distance,
                (
                    0.4 * ts_rank(content_tsv, plainto_tsquery('english', %s)) +
                    0.6 * (1 - (embedding <-> %s))
                ) AS hybrid_score
            FROM news
        """

        where_clauses = []
        params = []

        # --- Keyword search (optional) ---
        if parsed.keywords:
            keyword_query = " & ".join(parsed.keywords)
        else:
            keyword_query = ""  # empty tsquery is allowed

        # Add keyword params for ts_rank and hybrid score
        params.append(keyword_query)  # for ts_rank
        params.append(parsed.embedding)  # semantic vector
        params.append(keyword_query)  # for hybrid score
        params.append(parsed.embedding)  # semantic vector again

        # --- Date range ---
        if parsed.start_date and parsed.end_date:
            where_clauses.append("published_at BETWEEN %s AND %s")
            params.append(parsed.start_date)
            params.append(parsed.end_date)

        # --- Departments filter ---
        if parsed.departments:
            where_clauses.append("departments && %s::text[]")
            params.append(parsed.departments)

        # --- Keywords filter (optional) ---
        if parsed.keywords:
            where_clauses.append("content_tsv @@ plainto_tsquery('english', %s)")
            params.append(keyword_query)

        # --- Assemble WHERE clause ---
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)
        else:
            where_sql = ""

        # --- Final SQL ---
        sql = base + where_sql + " ORDER BY hybrid_score DESC LIMIT 50;"

        return sql, params
