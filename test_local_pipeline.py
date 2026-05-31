# lean-data-kit/test_local_pipeline.py
"""
Local Trial Run & Dry-Run Script.
Mocks Milvus connections to verify the Polars Lazy ETL and DuckDB zero-copy ingestion
natively without requiring external database services.
"""

import os
import sys
import unittest.mock as mock
import polars as pl

# Add current folder to python path to ensure direct imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from core.duckdb_client import DuckDBManager
from pipelines.data_pipeline import run_etl_and_vectorize


def create_sample_data() -> str:
    """
    Generates a sample CSV file with clean, null, and empty rows for testing.
    """
    print("Generating sample CSV data...")
    df = pl.DataFrame({
        "id": [1, 2, 3, 4, 5, 6],
        "text": [
            "Medium-scale data processing boilerplate without the distributed overhead",
            "Leveraging DuckDB and Polars to achieve absolute RAM optimization",
            "Enforced PyMilvus client integration for vector database operations",
            "Clean codebase with complete type hints and strict error handling",
            " ",   # Will be filtered out (whitespace only)
            None   # Will be dropped (null text)
        ],
        "category": ["A", "B", "A", "C", "D", "A"]
    })
    csv_path = os.path.join(current_dir, "sample_test_data.csv")
    df.write_csv(csv_path)
    print(f"Sample data written to: {csv_path}")
    return csv_path


def run_dry_run() -> None:
    """
    Executes the dry-run pipeline, displaying intermediate operations and outputs.
    """
    csv_path = create_sample_data()
    test_db_path = os.path.join(current_dir, "test_run.duckdb")
    
    print("\n--- Starting Dry-Run Trial (Mocking Milvus Connection) ---")
    
    # Mock MilvusManager to allow testing on machine without a running docker daemon
    with mock.patch("pipelines.data_pipeline.MilvusManager") as MockMilvusClass:
        # Mock instance insert return values
        mock_instance = MockMilvusClass.return_value
        mock_instance.insert_data.return_value = {
            "insert_count": 4,  # Expect 4 valid rows (2 filtered out)
            "primary_keys": [101, 102, 103, 104]
        }
        
        # Override DuckDB path to test_run.duckdb
        from core.config import settings
        settings.DUCKDB_PATH = test_db_path
        
        print("Executing ETL pipeline...")
        try:
            result = run_etl_and_vectorize(
                file_path=csv_path,
                collection_name="test_collection",
                text_column="text"
            )
            
            print("\n--- Pipeline Execution Output ---")
            print(f"Status: {result['status']}")
            print(f"Processed Rows: {result['rows_processed']} (Expected: 4)")
            print(f"Vectors Inserted (Mock Milvus): {result['vectors_inserted']}")
            print(f"Time Taken: {result['elapsed_seconds']} seconds")
            
            # Verify DuckDB content
            print("\n--- Verifying Tabular Data inside DuckDB ---")
            db = DuckDBManager(test_db_path)
            res_df = db.execute_query(
                "SELECT id, text, category, LENGTH(vector) as vector_dim FROM test_collection"
            )
            print(res_df)
            db.close()
            
        except Exception as e:
            print(f"\n[ERROR] Pipeline run failed: {e}")
            
        finally:
            # Cleanup temporary testing files
            print("\nCleaning up temporary files...")
            if os.path.exists(csv_path):
                os.remove(csv_path)
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
            print("Cleanup done. Trial run complete!")


if __name__ == "__main__":
    run_dry_run()
