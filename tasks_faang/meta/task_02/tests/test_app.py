"""Tests for Social Graph Service."""

import pytest
from app import SocialGraph, User


@pytest.fixture
def graph() -> SocialGraph:
    g = SocialGraph()
    for uid in ["alice", "bob", "carol", "dave", "eve", "frank"]:
        g.add_user(User(uid, uid.capitalize()))
    # alice - bob - carol - dave
    #           \         /
    #            eve ----
    g.add_friendship("alice", "bob")
    g.add_friendship("bob", "carol")
    g.add_friendship("bob", "eve")
    g.add_friendship("carol", "dave")
    g.add_friendship("eve", "dave")
    return g


class TestFriendship:
    def test_add_friendship(self, graph: SocialGraph):
        """PASSING: Adding friendship should be bidirectional."""
        assert "bob" in graph.get_friends("alice")
        assert "alice" in graph.get_friends("bob")

    def test_remove_friendship_bidirectional(self, graph: SocialGraph):
        """FAILING: Removing friendship should remove both directions.

        Bug: Only one direction is removed.
        """
        graph.remove_friendship("alice", "bob")
        assert "bob" not in graph.get_friends("alice"), "bob should not be alice's friend"
        assert "alice" not in graph.get_friends("bob"), "alice should not be bob's friend"

    def test_self_friendship_rejected(self, graph: SocialGraph):
        """PASSING: Cannot be friends with yourself."""
        result = graph.add_friendship("alice", "alice")
        assert result is False


class TestMutualFriends:
    def test_mutual_friends_correct(self, graph: SocialGraph):
        """FAILING: Mutual friends count should not include the users themselves.

        Bug: One of the queried users is included in the mutual set.
        """
        # alice and carol have bob as mutual friend (only)
        mutual = graph.get_mutual_friends("alice", "carol")
        assert mutual == {"bob"}, f"Expected {{'bob'}}, got {mutual}"

    def test_mutual_friends_none(self, graph: SocialGraph):
        """PASSING: Users with no mutual friends should return empty set."""
        mutual = graph.get_mutual_friends("alice", "dave")
        # alice is friends with bob; dave is friends with carol, eve
        # They share no direct friends
        assert len(mutual) == 0 or mutual == set()


class TestFriendsOfFriends:
    def test_fof_no_infinite_loop(self, graph: SocialGraph):
        """FAILING: FoF query should not hang due to cycles.

        Bug: No visited tracking causes infinite loop.
        """
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("FoF query took too long — likely infinite loop")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(3)  # 3 second timeout
        try:
            fof = graph.get_friends_of_friends("alice")
            # alice's direct friends: bob
            # bob's friends: alice, carol, eve -> FoF = carol, eve
            assert "carol" in fof
            assert "eve" in fof
            assert "bob" not in fof  # direct friend, excluded
            assert "alice" not in fof  # self, excluded
        finally:
            signal.alarm(0)

    def test_fof_excludes_direct_friends(self, graph: SocialGraph):
        """PASSING (if loop bug fixed): FoF should not include direct friends."""
        # Need loop fix first for this to work
        pass


class TestFriendSuggestions:
    def test_suggest_by_mutual_count(self, graph: SocialGraph):
        """TODO: Friend suggestions based on mutual connections."""
        suggestions = graph.suggest_friends("alice", limit=5)
        # alice is friends with bob
        # carol is FoF (mutual: bob), eve is FoF (mutual: bob)
        # dave is 3rd degree via carol/eve
        suggested_ids = [uid for uid, count in suggestions]
        assert "carol" in suggested_ids
        assert "eve" in suggested_ids
        assert "bob" not in suggested_ids  # already a friend

    def test_suggest_excludes_blocked(self, graph: SocialGraph):
        """TODO: Blocked users should not appear in suggestions."""
        graph.block_user("alice", "carol")
        suggestions = graph.suggest_friends("alice", limit=5)
        suggested_ids = [uid for uid, count in suggestions]
        assert "carol" not in suggested_ids


class TestDegreesOfSeparation:
    def test_direct_friends_degree_1(self, graph: SocialGraph):
        """TODO: Direct friends should have degree 1."""
        assert graph.degrees_of_separation("alice", "bob") == 1

    def test_fof_degree_2(self, graph: SocialGraph):
        """TODO: Friends of friends should have degree 2."""
        assert graph.degrees_of_separation("alice", "carol") == 2

    def test_no_path(self, graph: SocialGraph):
        """TODO: Disconnected users should return -1."""
        graph.add_user(User("isolated", "Isolated"))
        assert graph.degrees_of_separation("alice", "isolated") == -1


class TestBlocking:
    def test_block_removes_friendship(self, graph: SocialGraph):
        """TODO: Blocking should remove existing friendship."""
        graph.block_user("alice", "bob")
        assert "bob" not in graph.get_friends("alice")
        assert "alice" not in graph.get_friends("bob")

    def test_blocked_cannot_add_friend(self, graph: SocialGraph):
        """TODO: Cannot add friendship with blocked user."""
        graph.block_user("alice", "frank")
        result = graph.add_friendship("alice", "frank")
        assert result is False
