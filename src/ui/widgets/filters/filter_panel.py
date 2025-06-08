"""
Основная панель фильтров с использованием композиции
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, List, Callable
from .base_filter import SignalTypeFilter, LineFilter, WagonFilter

class FilterPanel:
    """Композитная панель фильтров"""
    
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Фильтры
        self.filters: Dict[str, BaseFilter] = {}
        self.frame = None
        self.filtered_count_label = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создание панели фильтров"""
        self.frame = ttk.Frame(self.parent)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Контейнер для фильтров
        filters_container = ttk.Frame(self.frame)
        filters_container.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        filters_container.grid_columnconfigure([0, 1, 2, 3, 4], weight=1)
        
        # Создание фильтров
        self.create_filters(filters_container)
        
        # Панель информации и управления
        self.create_info_panel()
        self.create_control_panel()
    
    def create_filters(self, container):
        """Создание отдельных фильтров"""
        # Фильтр по типам сигналов
        self.filters['signal_types'] = SignalTypeFilter(
            container, self.on_filter_change
        )
        self.filters['signal_types'].grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        
        # Фильтр по линиям
        self.filters['lines'] = LineFilter(
            container, self.on_filter_change
        )
        self.filters['lines'].grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
        
        # Фильтр по вагонам
        self.filters['wagons'] = WagonFilter(
            container, self.on_filter_change
        )
        self.filters['wagons'].grid(row=0, column=2, sticky="nsew", padx=1, pady=1)
        
        # Дополнительные фильтры можно добавить аналогично
    
    def create_info_panel(self):
        """Создание панели информации"""
        info_frame = ttk.Frame(self.frame)
        info_frame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        
        self.filtered_count_label = ttk.Label(
            info_frame, 
            text="Отфильтровано параметров: 0", 
            font=('Arial', 9)
        )
        self.filtered_count_label.grid(row=0, column=0, sticky="w", padx=5)
    
    def create_control_panel(self):
        """Создание панели управления"""
        controls_frame = ttk.Frame(self.frame)
        controls_frame.grid(row=2, column=0, sticky="ew", padx=2, pady=2)
        controls_frame.grid_columnconfigure([0, 1, 2], weight=1)
        
        ttk.Button(controls_frame, text="Применить",
                  command=self.apply_filters, 
                  style='Accent.TButton').grid(row=0, column=0, padx=2, sticky="ew")
        
        ttk.Button(controls_frame, text="Сбросить",
                  command=self.reset_all_filters, 
                  style='Warning.TButton').grid(row=0, column=1, padx=2, sticky="ew")
        
        ttk.Button(controls_frame, text="Инвертировать",
                  command=self.invert_all_filters).grid(row=0, column=2, padx=2, sticky="ew")
    
    def on_filter_change(self):
        """Обработчик изменения любого фильтра"""
        if hasattr(self.controller, 'apply_filters'):
            try:
                self.controller.apply_filters()
            except Exception as e:
                self.logger.error(f"Ошибка применения фильтров: {e}")
    
    def apply_filters(self):
        """Принудительное применение фильтров"""
        self.on_filter_change()
    
    def reset_all_filters(self):
        """Сброс всех фильтров"""
        for filter_widget in self.filters.values():
            filter_widget.toggle_all(True)
        self.logger.info("Все фильтры сброшены")
    
    def invert_all_filters(self):
        """Инвертирование всех фильтров"""
        for filter_widget in self.filters.values():
            for var in filter_widget.filter_vars.values():
                var.set(not var.get())
        self.on_filter_change()
        self.logger.info("Все фильтры инвертированы")
    
    def get_selected_filters(self) -> Dict[str, List[str]]:
        """Получение всех выбранных фильтров"""
        return {
            name: filter_widget.get_selected_items()
            for name, filter_widget in self.filters.items()
        }
    
    def set_filters(self, filters: Dict[str, List[str]]):
        """Установка фильтров"""
        for name, items in filters.items():
            if name in self.filters:
                self.filters[name].set_selected_items(items)
    
    def update_line_checkboxes(self, lines: List[str]):
        """Обновление чекбоксов линий"""
        if 'lines' in self.filters:
            self.filters['lines'].update_lines(lines)
    
    def update_filtered_count(self, count: int):
        """Обновление счетчика отфильтрованных параметров"""
        if self.filtered_count_label:
            self.filtered_count_label.config(
                text=f"Отфильтровано параметров: {count}"
            )
    
    def grid(self, **kwargs):
        """Размещение панели"""
        self.frame.grid(**kwargs)
