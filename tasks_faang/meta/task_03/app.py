"""
Content Moderation Pipeline
Classify and moderate user-generated content.
"""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ModerationAction(Enum):
    NONE = "none"
    WARN = "warn"
    HIDE = "hide"
    REMOVE = "remove"


class AppealStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class ReviewStatus(Enum):
    AUTO_ACTIONED = "auto_actioned"
    QUEUED_FOR_REVIEW = "queued_for_review"
    NO_ACTION = "no_action"


@dataclass
class ModerationRule:
    rule_id: str
    name: str
    pattern: str  # regex pattern
    action: ModerationAction
    priority: int  # higher = more important
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class ContentItem:
    content_id: str
    author_id: str
    text: str
    created_at: float = field(default_factory=time.time)


@dataclass
class ModerationDecision:
    """Record of a moderation decision. Should be immutable after creation."""
    decision_id: str
    content_id: str
    rule_id: str
    action: ModerationAction
    timestamp: float
    reason: str
    # BUG: This is a regular dataclass, not frozen — fields can be mutated
    # after creation, breaking audit trail immutability.


@dataclass
class Appeal:
    appeal_id: str
    decision_id: str
    content_id: str
    author_id: str
    reason: str
    status: AppealStatus = AppealStatus.PENDING
    reviewed_at: Optional[float] = None


class ModerationPipeline:
    """Content moderation pipeline with rule evaluation and history."""

    def __init__(self) -> None:
        self.rules: list[ModerationRule] = []
        self.history: list[ModerationDecision] = []
        self.appeals: dict[str, Appeal] = {}
        self.content_actions: dict[str, ModerationAction] = {}

    def add_rule(self, rule: ModerationRule) -> None:
        self.rules.append(rule)

    def _match_rule(self, rule: ModerationRule, text: str) -> bool:
        """Check if content matches a moderation rule's regex pattern."""
        try:
            # BUG: No timeout for regex matching. Patterns with catastrophic
            # backtracking (e.g., (a+)+ or (a|a)*) will hang.
            # The pattern itself may also be poorly written.
            return bool(re.search(rule.pattern, text, re.IGNORECASE))
        except re.error:
            return False

    def evaluate(self, content: ContentItem) -> ModerationDecision | None:
        """Evaluate content against all moderation rules.

        Should apply only the highest-priority matching rule's action.

        BUG: All matching rules are applied, and the LAST one wins instead
        of the highest priority one.
        """
        matched_decisions: list[tuple[ModerationRule, ModerationDecision]] = []

        for rule in self.rules:
            if self._match_rule(rule, content.text):
                decision = ModerationDecision(
                    decision_id=str(uuid.uuid4()),
                    content_id=content.content_id,
                    rule_id=rule.rule_id,
                    action=rule.action,
                    timestamp=time.time(),
                    reason=f"Matched rule: {rule.name}",
                )
                matched_decisions.append((rule, decision))

        if not matched_decisions:
            return None

        # BUG: Takes the last matched rule instead of highest priority
        final_rule, final_decision = matched_decisions[-1]

        self.history.append(final_decision)
        self.content_actions[content.content_id] = final_decision.action
        return final_decision

    def evaluate_with_confidence(
        self, content: ContentItem
    ) -> tuple[ReviewStatus, ModerationDecision | None]:
        """Evaluate with confidence-based auto-moderation.

        - confidence > 0.9: auto-action
        - 0.5 <= confidence <= 0.9: queue for review
        - confidence < 0.5: no action

        TODO: Implement this method.
        """
        return ReviewStatus.NO_ACTION, None

    def bulk_moderate(
        self, content_items: list[ContentItem]
    ) -> list[ModerationDecision | None]:
        """Evaluate multiple content items at once.

        TODO: Implement bulk moderation.
        """
        return []

    def submit_appeal(
        self, decision_id: str, content_id: str, author_id: str, reason: str
    ) -> Appeal | None:
        """Submit an appeal for a moderation decision.

        TODO: Implement appeal submission.
        """
        return None

    def review_appeal(self, appeal_id: str, approved: bool) -> Appeal | None:
        """Review an appeal. If approved, reverse the moderation action.

        TODO: Implement appeal review.
        """
        return None

    def get_history(self, content_id: str | None = None) -> list[ModerationDecision]:
        """Get moderation history, optionally filtered by content_id."""
        if content_id:
            return [d for d in self.history if d.content_id == content_id]
        return list(self.history)
