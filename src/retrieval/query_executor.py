"""
Centralized query execution for knowledge graph operations.
Handles database connectivity, caching, and error handling.
"""

from typing import Dict, List, Any, Optional
from langchain_community.graphs import Neo4jGraph

from src.utils.config import config
from src.utils.logger import get_logger
from src.utils.exceptions import QueryError, DatabaseError
from src.kg.query_cache import QueryCache

logger = get_logger(__name__)


class QueryExecutor:
    """Centralized executor for Neo4j queries with caching support."""

    def __init__(
        self,
        uri: str = None,
        username: str = None,
        password: str = None,
        enable_cache: bool = True,
        cache_ttl: int = 3600
    ):
        """
        Initialize query executor.

        Args:
            uri: Neo4j connection URI (defaults to config.NEO4J_URI)
            username: Neo4j username (defaults to config.NEO4J_USERNAME)
            password: Neo4j password (defaults to config.NEO4J_PASSWORD)
            enable_cache: Enable query result caching
            cache_ttl: Cache time-to-live in seconds
        """
        self.uri = uri or config.NEO4J_URI
        self.username = username or config.NEO4J_USERNAME
        self.password = password or config.NEO4J_PASSWORD
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl

        self.cache = QueryCache(ttl_seconds=cache_ttl) if enable_cache else None
        self.graph: Optional[Neo4jGraph] = None

        self._initialize_graph()

    def _initialize_graph(self) -> None:
        """Initialize Neo4j graph connection."""
        try:
            self.graph = Neo4jGraph(
                url=self.uri,
                username=self.username,
                password=self.password,
                refresh_schema=False
            )
            logger.info("Neo4j graph connection established successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j graph: {e}")
            raise DatabaseError(f"Could not connect to Neo4j: {str(e)}")

    def execute(
        self,
        query: str,
        params: Dict[str, Any] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query with optional caching.

        Args:
            query: Cypher query string
            params: Query parameters
            use_cache: Whether to use caching for this query

        Returns:
            List of result dictionaries

        Raises:
            QueryError: If query execution fails
        """
        if params is None:
            params = {}

        if use_cache and self.cache:
            cached_result = self.cache.get(query, params)
            if cached_result is not None:
                logger.debug(f"Query cache hit (params: {params})")
                return cached_result

        try:
            logger.debug(f"Executing query (params: {params})")
            results = self.graph.query(query, params)

            if use_cache and self.cache:
                self.cache.set(query, params, results)

            return results

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryError(f"Failed to execute query: {str(e)}")

    def execute_write(
        self,
        query: str,
        params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a write query (don't cache).

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            List of result dictionaries
        """
        return self.execute(query, params, use_cache=False)

    def clear_cache(self) -> None:
        """Clear all cached query results."""
        if self.cache:
            self.cache.clear()
            logger.info("Query cache cleared")

    def cleanup_expired_cache(self) -> None:
        """Clean up expired cache entries."""
        if self.cache:
            self.cache.cleanup_expired()
            logger.debug(f"Cache cleanup completed. Cache size: {self.cache.size()}")

    def close(self) -> None:
        """Close database connection."""
        if self.graph:
            try:
                self.graph._driver.close()
                logger.info("Neo4j connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


_global_executor: Optional[QueryExecutor] = None


def get_query_executor() -> QueryExecutor:
    """
    Get or create global query executor instance.

    Returns:
        QueryExecutor instance
    """
    global _global_executor
    if _global_executor is None:
        _global_executor = QueryExecutor()
    return _global_executor


def reset_query_executor() -> None:
    """Reset global query executor (useful for testing)."""
    global _global_executor
    if _global_executor:
        _global_executor.close()
    _global_executor = None
