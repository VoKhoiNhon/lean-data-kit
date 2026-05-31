# lean-data-kit/pipelines/data_pipeline.py
"""
High-Performance ETL and Vectorization Pipeline.
Loads CSV/Parquet datasets using Polars Lazy API, cleans data, mocks vector embeddings,
and loads them into DuckDB (tabular) and Milvus (vector).
"""

import os
import random
import time
from typing import Dict, Any

import polars as pl

from core.config import settings
from core.duckdb_client import DuckDBManager
from core.milvus_client import MilvusManager


def run_etl_and_vectorize(
    file_path: str, 
    collection_name: str = "lean_collection",
    text_column: str = "text"
) -> Dict[str, Any]:
    """
    Executes the End-to-End ETL and Vector Ingestion pipeline.

    Args:
        file_path (str): Path to the input CSV or Parquet file.
        collection_name (str): Name of the target Milvus collection.
        text_column (str): The column containing text to vectorize. Defaults to 'text'.

    Returns:
        Dict[str, Any]: Metrics about the pipeline execution (status, elapsed_time, counts).
    """
    start_time = time.time()
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input data file not found: {file_path}")

    # 1. Initialize Clients
    db_manager = DuckDBManager(db_path=settings.DUCKDB_PATH)
    milvus_manager = MilvusManager(host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)

    try:
        # 2. Polars Lazy Data Ingestion & Transformation
        file_ext = os.path.splitext(file_path)[-1].lower()
        if file_ext == ".csv":
            lazy_frame = pl.scan_csv(file_path)
        elif file_ext in (".parquet", ".pq"):
            lazy_frame = pl.scan_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}. Use .csv or .parquet")

        # Select columns, drop rows with null text, and filter out empty text
        # Also clean whitespaces in the text column
        lazy_frame = (
            lazy_frame
            .drop_nulls(subset=[text_column])
            .filter(pl.col(text_column).str.strip_chars() != "")
        )

        # Collect data in-memory after lazy execution optimization
        df = lazy_frame.collect()
        num_rows = df.height

        if num_rows == 0:
            return {
                "status": "success",
                "message": "Pipeline completed successfully with 0 valid rows.",
                "rows_processed": 0,
                "vectors_inserted": 0,
                "elapsed_seconds": round(time.time() - start_time, 4)
            }

        # 3. Vector Embeddings Generation (Mocking 768-dim float array)
        # We mock this efficiently using standard library random tools
        mock_vectors = [
            [random.uniform(-1.0, 1.0) for _ in range(768)] 
            for _ in range(num_rows)
        ]
        
        # Inject the mock vectors into the Polars DataFrame
        df = df.with_columns(
            pl.Series(name="vector", values=mock_vectors, dtype=pl.List(pl.Float32))
        )

        # 4. Ingest Tabular Data into DuckDB
        # We explicitly register the Polars DataFrame with the DuckDB connection
        # to ensure zero-copy loading without scoping or name resolution issues.
        db_manager.conn.register("df_pipeline_temp", df)
        
        # Create a table and append data
        db_manager.conn.execute(
            f"CREATE TABLE IF NOT EXISTS {collection_name} AS SELECT * FROM df_pipeline_temp WHERE 1=0"
        )
        db_manager.conn.execute(
            f"INSERT INTO {collection_name} SELECT * FROM df_pipeline_temp"
        )
        db_manager.conn.unregister("df_pipeline_temp")

        # 5. Load Vector Embeddings & Text into Milvus
        # We define/initialize the collection (will overwrite if exists)
        milvus_manager.create_vector_collection(collection_name=collection_name, dim=768)
        
        # Prepare data for insertion (Milvus expects a list of dictionaries with matching keys)
        # We isolate 'text' and 'vector' columns
        milvus_df = df.select([text_column, "vector"]).rename({text_column: "text"})
        milvus_records = milvus_df.to_dicts()
        
        # Perform insertion in Milvus
        milvus_res = milvus_manager.insert_data(
            collection_name=collection_name, 
            data=milvus_records
        )

        elapsed_time = round(time.time() - start_time, 4)
        
        return {
            "status": "success",
            "message": "Data Pipeline executed successfully.",
            "rows_processed": num_rows,
            "vectors_inserted": milvus_res["insert_count"],
            "elapsed_seconds": elapsed_time
        }

    except Exception as e:
        raise RuntimeError(f"Pipeline execution failed: {e}")

    finally:
        # Guarantee resources are cleaned up
        db_manager.close()
