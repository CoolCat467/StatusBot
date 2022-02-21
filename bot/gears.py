#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Gears for bots.

"Gears for Bots"

# Programmed by CoolCat467

__title__ = 'Gears'
__author__ = 'CoolCat467'
__version__ = '0.1.6'
__ver_major__ = 0
__ver_minor__ = 1
__ver_patch__ = 6

import math
from typing import Union, Iterable
import asyncio
import concurrent.futures

import async_timeout

__all__ = ['State', 'AsyncState',
           'StateMachine', 'AsyncStateMachine',
           'Gear', 'BaseBot', 'Timer', 'StateTimer',
           'StateTimerExitState']

class State:
    "Base class for states."
    __slots__ = ('name', 'machine')
    def __init__(self, name: str):
        "Initialize state with a name."
        self.name = name
        self.machine: 'StateMachine'
    
    def __str__(self) -> str:
        "Return <{self.name} {classname}>."
        return f'<{self.name} {self.__class__.__name__}>'
    
    def __repr__(self) -> str:
        "Return str(self)."
        return str(self)
    
    # pylint: disable=no-self-use
    def entry_actions(self) -> None:
        "Preform entry actions for this State."
        return None
    
    def do_actions(self) -> None:
        "Preform actions for this State."
        return None
    
    def check_conditions(self) -> Union[str, None]:
        "Check state and return new state name. None -> remains in current state."
        return None
    
    def exit_actions(self) -> None:
        "Preform exit actions for this State."
        return None

class AsyncState:
    "Base class for asyncronous states."
    __slots__ = ('name', 'machine')
    def __init__(self, name: str):
        "Initialize state with a name."
        self.name = name
        self.machine: 'AsyncStateMachine'
    
    def __str__(self) -> str:
        "Return <{self.name} {classname}>."
        return f'<{self.name} {self.__class__.__name__}>'
    
    def __repr__(self) -> str:
        "Return str(self)."
        return str(self)
    
    # pylint: disable=no-self-use
    async def entry_actions(self) -> None:
        "Preform entry actions for this State."
        return None
    
    async def do_actions(self) -> None:
        "Preform actions for this State."
        return None
    
    async def check_conditions(self) -> Union[str, None]:
        "Check state and return new state name. None -> remains in current state."
        return None
    
    async def exit_actions(self) -> None:
        "Preform exit actions for this State."
        return None

class StateMachine:
    "StateMachine class."
##    TypeError: multiple bases have instance lay-out conflict
##    __slots__ = 'states', 'active_state'
    def __init__(self):
        "Initialize StateMachine."
        self.states = {} # Stores the states
        self.active_state: Union[State, None] = None# The currently active state
    
    def __repr__(self) -> str:
        "Return <{classname} {self.states}>"
        text = f'<{self.__class__.__name__}'
        if hasattr(self, 'states'):
            text += f' {self.states}'
        return text+'>'
    
    def add_state(self, state: State) -> None:
        "Add a State instance to the internal dictionary."
        if not isinstance(state, State):
            raise TypeError(f'"{type(state).__name__}" is not an instance of State!')
        state.machine = self
        self.states[state.name] = state
    
    def add_states(self, states: Iterable[State]) -> None:
        "Add multiple State instances to internal dictionary."
        for state in states:
            self.add_state(state)
    
    def remove_state(self, state_name: str) -> None:
        "Remove state with given name from internal dictionary."
        if not state_name in self.states:
            raise ValueError(f'{state_name} is not a registered State.')
        del self.states[state_name]
    
    def set_state(self, new_state_name:str) -> None:
        "Change states and preform any exit / entry actions."
        if not new_state_name in self.states:
            raise KeyError(f'"{new_state_name}" not found in internal states dictionary!')
        
        if not self.active_state is None:
            self.active_state.exit_actions()
        
        self.active_state = self.states[new_state_name]
        if not self.active_state is None:
            self.active_state.entry_actions()
    
    def think(self) -> None:
        "Preform the actions of the active state, check conditions, and potentially change states."
        # Only continue if there is an active state
        if self.active_state is None:
            return None
        # Preform the actions of the active state
        self.active_state.do_actions()
        # Check conditions and potentially change states.
        new_state_name = self.active_state.check_conditions()
        if not new_state_name is None:
            self.set_state(new_state_name)
        return None

class AsyncStateMachine:
    "Asyncronous State Machine class."
