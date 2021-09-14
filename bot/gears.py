#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Gears for bots.

"Gears for Bots"

# Programmed by CoolCat467

__title__ = 'Gears'
__author__ = 'CoolCat467'
__version__ = '0.1.0'
__ver_major__ = 0
__ver_minor__ = 1
__ver_patch__ = 0

from typing import Union
import asyncio
import async_timeout
import concurrent.futures

__all__ = ['State', 'AsyncState',
           'StateMachine', 'AsyncStateMachine',
           'Gear', 'BaseBot', 'Timer', 'StateTimer']

class State(object):
    "Base class for states."
    def __init__(self, name:str):
        "Initialize state with a name."
        self.name = name
        self.machine = None
        return None
    
    def __str__(self) -> str:
        "Return <{self.name} {classname}>."
        return f'<{self.name} {self.__class__.__name__}>'
    
    def __repr__(self) -> str:
        "Return str(self)."
        return str(self)
    
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
    pass

class AsyncState(State):
    "Base Class for Asyncronous States."
    async def entry_actions(self) -> None:
        return None
    
    async def do_actions(self) -> None:
        return None
    
    async def check_conditions(self) -> Union[str, None]:
        return None
    
    async def exit_actions(self) -> None:
        return None
    pass

class StateMachine(object):
    "StateMachine class."
    def __init__(self):
        "Initialize StateMachine."
        self.states = {} # Stores the states
        self.active_state = None # The currently active state
        return None
    
    def __repr__(self) -> str:
        "Return <{classname} {self.states}>"
        text = f'<{self.__class__.__name__}'
        if hasattr(self, 'states'):
            text += f' {self.states}'
        return text+'>'
    
    def add_state(self, state:State) -> None:
        "Add a State instance to the internal dictionary."
        if not isinstance(state, State):
            raise TypeError(f'"{type(state).__name__}" is not an instance of State!')
        state.machine = self
        self.states[state.name] = state
        return
    
    def add_states(self, states:Union[list, tuple]) -> None:
        "Add multiple State instances to internal dictionary."
        for state in states:
            self.add_state(state)
        return
    
    def set_state(self, new_state_name:str) -> None:
        "Change states and preform any exit / entry actions."
        if not new_state_name in self.states:
            raise KeyError(f'"{new_state_name}" not found in internal states dictionary!')
        
        if not self.active_state is None:
            self.active_state.exit_actions()
        
        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()
        return None
    
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
    pass

class AsyncStateMachine(StateMachine):
    "Asyncronous State Machine class."
    def add_state(self, state:AsyncState) -> None:
        "Add an AsyncState instance to the internal dictionary."
        if not isinstance(state, AsyncState):
            raise TypeError(f'"{type(state).__name__}" is not an instance of AsyncState!')
        state.machine = self
        self.states[state.name] = state
        return None
    
    async def set_state(self, new_state_name:str) -> None:
        "Change states and preform any exit / entry actions."
        if not new_state_name in self.states:
            raise KeyError(f'"{new_state_name}" not found in internal states dictionary!')
        
        if not self.active_state is None:
            await self.active_state.exit_actions()
        
        self.active_state = self.states[new_state_name]
        await self.active_state.entry_actions()
        return None
    
    async def think(self) -> None:
        "Preform the actions of the active state, check conditions, and potentially change states."
        # Only continue if there is an active state
        if self.active_state is None:
            return None
        # Preform the actions of the active state
        await self.active_state.do_actions()
        # Check conditions and potentially change states.
        new_state_name = await self.active_state.check_conditions()
        if not new_state_name is None:
            await self.set_state(new_state_name)
        return None
    pass

class Gear(object):
    "Class that get's run by bots."
    def __init__(self, bot, name:str):
        "Store self.bot, and set self.running and self.stopped to False."
        self.bot = bot
        self.name = name
        self.running = False
        self.stopped = False
        return
    
    def gear_init(self) -> None:
        "Do whatever instance requires to start running. Must not stop bot."
        return None
    
    async def hault(self) -> None:
        self.running = False
        self.stopped = True
    
    def gear_shutdown(self) -> None:
        "Deinitialize gear. Only called after it's been stopped. Must not stop bot."
        return None
    
    def __repr__(self) -> str:
        "Return <{classname}>"
        return f'<{self.__class__.__name__}>'
    pass

class BaseBot(object):
    "Bot base class. Must initialize AFTER discord bot class."
    def __init__(self, eventloop):
        self.loop = eventloop
        self.gears = {}
        return None
    
    def __repr__(self) -> str:
        "Return <{classname}>"
        return f'<{self.__class__.__name__}>'
    
    def add_gear(self, new_gear:Gear) -> None:
        "Add a new gear to this bot."
        if not isinstance(new_gear, Gear):
            raise TypeError(f'"{type(state).__name__}" is not an instance of Gear!')
        self.gears[new_gear.name] = new_gear
        self.gears[new_gear.name].gear_init()
        return None
    
    def remove_gear(self, gear_name:Union[str, int]) -> None:
        "Remove a gear from this bot."
        if gear_name in self.gears:
            if not self.gears[gear_name].stopped:
                raise RuntimeError('Gear has not been stopped!')
            self.gears[gear_name].gear_shutdown()
            del self.gears[gear_name]
        else:
            raise KeyError(f'Gear {gear_name} not found!')
        return None
    
    @property
    def gear_close(self) -> bool:
        "True if gear objects should be closed."
        return False
    
    async def close(self) -> None:
        "Close this bot and it's gears."
        coros = [self.gears[gkey].hault() for gkey in tuple(self.gears.keys()) if not self.gears[gkey].stopped]
        await asyncio.gather(*coros)
        for gkey in tuple(self.gears.keys()):
            self.remove_gear(gkey)
        return
    pass

