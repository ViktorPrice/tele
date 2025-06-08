"""
Базовый класс для всех фильтров
"""
from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any, Callable
import logging

class BaseFilter(ABC):
    """Абстрактный базовый класс для фильтров"""
    
    def __init__(self, parent, title: str, on_change_callback: Callable = None):
        self.parent = parent
        self.title = title
        self.on_change_callback = on_change_callback
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Переменные фильтра
        self.filter_vars: Dict[str, tk.BooleanVar] = {}
        self.frame = None
        
        self.create_widgets()
    
    @abstractmethod
    def get_filter_items(self) -> List[str]:
        """Получение элементов для фильтрации"""
        pass
    
    @abstractmethod
    def get_display_name(self, item: str) -> str:
        """Получение отображаемого имени элемента"""
        pass
    
    def create_widgets(self):
        """Создание виджетов фильтра"""
        self.frame = ttk.LabelFrame(self.parent, text=self.title)
        
        # Кнопки управления
        self.create_control_buttons()
        
        # Чекбоксы
        self.create_checkboxes()
    
    def create_control_buttons(self):
        """Создание кнопок управления"""
        btn_frame = ttk.Frame(self.frame)
        btn_frame.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        
        ttk.Button(btn_frame, text="Все", width=4,
                  command=lambda: self.toggle_all(True)).grid(row=0, column=0, padx=1)
        
        ttk.Button(btn_frame, text="×", width=2,
                  command=lambda: self.toggle_all(False)).grid(row=0, column=1, padx=1)
    
    def create_checkboxes(self):
        """Создание чекбоксов для элементов фильтра"""
        cb_frame = ttk.Frame(self.frame)
        cb_frame.grid(row=1, column=0, sticky="ew", padx=1, pady=1)
        
        items = self.get_filter_items()
        for i, item in enumerate(items):
            var = tk.BooleanVar(value=True)
            self.filter_vars[item] = var
            var.trace_add('write', lambda *args: self.on_filter_change())
            
            display_name = self.get_display_name(item)
            cb = ttk.Checkbutton(cb_frame, text=display_name, variable=var)
            
            # Размещение в сетке (настраивается в подклассах)
            self.place_checkbox(cb, i)
    
    def place_checkbox(self, checkbox: ttk.Checkbutton, index: int):
        """Размещение чекбокса (переопределяется в подклассах)"""
        checkbox.grid(row=index//2, column=index % 2, sticky="w", padx=1, pady=1)
    
    def toggle_all(self, value: bool):
        """Переключение всех фильтров"""
        for var in self.filter_vars.values():
            var.set(value)
        self.on_filter_change()
    
    def on_filter_change(self):
        """Обработчик изменения фильтра"""
        if self.on_change_callback:
            self.on_change_callback()
    
    def get_selected_items(self) -> List[str]:
        """Получение выбранных элементов"""
        return [item for item, var in self.filter_vars.items() if var.get()]
    
    def set_selected_items(self, items: List[str]):
        """Установка выбранных элементов"""
        for item, var in self.filter_vars.items():
            var.set(item in items)
    
    def grid(self, **kwargs):
        """Размещение фильтра"""
        self.frame.grid(**kwargs)

class SignalTypeFilter(BaseFilter):
    """Фильтр по типам сигналов"""
    
    def __init__(self, parent, on_change_callback=None):
        self.signal_types = ['B', 'BY', 'W', 'DW', 'F', 'WF']
        super().__init__(parent, "Тип", on_change_callback)
    
    def get_filter_items(self) -> List[str]:
        return self.signal_types
    
    def get_display_name(self, item: str) -> str:
        return item
    
    def place_checkbox(self, checkbox: ttk.Checkbutton, index: int):
        checkbox.grid(row=index//3, column=index % 3, sticky="w", padx=1, pady=1)

class LineFilter(BaseFilter):
    """Фильтр по линиям связи"""
    
    def __init__(self, parent, on_change_callback=None):
        self.lines = []
        super().__init__(parent, "Линии", on_change_callback)
    
    def get_filter_items(self) -> List[str]:
        return self.lines
    
    def get_display_name(self, item: str) -> str:
        # Сокращение длинных названий
        return item[:10] + "..." if len(item) > 10 else item
    
    def update_lines(self, lines: List[str]):
        """Обновление списка линий"""
        # Сохраняем текущие значения
        current_values = {line: var.get() for line, var in self.filter_vars.items()}
        
        # Очищаем старые чекбоксы
        for widget in self.frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Checkbutton):
                        child.destroy()
        
        # Обновляем список и пересоздаем чекбоксы
        self.lines = lines
        self.filter_vars.clear()
        self.create_checkboxes()
        
        # Восстанавливаем значения
        for line, value in current_values.items():
            if line in self.filter_vars:
                self.filter_vars[line].set(value)

class WagonFilter(BaseFilter):
    """Фильтр по номерам вагонов"""
    
    def __init__(self, parent, on_change_callback=None):
        self.wagon_numbers = [str(i) for i in range(1, 16)]
        super().__init__(parent, "Вагоны", on_change_callback)
    
    def get_filter_items(self) -> List[str]:
        return self.wagon_numbers[:8]  # Показываем только первые 8
    
    def get_display_name(self, item: str) -> str:
        return item
    
    def place_checkbox(self, checkbox: ttk.Checkbutton, index: int):
        checkbox.grid(row=index//4, column=index % 4, sticky="w", padx=1, pady=1)
