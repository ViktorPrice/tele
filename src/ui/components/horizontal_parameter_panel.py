# src/ui/components/horizontal_parameter_panel.py - СОЗДАТЬ ФАЙЛ

"""
Горизонтальная панель параметров: Все слева (50%), Выбранные справа (50%)
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any

class HorizontalParameterPanel(ttk.Frame):
    """Горизонтальная панель параметров 50/50"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Данные параметров
        self.all_parameters: List[Dict[str, Any]] = []
        self.selected_parameters: List[Dict[str, Any]] = []

        # UI элементы
        self.tree_all = None
        self.tree_selected = None

        self._setup_horizontal_ui()

    def _setup_horizontal_ui(self):
        """Настройка горизонтального UI 50/50"""
        # Настройка сетки - две колонки 50/50
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)  # Левая часть
        self.grid_columnconfigure(1, weight=1)  # Правая часть

        # Левая часть - все параметры
        all_frame = ttk.LabelFrame(self, text="Все параметры", padding="3")
        all_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        all_frame.grid_rowconfigure(0, weight=1)
        all_frame.grid_columnconfigure(0, weight=1)

        # Дерево всех параметров
        self.tree_all = ttk.Treeview(
            all_frame,
            columns=("description",),
            show="tree headings",
            height=15
        )
        self.tree_all.heading("#0", text="Код", anchor=tk.W)
        self.tree_all.heading("description", text="Описание", anchor=tk.W)
        self.tree_all.column("#0", width=120)
        self.tree_all.column("description", width=200)

        scrollbar_all = ttk.Scrollbar(all_frame, orient="vertical", command=self.tree_all.yview)
        self.tree_all.configure(yscrollcommand=scrollbar_all.set)

        self.tree_all.grid(row=0, column=0, sticky="nsew")
        scrollbar_all.grid(row=0, column=1, sticky="ns")

        # События
        self.tree_all.bind("<Double-1>", self._on_all_double_click)

        # Правая часть - выбранные параметры
        selected_frame = ttk.LabelFrame(self, text="Выбранные параметры", padding="3")
        selected_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0))
        selected_frame.grid_rowconfigure(0, weight=1)
        selected_frame.grid_columnconfigure(0, weight=1)

        # Дерево выбранных параметров
        self.tree_selected = ttk.Treeview(
            selected_frame,
            columns=("description",),
            show="tree headings",
            height=15
        )
        self.tree_selected.heading("#0", text="Код", anchor=tk.W)
        self.tree_selected.heading("description", text="Описание", anchor=tk.W)
        self.tree_selected.column("#0", width=120)
        self.tree_selected.column("description", width=200)

        scrollbar_selected = ttk.Scrollbar(selected_frame, orient="vertical", command=self.tree_selected.yview)
        self.tree_selected.configure(yscrollcommand=scrollbar_selected.set)

        self.tree_selected.grid(row=0, column=0, sticky="nsew")
        scrollbar_selected.grid(row=0, column=1, sticky="ns")

        # События
        self.tree_selected.bind("<Double-1>", self._on_selected_double_click)

    def _on_all_double_click(self, event):
        """Двойной клик - добавить в выбранные"""
        selection = self.tree_all.selection()
        if selection:
            item = selection[0]
            signal_code = self.tree_all.item(item, 'text')
            
            # Найти параметр по коду
            for param in self.all_parameters:
                if param.get('signal_code') == signal_code:
                    if param not in self.selected_parameters:
                        self.selected_parameters.append(param)
                        self._populate_selected_tree()
                    break

    def _on_selected_double_click(self, event):
        """Двойной клик - удалить из выбранных"""
        selection = self.tree_selected.selection()
        if selection:
            item = selection[0]
            signal_code = self.tree_selected.item(item, 'text')
            
            # Удалить из выбранных
            self.selected_parameters = [p for p in self.selected_parameters 
                                      if p.get('signal_code') != signal_code]
            self._populate_selected_tree()

    def update_parameters(self, parameters: List[Dict[str, Any]]):
        """Обновление списка параметров"""
        try:
            self.all_parameters = parameters.copy()
            self._populate_all_tree()
            self.logger.info(f"HorizontalParameterPanel: обновлено {len(parameters)} параметров")
        except Exception as e:
            self.logger.error(f"Ошибка обновления параметров: {e}")

    def _populate_all_tree(self):
        """Заполнение дерева всех параметров"""
        # Очищаем дерево
        for item in self.tree_all.get_children():
            self.tree_all.delete(item)

        # Группировка по типу сигнала
        groups = {}
        for param in self.all_parameters:
            signal_code = param.get('signal_code', '')
            signal_type = signal_code[0] if signal_code else 'Unknown'
            group_key = f"Тип {signal_type}"
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(param)

        # Добавляем группы
        for group_name, group_params in sorted(groups.items()):
            group_id = self.tree_all.insert("", "end", text=group_name, 
                                          values=(f"({len(group_params)} параметров)",))
            
            for param in sorted(group_params, key=lambda x: x.get('signal_code', '')):
                description = param.get('description', '')[:50]
                self.tree_all.insert(group_id, "end", 
                                    text=param.get('signal_code', ''),
                                    values=(description,))

    def _populate_selected_tree(self):
        """Заполнение дерева выбранных параметров"""
        # Очищаем дерево
        for item in self.tree_selected.get_children():
            self.tree_selected.delete(item)

        # Добавляем выбранные параметры
        for param in self.selected_parameters:
            description = param.get('description', '')[:50]
            self.tree_selected.insert("", "end",
                                    text=param.get('signal_code', ''),
                                    values=(description,))

    def get_selected_parameters(self) -> List[Dict[str, Any]]:
        """Получение выбранных параметров"""
        return self.selected_parameters.copy()

    def cleanup(self):
        self.controller = None
