"""textual_gpio_interface.py
--------------------------------------------------
Super‑slim Textual UI (gap‑free)
• **9 buttons** in custom 4×4 grid.
• Each shows **last on** using `humanize`.
• **6 read‑only indicators** below.
• Big red **Quit** button; *q* key works too.

Grid pattern:
```
x-xx
x---
x-x-
-xxx
```

Run:
```bash
pip install textual rich humanize
python textual_gpio_interface.py
```
"""
from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import Callable, List, Sequence

import humanize
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Button, Static

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(text: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z_-]", "_", text)
    return f"n_{slug}" if slug and slug[0].isdigit() else slug or "unnamed"


class TimeLabel(Static):
    """Shows *relative time* since the stamp."""

    _stamp: reactive[datetime] = reactive(datetime.now())

    def reset(self) -> None:
        self._stamp = datetime.now()
        self.refresh()

    def render(self) -> Text:  # noqa: D401
        return Text(humanize.naturaltime(datetime.now() - self._stamp), style="dimgray")


class ToggleBlock(Container):
    """Button + “last on” label."""

    def __init__(
        self,
        name: str,
        *,
        color_off: str = "#595959",
        color_on: str = "green",
        on_toggle: Callable[[str, bool], None] | None = None,
    ) -> None:
        super().__init__(id=f"block-{_slug(name)}", name=name)
        self._state = False
        self._color_off = color_off
        self._color_on = color_on
        self._callback = on_toggle or (lambda *_: None)
        self._last_on = TimeLabel()

    def compose(self) -> ComposeResult:  # noqa: D401
        self._btn = Button(self._label, id=f"btn-{_slug(self.name)}")
        self._btn.styles.background = self._bg
        yield self._btn
        yield self._last_on

    async def on_button_pressed(self, _: Button.Pressed) -> None:  # noqa: D401
        self._state = not self._state
        self._btn.label = self._label
        self._btn.styles.background = self._bg
        if self._state:
            self._last_on.reset()
        self._callback(self.name, self._state)

    @property
    def _label(self) -> str:
        return f"{self.name}: {'ON' if self._state else 'OFF'}"

    @property
    def _bg(self) -> str:
        return self._color_on if self._state else self._color_off


class IndicatorBlock(Container):
    """Read‑only indicator block."""

    def __init__(
        self,
        name: str,
        *,
        color_off: str = "#595959",
        color_on: str = "dodgerblue",
    ) -> None:
        super().__init__(id=f"ind-{_slug(name)}", name=name)
        self._state = False
        self._color_off = color_off
        self._color_on = color_on
        self._label = Static(self._render_label())
        self._label.styles.background = self._bg

    def compose(self) -> ComposeResult:  # noqa: D401
        yield self._label

    def set(self, value: bool) -> None:
        if value != self._state:
            self._state = value
            self._label.update(self._render_label())
            self._label.styles.background = self._bg

    def _render_label(self) -> str:
        return f"{self.name}: {'ON' if self._state else 'OFF'}"

    @property
    def _bg(self) -> str:
        return self._color_on if self._state else self._color_off


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

class GPIOInterface(App):
    """Buttons + indicators + quit."""

    CSS = """
    #button-grid {
        layout: grid;
        grid-size: 4;
        padding: 1;
    }
    #indicators {
        layout: horizontal;
        padding: 1;
        content-align: center middle;
    }
    #controls {
        padding: 0 1 1 1;
        layout: horizontal;
        content-align: center middle;
    }
    Button { width: 18; }
    #quit-btn { background: red; color: white; }
    TimeLabel { width: 100%; content-align: center middle; }
    """

    BINDINGS = [("q", "quit", "Quit")]

    GRID_PATTERN = [
        "x-xx",
        "x---",
        "x-x-",
        "-xxx",
    ]

    def __init__(
        self,
        button_names: Sequence[str] | None = None,
        indicator_names: Sequence[str] | None = None,
        on_button_toggle: Callable[[str, bool], None] | None = None,
    ) -> None:
        super().__init__()
        self._button_names = button_names or [f"Btn {i}" for i in range(1, 10)]
        self._indicator_names = indicator_names or [f"Sw {i}" for i in range(1, 7)]
        self._on_button = on_button_toggle or (lambda *_: None)
        self._buttons: List[ToggleBlock] = []
        self._indicators: List[IndicatorBlock] = []

    def compose(self) -> ComposeResult:  # noqa: D401
        name_iter = iter(self._button_names)
        with Container(id="button-grid"):
            for row in self.GRID_PATTERN:
                for cell in row:
                    if cell == "x":
                        tb = ToggleBlock(next(name_iter), on_toggle=self._on_button)
                        self._buttons.append(tb)
                        yield tb
                    else:
                        yield Static()
        with Container(id="indicators"):
            for n in self._indicator_names:
                ind = IndicatorBlock(n)
                self._indicators.append(ind)
                yield ind
        with Container(id="controls"):
            yield Button("Quit", id="quit-btn")

    async def on_button_pressed(self, event: Button.Pressed) -> None:  # noqa: D401
        if event.button.id == "quit-btn":
            self.exit()

    def set_indicator(self, idx: int | str, value: bool) -> None:
        if isinstance(idx, str):
            idx = self._indicator_names.index(idx)
        self._indicators[idx].set(value)

    async def on_mount(self) -> None:  # noqa: D401
        self.set_interval(1.0, lambda: [b._last_on.refresh() for b in self._buttons])  # type: ignore[attr-defined]


if __name__ == "__main__":

    async def main() -> None:
        app = GPIOInterface()
        run_coro = app.run_async() if hasattr(app, "run_async") else app.run_asyncio()  # type: ignore[attr-defined]
        await run_coro

    asyncio.run(main())
