"""
Caching layer for knowledge graph queries.
Reduces repeated database queries for performance optimization.
"""

import hashlib
from typing import Dict, List, Any, Optional
from time import time


class QueryCache:
    """Simple in-memory cache for query results."""

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize query cache.

        Args:
            ttl_seconds: Time-to-live for cached entries in seconds
        """
        self.cache: Dict[str, tuple] = {}
        self.ttl_seconds = ttl_seconds

    def _generate_key(self, query: str, params: Dict[str, Any]) -> str:
        """
        Generate cache key from query and parameters.

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            Hash key for caching
        """
        key_str = f"{query}:{sorted(params.items())}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, query: str, params: Dict[str, Any]) -> Optional[List[Dict]]:
        """
        Get cached query result if available and not expired.

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            Cached results or None if not found/expired
        """
        key = self._generate_key(query, params)

        if key in self.cache:
            result, timestamp = self.cache[key]
            if time() - timestamp < self.ttl_seconds:
                return result
            else:
                del self.cache[key]

        return None

    def set(self, query: str, params: Dict[str, Any], result: List[Dict]) -> None:
        """
        Cache query result.

        Args:
            query: Cypher query string
            params: Query parameters
            result: Query results to cache
        """
        key = self._generate_key(query, params)
        self.cache[key] = (result, time())

    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()

    def size(self) -> int:
        """Get number of cached entries."""
        return len(self.cache)

    def cleanup_expired(self) -> None:
        """Remove expired cache entries."""
        current_time = time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.ttl_seconds
        ]

        for key in expired_keys:
            del self.cache[key]
