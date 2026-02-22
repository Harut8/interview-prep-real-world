import random
from typing import Optional


class RandomizedSet:
    """Data structure supporting insert, delete, and getRandom in O(1)."""

    def __init__(self):
        self._list: list[int] = []
        self._index_map: dict[int, int] = {}  # value -> index in list

    def insert(self, val: int) -> bool:
        """Insert a value. Returns True if the value was inserted, False if already present."""
        # BUG: doesn't check for duplicates
        self._index_map[val] = len(self._list)
        self._list.append(val)
        return True

    def remove(self, val: int) -> bool:
        """Remove a value. Returns True if the value was removed, False if not present."""
        if val not in self._index_map:
            return False

        # BUG: doesn't swap with last element — just removes at index
        # This makes the list sparse and breaks O(1) getRandom
        idx = self._index_map[val]
        del self._index_map[val]
        self._list.pop(idx)

        # BUG: after pop, all indices after `idx` are shifted, but index_map is not updated
        return True

    def get_random(self) -> int:
        """Return a random element from the set."""
        # BUG: crashes with IndexError on empty set
        return random.choice(self._list)

    def size(self) -> int:
        """Return the number of elements in the set."""
        return len(self._list)

    def contains(self, val: int) -> bool:
        """Check if a value exists in the set."""
        return val in self._index_map

    def to_list(self) -> list[int]:
        """Return all elements as a list."""
        return list(self._list)


# TODO: Add get_random_weighted(weights) method
# TODO: Add bulk_insert(values) and bulk_remove(values) methods
# TODO: Add get_random_n(n) for n unique random elements
# TODO: Add __iter__, __len__, __contains__ dunder methods
# TODO: Add snapshot() and restore(snapshot) methods
