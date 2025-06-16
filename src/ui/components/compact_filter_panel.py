# src/ui/components/compact_filter_panel.py - СОЗДАТЬ ФАЙЛ

"""
Компактная панель фильтров в одну строку
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, List

class CompactFilterPanel(ttk.Frame):
    """Компактная панель фильтров в одну строку"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Переменные для чекбоксов
        self.signal_vars = {}
        self.line_vars = {}
        self.wagon_vars = {}

        self._setup_compact_ui()

    def _setup_compact_ui(self):
        """Настройка компактного UI в одну строку"""
        # Настройка сетки
        self.grid_columnconfigure(1, weight=0)  # Типы сигналов
        self.grid_columnconfigure(3, weight=1)  # Линии (растягиваются)
        self.grid_columnconfigure(5, weight=0)  # Вагоны

        row = 0

        # Типы сигналов
        ttk.Label(self, text="Типы:", font=('Arial', 9)).grid(row=row, column=0, sticky="w")

        types_frame = ttk.Frame(self)
        types_frame.grid(row=row, column=1, sticky="w", padx=(5, 10))

        signal_types = ['B', 'BY', 'W', 'DW', 'F', 'WF']
        for i, signal_type in enumerate(signal_types):
            var = tk.BooleanVar()
            var.set(True)
            self.signal_vars[signal_type] = var

            checkbox = ttk.Checkbutton(
                types_frame,
                text=signal_type,
                variable=var,
                command=self._on_filter_changed
            )
            checkbox.grid(row=0, column=i, sticky="w", padx=2)

        # Разделитель
        ttk.Separator(self, orient='vertical').grid(row=row, column=2, sticky="ns", padx=5)

        # Линии связи
        ttk.Label(self, text="Линии:", font=('Arial', 9)).grid(row=row, column=3, sticky="w")

        lines_frame = ttk.Frame(self)
        lines_frame.grid(row=row, column=3, sticky="ew", padx=(5, 10))

        # Разделитель
        ttk.Separator(self, orient='vertical').grid(row=row, column=4, sticky="ns", padx=5)

        # Вагоны
        ttk.Label(self, text="Вагоны:", font=('Arial', 9)).grid(row=row, column=5, sticky="w")

        wagons_frame = ttk.Frame(self)
        wagons_frame.grid(row=row, column=5, sticky="w", padx=(5, 0))

        for i in range(1, 9):  # Вагоны 1-8
            var = tk.BooleanVar()
            var.set(True)
            self.wagon_vars[str(i)] = var

            checkbox = ttk.Checkbutton(
                wagons_frame,
                text=str(i),
                variable=var,
                command=self._on_filter_changed
            )
            checkbox.grid(row=0, column=i-1, sticky="w", padx=1)

    def _on_filter_changed(self):
        """Обработка изменения фильтров"""
        if self.controller:
            self.controller.apply_filters()

    def update_line_checkboxes(self, lines: List[str]):
        """Обновление чекбоксов линий"""
        # Простая реализация - показываем количество
        if hasattr(self, 'lines_label'):
            self.lines_label.config(text=f"Линий: {len(lines)}")

    def get_selected_filters(self) -> Dict[str, Any]:
        """Получение выбранных фильтров"""
        return {
            'signal_types': [k for k, v in self.signal_vars.items() if v.get()],
            'lines': [k for k, v in self.line_vars.items() if v.get()],
            'wagons': [k for k, v in self.wagon_vars.items() if v.get()],
        }

    def cleanup(self):
        self.controller = None
