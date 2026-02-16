"""
User Privacy Settings Manager
Manage complex privacy rules for profile visibility and content access.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Optional


class Audience(IntEnum):
    """Privacy audience levels, ordered from most to least restrictive."""
    ONLY_ME = 0
    FRIENDS = 1
    FRIENDS_OF_FRIENDS = 2
    PUBLIC = 3


class PrivacyField(Enum):
    PROFILE_PHOTO = "profile_photo"
    FRIEND_LIST = "friend_list"
    POSTS = "posts"
    EMAIL = "email"
    PHONE = "phone"
    BIO = "bio"


@dataclass
class UserProfile:
    user_id: str
    name: str
    email: str = ""
    phone: str = ""
    bio: str = ""
    friends: set[str] = field(default_factory=set)
    groups: list[str] = field(default_factory=list)  # group IDs
    blocked_users: set[str] = field(default_factory=set)


@dataclass
class PostItem:
    post_id: str
    author_id: str
    content: str
    audience: Audience
    created_at: float = field(default_factory=time.time)


@dataclass
class PrivacySettings:
    """Privacy settings for a user or group."""
    settings: dict[PrivacyField, Audience] = field(default_factory=dict)

    def get(self, field_name: PrivacyField, default: Audience = Audience.PUBLIC) -> Audience:
        return self.settings.get(field_name, default)

    def set(self, field_name: PrivacyField, audience: Audience) -> None:
        self.settings[field_name] = audience


class PrivacyManager:
    """Manages user privacy settings and access control."""

    PRESETS: dict[str, dict[PrivacyField, Audience]] = {
        "strict": {
            PrivacyField.PROFILE_PHOTO: Audience.FRIENDS,
            PrivacyField.FRIEND_LIST: Audience.ONLY_ME,
            PrivacyField.POSTS: Audience.FRIENDS,
            PrivacyField.EMAIL: Audience.ONLY_ME,
            PrivacyField.PHONE: Audience.ONLY_ME,
            PrivacyField.BIO: Audience.FRIENDS,
        },
        "moderate": {
            PrivacyField.PROFILE_PHOTO: Audience.PUBLIC,
            PrivacyField.FRIEND_LIST: Audience.FRIENDS,
            PrivacyField.POSTS: Audience.FRIENDS_OF_FRIENDS,
            PrivacyField.EMAIL: Audience.FRIENDS,
            PrivacyField.PHONE: Audience.ONLY_ME,
            PrivacyField.BIO: Audience.PUBLIC,
        },
        "open": {
            PrivacyField.PROFILE_PHOTO: Audience.PUBLIC,
            PrivacyField.FRIEND_LIST: Audience.PUBLIC,
            PrivacyField.POSTS: Audience.PUBLIC,
            PrivacyField.EMAIL: Audience.PUBLIC,
            PrivacyField.PHONE: Audience.FRIENDS,
            PrivacyField.BIO: Audience.PUBLIC,
        },
    }

    def __init__(self) -> None:
        self.users: dict[str, UserProfile] = {}
        self.user_settings: dict[str, PrivacySettings] = {}
        self.group_settings: dict[str, PrivacySettings] = {}
        self.posts: dict[str, PostItem] = {}

    def add_user(self, profile: UserProfile) -> None:
        self.users[profile.user_id] = profile
        self.user_settings[profile.user_id] = PrivacySettings()

    def add_post(self, post: PostItem) -> None:
        self.posts[post.post_id] = post

    def set_group_privacy(self, group_id: str, settings: PrivacySettings) -> None:
        self.group_settings[group_id] = settings

    def set_user_privacy(self, user_id: str, field_name: PrivacyField,
                         audience: Audience) -> None:
        if user_id not in self.user_settings:
            self.user_settings[user_id] = PrivacySettings()
        self.user_settings[user_id].set(field_name, audience)

    def get_effective_privacy(self, user_id: str, field_name: PrivacyField) -> Audience:
        """Get effective privacy setting, considering group inheritance.

        Priority: user setting > group setting > default (PUBLIC).

        BUG: Group settings are completely ignored. Only user settings are returned.
        """
        user_priv = self.user_settings.get(user_id)
        if user_priv and field_name in user_priv.settings:
            return user_priv.get(field_name)

        # BUG: Group settings should be checked here, but they're skipped.
        # Should iterate through user's groups and use the most restrictive group setting.
        return Audience.PUBLIC

    def _are_friends(self, user_a: str, user_b: str) -> bool:
        """Check if two users are direct friends."""
        profile_a = self.users.get(user_a)
        if profile_a is None:
            return False
        return user_b in profile_a.friends

    def _are_friends_of_friends(self, user_a: str, user_b: str) -> bool:
        """Check if user_b is a friend-of-friend of user_a.

        BUG: Only checks direct friends, not second-degree connections.
        """
        # BUG: This just checks direct friendship again
        return self._are_friends(user_a, user_b)

    def can_view(self, viewer_id: str, owner_id: str,
                 field_name: PrivacyField) -> bool:
        """Check if viewer can see owner's field based on privacy settings.

        BUG: Does not check block list for content access.
        """
        if viewer_id == owner_id:
            return True

        # BUG: Should check if owner has blocked viewer, but this check is missing
        audience = self.get_effective_privacy(owner_id, field_name)

        if audience == Audience.PUBLIC:
            return True
        if audience == Audience.FRIENDS:
            return self._are_friends(owner_id, viewer_id)
        if audience == Audience.FRIENDS_OF_FRIENDS:
            return (self._are_friends(owner_id, viewer_id)
                    or self._are_friends_of_friends(owner_id, viewer_id))
        if audience == Audience.ONLY_ME:
            return False
        return False

    def can_view_post(self, viewer_id: str, post_id: str) -> bool:
        """Check if viewer can see a specific post."""
        post = self.posts.get(post_id)
        if post is None:
            return False
        if viewer_id == post.author_id:
            return True

        # BUG: Does not check block list
        owner = self.users.get(post.author_id)
        if owner is None:
            return False

        if post.audience == Audience.PUBLIC:
            return True
        if post.audience == Audience.FRIENDS:
            return self._are_friends(post.author_id, viewer_id)
        if post.audience == Audience.FRIENDS_OF_FRIENDS:
            return (self._are_friends(post.author_id, viewer_id)
                    or self._are_friends_of_friends(post.author_id, viewer_id))
        return False

    def block_user(self, blocker_id: str, blocked_id: str) -> None:
        """Block a user."""
        if blocker_id in self.users:
            self.users[blocker_id].blocked_users.add(blocked_id)
            # Also remove from friends
            self.users[blocker_id].friends.discard(blocked_id)
            if blocked_id in self.users:
                self.users[blocked_id].friends.discard(blocker_id)

    def apply_preset(self, user_id: str, preset_name: str) -> bool:
        """Apply a privacy preset to a user.

        TODO: Implement preset application.
        """
        return False

    def export_user_data(self, user_id: str) -> dict[str, Any] | None:
        """Export all user data for GDPR compliance.

        Returns dict with profile info, posts, privacy settings.

        TODO: Implement data export.
        """
        return None

    def get_audience_list(self, post_id: str) -> list[str]:
        """Return list of user IDs who can see the given post.

        TODO: Implement audience computation.
        """
        return []
