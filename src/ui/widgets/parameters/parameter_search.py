"""
Виджет поиска параметров
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Callable, Optional

class ParameterSearchWidget:
    """Виджет поиска параметров с автодополнением"""
    
    def __init__(self, parent, on_search_callback: Callable[[str], None]):
        self.parent = parent
        self.on_search = on_search_callback
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Состояние
        self.search_var = tk.StringVar()
        self.results_count = tk.StringVar(value="")
        
        # Виджеты
        self.frame: Optional[ttk.Frame] = None
        self.search_entry: Optional[ttk.Entry] = None
        self.clear_button: Optional[ttk.Button] = None
        self.results_label: Optional[ttk.Label] = None
        
        self.create_widgets()
        self.setup_bindings()
    
    def create_widgets(self):
        """Создание виджетов поиска"""
        self.frame = ttk.Frame(self.parent)
        self.frame.grid_columnconfigure(1, weight=1)
        
        # Метка
        ttk.Label(self.frame, text="Поиск:").grid(row=0, column=0, padx=5, sticky="w")
        
        # Поле ввода
        self.search_entry = ttk.Entry(self.frame, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Кнопка очистки
        self.clear_button = ttk.Button(self.frame, text="×", width=3, command=self.clear_search)
        self.clear_button.grid(row=0, column=2, padx=5)
        
        # Счетчик результатов
        self.results_label = ttk.Label(self.frame, textvariable=self.results_count, font=('Arial', 8))
        self.results_label.grid(row=0, column=3, padx=5)
    
    def setup_bindings(self):
        """Настройка привязок событий"""
        # Поиск в реальном времени с задержкой
        self.search_var.trace_add('write', self.on_search_change)
        
        # Горячие клавиши
        self.search_entry.bind('<Return>', lambda e: self.perform_search())
        self.search_entry.bind('<Escape>', lambda e: self.clear_search())
    
    def on_search_change(self, *args):
        """Обработчик изменения поискового запроса"""
        # Задержка для избежания слишком частых запросов
        if hasattr(self, '_search_after_id'):
            self.parent.after_cancel(self._search_after_id)
        
        self._search_after_id = self.parent.after(300, self.perform_search)
    
    def perform_search(self):
        """Выполнение поиска"""
        query = self.search_var.get().strip()
        if self.on_search:
            self.on_search(query)
    
    def clear_search(self):
        """Очистка поиска"""
        self.search_var.set("")
        self.update_results_count(0)
    
    def update_results_count(self, count: int):
        """Обновление счетчика результатов"""
        if count == 0:
            self.results_count.set("")
        elif count == 1:
            self.results_count.set("1 результат")
        else:
            self.results_count.set(f"{count} результатов")
    
    def grid(self, **kwargs):
        """Размещение виджета"""
        if self.frame:
            self.frame.grid(**kwargs)
