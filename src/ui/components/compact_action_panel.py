# compact_action_panel.py

import tkinter as tk
from tkinter import ttk, filedialog
import logging
from typing import Any

class CompactActionPanel(ttk.Frame):
    """Универсальная компактная панель действий."""

    def __init__(self, parent: ttk.Widget, controller: Any = None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_ui()
        self.logger.info("CompactActionPanel initialized")  # [4]

    def _setup_ui(self):
        """Создаёт кнопки: загрузка CSV, построение графиков, отчёт, SOP.»"""
        frame = ttk.LabelFrame(self, text="Действия", padding=5)
        frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(frame, text="Загрузить CSV", command=self._upload_csv).pack(side="left", padx=2)
        ttk.Button(frame, text="Построить графики", command=self._plot).pack(side="left", padx=2)
        ttk.Button(frame, text="Генерировать отчёт", command=self._report).pack(side="left", padx=2)
        ttk.Button(frame, text="Создать SOP", command=self._sop).pack(side="left", padx=2)

    def _upload_csv(self):
        """Вызывает контроллер для диалога загрузки CSV."""
        if hasattr(self.controller, 'upload_csv'):
            self.controller.upload_csv()  # [1]

    def _plot(self):
        """Запускает построение графиков через контроллер."""
        if hasattr(self.controller, 'plot_selected_parameters'):
            self.controller.plot_selected_parameters()  # [1]

    def _report(self):
        """Запускает генерацию отчёта через контроллер."""
        if hasattr(self.controller, 'generate_report'):
            self.controller.generate_report()  # [1]

    def _sop(self):
        """Запускает создание SOP через контроллер."""
        if hasattr(self.controller, 'create_sop'):
            self.controller.create_sop()  # [1]
        else:
            self.logger.warning("SOP manager not available")  # [4]

    def set_loading_state(self, loading: bool):
        """Блокирует или разблокирует кнопки при загрузке/обработке."""
        state = tk.DISABLED if loading else tk.NORMAL
        for child in self.winfo_children():
            try:
                child.configure(state=state)
            except Exception:
                pass  # игнорируем виджеты без state ¹³

    def cleanup(self):
        """Очистка ресурсов панели и удаление виджетов."""
        self.controller = None
        for child in self.winfo_children():
            child.destroy()
        self.logger.info("CompactActionPanel cleaned up")  # [4]
