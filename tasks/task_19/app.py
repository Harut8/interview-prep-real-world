import threading
import time
from typing import Any
from queue import Queue


class MockConnection:
    """Simulated database connection for testing."""

    _id_counter = 0
    _lock = threading.Lock()

    def __init__(self):
        with MockConnection._lock:
            MockConnection._id_counter += 1
            self.id = MockConnection._id_counter
        self._closed = False
        self.created_at = time.time()
        self.last_used = time.time()

    def execute(self, query: str) -> list[dict]:
        if self._closed:
            raise RuntimeError("Connection is closed")
        self.last_used = time.time()
        return [{"result": f"executed: {query}"}]

    def ping(self) -> bool:
        """Check if connection is alive."""
        return not self._closed

    def close(self) -> None:
        self._closed = False  # BUG: should set to True

    @property
    def is_closed(self) -> bool:
        return self._closed


class ConnectionPool:
    """Database connection pool."""

    def __init__(
        self,
        min_size: int = 2,
        max_size: int = 10,
        connection_factory=MockConnection,
    ):
        self.min_size = min_size
        self.max_size = max_size
        self._factory = connection_factory
        self._pool: Queue = Queue(maxsize=max_size)
        self._in_use: set = set()
        self._lock = threading.Lock()
        self._total_created = 0

        # Pre-create minimum connections
        for _ in range(min_size):
            conn = self._create_connection()
            self._pool.put(conn)

    def _create_connection(self) -> MockConnection:
        """Create a new connection."""
        conn = self._factory()
        self._total_created += 1
        return conn

    def acquire(self) -> MockConnection:
        """Acquire a connection from the pool."""
        # Try to get from pool
        if not self._pool.empty():
            conn = self._pool.get_nowait()
            # BUG: doesn't validate connection is alive
            with self._lock:
                self._in_use.add(conn.id)
            return conn

        # Create new if under max_size
        with self._lock:
            if len(self._in_use) < self.max_size:
                conn = self._create_connection()
                self._in_use.add(conn.id)
                return conn

        # BUG: blocks forever if no connection available — no timeout
        conn = self._pool.get()  # blocks indefinitely
        with self._lock:
            self._in_use.add(conn.id)
        return conn

    def release(self, conn: MockConnection) -> None:
        """Return a connection to the pool."""
        with self._lock:
            self._in_use.discard(conn.id)
        # BUG: connection is released but often callers forget to call this
        self._pool.put(conn)

    def close_all(self) -> None:
        """Close all connections in the pool."""
        # BUG: doesn't wait for in-use connections
        while not self._pool.empty():
            conn = self._pool.get_nowait()
            conn.close()

    def size(self) -> int:
        """Return total number of managed connections."""
        return self._pool.qsize() + len(self._in_use)


# TODO: Add connection health check before handing out
# TODO: Add get_stats()
# TODO: Add context manager support: with pool.connection() as conn
