# src/ui/components/horizontal_action_panel.py - СОЗДАТЬ ФАЙЛ

"""
Горизонтальная панель действий в одну строку
"""
import tkinter as tk
from tkinter import ttk
import logging

class HorizontalActionPanel(ttk.Frame):
    """Горизонтальная панель действий"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        self._setup_horizontal_ui()

    def _setup_horizontal_ui(self):
        """Настройка горизонтального UI"""
        # Все кнопки в одну строку
        buttons = [
            ("📊 Построить график", self._build_plot),
            ("📄 Создать отчет", self._generate_report),
            ("📋 Создать SOP", self._generate_sop),
            ("🧪 Тест данных", self._load_test_data)
        ]

        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(self, text=text, command=command, width=15)
            btn.grid(row=0, column=i, padx=2, pady=2)

    def _build_plot(self):
        if self.controller:
            self.controller.build_plot()

    def _generate_report(self):
        if self.controller:
            self.controller.generate_report()

    def _generate_sop(self):
        if self.controller:
            self.controller.generate_sop()

    def _load_test_data(self):
        if self.controller:
            self.controller.load_test_data()

    def cleanup(self):
        self.controller = None
