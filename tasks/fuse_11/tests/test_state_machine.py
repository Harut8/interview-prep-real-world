import pytest
from app import StateMachine, InvalidTransitionError


@pytest.fixture
def order_sm():
    sm = StateMachine("created")
    sm.add_transition("created", "pay", "paid")
    sm.add_transition("paid", "ship", "shipped")
    sm.add_transition("shipped", "deliver", "delivered")
    sm.add_transition("paid", "cancel", "cancelled")
    sm.add_transition("shipped", "return", "returned")
    return sm


class TestBasicTransitions:
    def test_initial_state(self, order_sm):
        assert order_sm.current_state == "created"

    def test_valid_transition(self, order_sm):
        order_sm.trigger("pay")
        assert order_sm.current_state == "paid"

    def test_chain_transitions(self, order_sm):
        order_sm.trigger("pay")
        order_sm.trigger("ship")
        order_sm.trigger("deliver")
        assert order_sm.current_state == "delivered"

    def test_invalid_transition(self, order_sm):
        with pytest.raises(InvalidTransitionError):
            order_sm.trigger("ship")  # can't ship from "created"

    def test_no_transition_from_terminal(self, order_sm):
        order_sm.trigger("pay")
        order_sm.trigger("cancel")
        with pytest.raises(InvalidTransitionError):
            order_sm.trigger("ship")


class TestCanTrigger:
    def test_can_trigger_valid(self, order_sm):
        assert order_sm.can_trigger("pay") is True

    def test_cannot_trigger_invalid(self, order_sm):
        assert order_sm.can_trigger("ship") is False


class TestGuards:
    def test_guard_allows(self):
        sm = StateMachine("locked")
        sm.add_transition("locked", "unlock", "unlocked", guard=lambda **ctx: ctx.get("key") == "secret")
        sm.trigger("unlock", key="secret")
        assert sm.current_state == "unlocked"

    def test_guard_blocks(self):
        sm = StateMachine("locked")
        sm.add_transition("locked", "unlock", "unlocked", guard=lambda **ctx: ctx.get("key") == "secret")
        with pytest.raises(InvalidTransitionError):
            sm.trigger("unlock", key="wrong")
        assert sm.current_state == "locked"


class TestCallbacks:
    def test_on_enter_called(self, order_sm):
        entered = []
        order_sm.add_on_enter("paid", lambda: entered.append("paid"))
        order_sm.trigger("pay")
        assert entered == ["paid"]

    def test_on_exit_called(self, order_sm):
        exited = []
        order_sm.add_on_exit("created", lambda: exited.append("created"))
        order_sm.trigger("pay")
        assert exited == ["created"]

    def test_exit_before_enter(self):
        log = []
        sm = StateMachine("a")
        sm.add_transition("a", "go", "b")
        sm.add_on_exit("a", lambda: log.append("exit_a"))
        sm.add_on_enter("b", lambda: log.append("enter_b"))
        sm.trigger("go")
        assert log == ["exit_a", "enter_b"]


class TestHistory:
    def test_records_transitions(self, order_sm):
        order_sm.trigger("pay")
        order_sm.trigger("ship")
        assert order_sm.history() == [
            ("created", "pay", "paid"),
            ("paid", "ship", "shipped"),
        ]

    def test_empty_history(self, order_sm):
        assert order_sm.history() == []
