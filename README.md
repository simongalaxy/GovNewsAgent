# Government News Summary Agent

An LLM‑powered, fully automated news‑intelligence pipeline that crawls government websites, extracts structured data and produces clean Markdown summaries — all without manual reading.

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
- Full Text search in Postgresql
- Automated Markdown report generation

The result: a fully automated government news intelligence system.
---

## 🎯 What Problem Does This Project Solve?

The system converts raw HTML news pages into structured, queryable data, including:

- id
- Published_date
- Title
- Content
- URL

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

### 🦙 Ollama (Local/Cloud)
- Local LLM inference for privacy + zero cost
- Handles query parsing, extraction and summarization
(“Runs LLMs locally for speed, and zero cost”)

### 🐘 PostgreSQL
- Stores structured news
- Full Text search

### Instructor
-  provides type-safe data extraction with automatic validation, retries, and streaming support.

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
├── src/
│   ├── __init__.py
│   ├── DataClasses.py        # Pydantic Classes for parsed query, news items
│   ├── LLMAgent.py           # LLM-based query parsing and generate markdown summary
│   ├── NewsScraper.py        # Async news crawler
│   ├── PG_DBHandler.py       # PostgreSQL storage and queries
│   ├── logger.py             # Logging utilities
│   └── Settings.py           # Extract the settings parameters.
│
├── main.py                   # Main entry point
├── .env                      # Environment variables
├── pyproject.toml
├── uv.lock
└── README.md


---

## 🚀 How It Works

1. **Parse user request (topics, date range, departments)** using LLMs
2. **Crawl Government news webpages** using Aiohttp and Beautifulsoup
3. **Extract structured fields (title, content, URL, etc.)**
4. **Store data** in PostgreSQL
5. **Perform full-text search** to retrieve relevant articles
6. **Generate a clean, structured media summary** in Markdown using LLMs

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