##    TypeError: multiple bases have instance lay-out conflict
##    __slots__ = 'states', 'active_state'
    def __init__(self):
        "Initialize AsyncStateMachine."
        self.states = {} # Stores the states
        self.active_state: Union[AsyncState, None] = None# The currently active state
    
    def __repr__(self) -> str:
        "Return <{classname} {self.states}>"
        text = f'<{self.__class__.__name__}'
        if hasattr(self, 'states'):
            text += f' {self.states}'
        return text+'>'
    
    def add_state(self, state: AsyncState) -> None:
        "Add an AsyncState instance to the internal dictionary."
        if not isinstance(state, AsyncState):
            raise TypeError(f'"{type(state).__name__}" is not an instance of AsyncState!')
        state.machine = self
        self.states[state.name] = state
    
    def add_states(self, states: Iterable[AsyncState]) -> None:
        "Add multiple State instances to internal dictionary."
        for state in states:
            self.add_state(state)
    
    def remove_state(self, state_name: str) -> None:
        "Remove state with given name from internal dictionary."
        if not state_name in self.states:
            raise ValueError(f'{state_name} is not a registered AsyncState.')
        del self.states[state_name]
    
    async def set_state(self, new_state_name: str) -> None:
        "Change states and preform any exit / entry actions."
        if not new_state_name in self.states:
            raise KeyError(f'"{new_state_name}" not found in internal states dictionary!')
        
        if not self.active_state is None:
            await self.active_state.exit_actions()
        
        self.active_state = self.states[new_state_name]
        
        if not self.active_state is None:
            await self.active_state.entry_actions()
    
    async def think(self) -> None:
        "Preform the actions of the active state, check conditions, and potentially change states."
        # Only continue if there is an active state
        if self.active_state is None:
            return None
        # Preform the actions of the active state
        await self.active_state.do_actions()
        # Check conditions and potentially change states.
        new_state_name = await self.active_state.check_conditions()
        if new_state_name is not None:
            await self.set_state(new_state_name)

class Gear:
    "Class that get's run by bots."
##    __slots__ = 'bot', 'name', 'running', 'stopped'
    def __init__(self, bot: 'BaseBot', name: str):
        "Store self.bot, and set self.running and self.stopped to False."
        self.bot = bot
        self.name = name
        self.running = False
        self.stopped = False
    
    def gear_init(self) -> None:# pylint: disable=no-self-use
        "Do whatever instance requires to start running. Must not stop bot."
        return None
    
    def submit_coro(self, coro):
        "Submit a coro as task for bot event loop to complete"
        return self.bot.loop.create_task(coro)
    
    async def hault(self) -> None:
        "Set self.running to False and self.stopped to True."
        self.running = False
        self.stopped = True
    
    def gear_shutdown(self) -> None:# pylint: disable=no-self-use
        "Deinitialize gear. Only called after it's been stopped. Must not stop bot."
        return None
    
    def __repr__(self) -> str:
        "Return <{classname}>"
        return f'<{self.__class__.__name__}>'

class BaseBot:
    "Bot base class. Must initialize AFTER discord bot class."
    __slots__ = ('loop', 'gears')
    def __init__(self, eventloop):
        self.loop = eventloop
        self.gears = {}
    
    def __repr__(self) -> str:
        "Return <{classname}>"
        return f'<{self.__class__.__name__}>'
    
    def add_gear(self, new_gear: Gear) -> None:
        "Add a new gear to this bot."
        if not isinstance(new_gear, Gear):
            raise TypeError(f'"{type(new_gear).__name__}" is not an instance of Gear!')
        if new_gear.name in self.gears:
            raise RuntimeError(f'A gear named "{new_gear.name}" already exists!')
        self.gears[new_gear.name] = new_gear
        self.gears[new_gear.name].gear_init()
    
    def remove_gear(self, gear_name: Union[str, int]) -> None:
        "Remove a gear from this bot."
        if gear_name in self.gears:
            if not self.gears[gear_name].stopped:
                raise RuntimeError('Gear has not been stopped!')
            self.gears[gear_name].gear_shutdown()
            del self.gears[gear_name]
        else:
            raise KeyError(f'Gear {gear_name} not found!')
    
    def get_gear(self, gear_name: str) -> Union[Gear, None]:
        "Return a gear object if a gear with given name exists or None"
        if gear_name in self.gears:
            return self.gears[gear_name]
        return None
    
    @property
    def gear_close(self) -> bool:
        "True if gear objects should be closed."
        return False
    
    async def close(self) -> None:
        "Close this bot and it's gears."
        coros = [gear.hault()
                 for gear in iter(self.gears.values())
                 if not gear.stopped]
        await asyncio.gather(*coros)
        for gkey in tuple(self.gears.keys()):
            self.remove_gear(gkey)
    
    async def wait_ready(self) -> None:
        "Blocking until ready"

class Timer(Gear):
    "Class that will run coroutine self.run every delay seconds."
