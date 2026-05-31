# lean-data-kit/core/duckdb_client.py
"""
DuckDB Database Client Manager.
Provides high-performance, in-memory SQL analytics and query execution,
returning results as PyArrow Tables or Polars DataFrames with zero-copy.
"""

import duckdb
import polars as pl
import pyarrow as pa
from typing import Union, Literal


class DuckDBManager:
    """
    Manages DuckDB connections and executes high-performance SQL queries.
    """

    def __init__(self, db_path: str):
        """
        Initialize the DuckDB manager with a path to the database file.
        Use ':memory:' for a transient, in-memory database.

        Args:
            db_path (str): Path to the DuckDB database file.
        """
        self.db_path: str = db_path
        try:
            # Connect to DuckDB database file (creates it if it does not exist)
            self.conn: duckdb.DuckDBPyConnection = duckdb.connect(database=self.db_path)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to DuckDB database at '{db_path}': {e}")

    def execute_query(
        self, 
        query: str, 
        return_format: Literal["polars", "arrow"] = "polars"
    ) -> Union[pl.DataFrame, pa.Table]:
        """
        Executes a SQL query and returns the results in the requested format.

        Args:
            query (str): The SQL query string to run.
            return_format (Literal["polars", "arrow"]): 'polars' or 'arrow'. Defaults to 'polars'.

        Returns:
            Union[pl.DataFrame, pa.Table]: Query results in the specified format.
        """
        if return_format not in ("polars", "arrow"):
            raise ValueError("return_format must be either 'polars' or 'arrow'")

        try:
            # Execute query and get relation object
            relation = self.conn.execute(query)
            
            if return_format == "polars":
                try:
                    # Attempt native conversion to Polars DataFrame
                    return relation.pl()
                except (AttributeError, Exception):
                    # Fallback through Arrow to Polars DataFrame
                    arrow_table: pa.Table = relation.arrow()
                    return pl.from_arrow(arrow_table)
            else:
                # Return PyArrow Table
                return relation.arrow()
        except Exception as e:
            raise RuntimeError(f"Error executing SQL query on DuckDB: {e}")

    def close(self) -> None:
        """
        Close the DuckDB connection safely.
        """
        try:
            self.conn.close()
        except Exception:
            pass
