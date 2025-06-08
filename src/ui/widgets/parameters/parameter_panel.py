"""
Основная панель управления параметрами
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Dict, Any, Optional

from .all_parameters_tree import AllParametersTree
from .selected_parameters_tree import SelectedParametersTree
from .parameter_search import ParameterSearchWidget
from ...utils.base_ui import TooltipMixin

class ParameterPanel:
    """Главная панель управления параметрами с двумя деревьями"""
    
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Компоненты
        self.frame: Optional[ttk.Frame] = None
        self.all_params_tree: Optional[AllParametersTree] = None
        self.selected_params_tree: Optional[SelectedParametersTree] = None
        self.search_widget: Optional[ParameterSearchWidget] = None
        self.buttons_frame: Optional[ttk.Frame] = None
        self.info_frame: Optional[ttk.Frame] = None
        
        # Статистика
        self.stats_labels: Dict[str, ttk.Label] = {}
        
        self.create_widgets()
        self.setup_observers()
    
    def create_widgets(self):
        """Создание виджетов панели параметров"""
        # Основной контейнер
        self.frame = ttk.Frame(self.parent)
        self.frame.grid_columnconfigure([0, 2], weight=1)
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_rowconfigure(1, weight=1)
        
        # Поиск
        self.search_widget = ParameterSearchWidget(self.frame, self.on_search)
        self.search_widget.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        # Дерево всех параметров
        self.all_params_tree = AllParametersTree(self.frame, self.controller)
        self.all_params_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Кнопки управления
        self.create_control_buttons()
        
        # Дерево выбранных параметров
        self.selected_params_tree = SelectedParametersTree(self.frame, self.controller)
        self.selected_params_tree.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
        
        # Информационная панель
        self.create_info_panel()
    
    def create_control_buttons(self):
        """Создание кнопок управления между деревьями"""
        self.buttons_frame = ttk.Frame(self.frame)
        self.buttons_frame.grid(row=1, column=1, sticky="ns", padx=10, pady=5)
        
        buttons_config = [
            ("Добавить →", self.add_params_to_selected, "Добавить выделенные параметры"),
            ("← Удалить", self.remove_params_from_selected, "Удалить выделенные параметры"),
            ("Очистить", self.clear_selected_params, "Очистить все выбранные параметры"),
            ("Избранное", self.toggle_favorites, "Работа с избранными параметрами"),
            ("Экспорт", self.export_parameters, "Экспорт параметров в файл")
        ]
        
        for i, (text, command, tooltip) in enumerate(buttons_config):
            btn = ttk.Button(self.buttons_frame, text=text, command=command)
            btn.grid(row=i, column=0, pady=5, sticky="ew")
            TooltipMixin.create_tooltip(btn, tooltip)
        
        # Счетчик параметров
        self.count_label = ttk.Label(
            self.buttons_frame,
            text="Выбрано: 0",
            font=('Arial', 9, 'bold')
        )
        self.count_label.grid(row=len(buttons_config), column=0, pady=10)
    
    def create_info_panel(self):
        """Создание информационной панели"""
        self.info_frame = ttk.LabelFrame(self.frame, text="Информация")
        self.info_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.info_frame.grid_columnconfigure([0, 1, 2, 3], weight=1)
        
        # Статистика
        stats = [
            ("total", "Всего параметров:"),
            ("filtered", "Отфильтровано:"),
            ("selected", "Выбрано:"),
            ("favorites", "Избранных:")
        ]
        
        for i, (key, text) in enumerate(stats):
            ttk.Label(self.info_frame, text=text).grid(row=0, column=i*2, sticky="w", padx=5)
            label = ttk.Label(self.info_frame, text="0", font=('Arial', 9, 'bold'))
            label.grid(row=0, column=i*2+1, sticky="w", padx=5)
            self.stats_labels[key] = label
    
    def setup_observers(self):
        """Настройка наблюдателей для синхронизации деревьев"""
        if self.all_params_tree:
            self.all_params_tree.add_observer(self.on_all_params_event)
        
        if self.selected_params_tree:
            self.selected_params_tree.add_observer(self.on_selected_params_event)
    
    def on_all_params_event(self, event_type: str, data: Any):
        """Обработчик событий дерева всех параметров"""
        if event_type == 'double_click':
            # Автоматическое добавление при двойном клике
            self.add_params_to_selected()
        elif event_type == 'data_updated':
            self.update_stats()
        elif event_type == 'filtered':
            self.update_stats()
    
    def on_selected_params_event(self, event_type: str, data: Any):
        """Обработчик событий дерева выбранных параметров"""
        if event_type == 'double_click':
            # Автоматическое удаление при двойном клике
            self.remove_params_from_selected()
        elif event_type == 'data_updated':
            self.update_stats()
    
    def on_search(self, query: str):
        """Обработчик поиска"""
        if hasattr(self.controller, 'search_parameters'):
            results = self.controller.search_parameters(query)
            if self.all_params_tree:
                self.all_params_tree.update_data(results)
    
    def add_params_to_selected(self):
        """Добавление параметров в выбранные"""
        if not self.all_params_tree or not self.selected_params_tree:
            return
        
        try:
            selected_items = self.all_params_tree.get_selected_items()
            if not selected_items:
                messagebox.showwarning("Добавление", "Нет выделенных параметров")
                return
            
            # Получаем уже существующие параметры
            existing_items = self.selected_params_tree.get_selected_items()
            existing_codes = {item[0] for item in existing_items if item}
            
            # Добавляем только новые параметры
            new_items = []
            for item in selected_items:
                if item and item[0] not in existing_codes:
                    new_items.append(item)
            
            if new_items:
                current_data = self.selected_params_tree.all_data.copy()
                current_data.extend(new_items)
                self.selected_params_tree.update_data(current_data)
                
                self.logger.info(f"Добавлено {len(new_items)} параметров")
                self.update_stats()
            else:
                messagebox.showinfo("Добавление", "Все выделенные параметры уже добавлены")
                
        except Exception as e:
            self.logger.error(f"Ошибка добавления параметров: {e}")
            messagebox.showerror("Ошибка", f"Ошибка добавления параметров: {e}")
    
    def remove_params_from_selected(self):
        """Удаление параметров из выбранных"""
        if not self.selected_params_tree:
            return
        
        try:
            selected_items = self.selected_params_tree.get_selected_items()
            if not selected_items:
                messagebox.showwarning("Удаление", "Нет выделенных параметров")
                return
            
            # Удаляем выделенные элементы
            selected_codes = {item[0] for item in selected_items if item}
            current_data = self.selected_params_tree.all_data.copy()
            filtered_data = [item for item in current_data 
                           if (isinstance(item, (list, tuple)) and item[0] not in selected_codes)]
            
            self.selected_params_tree.update_data(filtered_data)
            
            self.logger.info(f"Удалено {len(selected_items)} параметров")
            self.update_stats()
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления параметров: {e}")
            messagebox.showerror("Ошибка", f"Ошибка удаления параметров: {e}")
    
    def clear_selected_params(self):
        """Очистка всех выбранных параметров"""
        if not self.selected_params_tree:
            return
        
        try:
            self.selected_params_tree.update_data([])
            self.logger.info("Список выбранных параметров очищен")
            self.update_stats()
        except Exception as e:
            self.logger.error(f"Ошибка очистки параметров: {e}")
    
    def toggle_favorites(self):
        """Переключение режима избранных параметров"""
        try:
            if hasattr(self.controller, 'get_favorite_parameters'):
                favorites = self.controller.get_favorite_parameters()
                if self.all_params_tree:
                    self.all_params_tree.update_data(favorites)
        except Exception as e:
            self.logger.error(f"Ошибка работы с избранными: {e}")
    
    def export_parameters(self):
        """Экспорт параметров"""
        if hasattr(self.controller, 'export_parameters'):
            self.controller.export_parameters()
    
    def update_all_params(self, params: List[Any]):
        """Обновление дерева всех параметров"""
        if self.all_params_tree:
            self.all_params_tree.update_data(params)
        self.update_stats()
    
    def update_selected_params(self, params: List[Any]):
        """Обновление дерева выбранных параметров"""
        if self.selected_params_tree:
            self.selected_params_tree.update_data(params)
        self.update_stats()
    
    def update_stats(self):
        """Обновление статистики"""
        try:
            total = len(self.all_params_tree.all_data) if self.all_params_tree else 0
            filtered = len(self.all_params_tree.filtered_data) if self.all_params_tree else 0
            selected = len(self.selected_params_tree.all_data) if self.selected_params_tree else 0
            favorites = 0  # Получить из контроллера
            
            if hasattr(self.controller, 'get_favorites_count'):
                favorites = self.controller.get_favorites_count()
            
            self.stats_labels['total'].config(text=str(total))
            self.stats_labels['filtered'].config(text=str(filtered))
            self.stats_labels['selected'].config(text=str(selected))
            self.stats_labels['favorites'].config(text=str(favorites))
            
            if self.count_label:
                self.count_label.config(text=f"Выбрано: {selected}")
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления статистики: {e}")
    
    def grid(self, **kwargs):
        """Размещение панели"""
        if self.frame:
            self.frame.grid(**kwargs)
