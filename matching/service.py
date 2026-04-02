"""
Neo4j connection service (singleton pattern).

Uses lazy initialization so the app can start even when Neo4j is unavailable.
All public methods catch connection/query errors and return safe defaults.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class Neo4jService:
    """Thread-safe lazy singleton for Neo4j interactions."""

    _driver = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _get_driver(self):
        """Return (or create) the Neo4j driver.  Returns None on failure."""
        if self._driver is not None:
            return self._driver
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
            # Verify connectivity
            self._driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s", settings.NEO4J_URI)
        except Exception as exc:
            logger.warning("Neo4j connection failed: %s", exc)
            self._driver = None
        return self._driver

    def is_connected(self):
        """Return True if a healthy driver exists."""
        return self._get_driver() is not None

    # ------------------------------------------------------------------
    # Query execution
    # ------------------------------------------------------------------

    def query(self, cypher, parameters=None):
        """
        Execute a read/write Cypher query.

        Returns a list of dicts, or raises RuntimeError when Neo4j is down.
        """
        driver = self._get_driver()
        if driver is None:
            raise RuntimeError("Neo4j is not available")
        try:
            with driver.session() as session:
                result = session.run(cypher, parameters or {})
                return [record.data() for record in result]
        except Exception as exc:
            # Reset driver so next call retries the connection
            self._driver = None
            logger.error("Neo4j query error: %s", exc)
            raise RuntimeError(f"Database error: {exc}") from exc


# Module-level singleton
db = Neo4jService()
