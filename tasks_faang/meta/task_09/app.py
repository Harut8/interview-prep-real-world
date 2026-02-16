"""
Feature Flags Service
Manage feature rollouts with targeting rules, dependencies, and kill switches.
"""

from __future__ import annotations

import hashlib
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class RuleOperator(Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"


class LogicOperator(Enum):
    AND = "and"
    OR = "or"


class AuditAction(Enum):
    CREATED = "created"
    UPDATED = "updated"
    TOGGLED = "toggled"
    KILLED = "killed"
    ROLLOUT_SCHEDULED = "rollout_scheduled"


@dataclass
class TargetingRule:
    """A single targeting rule, e.g., country equals 'US'."""
    attribute: str
    operator: RuleOperator
    value: Any


@dataclass
class TargetingConfig:
    """Targeting configuration with multiple rules and logic operator."""
    rules: list[TargetingRule] = field(default_factory=list)
    logic: LogicOperator = LogicOperator.AND


@dataclass
class RolloutSchedule:
    """Schedule for gradual rollout."""
    stages: list[tuple[float, float]] = field(default_factory=list)
    # list of (timestamp, percentage) — sorted by timestamp


@dataclass
class AuditEntry:
    flag_name: str
    action: AuditAction
    changed_by: str
    timestamp: float
    details: str = ""


@dataclass
class FeatureFlag:
    name: str
    enabled: bool = True
    rollout_percentage: float = 100.0  # 0-100
    targeting: Optional[TargetingConfig] = None
    dependencies: list[str] = field(default_factory=list)  # flag names
    killed: bool = False
    rollout_schedule: Optional[RolloutSchedule] = None


@dataclass
class UserContext:
    """User attributes for targeting evaluation."""
    user_id: str
    attributes: dict[str, Any] = field(default_factory=dict)


class FeatureFlagService:
    """Manages feature flags with targeting, rollouts, and dependencies."""

    def __init__(self) -> None:
        self.flags: dict[str, FeatureFlag] = {}
        self.audit_log: list[AuditEntry] = []

    def create_flag(self, name: str, enabled: bool = True,
                    rollout_percentage: float = 100.0,
                    targeting: TargetingConfig | None = None,
                    dependencies: list[str] | None = None) -> FeatureFlag:
        flag = FeatureFlag(
            name=name,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            targeting=targeting,
            dependencies=dependencies or [],
        )
        self.flags[name] = flag
        return flag

    def _is_in_rollout(self, flag_name: str, user_id: str,
                       percentage: float) -> bool:
        """Determine if user falls within the rollout percentage.

        Should be deterministic: same user + flag always gets same result.

        BUG: Uses random() instead of deterministic hash.
        """
        if percentage >= 100.0:
            return True
        if percentage <= 0.0:
            return False
        # BUG: random() is not deterministic — same user gets different results
        roll = random.random() * 100
        return roll < percentage

    def _evaluate_rule(self, rule: TargetingRule, context: UserContext) -> bool:
        """Evaluate a single targeting rule against user context."""
        user_value = context.attributes.get(rule.attribute)
        if user_value is None:
            return False

        if rule.operator == RuleOperator.EQUALS:
            return user_value == rule.value
        if rule.operator == RuleOperator.NOT_EQUALS:
            return user_value != rule.value
        if rule.operator == RuleOperator.IN:
            return user_value in rule.value
        if rule.operator == RuleOperator.NOT_IN:
            return user_value not in rule.value
        if rule.operator == RuleOperator.GREATER_THAN:
            return user_value > rule.value
        if rule.operator == RuleOperator.LESS_THAN:
            return user_value < rule.value
        return False

    def _evaluate_targeting(self, targeting: TargetingConfig,
                            context: UserContext) -> bool:
        """Evaluate targeting rules with AND/OR logic.

        BUG: AND and OR logic are swapped.
        """
        if not targeting.rules:
            return True

        results = [self._evaluate_rule(r, context) for r in targeting.rules]

        # BUG: AND uses `any()` (should be `all()`), OR uses `all()` (should be `any()`)
        if targeting.logic == LogicOperator.AND:
            return any(results)  # BUG: should be all()
        else:  # OR
            return all(results)  # BUG: should be any()

    def _check_dependencies(self, flag: FeatureFlag, context: UserContext) -> bool:
        """Check if all dependency flags are enabled for the user.

        BUG: Only checks if dependency flag exists, not if it's enabled
        for this specific user.
        """
        for dep_name in flag.dependencies:
            # BUG: Only checks existence, not evaluation for user
            if dep_name not in self.flags:
                return False
        return True

    def evaluate(self, flag_name: str, context: UserContext,
                 now: float | None = None) -> bool:
        """Evaluate whether a flag is enabled for a given user.

        Checks: enabled, kill switch, dependencies, targeting, rollout percentage.
        """
        flag = self.flags.get(flag_name)
        if flag is None:
            return False

        if not flag.enabled or flag.killed:
            return False

        if not self._check_dependencies(flag, context):
            return False

        if flag.targeting and not self._evaluate_targeting(flag.targeting, context):
            return False

        percentage = flag.rollout_percentage
        return self._is_in_rollout(flag_name, context.user_id, percentage)

    def kill_flag(self, flag_name: str, killed_by: str = "system") -> bool:
        """Kill switch: immediately disable a flag for all users.

        TODO: Implement kill switch with audit logging.
        """
        return False

    def revive_flag(self, flag_name: str, revived_by: str = "system") -> bool:
        """Revive a killed flag.

        TODO: Implement flag revival.
        """
        return False

    def schedule_rollout(self, flag_name: str,
                         stages: list[tuple[float, float]],
                         scheduled_by: str = "system") -> bool:
        """Schedule gradual rollout.

        stages: list of (timestamp, percentage) tuples.

        TODO: Implement rollout scheduling.
        """
        return False

    def get_effective_rollout(self, flag_name: str, now: float) -> float:
        """Get the effective rollout percentage based on schedule.

        TODO: Implement schedule evaluation.
        """
        flag = self.flags.get(flag_name)
        if flag is None:
            return 0.0
        return flag.rollout_percentage

    def get_audit_log(self, flag_name: str | None = None) -> list[AuditEntry]:
        """Get audit log entries, optionally filtered by flag name.

        TODO: Implement audit log retrieval.
        """
        return []
