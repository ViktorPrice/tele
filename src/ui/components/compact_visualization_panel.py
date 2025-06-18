# compact_visualization_panel.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from typing import Any, Dict, List, Tuple
from datetime import datetime
from .base_ui_component import BaseUIComponent
from ...core.application.usecases.plotgenerationusecase import (
    PlotGenerationUseCase, PlotGenerationRequest
)
from ...infrastructure.plotting.adapters.tkinterplotadapter import TkinterPlotAdapter

class CompactVisualizationPanel(BaseUIComponent):
    """
    Компактная панель для отображения графиков и таблиц.
    Использует Use Case и адаптер для рисования в Tkinter.
    """

    def __init__(self, parent: ttk.Widget, controller: Any = None):
        super().__init__(parent, controller)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.plot_usecase: PlotGenerationUseCase = None
        self.plot_adapter = TkinterPlotAdapter()
        self.tabs: Dict[str, ttk.Frame] = {}
        self.setup_ui()
        self.setup_usecase()
        self.logger.info("CompactVisualizationPanel initialized")

    def setup_ui(self):
        """Создание панели управления и области вкладок."""
        self.grid(sticky="nsew")
        # Панель управления
        controls = ttk.LabelFrame(self, text="Графики", padding=5)
        controls.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        controls.grid_columnconfigure(1, weight=1)

        ttk.Button(controls, text="Обновить", command=self.refresh_all).grid(row=0, column=0, padx=2)
        ttk.Button(controls, text="Экспорт всех", command=self.export_all).grid(row=0, column=1, padx=2)
        ttk.Button(controls, text="Очистить все", command=self.clear_all).grid(row=0, column=2, padx=2)

        # Notebook для вкладок графиков
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def setup_usecase(self):
        """Инициализация Use Case построения графиков."""
        try:
            self.plot_usecase = PlotGenerationUseCase(self.controller.model.parameter_repository,
                                                      self.controller.model.data_loader)
            self.logger.info("PlotGenerationUseCase initialized")
        except Exception as e:
            self.logger.error(f"UseCase init error: {e}")

    def build_charts(self, params: List[Dict[str, Any]], 
                     time_range: Tuple[str, str]):
        """Запуск генерации и отрисовки графиков по списку параметров."""
        self.clear_all()
        start, end = time_range
        req = PlotGenerationRequest(parameters=params, 
                                    from_time=start, to_time=end)
        try:
            charts = self.plot_usecase.execute(req)
            for name, fig in charts.items():
                frame = ttk.Frame(self.notebook)
                self.notebook.add(frame, text=name)
                self.plot_adapter.draw_figure(frame, fig)
                self.tabs[name] = frame
            self.logger.info(f"Built {len(charts)} charts")
        except Exception as e:
            self.logger.error(f"Build error: {e}")
            messagebox.showerror("Ошибка", f"Не удалось построить графики: {e}")

    def refresh_all(self):
        """Обновить текущие графики заново."""
        if not self.tabs:
            return
        # Сохраняем параметры и время из первой вкладки
        params = self.controller.get_selected_parameters()
        time_range = self.controller.get_time_range()
        self.build_charts(params, time_range)

    def export_all(self):
        """Экспорт всех построенных графиков в файлы PNG."""
        if not self.tabs:
            return
        folder = filedialog.askdirectory(title="Папка для экспорта")
        if not folder:
            return
        count = self.plot_adapter.export_all(self.tabs, folder)
        messagebox.showinfo("Экспорт", f"Экспортировано {count} графиков")

    def clear_all(self):
        """Удаление всех вкладок и фигур."""
        for name, frame in list(self.tabs.items()):
            self.notebook.forget(frame)
            frame.destroy()
            self.tabs.pop(name, None)
        self.logger.info("Cleared all charts")

    def cleanup(self):
        """Очистка ресурсов панели."""
        self.plot_adapter.cleanup()
        for frame in self.tabs.values():
            frame.destroy()
        self.tabs.clear()
        super().cleanup()