##    __slots__ = 'delay', 'task', 'ticks'
    min_delay: int = 1
    def __init__(self, bot: BaseBot, name: str, delay: int=60) -> None:
        "self.name = name. Delay is secconds."
        super().__init__(bot, name)
        self.delay = max(0, int(delay))
        self.task: asyncio.Task
        self.ticks = math.inf
    
    def gear_init(self) -> None:
        "Create task in bot's event loop."
        self.task = self.submit_coro(self.wait_for_ready_start())
    
    def on_stop(self) -> None:
        "Function called when timer has stopped ticking."
    
    async def wait_for_ready_start(self) -> None:
        "Await self.bot.wait_until_ready(), then await self.start()."
        await self.bot.wait_ready()
        self.running = True
        try:
            await self.start()
        except concurrent.futures.CancelledError:
            print(f'{self.__class__.__name__} "{self.name}"\'s task canceled, likely from hault.')
        finally:
            self.stopped = True
            self.on_stop()
    
    async def hault(self) -> None:
        "Set self.running to False, cancel self.task, and wait for it to cancel completely."
        # Stop running no matter what
        self.running = False
        # Cancel task
        try:
            async with async_timeout.timeout(self.delay):
                await self.task
        except (concurrent.futures.TimeoutError, asyncio.TimeoutError):
            try:
                self.task.cancel()
            except Exception:# pylint: disable=broad-except
                pass
        if not self.stopped:
            async def wait_for_cancelled():
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
    
    async def tick(self) -> bool:# pylint: disable=no-self-use
        "Return False if Timer should continue running. Called every self.delay seconds."
        return True
    
    async def start(self) -> None:
        "Keep running self.tick every self.delay second or until self.bot.gear_close is True."
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
                    to_wait = min(self.min_delay, self.delay-waited)
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
    "State Timer Exit State. Cause StateTimer to finally finish."
    __slots__: tuple = tuple()
    def __init__(self):
        super().__init__('Hault')
    
    async def check_conditions(self) -> None:
        "Set self.state_timer.active_state to None."
        self.machine.active_state = None

class StateTimer(Timer, AsyncStateMachine):
    """StateTimer is a StateMachine Timer, or a timer with different
       states it can switch in and out of."""
##    __slots__: tuple = tuple()
    def __init__(self, bot: BaseBot, name: str, delay: int=1):
        AsyncStateMachine.__init__(self)
        Timer.__init__(self, bot, name, delay)
        
        self.add_state(StateTimerExitState())
    
    def __repr__(self) -> str:
        "Return representation of self."
        return AsyncStateMachine.__repr__(self)
    
    async def initialize_state(self) -> None:# pylint: disable=no-self-use
        "In subclass, set initial asyncronous state."
##        await self.set_state('Hault')
        return None
    
    async def start(self) -> None:
        await self.initialize_state()
        return await super().start()
    
    async def tick(self) -> bool:
        "Preform actions for AsyncStateTimer. Return False if no active state is set."
        await self.think()
        if self.bot.gear_close:
            self.active_state = None
        return self.active_state is None
    
    async def hault(self) -> None:
        await self.set_state('Hault')
        self.ticks = math.inf
        async def wait_stop():
            while self.running:
                await asyncio.sleep(self.min_delay)
            while not self.stopped:
                await asyncio.sleep(1)
        try:
            async with async_timeout.timeout(self.delay*1.5):
                await wait_stop()
        except asyncio.TimeoutError:
            pass
        await super().hault()

def run():
    "Run an example of this module."
    print('This is hacked example of StateTimer.')
    loop = asyncio.new_event_loop()
    # hack bot to close loop when closed
    class _Bot(BaseBot):
        __slots__: tuple = tuple()
        async def close(self) -> None:
            await super().close()
            print('Closed, stopping loop.')
            self.loop.stop()
    mr_bot = _Bot(loop)
    # hack state timer to create bot close task on completion
    class _StateTimerWithClose(StateTimer):
        __slots__: tuple = tuple()
        async def wait_for_ready_start(self) -> None:
            await super().wait_for_ready_start()
            self.submit_coro(self.bot.close())
            print('Close created.')
    multi_speed_clock = _StateTimerWithClose(mr_bot, 'MultiSpeedClock', 0.5)
    # Define async state to just wait and then change state.
    class WaitState(AsyncState):
        "Wait state example class"
        __slots__ = ('delay', 'next')
        def __init__(self, delay: int, next_: str):
            super().__init__(f'wait_{delay}->{next_}')
            self.delay = delay
            self.next = next_
        
        async def do_actions(self) -> None:
            print(f'{self.name} waits {self.delay}.')
            await asyncio.sleep(self.delay)
        
        async def check_conditions(self) -> str:
            print(f'Going to next state {self.next}.')
            return self.next
    # Register states with state timer instance
    multi_speed_clock.add_state(WaitState(3, 'Hault'))
    multi_speed_clock.add_state(WaitState(5, 'wait_3->Hault'))
    # Tell mr. bot's loop to set the state of the state timer instance's state to the start one
    mr_bot.loop.run_until_complete(multi_speed_clock.set_state('wait_5->wait_3->Hault'))
    # Add state timer insance as gear to mr bot
    mr_bot.add_gear(multi_speed_clock)
    # Now run mr bot and their gears.
    try:
        mr_bot.loop.run_forever()
    except KeyboardInterrupt:
        print('Closing from keyboard interrupt.')
    finally:
        mr_bot.loop.close()

if __name__ == '__main__':
    print(f'{__title__} v{__version__}\nProgrammed by {__author__}.')
    run()
