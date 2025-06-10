"""
Горизонтальная панель параметров: Все слева (50%), Кнопки управления по центру, Выбранные справа (50%)
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Optional

class HorizontalParameterPanel(ttk.Frame):
    """Горизонтальная панель параметров 50/50 + кнопки управления"""

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
        self.selection_info = None

        self._setup_horizontal_ui()

    def _setup_horizontal_ui(self):
        """Настройка горизонтального UI 50/50 + кнопки управления"""
        # Настройка сетки - три колонки: Все | Кнопки | Выбранные
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2)  # Левая часть (больше)
        self.grid_columnconfigure(1, weight=0)  # Кнопки (фиксированная ширина)
        self.grid_columnconfigure(2, weight=1)  # Правая часть

        # Левая часть - все параметры
        self._create_all_parameters_section()

        # Центральная панель с кнопками управления
        self._create_control_buttons()

        # Правая часть - выбранные параметры
        self._create_selected_parameters_section()

    def _create_all_parameters_section(self):
        """Создание секции всех параметров"""
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

    def _create_control_buttons(self):
        """Создание центральной панели с кнопками управления"""
        control_frame = ttk.Frame(self)
        control_frame.grid(row=0, column=1, sticky="ns", padx=5)

        # Заголовок
        ttk.Label(control_frame, text="Управление", font=('Arial', 9, 'bold')).grid(row=0, column=0, pady=(0, 10))

        # Кнопки добавления
        add_btn = ttk.Button(
            control_frame,
            text="→ Добавить",
            width=12,
            command=self._add_selected_parameters
        )
        add_btn.grid(row=1, column=0, pady=2, sticky="ew")

        add_all_btn = ttk.Button(
            control_frame,
            text="→→ Все",
            width=12,
            command=self._add_all_parameters
        )
        add_all_btn.grid(row=2, column=0, pady=2, sticky="ew")

        # Разделитель
        ttk.Separator(control_frame, orient='horizontal').grid(row=3, column=0, sticky="ew", pady=10)

        # Кнопки удаления
        remove_btn = ttk.Button(
            control_frame,
            text="← Удалить",
            width=12,
            command=self._remove_selected_parameters
        )
        remove_btn.grid(row=4, column=0, pady=2, sticky="ew")

        remove_all_btn = ttk.Button(
            control_frame,
            text="←← Очистить",
            width=12,
            command=self._remove_all_parameters
        )
        remove_all_btn.grid(row=5, column=0, pady=2, sticky="ew")

        # Разделитель
        ttk.Separator(control_frame, orient='horizontal').grid(row=6, column=0, sticky="ew", pady=10)

        # Кнопки сортировки
        sort_up_btn = ttk.Button(
            control_frame,
            text="↑ Вверх",
            width=12,
            command=self._move_parameter_up
        )
        sort_up_btn.grid(row=7, column=0, pady=2, sticky="ew")

        sort_down_btn = ttk.Button(
            control_frame,
            text="↓ Вниз",
            width=12,
            command=self._move_parameter_down
        )
        sort_down_btn.grid(row=8, column=0, pady=2, sticky="ew")

        # Информация
        self.selection_info = ttk.Label(
            control_frame,
            text="Выбрано: 0",
            font=('Arial', 8),
            foreground='gray'
        )
        self.selection_info.grid(row=9, column=0, pady=(20, 0))

    def _create_selected_parameters_section(self):
        """Создание секции выбранных параметров"""
        selected_frame = ttk.LabelFrame(self, text="Выбранные параметры", padding="3")
        selected_frame.grid(row=0, column=2, sticky="nsew", padx=(2, 0))
        selected_frame.grid_rowconfigure(0, weight=1)
        selected_frame.grid_columnconfigure(0, weight=1)

        # Дерево выбранных параметров
        self.tree_selected = ttk.Treeview(
            selected_frame,
            columns=("description",),
            show="tree headings",
            height=15
        )
        self.tree_selected.heading("#0", text="№", anchor=tk.W)
        self.tree_selected.heading("description", text="Описание", anchor=tk.W)
        self.tree_selected.column("#0", width=30)
        self.tree_selected.column("description", width=200)

        scrollbar_selected = ttk.Scrollbar(selected_frame, orient="vertical", command=self.tree_selected.yview)
        self.tree_selected.configure(yscrollcommand=scrollbar_selected.set)

        self.tree_selected.grid(row=0, column=0, sticky="nsew")
        scrollbar_selected.grid(row=0, column=1, sticky="ns")

        # События
        self.tree_selected.bind("<Double-1>", self._on_selected_double_click)
        self.tree_selected.bind("<<TreeviewSelect>>", self._on_selection_changed)

    def _add_selected_parameters(self):
        """Добавление выбранных параметров"""
        try:
            selection = self.tree_all.selection()
            added_count = 0

            for item in selection:
                # Проверяем, что это параметр, а не группа
                if self.tree_all.item(item, 'text'):  # У параметра есть signal_code в text
                    signal_code = self.tree_all.item(item, 'text')
                    param_data = self._find_parameter_by_code(signal_code)

                    if param_data and self._add_param_to_selected(param_data):
                        added_count += 1

            if added_count > 0:
                self._populate_selected_tree()
                self._update_selection_info()
                self.logger.info(f"Добавлено {added_count} параметров")
            else:
                self.logger.warning("Выберите параметры для добавления")

        except Exception as e:
            self.logger.error(f"Ошибка добавления параметров: {e}")

    def _add_all_parameters(self):
        """Добавление всех видимых параметров"""
        try:
            added_count = 0

            for param in self.all_parameters:
                if self._add_param_to_selected(param):
                    added_count += 1

            self._populate_selected_tree()
            self._update_selection_info()
            self.logger.info(f"Добавлено всех параметров: {added_count}")

        except Exception as e:
            self.logger.error(f"Ошибка добавления всех параметров: {e}")

    def _remove_selected_parameters(self):
        """Удаление выбранных параметров"""
        try:
            selection = self.tree_selected.selection()
            if not selection:
                self.logger.warning("Выберите параметры для удаления")
                return

            indices_to_remove = []
            for item in selection:
                index = self.tree_selected.index(item)
                indices_to_remove.append(index)

            # Удаляем в обратном порядке
            for index in sorted(indices_to_remove, reverse=True):
                if 0 <= index < len(self.selected_parameters):
                    removed_param = self.selected_parameters.pop(index)
                    self.logger.debug(f"Удален: {removed_param.get('signal_code', 'Unknown')}")

            self._populate_selected_tree()
            self._update_selection_info()

        except Exception as e:
            self.logger.error(f"Ошибка удаления параметров: {e}")

    def _remove_all_parameters(self):
        """Очистка всех выбранных параметров"""
        try:
            count = len(self.selected_parameters)
            self.selected_parameters.clear()
            self._populate_selected_tree()
            self._update_selection_info()
            self.logger.info(f"Очищено {count} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка очистки параметров: {e}")

    def _move_parameter_up(self):
        """Перемещение параметра вверх"""
        try:
            selection = self.tree_selected.selection()
            if not selection:
                return

            index = self.tree_selected.index(selection[0])
            if index > 0:
                # Меняем местами
                self.selected_parameters[index], self.selected_parameters[index-1] = \
                    self.selected_parameters[index-1], self.selected_parameters[index]

                self._populate_selected_tree()

                # Восстанавливаем выбор
                new_item = self.tree_selected.get_children()[index-1]
                self.tree_selected.selection_set(new_item)

        except Exception as e:
            self.logger.error(f"Ошибка перемещения вверх: {e}")

    def _move_parameter_down(self):
        """Перемещение параметра вниз"""
        try:
            selection = self.tree_selected.selection()
            if not selection:
                return

            index = self.tree_selected.index(selection[0])
            if index < len(self.selected_parameters) - 1:
                # Меняем местами
                self.selected_parameters[index], self.selected_parameters[index+1] = \
                    self.selected_parameters[index+1], self.selected_parameters[index]

                self._populate_selected_tree()

                # Восстанавливаем выбор
                new_item = self.tree_selected.get_children()[index+1]
                self.tree_selected.selection_set(new_item)

        except Exception as e:
            self.logger.error(f"Ошибка перемещения вниз: {e}")

    def _find_parameter_by_code(self, signal_code: str) -> Optional[Dict[str, Any]]:
        """Поиск параметра по коду"""
        for param in self.all_parameters:
            if param.get('signal_code') == signal_code:
                return param
        return None

    def _add_param_to_selected(self, param_data: Dict[str, Any]) -> bool:
        """Добавление параметра в выбранные (без дубликатов)"""
        signal_code = param_data.get('signal_code', '')

        # Проверяем дубликаты
        for existing in self.selected_parameters:
            if existing.get('signal_code') == signal_code:
                return False

        self.selected_parameters.append(param_data)
        return True

    def _update_selection_info(self):
        """Обновление информации о выборе"""
        try:
            count = len(self.selected_parameters)
            if self.selection_info:
                self.selection_info.config(text=f"Выбрано: {count}")

            # Уведомляем контроллер об изменении
            if self.controller and hasattr(self.controller, '_on_parameter_selection_changed'):
                self.controller._on_parameter_selection_changed(count)

        except Exception as e:
            self.logger.error(f"Ошибка обновления информации: {e}")

    def _on_selection_changed(self, event):
        """Обработка изменения выбора в дереве"""
        self._update_selection_info()

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
                        self._update_selection_info()
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
            self._update_selection_info()

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
        for idx, param in enumerate(self.selected_parameters, start=1):
            description = param.get('description', '')[:50]
            self.tree_selected.insert("", "end",
                                      text=str(idx),
                                      values=(description,))

    def get_selected_parameters(self) -> List[Dict[str, Any]]:
        """Получение выбранных параметров"""
        return self.selected_parameters.copy()

    def cleanup(self):
        self.controller = None
