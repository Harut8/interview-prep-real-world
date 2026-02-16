import pytest
import threading
from app import ConnectionPool, MockConnection


@pytest.fixture
def pool():
    p = ConnectionPool(min_size=2, max_size=5)
    yield p
    p.close_all()


def test_acquire_connection(pool):
    conn = pool.acquire()
    assert conn is not None
    assert isinstance(conn, MockConnection)
    pool.release(conn)


def test_min_size_preloaded(pool):
    assert pool.size() >= 2


# Tests that connections are reused
def test_connection_reuse(pool):
    conn1 = pool.acquire()
    conn_id = conn1.id
    pool.release(conn1)
    conn2 = pool.acquire()
    assert conn2.id == conn_id
    pool.release(conn2)


# Tests connection close bug
def test_connection_close():
    conn = MockConnection()
    conn.close()
    assert conn.is_closed is True  # FAILS due to close() bug


# Tests that pool doesn't hand out closed connections
def test_stale_connection_replaced(pool):
    conn = pool.acquire()
    conn.close()  # simulate broken connection
    pool.release(conn)
    conn2 = pool.acquire()
    assert conn2.ping() is True  # should get a healthy connection


# TODO: Add test for acquire timeout (no deadlock)
# TODO: Add test for context manager
# TODO: Add test for get_stats()
# TODO: Add test for concurrent acquire/release
# TODO: Add test for close_all waiting for in-use connections
