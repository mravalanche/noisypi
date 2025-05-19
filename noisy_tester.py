import datetime
import humanize
from functools import partial
from random import random

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult  # Textual <= 0.52 has no get_app()
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Button, Footer, Header, Label, Switch

# Global reference to the running Textual app (set in NoisyTesterApp.on_mount)
APP: "NoisyTesterApp | None" = None

# ────────────────────────────────────────────────────────────────────────────
# Test‑mode stubs (run happily on non‑Pi systems)
# ────────────────────────────────────────────────────────────────────────────
class Dummy:
    """No‑op replacement for gpiozero classes when not on a Pi."""

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, _name):
        return lambda *a, **kw: None  # noqa: E731 – terse no‑op


try:
    from gpiozero import LED as GPIOLED, Button as GPIOButton  # type: ignore
except ImportError:  # Desktops / CI boxes
    TEST_MODE = True

    class GPIOLED(Dummy):
        pass

    class GPIOButton(Dummy):
        pass
else:
    TEST_MODE = False

# ────────────────────────────────────────────────────────────────────────────
# GPIO pin ↔ widget‑id mapping
# ────────────────────────────────────────────────────────────────────────────
GPIO_ID_TABLE: dict[int, str] = {
    # LEDs
    25: "lsled1",
    24: "lsled2",
    23: "lsled3",
    12: "blinkyled1",
    16: "blinkyled2",
    7: "blasterled",
    8: "discoleds",
    # Switches / Buttons
    26: "lsswitch",
    19: "blinkyswitch",
    13: "r2d2button",
    6: "blasterbutton",
    5: "discoswitch",
}

LEDS = [25, 24, 23, 12, 16, 7, 8]
BUTTONS = [26, 19, 13, 6, 5]

# Given a widget id (e.g. "lsled1") return its GPIO pin number
gpio_from_id = lambda wid: next(p for p, i in GPIO_ID_TABLE.items() if i == wid)

# ────────────────────────────────────────────────────────────────────────────
# GPIO → UI helpers
# ────────────────────────────────────────────────────────────────────────────

gpio_buttons = [GPIOButton(pin) for pin in BUTTONS]


def _set_switch_state_from_thread(widget_id: str, state: bool) -> None:
    """Ensure DOM mutation happens on the main Textual thread."""

    if APP is None:
        return  # App not mounted yet

    def _do():
        switch = APP.query_one(f"#{widget_id}", ToggleSwitch, expect_none=True)
        if switch and not switch.disabled:
            switch.value = state  # fires Switch.Changed event

    APP.call_from_thread(_do)


# gpiozero callback wrappers -------------------------------------------------

def _pin_from_btn(btn) -> int | None:
    return getattr(getattr(btn, "pin", None), "number", None)


def handle_gpio_on(btn) -> None:
    wid = GPIO_ID_TABLE.get(_pin_from_btn(btn))
    if wid:
        _set_switch_state_from_thread(wid, True)


def handle_gpio_off(btn) -> None:
    wid = GPIO_ID_TABLE.get(_pin_from_btn(btn))
    if wid:
        _set_switch_state_from_thread(wid, False)


for b in gpio_buttons:
    b.when_activated = partial(handle_gpio_on, b)  # type: ignore
    b.when_deactivated = partial(handle_gpio_off, b)  # type: ignore

# Seed initial states so UI matches hardware at startup
for b in gpio_buttons:
    if getattr(b, "is_active", False):
        handle_gpio_on(b)

# ────────────────────────────────────────────────────────────────────────────
# Widgets
# ────────────────────────────────────────────────────────────────────────────
class ToggleButton(Button):
    """A Textual button that mirrors an output GPIO LED."""

    def __init__(self, *args, **kwargs):
        self._last_toggle: datetime.datetime | None = None
        self.is_on = False
        self.button_name: str = args[0] if args else ""
        super().__init__(*args, **kwargs)

        if self.id and not self.disabled and not TEST_MODE:
            self.gpio_pin = gpio_from_id(self.id)
            self._led = GPIOLED(self.gpio_pin)  # type: ignore
        else:
            self._led = Dummy()

    # Helpers ---------------------------------------------------------
    @property
    def last_toggle_str(self) -> str:
        return "never" if self._last_toggle is None else humanize.naturaltime(
            datetime.datetime.now() - self._last_toggle
        )

    def _refresh_label(self) -> None:
        if self.disabled:
            return
        self.label = Text.assemble(
            (self.button_name, "bold"),
            (f"\nLast Toggle: {self.last_toggle_str}", "dim italic"),
        )

    # Public ----------------------------------------------------------
    def toggle(self) -> None:
        self.is_on = not self.is_on
        self._last_toggle = datetime.datetime.now()
        self.variant = "success" if self.is_on else "default"
        self._led.toggle()
        self._refresh_label()

    # Lifecycle -------------------------------------------------------
    def on_mount(self):
        self._refresh_label()
        self.set_interval(1.0, self._refresh_label)


