import json
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import List, Tuple
from pprint import pformat

from src.Util.Settings import settings
from src.Util.logger import Logger
from src.Core.State import State
from src.Data.DataClasses import NewsItem, ParsedQuery, ExtractedData

class PG_DBHandler:
    def __init__(self, logger: Logger):
        # logger settings.
        self.logger = logger
         
        # neon database settings.
        self.conn_str = settings.neon_connection_str
        self.db_name = settings.pgdatabase
        
        # Create persistent connection with autocommit
        self.conn = psycopg2.connect(self.conn_str)
        self.conn.autocommit = True
        
        self.logger.info(f"DBHandler initialized and connected to {self.db_name}")
        
        # ensure database and table was created.
        self._ensure_database_exists()
        self._create_table()

    # check whether the database exists.
    def _ensure_database_exists(self) -> None:
        """
        Check if a PostgreSQL database exists. 
        If not, create it. If yes, do nothing.
        """

        # Step 1 — connect to default 'postgres' database
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        with self.conn.cursor() as cur:
            # Step 2 — check if database exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (self.db_name,))
            exists = cur.fetchone()

            if exists:
                print(f"Database '{self.db_name}' already exists — skipping creation.")
            else:
                print(f"Database '{self.db_name}' does not exist — creating now...")
                cur.execute(f'CREATE DATABASE "{self.db_name}";')
                print(f"Database '{self.db_name}' created successfully.")

        return

    # create table when needed.
    def _create_table(self) -> None:
        create_table_query = """
        CREATE EXTENSION IF NOT EXISTS vector;
        
        CREATE TABLE IF NOT EXISTS PressReleases (
            id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT NOT NULL,
            published_date DATE,
            subject_department TEXT,
            summary TEXT,
            summary_embeddings vector(1536),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(create_table_query)
            self.logger.info("Table GovNews created (or already exists)")
        except Exception as e:
            self.logger.error(f"Failed to create table: {e}")
            raise
        
        return

    # ---------------------------------------------------------
    # Insert or update a news article
    # ---------------------------------------------------------
   
    # just add raw data of job info to database.
    def insert_news(self, item: NewsItem) -> None:
        
        """Insert or update a news item. Returns the id on success."""
        insert_query = """
        INSERT INTO PressReleases (
            id, title, content, url, published_date, subject_department, summary, summary_embeddings
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            url = EXCLUDED.url,
            published_date = EXCLUDED.published_date,
            subject_department = EXCLUDED.subject_department,
            summary = EXCLUDED.summary,
            summary_embeddings = EXCLUDED.summary_embeddings
        RETURNING id;
        """

        values = (
            item.id,
            item.title,
            item.content,
            item.url,
            item.published_date,
            item.extracted_data.subject_department if item.extracted_data else None,
            item.extracted_data.summary if item.summary else None,
            item.embeddings if item.summary else None
        )

        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(insert_query, values)
                row = cur.fetchone()

                if row:
                    inserted_id = row["id"]
                    self.logger.info(f"Inserted news with id - {inserted_id}")
                    return inserted_id
                else:
                    self.logger.info(f"No row returned for news with id - {item.id}")
                    return None

        except Exception as e:
            self.logger.error(f"Error inserting news with id - {item.id}: {e}")
            # Do NOT raise here if you want the pipeline to continue
            # raise  
            return None


    #update the records in database with extracted job information to respective job accordingly.
    def update_news_classification(self, item: ExtractedData) -> str | None:
        update_query = """UPDATE PressReleases SET
            subject_department = %s,
            summary = %s
            updated_at = NOW()
        WHERE id = %s
        RETURNING id;
        """

        # Note that job_item.id moves to the VERY END of the tuple to match the WHERE clause
        values = (
            item.subject_department,
            item.summary,
            item.id, 
        )

        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(update_query, values)
                row = cur.fetchone()

                if row:
                    inserted_id = row["id"]
                    self.logger.info(f"Inserted/Updated news_id - {inserted_id}")
                    return inserted_id
                else:
                    self.logger.info(f"No row returned for news id - {item.id}")
                    return None

        except Exception as e:
            self.logger.error(f"Error inserting job {item.id}: {e}")
            # Do NOT raise here if you want the pipeline to continue
            # raise  
            return None
    

    def query_full_text_search(self, state: State) -> None:
        base = """
            SELECT
                id,
                published_date,
                title,
                content,
                url
            FROM PressReleases
        """
        
        where_clauses = []
        params = []

        # date range.
        if state.parsed_query.start_date and state.parsed_query.end_date:
            where_clauses.append("published_date BETWEEN %s AND %s")
            params.append(state.parsed_query.start_date)
            params.append(state.parsed_query.end_date)
        elif state.parsed_query.start_date or state.parsed_query.end_date:
            where_clauses.append("published_date = %s")
            params.append(state.parsed_query.start_date)
        else:
            pass
        
        # build tsquery string
        # 1. Departments.
        depts = [f"({item.replace(" ", " <-> ")})" for item in state.parsed_query.departments]
        tsquery_depts = " | ".join(depts)
        self.logger.info(f"tsquery_depts: {tsquery_depts}")
        
        # 2. keywords.
        keywords = [f"({item.replace(" ", " <-> ")})" for item in state.parsed_query.keywords]
        tsquery_keywords = " | ".join(keywords)
        self.logger.info(f"tsquery_keywords: {tsquery_keywords}")

        tsquery = f"({tsquery_depts}) & ({tsquery_keywords})"
        # keyword Full Text Search filter
        if tsquery:
            where_clauses.append("to_tsvector('english', content) @@ to_tsquery('english', %s)")
            params.append(tsquery)
        
        #--- Assemble WHERE clause ---
        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)
        else:
            where_sql = ""

        # --- Final SQL ---
        sql = base + where_sql + " ORDER BY published_date ASC;"
            
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            state.search_results = [dict(row) for row in rows]
            for i, item in enumerate(state.search_results, start=1):
                self.logger.info(f"Query Search Result No.: {i}/{len(state.search_results)} - /n%s", pformat(item, indent=4))
            return
        
    #  Build a dynamic SQL query string based on the values present in ParsedQuery, Returns (sql_string, params_list).
#     def _build_news_query(self, state: State) -> tuple[str, list]:

#         base = """
#             SELECT
#                 published_date,
#                 title,
#                 content
#             FROM news
#         """
        
#         where_clauses = []
#         params = []

#         # date range
#         if state.parsed_query.start_date and state.parsed_query.end_date:
#             where_clauses.append("published_date BETWEEN %s AND %s")
#             params.append(state.parsed_query.start_date)
#             params.append(state.parsed_query.end_date)
#         elif state.parsed_query.start_date or state.parsed_query.end_date:
#             where_clauses.append("published_date = %s")
#             params.append(state.parsed_query.start_date)
#         else:
#             pass

#         # build tsquery string
#         if state.parsed_query.keywords:
#             tsquery = " | ".join(state.parsed_query.keywords)
#         else:
#             tsquery = None
            
#         # keyword Full Text Search filter
#         if tsquery:
#             where_clauses.append("tsv @@ plainto_tsquery('english', %s)")
#             params.append(tsquery)


#         # --- Assemble WHERE clause ---
#         where_sql = ""
#         if where_clauses:
#             where_sql = " WHERE " + " AND ".join(where_clauses)
#         else:
#             where_sql = ""

#         # --- Final SQL ---
#         sql = base + where_sql + " ORDER BY published_date ASC;"
        
#         return sql, params

#    # ---------------------------------------------------------
#     # search news: keyword + date filter
#     # ---------------------------------------------------------
#     def search_news(self, state: State) -> List[dict]:

#         """Perform a full text search combining keyword relevance, vector similarity, and date filtering."""
#         sql, params = self._build_news_query(state=state)

#         try:
#             with psycopg.connect(self.conn_str, row_factory=dict_row) as conn:
#                 with conn.cursor() as cur:
#                     self.logger.info("Executing SQL: \n%s", sql)
#                     self.logger.info("Params: %s", params)
                    
#                     cur.execute(sql, params)
#                     rows = cur.fetchall()
#                     self.logger.info("Fetched %d rows", len(rows))
                    
#                     return rows
        
#         except Exception as e:
#             self.logger.error(f"Database query failed: {e}")
#             return []