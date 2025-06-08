"""
Базовый класс для всех деревьев параметров
"""
from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Optional, Callable
from ...utils.base_ui import TooltipMixin

class BaseParameterTree(ABC):
    """Абстрактный базовый класс для деревьев параметров"""
    
    def __init__(self, parent, title: str, controller=None):
        self.parent = parent
        self.title = title
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # UI компоненты
        self.frame: Optional[ttk.LabelFrame] = None
        self.tree: Optional[ttk.Treeview] = None
        self.scrollbar_v: Optional[ttk.Scrollbar] = None
        self.scrollbar_h: Optional[ttk.Scrollbar] = None
        self.context_menu: Optional[tk.Menu] = None
        
        # Фильтры
        self.filter_entries: Dict[str, ttk.Entry] = {}
        self.filter_frame: Optional[ttk.Frame] = None
        
        # Данные
        self.all_data: List[Any] = []
        self.filtered_data: List[Any] = []
        
        # Наблюдатели
        self.observers: List[Callable] = []
        
        self.create_widgets()
    
    @abstractmethod
    def get_columns(self) -> tuple:
        """Получение конфигурации столбцов"""
        pass
    
    @abstractmethod
    def get_column_headers(self) -> Dict[str, tuple]:
        """Получение заголовков столбцов"""
        pass
    
    @abstractmethod
    def format_item_data(self, item: Any) -> tuple:
        """Форматирование данных элемента для отображения"""
        pass
    
    def create_widgets(self):
        """Создание виджетов дерева"""
        # Основной контейнер
        self.frame = ttk.LabelFrame(self.parent, text=self.title)
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Фрейм фильтров
        self.create_filter_frame()
        
        # Кнопки управления
        self.create_control_buttons()
        
        # Дерево с прокруткой
        self.create_tree_with_scrollbars()
        
        # Контекстное меню
        self.create_context_menu()
    
    def create_filter_frame(self):
        """Создание фрейма с фильтрами"""
        self.filter_frame = ttk.Frame(self.frame)
        self.filter_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        self.filter_frame.grid_columnconfigure([0, 1, 2, 3], weight=1)
        
        # Фильтры по столбцам
        filter_labels = ["Код сигнала", "Описание", "Линия", "№ вагона"]
        filter_keys = ["signal_name", "signal_desc", "line", "wagon"]
        
        for i, (label, key) in enumerate(zip(filter_labels, filter_keys)):
            ttk.Label(self.filter_frame, text=f"{label}:").grid(
                row=0, column=i, sticky="w", padx=2)
            
            entry = ttk.Entry(self.filter_frame, width=15)
            entry.grid(row=1, column=i, sticky="ew", padx=2)
            entry.bind("<KeyRelease>", self.on_filter_change)
            
            self.filter_entries[key] = entry
            TooltipMixin.create_tooltip(entry, f"Фильтр по {label.lower()}")
    
    def create_control_buttons(self):
        """Создание кнопок управления"""
        btn_frame = ttk.Frame(self.frame)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        btn_frame.grid_columnconfigure([0, 1, 2, 3], weight=1)
        
        buttons_config = [
            ("Выделить все", self.select_all, "Выделить все элементы"),
            ("Снять выделение", self.deselect_all, "Снять выделение"),
            ("Очистить фильтры", self.clear_filters, "Очистить все фильтры"),
            ("Экспорт", self.export_selected, "Экспортировать выделенные")
        ]
        
        for i, (text, command, tooltip) in enumerate(buttons_config):
            btn = ttk.Button(btn_frame, text=text, command=command)
            btn.grid(row=0, column=i, padx=2, pady=2, sticky="ew")
            TooltipMixin.create_tooltip(btn, tooltip)
    
    def create_tree_with_scrollbars(self):
        """Создание дерева с прокруткой"""
        # Контейнер для дерева и скроллбаров
        tree_container = ttk.Frame(self.frame)
        tree_container.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Дерево
        columns = self.get_columns()
        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            selectmode="extended"
        )
        
        # Настройка заголовков и ширины столбцов
        headers = self.get_column_headers()
        for col, (text, width) in headers.items():
            self.tree.heading(col, text=text, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=width, minwidth=50)
        
        # Скроллбары
        self.scrollbar_v = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar_v.set)
        
        self.scrollbar_h = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=self.scrollbar_h.set)
        
        # Размещение
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_v.grid(row=0, column=1, sticky="ns")
        self.scrollbar_h.grid(row=1, column=0, sticky="ew")
        
        # Привязка событий
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
    
    def create_context_menu(self):
        """Создание контекстного меню"""
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Выделить все", command=self.select_all)
        self.context_menu.add_command(label="Снять выделение", command=self.deselect_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Копировать", command=self.copy_selected)
        self.context_menu.add_command(label="Экспорт выделенных", command=self.export_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Добавить в избранное", command=self.add_to_favorites)
    
    def update_data(self, data: List[Any]):
        """Обновление данных в дереве"""
        try:
            self.all_data = data.copy()
            self.apply_filters()
            self.notify_observers('data_updated', len(data))
            self.logger.info(f"Обновлены данные дерева: {len(data)} элементов")
        except Exception as e:
            self.logger.error(f"Ошибка обновления данных: {e}")
    
    def apply_filters(self):
        """Применение текстовых фильтров"""
        try:
            filters = self.get_filter_values()
            
            if not any(filters.values()):
                self.filtered_data = self.all_data.copy()
            else:
                self.filtered_data = []
                for item in self.all_data:
                    if self.matches_filters(item, filters):
                        self.filtered_data.append(item)
            
            self.refresh_tree()
            self.notify_observers('filtered', len(self.filtered_data))
            
        except Exception as e:
            self.logger.error(f"Ошибка применения фильтров: {e}")
    
    def matches_filters(self, item: Any, filters: Dict[str, str]) -> bool:
        """Проверка соответствия элемента фильтрам"""
        try:
            formatted_data = self.format_item_data(item)
            if len(formatted_data) < 4:
                return False
            
            signal_name = str(formatted_data[0]).lower()
            signal_desc = str(formatted_data[1]).lower()
            line = str(formatted_data[2]).lower()
            wagon = str(formatted_data[3]).lower()
            
            return (
                (not filters['signal_name'] or filters['signal_name'] in signal_name) and
                (not filters['signal_desc'] or filters['signal_desc'] in signal_desc) and
                (not filters['line'] or filters['line'] in line) and
                (not filters['wagon'] or filters['wagon'] in wagon)
            )
        except Exception as e:
            self.logger.error(f"Ошибка проверки фильтров: {e}")
            return False
    
    def refresh_tree(self):
        """Обновление отображения дерева"""
        # Очистка
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Заполнение
        for item in self.filtered_data:
            try:
                values = self.format_item_data(item)
                self.tree.insert('', 'end', values=values)
            except Exception as e:
                self.logger.error(f"Ошибка добавления элемента в дерево: {e}")
    
    def get_filter_values(self) -> Dict[str, str]:
        """Получение значений фильтров"""
        return {
            key: entry.get().lower().strip()
            for key, entry in self.filter_entries.items()
        }
    
    def clear_filters(self):
        """Очистка всех фильтров"""
        for entry in self.filter_entries.values():
            entry.delete(0, tk.END)
        self.apply_filters()
    
    def on_filter_change(self, event=None):
        """Обработчик изменения фильтров"""
        self.apply_filters()
    
    def sort_by_column(self, col: str):
        """Сортировка по столбцу"""
        try:
            data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
            data.sort()
            
            for index, (val, child) in enumerate(data):
                self.tree.move(child, '', index)
                
        except Exception as e:
            self.logger.error(f"Ошибка сортировки: {e}")
    
    def on_double_click(self, event):
        """Обработчик двойного клика"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            self.notify_observers('double_click', values)
            self.logger.info(f"Двойной клик по элементу: {values[0] if values else 'Unknown'}")
    
    def select_all(self):
        """Выделение всех элементов"""
        self.tree.selection_set(self.tree.get_children())
    
    def deselect_all(self):
        """Снятие выделения"""
        self.tree.selection_remove(self.tree.get_children())
    
    def copy_selected(self):
        """Копирование выделенных элементов в буфер обмена"""
        try:
            selected_items = self.tree.selection()
            if not selected_items:
                return
            
            text = ""
            for item in selected_items:
                values = self.tree.item(item)['values']
                text += "\t".join(str(v) for v in values) + "\n"
            
            self.tree.clipboard_clear()
            self.tree.clipboard_append(text)
            self.logger.info(f"Скопировано {len(selected_items)} элементов")
            
        except Exception as e:
            self.logger.error(f"Ошибка копирования: {e}")
    
    def export_selected(self):
        """Экспорт выделенных элементов"""
        selected_items = self.tree.selection()
        if not selected_items:
            tk.messagebox.showwarning("Экспорт", "Нет выделенных элементов")
            return
        
        self.notify_observers('export_requested', selected_items)
    
    def add_to_favorites(self):
        """Добавление в избранное"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        favorites = []
        for item in selected_items:
            values = self.tree.item(item)['values']
            if values:
                favorites.append(values[0])  # signal_code
        
        self.notify_observers('add_to_favorites', favorites)
    
    def show_context_menu(self, event):
        """Показ контекстного меню"""
        try:
            self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.logger.error(f"Ошибка показа контекстного меню: {e}")
    
    def get_selected_items(self) -> List[tuple]:
        """Получение выделенных элементов"""
        selected = []
        for item in self.tree.selection():
            values = self.tree.item(item)['values']
            selected.append(values)
        return selected
    
    def add_observer(self, observer: Callable):
        """Добавление наблюдателя"""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def remove_observer(self, observer: Callable):
        """Удаление наблюдателя"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def notify_observers(self, event_type: str, data: Any):
        """Уведомление наблюдателей"""
        for observer in self.observers:
            try:
                observer(event_type, data)
            except Exception as e:
                self.logger.error(f"Ошибка в наблюдателе: {e}")
    
    def grid(self, **kwargs):
        """Размещение виджета"""
        self.frame.grid(**kwargs)

class AllParametersTree(BaseParameterTree):
    """Дерево всех параметров"""
    
    def __init__(self, parent, controller=None):
        super().__init__(parent, "Все параметры", controller)
    
    def get_columns(self) -> tuple:
        return ("signal_name", "signal_desc", "line", "wagon")
    
    def get_column_headers(self) -> Dict[str, tuple]:
        return {
            "signal_name": ("Код сигнала", 150),
            "signal_desc": ("Описание", 250),
            "line": ("Линия", 120),
            "wagon": ("№ вагона", 80)
        }
    
    def format_item_data(self, item: Any) -> tuple:
        """Форматирование данных параметра"""
        if isinstance(item, dict):
            return (
                item.get('signal_code', ''),
                item.get('description', ''),
                item.get('line', ''),
                item.get('wagon', '')
            )
        elif isinstance(item, (tuple, list)) and len(item) >= 4:
            return tuple(item[:4])
        else:
            return ('', '', '', '')

class SelectedParametersTree(BaseParameterTree):
    """Дерево выбранных параметров"""
    
    def __init__(self, parent, controller=None):
        super().__init__(parent, "Выбранные параметры", controller)
    
    def get_columns(self) -> tuple:
        return ("signal_name", "signal_desc", "line", "wagon")
    
    def get_column_headers(self) -> Dict[str, tuple]:
        return {
            "signal_name": ("Код сигнала", 150),
            "signal_desc": ("Описание", 250),
            "line": ("Линия", 120),
            "wagon": ("№ вагона", 80)
        }
    
    def format_item_data(self, item: Any) -> tuple:
        """Форматирование данных выбранного параметра"""
        if isinstance(item, (tuple, list)) and len(item) >= 4:
            return tuple(item[:4])
        elif isinstance(item, dict):
            return (
                item.get('signal_code', ''),
                item.get('description', ''),
                item.get('line', ''),
                item.get('wagon', '')
            )
        else:
            return ('', '', '', '')
