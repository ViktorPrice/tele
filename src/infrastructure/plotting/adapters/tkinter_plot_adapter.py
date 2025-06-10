#src\infrastructure\plotting\adapters\tkinter_plot_adapter.py
"""
Адаптер для интеграции matplotlib с Tkinter через Clean Architecture
"""
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from matplotlib.text import Annotation


class TkinterPlotAdapter:
    """Адаптер для создания matplotlib графиков в Tkinter"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.plots: Dict[str, Dict[str, Any]] = {}

    def create_plot_widget(self, parent, figure: Figure,
                           title: str, parameters: List[Dict[str, Any]]) -> Tuple[FigureCanvasTkAgg, ttk.Frame]:
        """Создание виджета графика"""
        try:
            # Контейнер для графика
            plot_container = ttk.Frame(parent)
            plot_container.grid_rowconfigure(0, weight=1)
            plot_container.grid_columnconfigure(0, weight=1)

            # Canvas для matplotlib
            canvas = FigureCanvasTkAgg(figure, plot_container)
            canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

            # Toolbar
            toolbar_frame = ttk.Frame(plot_container)
            toolbar_frame.grid(row=1, column=0, sticky="ew")

            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
            toolbar.pack(fill=tk.X)

            # Информационная панель
            info_panel = self._create_info_panel(plot_container, parameters)
            info_panel.grid(row=2, column=0, sticky="ew", pady=5)

            # Сохраняем информацию о графике
            self.plots[title] = {
                'container': plot_container,
                'canvas': canvas,
                'toolbar': toolbar,
                'info_panel': info_panel,
                'figure': figure,
                'parameters': parameters
            }

            return canvas, info_panel

        except Exception as e:
            self.logger.error(f"Ошибка создания виджета графика: {e}")
            raise

    def _create_info_panel(self, parent, parameters: List[Dict[str, Any]]) -> ttk.Frame:
        """Создание информационной панели"""
        info_frame = ttk.Frame(parent)

        # Информация о параметрах
        info_text = f"Параметров: {len(parameters)}"
        if parameters:
            lines = set(p.get('line', 'Unknown') for p in parameters)
            info_text += f" | Линий: {len(lines)}"

        info_label = ttk.Label(info_frame, text=info_text, font=('Arial', 8))
        info_label.pack(side=tk.LEFT, padx=5)

        return info_frame

    def update_plot(self, title: str, new_figure: Figure):
        """Обновление существующего графика"""
        if title in self.plots:
            plot_info = self.plots[title]
            plot_info['canvas'].figure = new_figure
            plot_info['canvas'].draw()

    def remove_plot(self, title: str):
        """Удаление графика"""
        if title in self.plots:
            plot_info = self.plots[title]
            plt.close(plot_info['figure'])
            del self.plots[title]

    def cleanup_all(self):
        """Очистка всех графиков"""
        for title in list(self.plots.keys()):
            self.remove_plot(title)

    def reset_zoom_all(self):
        """Сброс масштабирования для всех графиков"""
        for plot_info in self.plots.values():
            figure = plot_info['figure']
            for ax in figure.get_axes():
                ax.autoscale()
            plot_info['canvas'].draw()

    def clear_annotations_all(self):
        """Очистка аннотаций для всех графиков"""
        for plot_info in self.plots.values():
            figure = plot_info['figure']
            for ax in figure.get_axes():
                # Удаляем аннотации (если есть)
                for artist in ax.get_children():
                    if isinstance(artist, Annotation):
                        artist.remove()
            plot_info['canvas'].draw()
