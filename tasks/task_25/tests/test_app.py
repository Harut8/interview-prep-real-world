import pytest
from app import RandomizedSet


@pytest.fixture
def rset():
    return RandomizedSet()


def test_insert(rset):
    assert rset.insert(1) is True
    assert rset.contains(1) is True
    assert rset.size() == 1


# FAILS — fix: duplicate insert should return False
def test_insert_duplicate(rset):
    assert rset.insert(1) is True
    assert rset.insert(1) is False
    assert rset.size() == 1


def test_remove(rset):
    rset.insert(1)
    assert rset.remove(1) is True
    assert rset.contains(1) is False
    assert rset.size() == 0


def test_remove_nonexistent(rset):
    assert rset.remove(999) is False


# FAILS — fix: remove should use swap-and-pop
def test_remove_maintains_indices(rset):
    rset.insert(1)
    rset.insert(2)
    rset.insert(3)
    rset.remove(2)
    # After removing 2, set should have {1, 3} and getRandom should work
    assert rset.size() == 2
    assert rset.contains(1)
    assert rset.contains(3)
    assert not rset.contains(2)
    # Verify internal consistency
    for val in rset.to_list():
        assert rset.contains(val)


# FAILS — fix: getRandom on empty set
def test_get_random_empty(rset):
    with pytest.raises(ValueError):
        rset.get_random()


def test_get_random(rset):
    rset.insert(10)
    rset.insert(20)
    rset.insert(30)
    result = rset.get_random()
    assert result in {10, 20, 30}


def test_insert_remove_insert(rset):
    rset.insert(1)
    rset.remove(1)
    assert rset.insert(1) is True
    assert rset.size() == 1


# FAILS — fix: after multiple removes, internal state must be consistent
def test_multiple_removes_consistency(rset):
    for i in range(10):
        rset.insert(i)

    for i in range(0, 10, 2):  # remove evens
        rset.remove(i)

    assert rset.size() == 5
    for i in range(1, 10, 2):  # odds remain
        assert rset.contains(i)

    # Internal list should match index map
    assert len(rset._list) == len(rset._index_map)
    for val in rset._list:
        assert rset._index_map[val] == rset._list.index(val)


# TODO: Add tests for get_random_weighted
# TODO: Add tests for bulk_insert and bulk_remove
# TODO: Add tests for get_random_n
# TODO: Add tests for __iter__, __len__, __contains__
# TODO: Add tests for snapshot and restore
