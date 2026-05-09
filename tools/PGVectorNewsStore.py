import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from typing import List, Tuple
import numpy as np

import os
from dotenv import load_dotenv
load_dotenv()

from tools.logger import Logger
from tools.States import NewsItem, ParsedQuery, State


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

    #  Build a dynamic SQL query string based on the values present in ParsedQuery, Returns (sql_string, params_list).
    def _build_news_query(self, state: State) -> tuple[str, list]:

        base = """
            SELECT
                published_date,
                title,
                content
            FROM news
        """
        
        where_clauses = []
        params = []

        # date range
        if state.parsed_query.start_date and state.parsed_query.end_date:
            where_clauses.append("published_date BETWEEN %s AND %s")
            params.append(state.parsed_query.start_date)
            params.append(state.parsed_query.end_date)
        elif state.parsed_query.start_date:
            where_clauses.append("published_date = %s")
            params.append(state.parsed_query.start_date)
        else:
            pass

        # build tsquery string
        if state.parsed_query.keywords:
            tsquery = " | ".join(state.parsed_query.keywords)
        else:
            tsquery = None
            
        # keyword Full Text Search filter
        if tsquery:
            where_clauses.append(
                "tsv @@ plainto_tsquery('english', %s)"
            )
            params.append(tsquery)


        # --- Assemble WHERE clause ---
        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)
        else:
            where_sql = ""

        # --- Final SQL ---
        sql = base + where_sql + " ORDER BY published_date ASC;"
        
        return sql, params

   # ---------------------------------------------------------
    # search news: keyword + date filter
    # ---------------------------------------------------------
    def search_news(self, state: State) -> List[dict]:

        """Perform a full text search combining keyword relevance, vector similarity, and date filtering."""
        sql, params = self._build_news_query(state=state)

        try:
            with psycopg.connect(self.conn_str, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    self.logger.info("Executing SQL: \n%s", sql)
                    self.logger.info("Params: %s", params)
                    
                    cur.execute(sql, params)
                    rows = cur.fetchall()
                    
                    self.logger.info("Fetched %d rows", len(rows))
                    return rows
        
        except Exception as e:
            self.logger.error(f"Database query failed: {e}")
            return []