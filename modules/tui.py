
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Group
from collections import defaultdict

class TuiManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TuiManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.layout = Layout()
        self.panels = {}
        self.panel_content = defaultdict(str)
        self.live = Live(self.layout, screen=True, redirect_stderr=False)

    def add_panel(self, name, title):
        """Adds a new panel to the TUI."""
        self.panels[name] = Panel("", title=title, border_style="green")
        self._update_layout()

    def update_panel(self, name, content):
        """Updates the content of a panel."""
        self.panel_content[name] += content
        self.panels[name].renderable = self.panel_content[name]

    def _update_layout(self):
        """Updates the layout with the current panels."""
        self.layout.split_column(*self.panels.values())

    def start(self):
        """Starts the live display."""
        self.live.start()

    def stop(self):
        """Stops the live display."""
        self.live.stop()
