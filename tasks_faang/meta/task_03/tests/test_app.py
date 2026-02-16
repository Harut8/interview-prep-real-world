"""Tests for Content Moderation Pipeline."""

import time
import signal
import pytest
from app import (
    ModerationPipeline, ModerationRule, ModerationAction,
    ContentItem, ModerationDecision, AppealStatus, ReviewStatus,
)


@pytest.fixture
def pipeline() -> ModerationPipeline:
    p = ModerationPipeline()
    # Low priority: warn on mild language
    p.add_rule(ModerationRule(
        rule_id="r1", name="Mild language",
        pattern=r"\b(darn|heck)\b",
        action=ModerationAction.WARN,
        priority=1,
    ))
    # High priority: remove hate speech
    p.add_rule(ModerationRule(
        rule_id="r2", name="Hate speech",
        pattern=r"\b(hate|kill)\b",
        action=ModerationAction.REMOVE,
        priority=10,
    ))
    # Medium priority: hide spam patterns
    p.add_rule(ModerationRule(
        rule_id="r3", name="Spam detection",
        pattern=r"(buy now|free money|click here)",
        action=ModerationAction.HIDE,
        priority=5,
    ))
    return p


class TestRulePriority:
    def test_highest_priority_wins(self, pipeline: ModerationPipeline):
        """FAILING: When multiple rules match, highest priority should win.

        Bug: Last matched rule wins instead of highest priority.
        """
        # This content matches both "hate" (priority 10) and "darn" (priority 1)
        content = ContentItem("c1", "user1", "I hate when people say darn")
        decision = pipeline.evaluate(content)
        assert decision is not None
        assert decision.action == ModerationAction.REMOVE, (
            f"Expected REMOVE (hate speech, priority 10), got {decision.action}"
        )
        assert decision.rule_id == "r2"

    def test_single_rule_match(self, pipeline: ModerationPipeline):
        """PASSING: Single rule match should work correctly."""
        content = ContentItem("c2", "user1", "Oh heck that is surprising")
        decision = pipeline.evaluate(content)
        assert decision is not None
        assert decision.action == ModerationAction.WARN


class TestRegexPerformance:
    def test_catastrophic_backtracking_safe(self):
        """FAILING: Regex with catastrophic backtracking should not hang.

        Bug: No protection against pathological regex patterns.
        """
        p = ModerationPipeline()
        # This pattern has catastrophic backtracking: (a+)+ against "aaa...!"
        p.add_rule(ModerationRule(
            rule_id="bad", name="Bad regex",
            pattern=r"(a+)+b",
            action=ModerationAction.REMOVE,
            priority=1,
        ))
        content = ContentItem("c1", "user1", "a" * 25 + "!")

        def timeout_handler(signum, frame):
            raise TimeoutError("Regex took too long — catastrophic backtracking")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(2)
        try:
            # Should not hang — either match quickly or give up
            result = p._match_rule(p.rules[0], content.text)
            assert result is False  # Does not match (no 'b' at end)
        except TimeoutError:
            pytest.fail("Regex matching hung due to catastrophic backtracking")
        finally:
            signal.alarm(0)


class TestHistoryImmutability:
    def test_decision_is_immutable(self, pipeline: ModerationPipeline):
        """FAILING: Moderation decisions should be immutable (frozen dataclass).

        Bug: ModerationDecision is a regular dataclass, fields can be changed.
        """
        content = ContentItem("c3", "user1", "I hate this")
        decision = pipeline.evaluate(content)
        assert decision is not None
        with pytest.raises(AttributeError):
            decision.action = ModerationAction.NONE  # Should raise if frozen


class TestAppealSystem:
    def test_submit_appeal(self, pipeline: ModerationPipeline):
        """TODO: Users should be able to appeal a moderation decision."""
        content = ContentItem("c4", "user1", "I hate mondays")
        decision = pipeline.evaluate(content)
        assert decision is not None

        appeal = pipeline.submit_appeal(
            decision.decision_id, "c4", "user1", "This was not hate speech"
        )
        assert appeal is not None
        assert appeal.status == AppealStatus.PENDING

    def test_approve_appeal_reverses_action(self, pipeline: ModerationPipeline):
        """TODO: Approved appeal should reverse the moderation action."""
        content = ContentItem("c5", "user1", "I hate bugs in code")
        decision = pipeline.evaluate(content)
        appeal = pipeline.submit_appeal(
            decision.decision_id, "c5", "user1", "Not hate speech"
        )
        assert appeal is not None

        reviewed = pipeline.review_appeal(appeal.appeal_id, approved=True)
        assert reviewed is not None
        assert reviewed.status == AppealStatus.APPROVED
        assert pipeline.content_actions.get("c5") == ModerationAction.NONE


class TestBulkModeration:
    def test_bulk_evaluate(self, pipeline: ModerationPipeline):
        """TODO: Evaluate multiple content items at once."""
        items = [
            ContentItem("b1", "user1", "This is fine"),
            ContentItem("b2", "user1", "I hate everything"),
            ContentItem("b3", "user1", "Buy now for free money"),
        ]
        results = pipeline.bulk_moderate(items)
        assert len(results) == 3
        assert results[0] is None  # no rule match
        assert results[1] is not None
        assert results[1].action == ModerationAction.REMOVE
        assert results[2] is not None
        assert results[2].action == ModerationAction.HIDE


class TestConfidenceModeration:
    def test_high_confidence_auto_action(self):
        """TODO: High confidence (>0.9) should auto-apply action."""
        p = ModerationPipeline()
        p.add_rule(ModerationRule(
            rule_id="r1", name="Spam", pattern=r"buy now",
            action=ModerationAction.HIDE, priority=5, confidence=0.95,
        ))
        content = ContentItem("c1", "user1", "buy now and save big!")
        status, decision = p.evaluate_with_confidence(content)
        assert status == ReviewStatus.AUTO_ACTIONED
        assert decision is not None
        assert decision.action == ModerationAction.HIDE

    def test_medium_confidence_queued(self):
        """TODO: Medium confidence (0.5-0.9) should queue for review."""
        p = ModerationPipeline()
        p.add_rule(ModerationRule(
            rule_id="r1", name="Maybe spam", pattern=r"special offer",
            action=ModerationAction.HIDE, priority=5, confidence=0.7,
        ))
        content = ContentItem("c2", "user1", "Check out this special offer")
        status, decision = p.evaluate_with_confidence(content)
        assert status == ReviewStatus.QUEUED_FOR_REVIEW

    def test_low_confidence_no_action(self):
        """TODO: Low confidence (<0.5) should take no action."""
        p = ModerationPipeline()
        p.add_rule(ModerationRule(
            rule_id="r1", name="Uncertain", pattern=r"maybe",
            action=ModerationAction.WARN, priority=1, confidence=0.3,
        ))
        content = ContentItem("c3", "user1", "maybe this is fine")
        status, decision = p.evaluate_with_confidence(content)
        assert status == ReviewStatus.NO_ACTION
