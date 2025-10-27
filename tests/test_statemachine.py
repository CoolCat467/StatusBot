import pytest

from statusbot.statemachine import AsyncState, State


def test_state() -> None:
    state = State("waffle_time")

    assert state.name == "waffle_time"

    with pytest.raises(
        RuntimeError,
        match=r"^State has no statemachine bound$",
    ):
        print(state.machine)


def test_async_state() -> None:
    state = AsyncState("waffle_time")

    assert state.name == "waffle_time"

    with pytest.raises(
        RuntimeError,
        match=r"^State has no statemachine bound$",
    ):
        print(state.machine)
