# compact_navigation.py

import tkinter as tk
from tkinter import ttk
import logging

class CompactNavigation(ttk.Frame):
    """Панель навигации и поиска."""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(self, text="Найти", command=self.on_search).pack(side="left", padx=5)

        self.nav_buttons = {}
        for name in ["Фильтры", "Время", "Параметры", "Графики"]:
            btn = ttk.Button(self, text=name, command=lambda n=name: self.on_navigate(n))
            btn.pack(side="left", padx=2)
            self.nav_buttons[name] = btn

    def on_search(self):
        query = self.search_var.get()
        if self.controller and hasattr(self.controller, 'search_parameters'):
            self.controller.search_parameters(query)
        self.logger.debug(f"Search: {query}")

    def on_navigate(self, section):
        if self.controller and hasattr(self.controller, 'navigate_to'):
            self.controller.navigate_to(section)
        self.logger.debug(f"Navigate to: {section}")

    def cleanup(self):
        self.controller = None
        for w in self.winfo_children():
            w.destroy()
        self.logger.info("Navigation cleaned up")
