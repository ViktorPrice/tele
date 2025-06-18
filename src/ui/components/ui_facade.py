# ui_facade.py

import tkinter as tk
from .main_controller import MainController
from .compact_time_panel import CompactTimePanel
from .compact_filter_panel import CompactFilterPanel
from .compact_diagnostic_panel import CompactDiagnosticPanel
from .compact_parameter_panel import CompactParameterPanel
from .compact_action_panel import CompactActionPanel
from .compact_visualization_panel import CompactVisualizationPanel
from .compact_status_bar import CompactStatusBar
from .compact_navigation import CompactNavigation

class UIFacade:
    """Фасад для создания и управления всеми компонентами UI."""

    def __init__(self, root, model):
        self.root = root
        self.model = model
        self.controller = MainController(model, self)

        # Создание панелей
        self.nav = CompactNavigation(root, self.controller)
        self.nav.pack(fill="x")
        self.status = CompactStatusBar(root, self.controller)
        self.status.pack(fill="x", side="bottom")
        self.filter = CompactFilterPanel(root, self.controller)
        self.filter.pack(side="left", fill="y")
        self.time = CompactTimePanel(root, self.controller)
        self.time.pack(side="left", fill="y")
        self.parameter = CompactParameterPanel(root, self.controller)
        self.parameter.pack(side="left", fill="both", expand=True)
        self.action = CompactActionPanel(root, self.controller)
        self.action.pack(fill="x", side="bottom")
        self.visual = CompactVisualizationPanel(root, self.controller)
        self.visual.pack(fill="both", expand=True)

        # Регистрируем UI в контроллере
        self.controller.set_ui_components(self)
