# Government News Summary Agent

A fully automated AI‑powered pipeline that crawls government news webpages, converts unstructured text into structured data + embeddings, and generates topic‑based, date‑based, and department‑based media summaries in Markdown format.

---

## 🌟 Motivation

Government news portals publish large volumes of unstructured text every day across many bureaus and departments.
Manually reading, organizing, and summarizing these articles is:

- Time‑consuming
- Hard to scale
- Prone to human error
- Difficult when topics span multiple policy areas

Traditional scraping alone cannot extract meaningful insights from unstructured text.

This project solves the problem by combining LLMs, hybrid search, and structured extraction to automatically produce clean, accurate media summaries.

---

## 🎯 What Problem Does This Project Solve?

The system converts raw HTML news pages into structured, queryable data, including:

- News ID
- Title
- Full content
- URL
- Embeddings (for semantic + hybrid search)

Then, using LLMs, it generates media summaries tailored to the user’s request — grouped by topic, date, or department.

This enables analysts, researchers, and government teams to quickly understand what happened, without manually reading every article.

---

## 🧰 Technologies Used

### 🕷️ Crawl4AI
- High‑performance crawler for large‑scale scraping
- Asynchronous and reliable
- Extracts clean text from government news pages

### 🔗 LangChain
- Manages prompts, LLM calls, and structured output
- Provides a clean interface for reasoning and summarization

### 🦙 Ollama
- Runs LLMs locally for privacy, speed, and zero cost
- Performs:
    - Query parsing
    - Content extraction
    - Embedding generation
    - Final summarization

### 🐘 PostgreSQL and PGvector
- Stores structured news data
- Stores embeddings for semantic search
- Performs hybrid search (keyword + vector) using SQL
- Production‑ready and scalable 

### 🧩 Pydantic
- Strict schema validation
- Ensures extracted data is clean before insertion

### ⚡ Asyncio
- Enables concurrent crawling and processing
- Greatly improves throughput

---

## 📁 Project Structure

GovNewsAgent/
│
├── tools/
│   ├── __init__.py
│   ├── DataProcessor.py      # Extracts structured fields from CrawlResults
│   ├── LLMSummarizer.py      # Generates final news summaries
│   ├── logger.py             # Logging utilities
│   ├── NewsCrawler.py        # Crawl4AI-based news crawler
│   ├── PGVectorNewsStore.py  # PostgreSQL + PGvector storage and queries
│   ├── QueryParser.py        # Parses user requests using LLMs
│   ├── States.py             # Pydantic models for parsed queries and news items
│   └── writeReport.py        # Writes summaries to Markdown files
│
├── main.py                   # Main entry point
├── .env                      # Environment variables
├── pyproject.toml
├── uv.lock
└── README.md


---

## 🚀 How It Works

1. **Crawl news webpages** using Crawl4AI
2. **Extract structured fields (title, content, URL, etc.)**
3. **Generate embeddings** using a local LLM (via Ollama)
4. **Store data + embeddings** in PostgreSQL with PGvector
5. **Parse user request (topics, date range, departments)** using LLMs
6. **Perform hybrid search** to retrieve relevant articles
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
ollama_llm_model=llama3:latest
ollama_embedding_model=bge-m3:latest 

## Usage
uv run main.py
type the keyword(e.g. AI) for searching relevant jobs.

---

📌 Example Use Cases
- Daily media summary for internal government briefings
- Topic‑based monitoring (e.g., AI, housing, public health)
- Department‑specific summaries
- Historical trend analysis
- Automated reporting for analysts and policy teams

---