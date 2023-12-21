"""Gears for Bots."""

# Programmed by CoolCat467

# Copyright 2023 CoolCat467
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

__title__ = "Gears"
__author__ = "CoolCat467"
__license__ = "Apache License 2.0"
__version__ = "0.1.9"
__ver_major__ = 0
__ver_minor__ = 1
__ver_patch__ = 9

import asyncio
import concurrent.futures
import math
import traceback
from typing import TYPE_CHECKING, Any

import async_timeout

from statusbot.statemachine import AsyncState, AsyncStateMachine

if TYPE_CHECKING:
    from collections.abc import Coroutine

__all__ = [
    "Gear",
    "BaseBot",
    "Timer",
    "StateTimer",
    "StateTimerExitState",
]


class Gear(AsyncStateMachine):
    """Class that gets run by bots."""

    __slots__ = ("bot", "name", "running", "stopped")

    def __init__(self, bot: BaseBot, name: str) -> None:
        """Store self.bot, and set self.running and self.stopped to False."""
        super().__init__()

        self.bot = bot
        self.name = name
        self.running = False
        self.stopped = False

    def gear_init(self) -> None:
        """Do whatever instance requires to start running. Must not stop bot."""
        return

    def submit_coro(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Task[Any]:
        """Submit a coroutine as task for bot event loop to complete."""
        return self.bot.loop.create_task(coro)

    async def hault(self) -> None:
        """Set self.running to False and self.stopped to True."""
        self.running = False
        self.stopped = True

    def gear_shutdown(self) -> None:
        """Shutdown gear. Only called after it's been stopped."""
        return

    def __repr__(self) -> str:
        """Return <{class-name}>."""
        return f"{self.__class__.__name__}({self.bot!r}, {self.name!r})"


class BaseBot:
    """Bot base class. Must initialize AFTER discord bot class."""

    __slots__ = ("loop", "gears")

    def __init__(self, eventloop: asyncio.AbstractEventLoop) -> None:
        """Initialize with event loop and no gears."""
        self.loop = eventloop
        self.gears: dict[str, Gear] = {}

    def __repr__(self) -> str:
        """Return <{class-name}>."""
        return f"<{self.__class__.__name__}>"

    def add_gear(self, new_gear: Gear) -> None:
        """Add a new gear to this bot."""
        if not isinstance(new_gear, Gear):
            raise TypeError(
                f'"{type(new_gear).__name__}" is not an instance of Gear!',
            )
        if new_gear.name in self.gears:
            raise RuntimeError(
                f'A gear named "{new_gear.name}" already exists!',
            )
        self.gears[new_gear.name] = new_gear
        self.gears[new_gear.name].gear_init()

    def remove_gear(self, gear_name: str) -> None:
        """Remove a gear from this bot."""
        if gear_name in self.gears:
            if not self.gears[gear_name].stopped:
                raise RuntimeError("Gear has not been stopped!")
            self.gears[gear_name].gear_shutdown()
            del self.gears[gear_name]
        else:
            raise KeyError(f"Gear {gear_name} not found!")

    def get_gear(self, gear_name: str) -> Gear | None:
        """Return a gear object if a gear with given name exists or None."""
        if gear_name in self.gears:
            return self.gears[gear_name]
        return None

    @property
    def gear_close(self) -> bool:
        """True if gear objects should be closed."""
        return False

    async def close(self) -> None:
        """Close this bot and it's gears."""
        coros = [
            gear.hault()
            for gear in iter(self.gears.values())
            if not gear.stopped
        ]
        await asyncio.gather(*coros)
        for gkey in tuple(self.gears.keys()):
            self.remove_gear(gkey)

    async def wait_ready(self) -> None:
        """Blocking until ready."""


class Timer(Gear):
    """Class that will run coroutine self.run every delay seconds."""

    __slots__ = ("delay", "task", "ticks")
    min_delay: int | float = 1

    def __init__(
        self,
        bot: BaseBot,
        name: str,
        delay: float = 60,
    ) -> None:
        """self.name = name. Delay is seconds."""
        super().__init__(bot, name)

        self.delay = max(0, delay)
        self.task: asyncio.Task[Any] | None = None
        self.ticks = math.inf

    def gear_init(self) -> None:
        """Create task in the bot event loop."""
        self.task = self.submit_coro(self.wait_for_ready_start())

    def on_stop(self) -> None:
        """Timer has stopped ticking."""

    async def wait_for_ready_start(self) -> None:
        """Await self.bot.wait_until_ready(), then await self.start()."""
        await self.bot.wait_ready()
        self.running = True
        try:
            await self.start()
        except concurrent.futures.CancelledError:
            print(
                f'{self.__class__.__name__} "{self.name}"\'s task canceled, '
                "likely from hault.",
            )
        finally:
            self.stopped = True
            self.on_stop()

    async def hault(self) -> None:
        """Set self.running to False, cancel self.task, wait for it to cancel."""
        # Stop running no matter what
        self.running = False
        # Cancel task
        if self.task is not None:
            try:
                async with async_timeout.timeout(self.delay):
                    await self.task
            except (concurrent.futures.TimeoutError, asyncio.TimeoutError):
                try:
                    self.task.cancel()
                except Exception as exc:  # pylint: disable=broad-except
                    traceback.print_exception(exc)
        if not self.stopped:

            async def wait_for_cancelled() -> bool:
                try:
                    if self.task is None:
                        return True
                    async with async_timeout.timeout(self.delay):
                        while not self.task.cancelled():
                            await asyncio.sleep(0.1)
                except asyncio.TimeoutError:
                    pass
                return True

            self.stopped = await wait_for_cancelled()

    async def tick(self) -> bool:
        """Return False if Timer should continue running. Called periodically."""
        return True

    async def start(self) -> None:
        """Keep running self.tick every self.delay second or until close time."""
        if self.min_delay > 0:
            while self.running:
                waited = self.min_delay * self.ticks
                stop = False
                if waited >= self.delay:
                    stop = await self.tick()
                    self.ticks = 0
                    waited = 0
                if stop or self.bot.gear_close:
                    self.running = False
                else:
                    to_wait = min(self.min_delay, self.delay - waited)
                    try:
                        await asyncio.sleep(to_wait)
                    except concurrent.futures.CancelledError:
                        self.running = False
                    self.ticks += math.ceil(to_wait / self.min_delay)
        else:
            self.ticks = 0
            while self.running:
                if (await self.tick()) or self.bot.gear_close:
                    self.running = False


class StateTimerExitState(AsyncState):
    """State Timer Exit State. Cause StateTimer to finally finish."""

    __slots__ = ()

    def __init__(self) -> None:
        """Initialize Hault state."""
        super().__init__("Hault")

    async def check_conditions(self) -> None:
        """Set self.state_timer.active_state to None."""
        self.machine.active_state = None


class StateTimer(Timer):
    """StateTimer is a StateMachine Timer.

    A timer with different states it can switch in and out of.
    """

    __slots__ = ()

    def __init__(
        self,
        bot: BaseBot,
        name: str,
        delay: float = 1,
    ) -> None:
        """Initialize State Timer."""
        super().__init__(bot, name, delay)

        self.add_state(StateTimerExitState())

    def __repr__(self) -> str:
        """Return representation of self."""
        return AsyncStateMachine.__repr__(self)

    async def initialize_state(self) -> None:
        """In subclass, set initial asynchronous state."""
        # await self.set_state('Hault')
        return

    async def start(self) -> None:
        """Keep running self.tick every self.delay second or until close time."""
        await self.initialize_state()
        return await super().start()

    async def tick(self) -> bool:
        """Perform actions for AsyncStateTimer.

        Return False if no active state is set.
        """
        await self.think()
        if self.bot.gear_close:
            self.active_state = None
        return self.active_state is None

    async def hault(self) -> None:
        """Set self.running to False, cancel self.task, wait for it to cancel."""
        await self.set_state("Hault")
        self.ticks = math.inf

        async def wait_stop() -> None:
            while self.running:
                await asyncio.sleep(self.min_delay)
            while not self.stopped:
                await asyncio.sleep(1)

        try:
            async with async_timeout.timeout(self.delay * 1.5):
                await wait_stop()
        except asyncio.TimeoutError:
            pass
        await super().hault()


def run() -> None:
    """Run an example of this module."""
    print("This is hacked example of StateTimer.")
    loop = asyncio.new_event_loop()

    # hack bot to close loop when closed
    class _Bot(BaseBot):
        __slots__ = ()

        async def close(self) -> None:
            await super().close()
            print("Closed, stopping loop.")
            self.loop.stop()

    mr_bot = _Bot(loop)

    # hack state timer to create bot close task on completion
    class _StateTimerWithClose(StateTimer):
        __slots__ = ()

        async def wait_for_ready_start(self) -> None:
            await super().wait_for_ready_start()
            self.submit_coro(self.bot.close())
            print("Close created.")

    multi_speed_clock = _StateTimerWithClose(mr_bot, "MultiSpeedClock", 0.5)

    # Define asynchronous state to just wait and then change state.
    class WaitState(AsyncState):
        """Wait state example class."""

        __slots__ = ("delay", "next")

        def __init__(self, delay: int, next_: str) -> None:
            super().__init__(f"wait_{delay}->{next_}")
            self.delay = delay
            self.next = next_

        async def do_actions(self) -> None:
            print(f"{self.name} waits {self.delay}.")
            await asyncio.sleep(self.delay)

        async def check_conditions(self) -> str:
            print(f"Going to next state {self.next}.")
            return self.next

    # Register states with state timer instance
    multi_speed_clock.add_state(WaitState(3, "Hault"))
    multi_speed_clock.add_state(WaitState(5, "wait_3->Hault"))
    # Tell Mr. bots loop to set the state of the state timer
    # instance's state to the start one
    mr_bot.loop.run_until_complete(
        multi_speed_clock.set_state("wait_5->wait_3->Hault"),
    )
    # Add state timer instance as gear to Mr bot
    mr_bot.add_gear(multi_speed_clock)
    # Now run Mr bot and their gears.
    try:
        mr_bot.loop.run_forever()
    except KeyboardInterrupt:
        print("Closing from keyboard interrupt.")
    finally:
        mr_bot.loop.close()


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.")
    run()
