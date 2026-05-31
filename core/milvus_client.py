# lean-data-kit/core/milvus_client.py
"""
Milvus Vector DB Client Manager.
Handles collections, schema declarations, HNSW indexing, and vector data insertions.
"""

from typing import List, Dict, Any, Optional
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection
)


class MilvusManager:
    """
    Manages connections and operations on Milvus Vector Database.
    """

    def __init__(self, host: str = "localhost", port: int = 19530):
        """
        Initialize the Milvus manager and establish connection.

        Args:
            host (str): Milvus standalone server host. Defaults to 'localhost'.
            port (int): Milvus standalone server port. Defaults to 19530.
        """
        self.host: str = host
        self.port: int = port
        self.connect()

    def connect(self) -> None:
        """
        Establish a connection to the Milvus standalone instance.
        """
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=str(self.port)
            )
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Milvus standalone at {self.host}:{self.port}. "
                f"Ensure Milvus service is running. Error: {e}"
            )

    def create_vector_collection(self, collection_name: str, dim: int = 768) -> Collection:
        """
        Creates a collection with auto-increment ID, text, and float vector fields.
        Builds an HNSW index on the vector field and loads it into memory.

        Args:
            collection_name (str): Name of the collection to create.
            dim (int): Vector dimension size. Defaults to 768.

        Returns:
            Collection: The created PyMilvus Collection object.
        """
        try:
            # Check if the collection already exists and drop it for clean setup
            if utility.has_collection(collection_name):
                utility.drop_collection(collection_name)

            # Declare fields: id (Primary Key, auto ID), text, and vector
            fields = [
                FieldSchema(
                    name="id", 
                    dtype=DataType.INT64, 
                    is_primary=True, 
                    auto_id=True, 
                    description="Auto-generated Int64 primary key"
                ),
                FieldSchema(
                    name="text", 
                    dtype=DataType.VARCHAR, 
                    max_length=65535, 
                    description="Associated text content"
                ),
                FieldSchema(
                    name="vector", 
                    dtype=DataType.FLOAT_VECTOR, 
                    dim=dim, 
                    description="High-dimensional embedding vector"
                )
            ]

            schema = CollectionSchema(
                fields=fields, 
                description=f"Lean Data Kit Vector collection: {collection_name}"
            )
            
            # Create the collection
            collection = Collection(name=collection_name, schema=schema)

            # Define index parameters for HNSW (Highly Optimized Single-node search)
            index_params = {
                "metric_type": "L2",
                "index_type": "HNSW",
                "params": {
                    "M": 16,            # Max connections per node in graph
                    "efConstruction": 64 # Size of dynamic candidate list for index building
                }
            }

            # Create the index
            collection.create_index(field_name="vector", index_params=index_params)
            
            # Load collection to memory for search operations
            collection.load()
            return collection

        except Exception as e:
            raise RuntimeError(f"Failed to create collection '{collection_name}': {e}")

    def insert_data(self, collection_name: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Inserts structured dictionaries of records into the Milvus collection.

        Args:
            collection_name (str): Name of the target collection.
            data (List[Dict[str, Any]]): Data records, each containing 'text' and 'vector'.

        Returns:
            Dict[str, Any]: Status containing inserted count and auto-generated IDs.
        """
        if not data:
            return {"insert_count": 0, "primary_keys": []}

        try:
            if not utility.has_collection(collection_name):
                raise ValueError(f"Collection '{collection_name}' does not exist. Call create_vector_collection first.")

            collection = Collection(name=collection_name)
            
            # Extract columns (excluding id as auto_id is True)
            texts = [record["text"] for record in data]
            vectors = [record["vector"] for record in data]

            # Ingest list of columns
            mr = collection.insert([texts, vectors])
            
            # Flush memory index changes to disk
            collection.flush()
            
            return {
                "insert_count": mr.insert_count,
                "primary_keys": mr.primary_keys
            }
        except Exception as e:
            raise RuntimeError(f"Error inserting vector data into Milvus: {e}")
