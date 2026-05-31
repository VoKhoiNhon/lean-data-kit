# 🚀 Lean Data Starter Kit

> **A High-Performance Single-Node Data Processing & AI-Ready Boilerplate.**  
> *Processing medium-sized datasets at lightning-speed without the overhead of distributed systems.*

---

## 🛑 The Pain Point

### 💸 Are you over-paying for Spark and Databricks clusters?
Many teams make the costly mistake of spinning up expensive distributed clusters (Apache Spark, Databricks, AWS EMR) to process datasets ranging from **1GB to 250GB**.
- **Massive RAM & CPU Overhead**: JVM warm-ups, serialization costs, and network bottlenecks.
- **Complexity**: Setting up cluster managers, managing package dependencies across worker nodes.
- **Financial Drain**: High idle cluster costs and cloud orchestration fees.

---

## ⚡ The Solution

### 🏎️ Single-node High-Performance Data Processing
Modern single-node systems are extremely powerful. With **DuckDB** and **Polars**, we can process hundreds of millions of rows in seconds on a single developer machine.

| Technology | Role | Key Advantage |
| :--- | :--- | :--- |
| **Polars (Lazy API)** | ETL Ingestion & Filtering | Extremely fast multithreaded column-oriented processing in Rust. Memory-safe and supports out-of-core queries. |
| **DuckDB** | Tabular Storage & SQL Analytics | The "SQLite for Analytics." Seamless zero-copy memory transfers between Polars and DuckDB via PyArrow. |
| **Milvus Standalone** | Vector Search Engine | Production-ready vector indexing (HNSW) allowing direct AI integration and semantic similarity queries. |
| **FastAPI** | Deployment & API | Lightweight, asynchronous, auto-documented HTTP REST server. |

---

## 📁 Directory Structure

```text
lean-data-kit/
├── core/
│   ├── config.py              # Dynamic configuration loading (Pydantic settings)
│   ├── duckdb_client.py       # DuckDB Connection Manager
│   └── milvus_client.py       # Milvus Vector Database Client
├── pipelines/
│   └── data_pipeline.py       # Polars Lazy ETL & Vector Embeddings Pipeline
├── api/
│   ├── main.py                # FastAPI HTTP REST Server
│   └── Dockerfile             # Multi-stage optimized API container
├── docker-compose.yml         # Dev/Prod Orchestration for API & Milvus Standalone
├── requirements.txt           # Python dependency declarations
└── README.md                  # Comprehensive Documentation
```

---

## 🛠️ Quick Start Guide

### Prerequisites
- Install **Docker** and **Docker Compose**.
- Python 3.11+ (if running locally without Docker).

---

### Option 1: Docker Compose (Recommended)

1. Clone or copy this repository:
   ```bash
   cd lean-data-kit
   ```

2. Build and start the services:
   ```bash
   docker-compose up -d --build
   ```

3. Verify that both containers are running healthy:
   ```bash
   docker-compose ps
   ```
    - **FastAPI API**: `http://localhost:8000`
    - **FastAPI Interactive Docs (Swagger)**: `http://localhost:8000/docs`
    - **Attu (Milvus Web GUI Admin Panel)**: `http://localhost:3000`
    - **Milvus Standalone**: `localhost:19530` (gRPC) & `localhost:9091` (HTTP health)

---

### Option 2: Local Development Setup

1. Create a virtual environment and install packages:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Start the FastAPI local server:
   ```bash
   python api/main.py
   ```

---

## 🔌 API Usage Specifications

### 1. Health Check
- **Method**: `GET`
- **URL**: `http://localhost:8000/`
- **Response**:
  ```json
  {
    "status": "healthy",
    "service": "Lean Data Starter Kit API",
    "engine": "Polars LazyFrame + DuckDB + Milvus Standalone",
    "author": "Senior Data Architect & Backend Developer"
  }
  ```

---

### 2. Run ETL & Ingestion Pipeline
Processes the local file, drops nulls, adds 768-dimensional mock vectors, and writes to both DuckDB and Milvus.

- **Method**: `POST`
- **URL**: `http://localhost:8000/run-pipeline`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "file_path": "/app/data/sample.csv",
    "collection_name": "product_reviews",
    "text_column": "text"
  }
  ```

- **Response**:
  ```json
  {
    "status": "success",
    "message": "Data Pipeline executed successfully.",
    "rows_processed": 10520,
    "vectors_inserted": 10520,
    "elapsed_seconds": 1.4582
  }
  ```

---

## 💡 Key Architectural Details

### 1. Polars Out-of-Core Execution
Polars operates on a **Lazy Engine**. Query evaluations are optimized beforehand (predicate pushdown, projection selection), and operations execute only when `.collect()` is explicitly called. This minimizes RAM usage drastically by streaming files chunk-by-chunk.

### 2. Zero-Copy PyArrow Integration
Moving data from Polars to DuckDB is completely instant:
```python
db_manager.conn.register("df_pipeline_temp", df)
db_manager.conn.execute("INSERT INTO table SELECT * FROM df_pipeline_temp")
```
This registration creates an in-memory view utilizing **Apache Arrow**, bypassing disk write cycles or expensive parsing routines entirely.

### 3. Lightweight Single-Container Vector DB
The Milvus configuration is customized using:
- `ETCD_USE_EMBED=true`: Runs etcd inside the same container.
- `COMMON_STORAGETYPE=local`: Avoids running a separate MinIO server.
This decreases the Milvus base RAM requirement from **several gigabytes** down to **less than 300MB**.
