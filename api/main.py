# lean-data-kit/api/main.py
"""
FastAPI application exposing REST API endpoints for the Lean Data Starter Kit.
Allows users to trigger ETL, data cleansing, and vector ingestion pipelines.
"""

import os
import sys
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Ensure project root is in the python search path for seamless imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from pipelines.data_pipeline import run_etl_and_vectorize

app = FastAPI(
    title="Lean Data Starter Kit API",
    description="Ultra-fast Single-node Data Ingestion & Vector Ingest Service using Polars, DuckDB & Milvus",
    version="1.0.0"
)


class PipelineRequest(BaseModel):
    """
    Request payload schema for executing the data pipeline.
    """
    file_path: str = Field(
        ..., 
        description="Absolute path to the target CSV or Parquet file inside the workspace or host path mapped to the API.",
        examples=["/data/sample_dataset.csv"]
    )
    collection_name: str = Field(
        default="lean_collection", 
        description="Name of the collection to create in Milvus and table in DuckDB.",
        examples=["customer_reviews"]
    )
    text_column: str = Field(
        default="text", 
        description="The column name in the source file containing text that should be processed.",
        examples=["content"]
    )


@app.get("/", status_code=status.HTTP_200_OK)
def read_root() -> Dict[str, str]:
    """
    Service health check and metadata endpoint.
    """
    return {
        "status": "healthy",
        "service": "Lean Data Starter Kit API",
        "engine": "Polars LazyFrame + DuckDB + Milvus Standalone",
        "author": "Senior Data Architect & Backend Developer"
    }


@app.post("/run-pipeline", status_code=status.HTTP_200_OK)
def execute_pipeline(payload: PipelineRequest) -> Dict[str, Any]:
    """
    Triggers the ETL pipeline:
    1. Reads CSV or Parquet using Polars Lazy API.
    2. Drops nulls and removes empty records.
    3. Mocks high-performance 768-dimensional float embedding vectors.
    4. Registers and writes the structured records directly into DuckDB.
    5. Re-shapes the datasets and loads the vectors and texts into Milvus.
    """
    # Quick early check to make sure file exists on disk
    if not os.path.exists(payload.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source file not found at path: {payload.file_path}. Please verify the path is correct and accessible."
        )

    try:
        # Trigger ETL + Embeddings load pipeline
        metrics = run_etl_and_vectorize(
            file_path=payload.file_path,
            collection_name=payload.collection_name,
            text_column=payload.text_column
        )
        return metrics
    except Exception as e:
        # Return 500 error on any processing or connection failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    # Execute locally on port 8000 when running directly
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
