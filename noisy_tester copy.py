import datetime
import humanize

from functools import partial
from rich.text import Text
from random import random

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Button, Footer, Label, Switch, Header

class Dummy:
    """A dummy class that accepts any arguments and methods, but does nothing."""
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            pass
        return _noop

# Attempt to load gpiozero. If we can't, assume we're not on pi and go into TEST_MODE.
# This includes overloading GPIOLED and GPIOButton with our Dummy class

try:
    from gpiozero import LED as GPIOLED, Button as GPIOButton  # type: ignore[reportAssignmentType]
except ImportError:
    TEST_MODE = True
    
    class GPIOLED(Dummy):
        pass
    
    class GPIOButton(Dummy):
        pass      
else:
    TEST_MODE = False


GPIO_ID_TABLE = {
    # LEDs
    25: "lsled1",
    24: "lsled2",
    23: "lsled3",
    12: "blinkyled1",
    16: "blinkyled2",
    7:  "blasterled",
    8:  "discoleds",
    # Switches / Buttons
    26: "lsswitch",
    19: "blinkyswitch",
    13: "r2d2button",
    6:  "blasterbutton",
    5:  "discoswitch",
}

LEDS = [25,24,23,12,16,7,8]
BUTTONS = [26,19,13,6,5]

gpio_from_id = lambda v: next(k for k, val in GPIO_ID_TABLE.items() if val == v)

# GPIO Handlers
gpio_buttons = [GPIOButton(pin) for pin in BUTTONS]

def handle_gpio_on(button):
    pass

def handle_gpio_off(button):
    pass

for b in gpio_buttons:
    b.when_activated = partial(handle_gpio_on, b)  # type: ignore
    b.when_deactivated = partial(handle_gpio_off, b)  # type: ignore

# Grab initial state
for b in gpio_buttons:
    if b.is_active:
        handle_gpio_on(b)


class ToggleButton(Button):
    def __init__(self, *args, **kwargs):
        self._last_toggle:None|datetime.datetime = None
        self.is_on:bool = False
        self.button_name:str = args[0]
        
        super().__init__(*args, **kwargs)
        
        # GPIO Config
        if self.id and not self.disabled:
            self.gpio_pin = gpio_from_id(self.id)
            self._LED = GPIOLED(self.gpio_pin)  # type: ignore[reportAssignmentType]


    @property
    def last_toggle_str(self) -> str:
        if not self._last_toggle:
            return "never"
        return humanize.naturaltime(datetime.datetime.now() - self._last_toggle)
    
    def _refresh_label(self) -> None:
        """Re-render the label so that the time delta stays up-to-date."""
        if self.disabled: return None

        self.label = Text.assemble(
            (self.button_name, "bold"),
            (f"\nLast Toggle: {self.last_toggle_str}", "dim italic"),
        )
    
    def toggle(self) -> None:
        self.is_on = not self.is_on
        self._last_toggle = datetime.datetime.now()
        
        self.variant = "success" if self.is_on else "default"
        if not TEST_MODE:
            self._LED.toggle()
        self._refresh_label()

    def on_mount(self) -> None:
        """Called by Textual when the widget is added to the DOM."""
        self._refresh_label()
        self.set_interval(1.0, lambda: self._refresh_label())


class ToggleSwitch(Switch):
    def __init__(self, *args, **kwargs):
        self._last_toggle:datetime.datetime|None = None
        super().__init__(*args, **kwargs)

        self.gpio_pin = gpio_from_id(self.id)

    @property
    def last_toggle_str(self) -> str:
        if not self._last_toggle:
            return "never"
        return humanize.naturaltime(datetime.datetime.now() - self._last_toggle)
    
    @property
    def time_label(self) -> Text:
        return Text.assemble((f"{self.last_toggle_str}", "dim italic"))
    
    def _refresh_time_label(self) -> None:
        if not self.id:
            return
        label: Label | None = self.app.query_one(f"#{self.id}-time", Label)  # type: ignore[reportAssignmentType]
        if label:
            label.update(self.time_label)

    def toggle_action(self) -> None:
        self._last_toggle = datetime.datetime.now()
        self._refresh_time_label()

    def random_toggle_test(self) -> None:
        # Toggles the switch 5% of the time
        if random() < 5 / 100:
            self.value = not self.value

    def on_mount(self) -> None:
        self._refresh_time_label()
        self.set_interval(1.0, self._refresh_time_label)
        if TEST_MODE:
            self.set_interval(1, lambda: self.random_toggle_test())


