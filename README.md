# Government News Summary Agent

An LLM‑powered, fully automated news‑intelligence pipeline that crawls government websites, extracts structured data, generates embeddings, and produces clean Markdown summaries — all without manual reading.

---

## 🌟 Motivation

Government news portals publish large volumes of unstructured text every day across many bureaus and departments.
Manually reading, organizing, and summarizing these articles is:

- Time‑consuming
- Hard to scale
- Prone to human error
- Difficult when topics span multiple policy areas

Traditional scraping alone cannot extract meaningful insights from unstructured text.

This project solves that by combining:

- High‑performance async crawling
- LLM‑powered extraction + summarization
- Full Text search/Hybrid search (later) (keyword + vector)
- Automated Markdown report generation

The result: a fully automated government news intelligence system.
---

## 🎯 What Problem Does This Project Solve?

The system converts raw HTML news pages into structured, queryable data, including:

- News ID
- Title
- Full content
- URL
- Embeddings (for semantic + hybrid search)

Then, using LLMs, it generates media summaries tailored to the user’s request — grouped by:
- Topic
- Date/Date Range
- Department

This enables analysts, researchers, and government teams to quickly understand what happened, without manually reading every article.

---

## 🧰 Technologies Used

### Aiohttp
- Asynchronous, high‑throughput crawler
- Extracts clean text from government news pages 
(“High‑performance crawler for large‑scale scraping”)

### 🦙 Ollama
- Local LLM inference for privacy + zero cost
- Handles query parsing, extraction, embeddings, and summarization
(“Runs LLMs locally for privacy, speed, and zero cost”)

### 🐘 PostgreSQL and PGvector
- Stores structured news
- Embedding search + hybrid search
(“Stores embeddings for semantic search… performs hybrid search”)

### 🧩 Pydantic
- Strict schema validation
- Ensures extracted data is clean before insertion

### ⚡ Asyncio
- Concurrent crawling + processing
- Major throughput improvements

---

## 📁 Project Structure

GovNewsAgent/
│
├── tools/
│   ├── __init__.py
│   ├── States.py             # Pydantic models for parsing queries and storing news items
│   ├── QueryParser.py        # LLM-based query parsing
│   ├── NewsFetcher.py        # Async news crawler
│   ├── PGVectorNewsStore.py  # PostgreSQL + PGvector storage and queries
│   ├── logger.py             # Logging utilities
│   ├── ContentEmbedder.py    # Embedding generation
│   └── ReportGenerator.py    # Generate final news summaries in Markdown files
│
├── main.py                   # Main entry point
├── .env                      # Environment variables
├── pyproject.toml
├── uv.lock
└── README.md


---

## 🚀 How It Works

1. **Parse user request (topics, date range, departments)** using LLMs
2. **Crawl Government news webpages** using Crawl4AI
3. **Extract structured fields (title, content, URL, etc.)**
4. **Generate embeddings** using a local LLM (via Ollama)
5. **Store data + embeddings** in PostgreSQL with PGvector
6. **Perform full-text/Hybrid search** to retrieve relevant articles
7. **Generate a clean, structured media summary** in Markdown

The result is a fully automated, end‑to‑end system for government news intelligence.
---

## 🛠️ Installation and Usage

Clone the repository:

git clone https://github.com/simongalaxy/GovNewsAgent.git
cd GovNewsAgent

# install dependences
uv sync

## Set up your .env file:
POSTGRES_URL=your_postgres_connection_string
ollama_llm_model=llama3.2:3b
ollama_embedding_model=bge-m3:latest
ollama_extraction_model=phi4-mini:latest

## Usage
uv run main.py
Enter the query to the Gov News or type 'q' for exit:

---

📌 Example Use Cases
- Daily media summary for internal government briefings
- Topic‑based monitoring (e.g., AI, housing, public health)
- Department‑specific summaries
- Historical trend analysis
- Automated reporting for analysts and policy teams

---