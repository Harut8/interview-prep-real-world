"""
Social Graph Service
Manage friend connections, suggestions, and graph queries.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    user_id: str
    name: str


class SocialGraph:
    """Manages a social graph of friendships and queries."""

    def __init__(self) -> None:
        # Adjacency list: user_id -> set of friend user_ids
        self.friendships: dict[str, set[str]] = {}
        self.users: dict[str, User] = {}
        self.blocked: dict[str, set[str]] = {}  # user_id -> set of blocked user_ids

    def add_user(self, user: User) -> None:
        self.users[user.user_id] = user
        if user.user_id not in self.friendships:
            self.friendships[user.user_id] = set()

    def add_friendship(self, user_a: str, user_b: str) -> bool:
        """Add bidirectional friendship. Returns False if either user doesn't exist."""
        if user_a not in self.users or user_b not in self.users:
            return False
        if user_a == user_b:
            return False
        self.friendships[user_a].add(user_b)
        self.friendships[user_b].add(user_a)
        return True

    def remove_friendship(self, user_a: str, user_b: str) -> bool:
        """Remove friendship between two users.

        BUG: Only removes one direction of the friendship.
        """
        if user_a not in self.friendships or user_b not in self.friendships:
            return False
        if user_b not in self.friendships[user_a]:
            return False
        # BUG: Only removes user_b from user_a's friends, not the reverse
        self.friendships[user_a].discard(user_b)
        return True

    def get_friends(self, user_id: str) -> set[str]:
        return self.friendships.get(user_id, set()).copy()

    def get_mutual_friends(self, user_a: str, user_b: str) -> set[str]:
        """Return mutual friends between two users.

        BUG: Includes one of the users themselves in the intersection.
        """
        friends_a = self.friendships.get(user_a, set())
        friends_b = self.friendships.get(user_b, set())
        # BUG: union with {user_a} before intersection inflates count
        mutual = (friends_a | {user_a}) & friends_b
        return mutual

    def get_friends_of_friends(self, user_id: str) -> set[str]:
        """Return friends-of-friends (2nd degree connections).

        Excludes direct friends and the user themselves.

        BUG: Does not track visited nodes, causing infinite cycle
        when mutual friendships create loops.
        """
        direct_friends = self.friendships.get(user_id, set())
        fof: set[str] = set()

        # BUG: No visited tracking — if A->B->A->B... it loops
        queue = list(direct_friends)
        while queue:
            friend = queue.pop(0)
            second_degree = self.friendships.get(friend, set())
            for fof_user in second_degree:
                if fof_user != user_id and fof_user not in direct_friends:
                    fof.add(fof_user)
                    # BUG: keeps adding to queue without checking visited
                    queue.append(fof_user)
        return fof

    def suggest_friends(self, user_id: str, limit: int = 10) -> list[tuple[str, int]]:
        """Suggest friends based on mutual connection count.

        Returns list of (user_id, mutual_count) sorted by mutual count descending.
        Excludes existing friends, blocked users, and the user themselves.

        TODO: Implement this method.
        """
        return []

    def degrees_of_separation(self, user_a: str, user_b: str) -> int:
        """Find shortest path length between two users using BFS.

        Returns -1 if no path exists.

        TODO: Implement this method.
        """
        return -1

    def block_user(self, blocker: str, blocked: str) -> None:
        """Block a user. Removes any existing friendship.

        TODO: Implement blocking logic.
        """
        pass

    def is_blocked(self, user_a: str, user_b: str) -> bool:
        """Check if user_a has blocked user_b."""
        return user_b in self.blocked.get(user_a, set())