class Timer(Gear):
    "Class that will run coroutine self.run every delay seconds."
    def __init__(self, bot:BaseBot, name:str, delay:int=60) -> None:
        "self.name = name+'Timer'. Delay is seconds."
        super().__init__(bot, name)#+'Timer')
        self.delay = max(0, int(delay))
        self.task = None
        return
    
    def gear_init(self) -> None:
        "Create task in bot's event loop."
        self.task = self.bot.loop.create_task(self.wait_for_ready_start())
        return None
    
    async def wait_for_ready_start(self) -> None:
        "Await self.bot.wait_until_ready(), then await self.start()."
        if hasattr(self.bot, 'wait_until_ready'):
            await self.bot.wait_until_ready()
        self.running = True
        try:
            await self.start()
        except concurrent.futures.CancelledError:
            print(f'{self.__class__.__name__} "{self.name}"\'s task canceled, likely from hault.')
        self.stopped = True
        return None
    
    async def hault(self) -> None:
        "Set self.running to False, cancel self.task, and wait for it to cancel completely."
        # Stop running no matter what
        self.running = False
        # Cancel task
        try:
            self.task.cancel()
        except Exception:
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
        return None
    
    async def tick(self) -> bool:
        "Return False if Timer should continue running. Called every self.delay seconds."
        return True
    
    async def start(self) -> None:
        "Keep running self.tick every self.delay second or until self.bot.gear_close is True."
        while self.running:
            stop = await self.tick()
            if stop or self.bot.gear_close:
                self.running = False
            else:
                await asyncio.sleep(self.delay)
        return None
    pass

class _StateTimerExitState(AsyncState):
    "State Timer Exit State. Cause StateTimer to finally finish."
    def __init__(self):
        super().__init__('Hault')
        return None
    
    async def check_conditions(self) -> None:
        "Set self.state_timer.active_state to None."
        self.machine.active_state = None
        return None
    pass

class StateTimer(Timer, AsyncStateMachine):
    """StateTimer is a StateMachine Timer, or a timer with different
       states it can switch in and out of."""
    def __init__(self, bot:BaseBot, name:str, delay:int=1):
        AsyncStateMachine.__init__(self)
        Timer.__init__(self, bot, name, delay)#+'State', delay)
        self.add_state(_StateTimerExitState())
        pass
    
    def __repr__(self) -> str:
        "Return representation of self."
        return StateMachine.__repr__(self)
    
    async def initialize_state(self) -> None:
        "In subclass, set initial asyncronous state."
        return None
    
    async def start(self) -> None:
        await self.initialize_state()
        return await super().start()
    
    async def tick(self) -> bool:
        "Preform actions for AsyncStateTimer. Return False if no active state is set."
        await self.think()
        return self.active_state is None
    
    async def hault(self) -> None:
        self.delay = 0
        await self.set_state('Hault')
        async def wait_stop():
            while self.running:
                await asyncio.sleep(0.1)
        try:
            async with async_timeout.timeout(self.delay*1.1):
                await wait_stop()
        except asyncio.TimeoutError:
            await super().hault()
    pass

def run():
    print('This is hacked example of StateTimer.')
    loop = asyncio.get_event_loop()
    # hack bot to close loop when closed
    class _Bot(BaseBot):
        async def close(self):
            await super().close()
            print('Closed, stopping loop.')
            self.loop.stop()
        pass
    mr_bot = _Bot(loop)
    # hack state timer to create bot close task on completion
    class _StateTimerWithClose(StateTimer):
        async def wait_for_ready_start(self):
            await super().wait_for_ready_start()
            self.bot.loop.create_task(self.bot.close())
            print('Close created.')
        pass
    multi_speed_clock = _StateTimerWithClose(mr_bot, 'MultiSpeedClock', 0.5)
    # Define async state to just wait and then change state.
    class waitState(AsyncState):
        def __init__(self, delay, next_):
            super().__init__(f'wait_{delay}->{next_}')
            self.delay = delay
            self.next = next_
            return
        
        async def do_actions(self):
            print(f'{self.name} waits {self.delay}.')
            await asyncio.sleep(self.delay)
            return
        
        async def check_conditions(self):
            print(f'Going to next state {self.next}.')
            return self.next
        pass
    # Register states with state timer instance
    multi_speed_clock.add_state(waitState(3, 'Hault'))
    multi_speed_clock.add_state(waitState(5, 'wait_3->Hault'))
    # Tell mr. bot's loop to set the state of the state timer instance's state to the start one
    mr_bot.loop.run_until_complete(multi_speed_clock.set_state('wait_5->wait_3->Hault'))
    # Add state timer insance as gear to mr bot
    mr_bot.add_gear(multi_speed_clock)
    # Now run mr bot and their gears.
    try:
        mr_bot.loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        mr_bot.loop.close()
    return None

if __name__ == '__main__':
    run()