class NoisyTesterApp(App):

    CSS_PATH = "noisy_tester.tcss"

    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the tester")
    ]

    def on_mount(self) -> None:
        self.theme = "catppuccin-mocha"
        self.title = "Noisy Tester"
        self.sub_title = "Test all your LEDs, buttons, and switches."

        if TEST_MODE:
            self.notify(
                "We're running in test mode, because [i]GPIOZero[/i] couldn't be loaded.\nI don't think we're on a pi...",
                severity="error", title="Test Mode"
            )
            self.notify("We'll be randomly toggling switches, to put on a show")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        
        with Container(id="screen"):
            yield Label("LED Toggles", classes="header")
            
            with Container(id="buttons"):
                # Row 1
                yield ToggleButton("Lightsaber 3", id="lsled3")
                yield ToggleButton("", disabled=True)
                yield ToggleButton("Blinky 1", id="blinkyled1")
                yield ToggleButton("Blinky 2", id="blinkyled2")
            
                # Row 2
                yield ToggleButton("Lightsaber 2", id="lsled2")
                yield ToggleButton("", disabled=True)
                yield ToggleButton("", disabled=True)
                yield ToggleButton("", disabled=True)
            
                # Row 3
                yield ToggleButton("Lightsaber 1", id="lsled1")
                yield ToggleButton("", disabled=True)
                yield ToggleButton("Blaster", id="blasterled")
                yield ToggleButton("", disabled=True)
            
                # Row 4
                yield ToggleButton("", disabled=True)
                yield ToggleButton("", disabled=True)
                yield ToggleButton("Disco LEDs x3", id="discoleds")
                yield ToggleButton("", disabled=True)

            yield Label("Switches and Buttons", classes="header")
            with Container(id="switches"):
                # Titles
                yield Label("Lightsaber Switch", classes="switch-label")
                yield Label("Blinky Switch", classes="switch-label")
                yield Label("R2D2 Button", classes="switch-label")
                yield Label("Blaster Button", classes="switch-label")
                yield Label("Disco Switch", classes="switch-label")

                # Switches
                yield ToggleSwitch(id="lsswitch", disabled=True)
                yield ToggleSwitch(id="blinkyswitch", disabled=True)
                yield ToggleSwitch(id="r2d2button", disabled=True)
                yield ToggleSwitch(id="blasterbutton", disabled=True)
                yield ToggleSwitch(id="discoswitch", disabled=True)

                # Times
                yield Label("never", id="lsswitch-time", classes="times")
                yield Label("never", id="blinkyswitch-time", classes="times")
                yield Label("never", id="r2d2button-time", classes="times")
                yield Label("never", id="blasterbutton-time", classes="times")
                yield Label("never", id="discoswitch-time", classes="times")            


    @on(ToggleButton.Pressed)
    def toggle_button(self, event: ToggleButton.Pressed) -> None:
        assert event.button.id is not None

        button:ToggleButton = event.button  # type: ignore[reportAssignmentType]
        button.toggle()

    @on(ToggleSwitch.Changed)
    def toggle_switch(self, event: ToggleSwitch.Changed) -> None:
        switch:ToggleSwitch = event.switch  # type: ignore[reportAssignmentType]
        switch.toggle_action()


if __name__ == "__main__":
    app = NoisyTesterApp()
    app.run()
