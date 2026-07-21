import json
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import List, Tuple


from src.Settings import settings
from src.logger import Logger
from src.States import NewsItem, ParsedQuery, State


class PG_DBHandler:
    def __init__(self, logger: Logger):
        # logger settings.
        self.logger = logger
        
        # local postgresql db settings.
        # self.username = settings.username
        # self.password = settings.password
        # self.host = settings.host
        # self.port = settings.port
        # self.db_name = settings.db_name
        # self.conn_str = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        # self.embedding_dim = 1024
        
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

    
    def _create_table(self) -> None:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS GovNews (
            id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT NOT NULL,
            published_date DATE,
            subject_department TEXT[],
            summary TEXT[],
            category TEXT,
            keywords TEXT[],
            content_type TEXT,
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
    def insert_news(self, item: NewsItem) -> str | None:
        
        """Insert or update a news item. Returns the id on success."""
        insert_query = """
        INSERT INTO GovNews (
            id, title, content, url, published_date
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            url = EXCLUDED.url,
            published_date = EXCLUDED.published_date
        RETURNING id;
        """

        values = (
            item.id,
            item.title,
            item.content,
            item.url,
            item.published_date,
        )

        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(insert_query, values)
                row = cur.fetchone()

                if row:
                    inserted_id = row["id"]
                    self.logger.debug(f"Inserted news with id - {inserted_id}")
                    return inserted_id
                else:
                    self.logger.warning(f"No row returned for news with id - {item.id}")
                    return None

        except Exception as e:
            self.logger.error(f"Error inserting news with id - {item.id}: {e}")
            # Do NOT raise here if you want the pipeline to continue
            # raise  
            return None


    # update the records in database with extracted job information to respective job accordingly.
    def update_news(self, item: NewsItem) -> str | None:
        update_query = """UPDATE GovNews SET
            subject_department = %s,
            summary = %s,
            category = %s,
            keywords = %s,
            content_type = %s,
            updated_at = NOW()
        WHERE id = %s
        RETURNING id;
        """

        # Note that job_item.id moves to the VERY END of the tuple to match the WHERE clause
        values = (
            item.subject_department,
            item.summary,
            item.category,
            item.keywords,
            item.content_type,
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
    
    def retrieve_news_for_extracting_data(self, state: State) -> tuple[str, List]:
        base = """
            SELECT
                id,
                published_date,
                title,
                content
            FROM GovNews
        """
        
        where_clauses = []
        params = []

        # date range
        if state.parsed_query.start_date and state.parsed_query.end_date:
            where_clauses.append("published_date BETWEEN %s AND %s")
            params.append(state.parsed_query.start_date)
            params.append(state.parsed_query.end_date)
        elif state.parsed_query.start_date or state.parsed_query.end_date:
            where_clauses.append("published_date = %s")
            params.append(state.parsed_query.start_date)
        else:
            pass
        
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
            self.logger.info("Fetched %d rows", len(rows))
            
            return rows
        
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