"""Tests for User Privacy Settings Manager."""

import pytest
from app import (
    PrivacyManager, UserProfile, PostItem, PrivacySettings,
    PrivacyField, Audience,
)


@pytest.fixture
def manager() -> PrivacyManager:
    m = PrivacyManager()
    # Create users: alice (friends with bob), bob (friends with alice, carol),
    # carol (friends with bob), dave (no friends)
    alice = UserProfile("alice", "Alice", friends={"bob"}, groups=["group1"])
    bob = UserProfile("bob", "Bob", friends={"alice", "carol"}, groups=["group1"])
    carol = UserProfile("carol", "Carol", friends={"bob"})
    dave = UserProfile("dave", "Dave")

    for u in [alice, bob, carol, dave]:
        m.add_user(u)

    return m


class TestGroupPrivacyInheritance:
    def test_group_settings_inherited(self, manager: PrivacyManager):
        """FAILING: Group privacy settings should be inherited when user has no override.

        Bug: Group settings are ignored entirely.
        """
        # Set group-level privacy
        group_settings = PrivacySettings()
        group_settings.set(PrivacyField.POSTS, Audience.FRIENDS)
        manager.set_group_privacy("group1", group_settings)

        # Alice has no user-level override for POSTS
        effective = manager.get_effective_privacy("alice", PrivacyField.POSTS)
        assert effective == Audience.FRIENDS, (
            f"Should inherit FRIENDS from group, got {effective}"
        )

    def test_user_overrides_group(self, manager: PrivacyManager):
        """PASSING (once group inheritance fixed): User settings should override group."""
        group_settings = PrivacySettings()
        group_settings.set(PrivacyField.POSTS, Audience.FRIENDS)
        manager.set_group_privacy("group1", group_settings)

        manager.set_user_privacy("alice", PrivacyField.POSTS, Audience.ONLY_ME)
        effective = manager.get_effective_privacy("alice", PrivacyField.POSTS)
        assert effective == Audience.ONLY_ME


class TestFriendsOfFriends:
    def test_fof_can_view(self, manager: PrivacyManager):
        """FAILING: Friends-of-friends should be able to view FoF content.

        Bug: FoF check only checks direct friends.
        """
        # alice -> bob -> carol, so carol is alice's FoF
        manager.set_user_privacy("alice", PrivacyField.POSTS, Audience.FRIENDS_OF_FRIENDS)
        assert manager.can_view("carol", "alice", PrivacyField.POSTS) is True, (
            "Carol (FoF of Alice via Bob) should be able to view"
        )

    def test_non_fof_cannot_view(self, manager: PrivacyManager):
        """PASSING: Non-connected user cannot view FoF content."""
        manager.set_user_privacy("alice", PrivacyField.POSTS, Audience.FRIENDS_OF_FRIENDS)
        assert manager.can_view("dave", "alice", PrivacyField.POSTS) is False


class TestBlocking:
    def test_blocked_cannot_view_content(self, manager: PrivacyManager):
        """FAILING: Blocked user should not see any content.

        Bug: Block check is missing from can_view and can_view_post.
        """
        manager.set_user_privacy("alice", PrivacyField.POSTS, Audience.PUBLIC)
        manager.add_post(PostItem("post1", "alice", "Hello world", Audience.PUBLIC))

        manager.block_user("alice", "bob")

        assert manager.can_view("bob", "alice", PrivacyField.POSTS) is False, (
            "Blocked user bob should not see alice's profile"
        )
        assert manager.can_view_post("bob", "post1") is False, (
            "Blocked user bob should not see alice's posts"
        )

    def test_blocking_removes_friendship(self, manager: PrivacyManager):
        """PASSING: Blocking should remove friendship."""
        manager.block_user("alice", "bob")
        assert "bob" not in manager.users["alice"].friends
        assert "alice" not in manager.users["bob"].friends


class TestPrivacyPresets:
    def test_apply_strict_preset(self, manager: PrivacyManager):
        """TODO: Apply strict preset to a user."""
        result = manager.apply_preset("alice", "strict")
        assert result is True
        assert manager.get_effective_privacy(
            "alice", PrivacyField.EMAIL
        ) == Audience.ONLY_ME
        assert manager.get_effective_privacy(
            "alice", PrivacyField.POSTS
        ) == Audience.FRIENDS

    def test_apply_open_preset(self, manager: PrivacyManager):
        """TODO: Apply open preset to a user."""
        result = manager.apply_preset("alice", "open")
        assert result is True
        assert manager.get_effective_privacy(
            "alice", PrivacyField.POSTS
        ) == Audience.PUBLIC

    def test_invalid_preset(self, manager: PrivacyManager):
        """TODO: Invalid preset name should return False."""
        result = manager.apply_preset("alice", "nonexistent")
        assert result is False


class TestDataExport:
    def test_export_user_data(self, manager: PrivacyManager):
        """TODO: Export all user data in structured format."""
        manager.add_post(PostItem("post1", "alice", "Hello", Audience.PUBLIC))
        manager.set_user_privacy("alice", PrivacyField.EMAIL, Audience.ONLY_ME)

        data = manager.export_user_data("alice")
        assert data is not None
        assert data["user_id"] == "alice"
        assert data["name"] == "Alice"
        assert "posts" in data
        assert len(data["posts"]) == 1
        assert "privacy_settings" in data

    def test_export_nonexistent_user(self, manager: PrivacyManager):
        """TODO: Export for nonexistent user returns None."""
        data = manager.export_user_data("nonexistent")
        assert data is None


class TestAudienceSelector:
    def test_audience_list_public(self, manager: PrivacyManager):
        """TODO: Public post should list all users."""
        manager.add_post(PostItem("post1", "alice", "Hello", Audience.PUBLIC))
        audience = manager.get_audience_list("post1")
        # All non-blocked users (everyone except alice herself in the viewer list)
        for uid in ["bob", "carol", "dave"]:
            assert uid in audience

    def test_audience_list_friends(self, manager: PrivacyManager):
        """TODO: Friends-only post should list only friends."""
        manager.add_post(PostItem("post2", "alice", "Private", Audience.FRIENDS))
        audience = manager.get_audience_list("post2")
        assert "bob" in audience
        assert "carol" not in audience
        assert "dave" not in audience
