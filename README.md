# SQL Agent & Web Agent Framework

A multi-agent framework built with LangChain that provides natural language interfaces for **database querying** and **web research**. Uses local LLMs (Ollama) and cloud LLMs (Google Gemini) with both native and prompt-engineered tool calling.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Components](#components)
  - [SQL Agent](#sql-agent)
  - [Web Agent](#web-agent)
  - [Custom Tool Template](#custom-tool-template)
  - [LangChain Examples](#langchain-examples)
- [Database Schema](#database-schema)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Tool Reference](#tool-reference)
- [Technology Stack](#technology-stack)

---

## System Architecture

```
+-----------------------------------------------------------------------------------+
|                              USER INTERFACE (CLI)                                  |
|                         Interactive Terminal Sessions                              |
+----------+----------------------------+-------------------------------------------+
           |                            |
           v                            v
+---------------------+     +----------------------+     +-------------------------+
|     SQL AGENT       |     |     WEB AGENT        |     |  CUSTOM TOOL TEMPLATE   |
|  sql_agent.py       |     |  web_agent.py         |     |  custom_tool_template.py|
|                     |     |                      |     |                         |
| - Multi-turn chat   |     | - Async event loop   |     | - Provider selection    |
| - Tool routing      |     | - Deep research      |     | - Native/prompt modes   |
| - Response metrics  |     | - Parallel search    |     | - Extensible tools      |
+----------+----------+     +----------+-----------+     +------------+------------+
           |                            |                              |
           v                            v                              v
+---------------------+     +----------------------+     +-------------------------+
|   LLM PROVIDERS     |     |   LLM PROVIDERS      |     |   LLM PROVIDERS         |
|                     |     |                      |     |                         |
| Ollama (gpt-oss:20b)|     | Gemini 2.5 Flash     |     | Ollama / Gemini         |
| @ 192.168.2.54:11434|     | (primary)            |     | (configurable)          |
|                     |     | Ollama (fallback)    |     |                         |
+----------+----------+     +----------+-----------+     +------------+------------+
           |                            |                              |
           v                            v                              v
+---------------------+     +----------------------+     +-------------------------+
|   TOOL LAYER        |     |   TOOL LAYER         |     |   TOOL LAYER            |
|                     |     |                      |     |                         |
| - run_sql_query     |     | - fetch_metadata     |     | - get_lat_long_for_city |
| - get_table_schema  |     |   (SearXNG search)   |     | - get_weather_for_lat...|
| - list_tables       |     |                      |     | - [user-defined tools]  |
| - export_to_csv     |     |                      |     |                         |
+----------+----------+     +----------+-----------+     +------------+------------+
           |                            |                              |
           v                            v                              v
+---------------------+     +----------------------+     +-------------------------+
|   DATA LAYER        |     |   EXTERNAL SERVICES  |     |   EXTERNAL APIS         |
|                     |     |                      |     |                         |
|  PostgreSQL DB      |     | SearXNG (localhost)  |     | Open-Meteo Geocoding    |
|  (School Mgmt)      |     |   +-- Google         |     | Open-Meteo Weather      |
|                     |     |   +-- DuckDuckGo     |     |                         |
|  10 tables          |     |   +-- Bing           |     |                         |
|  5000+ records      |     |                      |     |                         |
+---------------------+     +----------------------+     +-------------------------+
```

### Data Flow

```
SQL Agent Query Lifecycle:
==========================

  User: "How many students passed math?"
    |
    v
  [LLM] Determines exploration strategy
    |
    +---> list_tables(pattern="%student%")    ---> PostgreSQL
    +---> get_table_schema("students")        ---> PostgreSQL
    +---> get_table_schema("grades")          ---> PostgreSQL
    +---> run_sql_query("SELECT COUNT(*)...")  ---> PostgreSQL
    |
    v
  [LLM] Synthesizes results into natural language
    |
    v
  Agent: "There are 87 students who passed math with a grade above 60..."


Web Agent Query Lifecycle:
==========================

  User: "Latest developments in quantum computing"
    |
    v
  [LLM] Breaks query into parallel sub-searches
    |
    +---> fetch_metadata("quantum computing breakthroughs 2025")  ---> SearXNG
    +---> fetch_metadata("quantum computing companies research")  ---> SearXNG
    +---> fetch_metadata("quantum error correction advances")     ---> SearXNG
    |
    v
  [LLM] Cross-references and synthesizes multi-source results
    |
    v
  Agent: "Here are the latest developments..."
```

### Tool Calling Architecture

The framework supports two execution models for LLM-tool interaction:

```
Native Tool Calling (Gemini, modern Ollama models):
=====================================================
  LLM ---> tool_calls: [{name: "run_sql_query", args: {...}}]
    |
    v
  Agent executes tools, feeds results back to LLM
    |
    v
  LLM generates natural language response


Prompt-Engineered Tool Calling (legacy models):
=====================================================
  System Prompt defines tools as JSON schema
    |
    v
  LLM ---> {"tool": "run_sql_query", "args": {"query": "..."}}
    |
    v
  Agent parses JSON, executes tools, injects results
    |
    v
  LLM generates natural language response (max 5 iterations)
```

---

## Project Structure

```
sql-agent/
|
+-- sql_agent/                      # SQL Agent module
|   +-- db_config.py                # PostgreSQL connection management
|   +-- sql_agent.py                # Interactive SQL assistant (CLI)
|   +-- tools.py                    # Database query & exploration tools
|
+-- webagent/                       # Web Agent module
|   +-- web_agent.py                # Async web research assistant (CLI)
|   +-- tools.py                    # SearXNG search integration
|
+-- setup_school_database.py        # Database schema creation + sample data
+-- populate_empty_tables.py        # Generic table population utility
+-- custom_tool_template.py         # Extensible tool template (Ollama/Gemini)
+-- main.py                         # Gemini weather agent example
+-- gemini_langchain.py             # Gemini native tool calling example
+-- ollama_langchain.py             # Ollama native tool calling example
+-- ollama_prompt_tools.py          # Ollama prompt-engineered tool example
+-- .env                            # Environment variables (not committed)
+-- .gitignore                      # Git ignore rules
```

---

## Components

### SQL Agent

An interactive natural language interface for querying PostgreSQL databases. The agent autonomously explores database structure before answering questions.

**Key behaviors:**
- Automatically discovers tables using pattern matching (avoids blind pagination)
- Inspects table schemas before constructing queries
- Formats results as pretty-printed tables (up to 20 rows)
- Suggests CSV export for large result sets
- Tracks response time and token usage per query

**LLM:** Ollama `gpt-oss:20b` (local, 120K context window)

**Tools available:**
| Tool | Purpose |
|------|---------|
| `run_sql_query` | Execute SQL, display up to 20 formatted rows |
| `get_table_schema` | Retrieve column names, types, constraints |
| `list_tables` | List tables with pattern filtering and pagination |
| `export_query_to_csv` | Export full query results to CSV file |

### Web Agent

An async web research assistant that performs deep, multi-source research using a local SearXNG meta-search engine.

**Key behaviors:**
- Breaks queries into parallel sub-searches for thoroughness
- Aggregates results from Google, DuckDuckGo, and Bing
- Cross-checks facts across multiple sources
- Generates follow-up searches automatically when gaps are found

**LLM:** Google Gemini 2.5 Flash (primary), Ollama (fallback)

**Tools available:**
| Tool | Purpose |
|------|---------|
| `fetch_metadata` | Async web search via SearXNG (returns top 10 results) |

### Custom Tool Template

A reusable template for building new tool-calling agents. Supports both Ollama and Gemini with automatic provider detection and dual execution modes.

**Configuration section** at the top of the file lets you:
- Choose LLM provider (`ollama` or `gemini`)
- Set model name and endpoint
- Toggle between native and prompt-engineered tool calling
- Define custom tools with the `@tool` decorator
- Register tools in the `TOOLS` list

### LangChain Examples

| File | Description |
|------|-------------|
| `main.py` | Weather agent using Gemini with parallel tool calls |
| `gemini_langchain.py` | Standalone Gemini + native tool calling demo |
| `ollama_langchain.py` | Ollama (qwen3:30b) + native tool calling demo |
| `ollama_prompt_tools.py` | Ollama with JSON-based prompt-engineered tools |

All examples use the Open-Meteo API for geocoding and weather forecasting.

---

## Database Schema

The project includes a complete **School Management System** database with 10 normalized tables and 5,000+ sample records generated via Faker.

```
+---------------+       +---------------+       +---------------+
|   students    |       |   subjects    |       |    staff      |
+---------------+       +---------------+       +---------------+
| student_id PK |       | subject_id PK |       | staff_id PK   |
| first_name    |       | subject_name  |       | first_name    |
| last_name     |       | subject_code  |       | last_name     |
| email (UQ)    |       | description   |       | email (UQ)    |
| phone         |       | credits       |       | phone         |
| date_of_birth |       | department    |       | role          |
| gender        |       +-------+-------+       | department    |
| address       |               |               | hire_date     |
| admission_date|               |               | salary        |
| grade_level   |               |               | status        |
| status        |               |               +-------+-------+
+-------+-------+               |                       |
        |                       |                       |
        |               +-------v-------+               |
        |               |   classes     |<--------------+
        |               +---------------+   (teacher_id FK)
        |               | class_id PK   |
        |               | class_name    |
        |               | subject_id FK |
        |               | teacher_id FK |
        |               | room_number   |
        |               | schedule      |
        |               | semester      |
        |               | year          |
        |               | max_students  |
        |               +-------+-------+
        |                       |
        v                       v
+---------------+       +---------------+       +-------------------+
| enrollments   |       |    grades     |       |   attendance      |
+---------------+       +---------------+       +-------------------+
| enrollment_id |       | grade_id PK   |       | attendance_id PK  |
| student_id FK |       | student_id FK |       | student_id FK     |
| class_id FK   |       | class_id FK   |       | class_id FK       |
| enrollment_dt |       | assignment_nm |       | attendance_date   |
| status        |       | grade         |       | status            |
+---------------+       | max_grade     |       | remarks           |
                        | grade_date    |       +-------------------+
                        | comments      |
                        +---------------+

+---------------+                       +-------------------------+
| assignments   |                       |  library_transactions   |
+---------------+                       +-------------------------+
| assignment_id |  +---------------+    | transaction_id PK       |
| class_id FK   |  | library_books |    | book_id FK              |
| title         |  +---------------+    | student_id FK           |
| description   |  | book_id PK    |    | checkout_date           |
| due_date      |  | title         |--->| due_date                |
| max_points    |  | author        |    | return_date             |
| type          |  | isbn (UQ)     |    | status                  |
+---------------+  | publisher     |    | fine_amount             |
                   | pub_year      |    +-------------------------+
                   | category      |
                   | total_copies  |
                   | avail_copies  |
                   | shelf_location|
                   +---------------+
```

### Record Counts

| Table | Records | Description |
|-------|---------|-------------|
| `students` | 150 | Student profiles with demographics |
| `subjects` | 120 | Course catalog across 8 departments |
| `staff` | 100 | Teachers, admins, counselors, IT |
| `classes` | 100 | Class offerings (Fall/Spring/Summer 2023-2025) |
| `enrollments` | 500 | Student-class enrollment records |
| `grades` | 1,000 | Assessment scores (quizzes, tests, projects) |
| `attendance` | 2,000 | Daily attendance tracking |
| `assignments` | 200 | Assignment definitions with due dates |
| `library_books` | 300 | Book catalog across 9 categories |
| `library_transactions` | 400 | Checkout/return logs with fine calculation |

---

## Setup & Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Ollama (for local LLM inference) or Google Gemini API key
- SearXNG instance (for web agent only)

### 1. Clone and install dependencies

```bash
git clone <repository-url>
cd sql-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install langchain langchain-ollama langchain-google-genai psycopg2-binary python-dotenv faker tabulate httpx requests
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=school_db
DB_USER=postgres
DB_PASSWORD=your_password

# Google Gemini (optional - for web agent and Gemini examples)
GOOGLE_API_KEY=your_gemini_api_key
```

### 3. Set up the database

```bash
# Create the PostgreSQL database first
createdb school_db

# Run the setup script to create tables and populate with sample data
python setup_school_database.py
```

This creates 10 tables with 5,000+ realistic records using Faker.

### 4. Set up Ollama (for SQL Agent)

```bash
# Install Ollama from https://ollama.com
# Pull the model
ollama pull gpt-oss:20b

# Or use any model that supports tool calling
ollama pull qwen3:30b
```

> **Note:** The SQL agent is configured to connect to Ollama at `192.168.2.54:11434`. Update the `base_url` in [sql_agent.py](sql_agent/sql_agent.py) if your Ollama instance is running elsewhere.

### 5. Set up SearXNG (for Web Agent, optional)

The web agent requires a SearXNG instance running at `http://localhost:8888`. You can deploy one using Docker:

```bash
docker run -d -p 8888:8080 searxng/searxng
```

Ensure JSON output is enabled in the SearXNG settings.

---

## Configuration

### LLM Provider Settings

| Parameter | SQL Agent | Web Agent | Template |
|-----------|-----------|-----------|----------|
| Provider | Ollama | Gemini (primary) | Configurable |
| Model | `gpt-oss:20b` | `gemini-2.5-flash` | `gpt-oss:20b` / `gemini-2.5-flash` |
| Temperature | 0.3 | 0.3 | 0.0 |
| Context Window | 120,000 tokens | Default | Default |
| Endpoint | `192.168.2.54:11434` | Google API | Configurable |

### Switching LLM Providers

In `custom_tool_template.py`, modify the configuration section:

```python
PROVIDER = "gemini"          # "ollama" or "gemini"
OLLAMA_MODEL = "qwen3:30b"   # Any Ollama model
NATIVE_TOOLS = True          # False for prompt-engineered approach
```

---

## Usage

### SQL Agent

```bash
cd sql_agent
python sql_agent.py
```

```
SQL Agent started. Type 'exit' or 'quit' to stop.

You: Show me the top 5 students with highest average grades
[Tools used: list_tables, get_table_schema, get_table_schema, run_sql_query]

Agent: Here are the top 5 students by average grade:

+----+------------+-----------+---------------+
| #  | First Name | Last Name | Average Grade |
+----+------------+-----------+---------------+
| 1  | Sarah      | Johnson   | 97.45         |
| 2  | Michael    | Chen      | 96.12         |
| ...                                         |
+----+------------+-----------+---------------+

Response time: 4.23s
Tokens - Input: 1542, Output: 287, Total: 1829
```

### Web Agent

```bash
cd webagent
python web_agent.py
```

```
You: What are the latest breakthroughs in AI?
[Tools Used -> fetch_metadata, fetch_metadata, fetch_metadata]

Agent -> Based on my research across multiple sources...

Response time -> 6.12s
Tokens: input=3210 | output=892 | total=4102
```

### Custom Tool Template

```bash
python custom_tool_template.py
```

### Examples

```bash
python main.py                  # Gemini weather agent
python gemini_langchain.py      # Gemini tool calling demo
python ollama_langchain.py      # Ollama native tools demo
python ollama_prompt_tools.py   # Ollama prompt-engineered tools
```

---

## Tool Reference

### SQL Agent Tools

#### `run_sql_query(query: str) -> str`
Executes a SQL query against PostgreSQL and returns formatted results. Displays up to 20 rows with column headers. For larger result sets, suggests using `export_query_to_csv`.

#### `get_table_schema(table_name: str) -> str`
Queries `information_schema.columns` to retrieve column names, data types, nullability, character length limits, and default values. Uses parameterized queries to prevent SQL injection.

#### `list_tables(schema="public", pattern=None, limit=50, offset=0) -> str`
Lists tables in the specified schema with optional `LIKE` pattern filtering and pagination. Returns total count alongside results.

#### `export_query_to_csv(query: str, filename=None) -> str`
Executes a query and writes all results to a CSV file in the `exports/` directory. Auto-generates timestamped filenames if none provided.

### Web Agent Tools

#### `fetch_metadata(query: str) -> dict`
Async tool that searches the web via a local SearXNG instance. Queries Google, DuckDuckGo, and Bing simultaneously. Returns top 10 results with title, URL, and snippet.

### Weather Tools (Examples)

#### `get_lat_long_for_city(city: str) -> dict`
Geocodes a city name to latitude/longitude using the Open-Meteo Geocoding API.

#### `get_weather_for_lat_long(lat: float, lon: float) -> dict`
Fetches current temperature for given coordinates using the Open-Meteo Forecast API.

---

## Technology Stack

| Category | Technology |
|----------|-----------|
| Language | Python 3.9+ |
| Agent Framework | LangChain, Langgraph |
| LLM (Local) | Ollama (gpt-oss:20b, gpt-oss:120b, qwen3:30b) |
| LLM (Cloud) | Google Gemini 2.5 Flash |
| Database | PostgreSQL 13+ |
| DB Driver | psycopg2 |
| Search Engine | SearXNG (meta-search) |
| HTTP Client | httpx (async), requests |
| Data Generation | Faker |
| Table Formatting | tabulate |
| Config | python-dotenv |

---

## License

This project is provided as a template for building LLM-powered agents. Use and modify freely.
