"""Statemachine tests."""

# Programmed by CoolCat467

# Copyright 2021-2026 CoolCat467
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from __future__ import annotations

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
