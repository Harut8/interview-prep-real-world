"""Tests for Feature Flags Service."""

import time
import pytest
from app import (
    FeatureFlagService, FeatureFlag, TargetingConfig, TargetingRule,
    UserContext, RuleOperator, LogicOperator, AuditAction,
)


@pytest.fixture
def service() -> FeatureFlagService:
    return FeatureFlagService()


@pytest.fixture
def user_alice() -> UserContext:
    return UserContext(
        user_id="alice",
        attributes={"country": "US", "age": 28, "plan": "premium"},
    )


@pytest.fixture
def user_bob() -> UserContext:
    return UserContext(
        user_id="bob",
        attributes={"country": "UK", "age": 35, "plan": "free"},
    )


class TestPercentageRollout:
    def test_deterministic_rollout(self, service: FeatureFlagService, user_alice):
        """FAILING: Same user should always get same result for same flag.

        Bug: Uses random() instead of deterministic hash.
        """
        service.create_flag("feature_x", rollout_percentage=50.0)

        results = set()
        for _ in range(20):
            results.add(service.evaluate("feature_x", user_alice))

        assert len(results) == 1, (
            "Deterministic rollout should give same result every time. "
            f"Got both True and False across 20 evaluations."
        )

    def test_100_percent_always_enabled(self, service: FeatureFlagService, user_alice):
        """PASSING: 100% rollout should always be enabled."""
        service.create_flag("full_rollout", rollout_percentage=100.0)
        assert service.evaluate("full_rollout", user_alice) is True

    def test_0_percent_always_disabled(self, service: FeatureFlagService, user_alice):
        """PASSING: 0% rollout should always be disabled."""
        service.create_flag("no_rollout", rollout_percentage=0.0)
        assert service.evaluate("no_rollout", user_alice) is False


class TestTargetingRules:
    def test_and_logic_all_must_match(self, service: FeatureFlagService, user_alice):
        """FAILING: AND logic should require ALL rules to match.

        Bug: AND uses any() instead of all().
        """
        targeting = TargetingConfig(
            rules=[
                TargetingRule("country", RuleOperator.EQUALS, "US"),
                TargetingRule("plan", RuleOperator.EQUALS, "enterprise"),  # Alice is premium, not enterprise
            ],
            logic=LogicOperator.AND,
        )
        service.create_flag("enterprise_us", targeting=targeting)

        # Alice is US + premium — should NOT match (plan != enterprise)
        result = service.evaluate("enterprise_us", user_alice)
        assert result is False, (
            "AND logic: country=US matches but plan!=enterprise, should be False"
        )

    def test_or_logic_any_must_match(self, service: FeatureFlagService, user_alice, user_bob):
        """FAILING: OR logic should require ANY rule to match.

        Bug: OR uses all() instead of any().
        """
        targeting = TargetingConfig(
            rules=[
                TargetingRule("country", RuleOperator.EQUALS, "US"),
                TargetingRule("country", RuleOperator.EQUALS, "UK"),
            ],
            logic=LogicOperator.OR,
        )
        service.create_flag("us_or_uk", targeting=targeting)

        # Alice is US — should match (one of OR conditions)
        assert service.evaluate("us_or_uk", user_alice) is True
        # Bob is UK — should also match
        assert service.evaluate("us_or_uk", user_bob) is True

    def test_single_rule_match(self, service: FeatureFlagService, user_alice):
        """PASSING: Single rule targeting should work."""
        targeting = TargetingConfig(
            rules=[TargetingRule("country", RuleOperator.EQUALS, "US")],
        )
        service.create_flag("us_only", targeting=targeting)
        assert service.evaluate("us_only", user_alice) is True


class TestDependencies:
    def test_dependency_must_be_enabled_for_user(self, service: FeatureFlagService, user_bob):
        """FAILING: Dependency flag must be evaluated for the user, not just exist.

        Bug: Only checks if dependency flag exists, not if enabled for user.
        """
        # base_flag targets US only
        targeting = TargetingConfig(
            rules=[TargetingRule("country", RuleOperator.EQUALS, "US")],
        )
        service.create_flag("base_flag", targeting=targeting)

        # dependent_flag depends on base_flag
        service.create_flag("dependent_flag", dependencies=["base_flag"])

        # Bob is UK — base_flag should be False for Bob
        # Therefore dependent_flag should also be False
        result = service.evaluate("dependent_flag", user_bob)
        assert result is False, (
            "Dependent flag should be False because base_flag is not enabled for Bob (UK)"
        )


class TestKillSwitch:
    def test_kill_disables_for_all(self, service: FeatureFlagService, user_alice):
        """TODO: Kill switch should disable flag for all users."""
        service.create_flag("feature_y", rollout_percentage=100.0)
        assert service.evaluate("feature_y", user_alice) is True

        result = service.kill_flag("feature_y", killed_by="admin")
        assert result is True
        assert service.evaluate("feature_y", user_alice) is False

    def test_revive_after_kill(self, service: FeatureFlagService, user_alice):
        """TODO: Reviving a killed flag should re-enable it."""
        service.create_flag("feature_y", rollout_percentage=100.0)
        service.kill_flag("feature_y")
        service.revive_flag("feature_y", revived_by="admin")
        assert service.evaluate("feature_y", user_alice) is True


class TestRolloutSchedule:
    def test_gradual_rollout(self, service: FeatureFlagService):
        """TODO: Rollout should follow the schedule."""
        now = time.time()
        service.create_flag("gradual", rollout_percentage=0.0)

        stages = [
            (now - 100, 10.0),    # Already past: 10%
            (now + 1000, 50.0),   # Future: 50%
            (now + 2000, 100.0),  # Far future: 100%
        ]
        service.schedule_rollout("gradual", stages, scheduled_by="admin")

        effective = service.get_effective_rollout("gradual", now)
        assert effective == 10.0, f"Expected 10% (past first stage), got {effective}%"

    def test_future_schedule_not_applied(self, service: FeatureFlagService):
        """TODO: Future schedule stages should not be applied yet."""
        now = time.time()
        service.create_flag("future_flag", rollout_percentage=5.0)

        stages = [
            (now + 1000, 50.0),   # Future
            (now + 2000, 100.0),  # Far future
        ]
        service.schedule_rollout("future_flag", stages, scheduled_by="admin")

        effective = service.get_effective_rollout("future_flag", now)
        assert effective == 5.0, f"Expected 5% (no past stages), got {effective}%"


class TestAuditLog:
    def test_audit_log_on_create(self, service: FeatureFlagService):
        """TODO: Creating a flag should generate an audit entry."""
        service.create_flag("audit_test")
        logs = service.get_audit_log("audit_test")
        assert len(logs) >= 1
        assert logs[0].action == AuditAction.CREATED

    def test_audit_log_on_kill(self, service: FeatureFlagService):
        """TODO: Killing a flag should generate an audit entry."""
        service.create_flag("kill_test")
        service.kill_flag("kill_test", killed_by="admin")
        logs = service.get_audit_log("kill_test")
        actions = [e.action for e in logs]
        assert AuditAction.KILLED in actions

    def test_audit_log_filter(self, service: FeatureFlagService):
        """TODO: Audit log should be filterable by flag name."""
        service.create_flag("flag_a")
        service.create_flag("flag_b")
        logs_a = service.get_audit_log("flag_a")
        logs_b = service.get_audit_log("flag_b")
        assert all(e.flag_name == "flag_a" for e in logs_a)
        assert all(e.flag_name == "flag_b" for e in logs_b)