class ToggleSwitch(Switch):
    """A Textual switch that keeps an accompanying time‑stamp label fresh."""

    def __init__(self, *args, **kwargs):
        self._last_toggle: datetime.datetime | None = None
        super().__init__(*args, **kwargs)

    # Helpers ---------------------------------------------------------
    @property
    def last_toggle_str(self) -> str:
        return "never" if self._last_toggle is None else humanize.naturaltime(
            datetime.datetime.now() - self._last_toggle
        )

    def _refresh_time_label(self) -> None:
        if not self.id:
            return
        lbl = self.app.query_one(f"#{self.id}-time", Label)  # type: ignore
        if lbl:
            lbl.update(Text.assemble((self.last_toggle_str, "dim italic")))

    # Public ----------------------------------------------------------
    def toggle_action(self):
        self._last_toggle = datetime.datetime.now()
        self._refresh_time_label()

    # Random twiddle for demo mode ------------------------------------
    def _demo_twiddle(self):
        if random() < 0.05:
            self.value = not self.value

    # Lifecycle -------------------------------------------------------
    def on_mount(self):
        self._refresh_time_label()
        self.set_interval(1.0, self._refresh_time_label)
        if TEST_MODE:
            self.set_interval(1.0, self._demo_twiddle)


# ────────────────────────────────────────────────────────────────────────────
# App
# ────────────────────────────────────────────────────────────────────────────
class NoisyTesterApp(App):
    CSS_PATH = "noisy_tester.tcss"
    BINDINGS = [Binding("q", "quit", "Quit the tester")]

    def on_mount(self):
        global APP
        APP = self  # let GPIO callbacks talk to us

        self.theme = "catppuccin-mocha"
        self.title = "Noisy Tester"
        self.sub_title = "Test all your LEDs, buttons, and switches."

        if TEST_MODE:
            self.notify(
                "Running in TEST_MODE – gpiozero unavailable; random switches will toggle.",
                severity="warning",
            )

    # Layout ----------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        with Container(id="screen"):
            # LED buttons ------------------------------------------------
            yield Label("LED Toggles", classes="header")
            with Container(id="buttons"):
                # Row 1
                yield ToggleButton("Lightsaber 1", id="lsled1")
                yield ToggleButton("", disabled=True)
                yield ToggleButton("Blinky 1", id="blinkyled1")
                yield ToggleButton("Blinky 2", id="blinkyled2")
                # Row 2
                yield ToggleButton("Lightsaber 2", id="lsled2")
                yield ToggleButton("", disabled=True)
                yield ToggleButton("", disabled=True)
                yield ToggleButton("", disabled=True)
                # Row 3
                yield ToggleButton("Lightsaber 3", id="lsled3")
                yield ToggleButton("", disabled=True)
                yield ToggleButton("Blaster", id="blasterled")
                yield ToggleButton("", disabled=True)
                # Row 4
                yield ToggleButton("", disabled=True)
                yield ToggleButton("", disabled=True)
                yield ToggleButton("Disco LEDs x3", id="discoleds")
                yield ToggleButton("", disabled=True)

            # Switches / Buttons ---------------------------------------
            yield Label("Switches and Buttons", classes="header")
            with Container(id="switches"):
                for title in [
                    "Lightsaber Switch",
                    "Blinky Switch",
                    "R2D2 Button",
                    "Blaster Button",
                    "Disco Switch",
                ]:
                    yield Label(title, classes="switch-label")

                yield ToggleSwitch(id="lsswitch", disabled=True)
                yield ToggleSwitch(id="blinkyswitch", disabled=True)
                yield ToggleSwitch(id="r2d2button", disabled=True)
                yield ToggleSwitch(id="blasterbutton", disabled=True)
                yield ToggleSwitch(id="discoswitch", disabled=True)

                for sid in [
                    "lsswitch",
                    "blinkyswitch",
                    "r2d2button",
                    "blasterbutton",
                    "discoswitch",
                ]:
                    yield Label("never", id=f"{sid}-time", classes="times")

    # Event handlers ---------------------------------------------------
    @on(ToggleButton.Pressed)
    def _on_button_pressed(self, event: ToggleButton.Pressed):
        event.button.toggle()

    @on(ToggleSwitch.Changed)
    def _on_switch_changed(self, event: ToggleSwitch.Changed):
        event.switch.toggle_action()


if __name__ == "__main__":
    NoisyTesterApp().run()
