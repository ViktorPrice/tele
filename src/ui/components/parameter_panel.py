# src/ui/components/parameter_panel.py - ПОЛНАЯ РЕАЛИЗАЦИЯ
"""
Панель управления параметрами телеметрии с интеграцией Use Cases
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Optional, Callable


class ParameterPanel(ttk.Frame):
    """Панель управления параметрами телеметрии (ПОЛНАЯ ВЕРСИЯ)"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Данные параметров
        self.all_parameters: List[Dict[str, Any]] = []
        self.filtered_parameters: List[Dict[str, Any]] = []
        self.selected_parameters: List[Dict[str, Any]] = []

        # Callback функции
        self.on_selection_changed: Optional[Callable[[int], None]] = None

        # UI элементы
        self.tree_all: Optional[ttk.Treeview] = None
        self.tree_selected: Optional[ttk.Treeview] = None
        self.search_var: Optional[tk.StringVar] = None
        self.search_entry: Optional[tk.Entry] = None
        self.counters_frame: Optional[ttk.Frame] = None
        self.total_label: Optional[ttk.Label] = None
        self.filtered_label: Optional[ttk.Label] = None
        self.selected_label: Optional[ttk.Label] = None

        # Состояние
        self.is_loading = False

        self._setup_ui()
        self.logger.info("ParameterPanel инициализирован")

    def _setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Главная область с деревьями

        # 1. Поиск по параметрам
        self._create_search_section()

        # 2. Счетчики параметров
        self._create_counters_section()

        # 3. Основная область с деревьями параметров
        self._create_parameter_trees()

        # 4. Кнопки управления
        self._create_control_buttons()

    def _create_search_section(self):
        """Создание секции поиска"""
        search_frame = ttk.Frame(self)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_frame.grid_columnconfigure(1, weight=1)

        # Метка поиска
        ttk.Label(search_frame, text="Поиск:").grid(
            row=0, column=0, sticky="w")

        # Поле поиска
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Arial', 9)
        )
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Привязка событий поиска
        self.search_var.trace('w', self._on_search_changed)

        # Кнопка очистки поиска
        clear_btn = ttk.Button(
            search_frame,
            text="✕",
            width=3,
            command=self._clear_search
        )
        clear_btn.grid(row=0, column=2, padx=(5, 0))

    def _create_counters_section(self):
        """Создание секции счетчиков"""
        self.counters_frame = ttk.Frame(self)
        self.counters_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Счетчики параметров
        self.total_label = ttk.Label(
            self.counters_frame,
            text="Всего: 0",
            font=('Arial', 8)
        )
        self.total_label.pack(side=tk.LEFT)

        ttk.Label(self.counters_frame, text=" | ",
                  font=('Arial', 8)).pack(side=tk.LEFT)

        self.filtered_label = ttk.Label(
            self.counters_frame,
            text="Отфильтровано: 0",
            font=('Arial', 8)
        )
        self.filtered_label.pack(side=tk.LEFT)

        ttk.Label(self.counters_frame, text=" | ",
                  font=('Arial', 8)).pack(side=tk.LEFT)

        self.selected_label = ttk.Label(
            self.counters_frame,
            text="Выбрано: 0",
            font=('Arial', 8),
            foreground='blue'
        )
        self.selected_label.pack(side=tk.LEFT)

    def _create_parameter_trees(self):
        """Создание деревьев параметров"""
        # PanedWindow для разделения области
        paned = tk.PanedWindow(self, orient=tk.VERTICAL)
        paned.grid(row=2, column=0, sticky="nsew")

        # Верхняя часть - все параметры
        top_frame = ttk.LabelFrame(
            paned, text="Доступные параметры", padding="5")
        paned.add(top_frame, minsize=200)

        # Нижняя часть - выбранные параметры
        bottom_frame = ttk.LabelFrame(
            paned, text="Выбранные параметры", padding="5")
        paned.add(bottom_frame, minsize=150)

        # Создание дерева всех параметров
        self._create_all_parameters_tree(top_frame)

        # Создание дерева выбранных параметров
        self._create_selected_parameters_tree(bottom_frame)

    def _create_all_parameters_tree(self, parent):
        """Создание дерева всех параметров"""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Контейнер для дерева
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Дерево параметров
        columns = ("signal_code", "description", "line", "wagon")
        self.tree_all = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            height=8
        )

        # Настройка столбцов
        self.tree_all.heading("#0", text="Тип", anchor=tk.W)
        self.tree_all.heading("signal_code", text="Код сигнала", anchor=tk.W)
        self.tree_all.heading("description", text="Описание", anchor=tk.W)
        self.tree_all.heading("line", text="Линия", anchor=tk.W)
        self.tree_all.heading("wagon", text="Вагон", anchor=tk.CENTER)

        # Ширина столбцов
        self.tree_all.column("#0", width=60, minwidth=50)
        self.tree_all.column("signal_code", width=120, minwidth=100)
        self.tree_all.column("description", width=200, minwidth=150)
        self.tree_all.column("line", width=150, minwidth=100)
        self.tree_all.column("wagon", width=50, minwidth=40)

        # Прокрутка
        scrollbar_all = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.tree_all.yview)
        self.tree_all.configure(yscrollcommand=scrollbar_all.set)

        self.tree_all.grid(row=0, column=0, sticky="nsew")
        scrollbar_all.grid(row=0, column=1, sticky="ns")

        # Обработчики событий
        self.tree_all.bind("<Double-1>", self._on_parameter_double_click)
        self.tree_all.bind("<Button-3>", self._on_parameter_right_click)

    def _create_selected_parameters_tree(self, parent):
        """Создание дерева выбранных параметров"""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Контейнер для дерева
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Дерево выбранных параметров
        columns = ("signal_code", "description")
        self.tree_selected = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            height=6
        )

        # Настройка столбцов
        self.tree_selected.heading("#0", text="№", anchor=tk.W)
        self.tree_selected.heading(
            "signal_code", text="Код сигнала", anchor=tk.W)
        self.tree_selected.heading("description", text="Описание", anchor=tk.W)

        # Ширина столбцов
        self.tree_selected.column("#0", width=30, minwidth=30)
        self.tree_selected.column("signal_code", width=120, minwidth=100)
        self.tree_selected.column("description", width=200, minwidth=150)

        # Прокрутка
        scrollbar_selected = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.tree_selected.yview)
        self.tree_selected.configure(yscrollcommand=scrollbar_selected.set)

        self.tree_selected.grid(row=0, column=0, sticky="nsew")
        scrollbar_selected.grid(row=0, column=1, sticky="ns")

        # Обработчики событий
        self.tree_selected.bind(
            "<Double-1>", self._on_selected_parameter_double_click)
        self.tree_selected.bind("<Delete>", self._on_delete_selected_parameter)

    def _create_control_buttons(self):
        """Создание кнопок управления"""
        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        # Кнопки для управления выбором
        ttk.Button(
            buttons_frame,
            text="Добавить выбранные",
            command=self._add_selected_parameters
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            buttons_frame,
            text="Удалить выбранные",
            command=self._remove_selected_parameters
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            buttons_frame,
            text="Очистить все",
            command=self._clear_all_selections
        ).pack(side=tk.LEFT, padx=(0, 5))

        # Кнопка автовыбора
        ttk.Button(
            buttons_frame,
            text="Авто-выбор (10)",
            command=self._auto_select_parameters
        ).pack(side=tk.RIGHT)

    # === ОБРАБОТЧИКИ СОБЫТИЙ ===

    def _on_search_changed(self, *args):
        """Обработка изменения поискового запроса"""
        try:
            search_text = self.search_var.get().strip().lower()
            self._filter_parameters_by_search(search_text)
        except Exception as e:
            self.logger.error(f"Ошибка поиска: {e}")

    def _on_parameter_double_click(self, event):
        """Обработка двойного клика по параметру"""
        try:
            selection = self.tree_all.selection()
            if selection:
                item = selection[0]
                # Получаем данные параметра
                param_data = self._get_parameter_from_tree_item(item)
                if param_data:
                    self._add_parameter_to_selected(param_data)
        except Exception as e:
            self.logger.error(f"Ошибка обработки двойного клика: {e}")

    def _on_parameter_right_click(self, event):
        """Обработка правого клика по параметру"""
        try:
            # Выделяем элемент под курсором
            item = self.tree_all.identify_row(event.y)
            if item:
                self.tree_all.selection_set(item)

                # Создаем контекстное меню
                context_menu = tk.Menu(self.tree_all, tearoff=0)
                context_menu.add_command(
                    label="Добавить в выбранные",
                    command=self._add_selected_parameters
                )
                context_menu.add_command(
                    label="Показать детали",
                    command=self._show_parameter_details
                )

                # Показываем меню
                context_menu.post(event.x_root, event.y_root)

        except Exception as e:
            self.logger.error(f"Ошибка контекстного меню: {e}")

    def _on_selected_parameter_double_click(self, event):
        """Обработка двойного клика по выбранному параметру"""
        try:
            selection = self.tree_selected.selection()
            if selection:
                # Удаляем параметр из выбранных
                self._remove_selected_parameters()
        except Exception as e:
            self.logger.error(
                f"Ошибка обработки двойного клика по выбранному: {e}")

    def _on_delete_selected_parameter(self, event):
        """Обработка нажатия Delete для удаления выбранного параметра"""
        try:
            self._remove_selected_parameters()
        except Exception as e:
            self.logger.error(f"Ошибка удаления параметра: {e}")

    # === МЕТОДЫ УПРАВЛЕНИЯ ПАРАМЕТРАМИ ===

    def update_parameters(self, parameters: List[Dict[str, Any]]):
        """Обновление списка всех параметров"""
        try:
            self.all_parameters = parameters.copy()
            self.filtered_parameters = parameters.copy()

            self._populate_parameters_tree()
            self._update_counters()

            self.logger.info(
                f"Обновлен список параметров: {len(parameters)} элементов")

        except Exception as e:
            self.logger.error(f"Ошибка обновления параметров: {e}")

    def _populate_parameters_tree(self):
        """Заполнение дерева всех параметров"""
        try:
            # Очищаем дерево
            for item in self.tree_all.get_children():
                self.tree_all.delete(item)

            if not self.filtered_parameters:
                return

            # Группируем параметры по типам данных
            groups = {}
            for param in self.filtered_parameters:
                signal_type = param.get('signal_type', 'Unknown')
                if signal_type not in groups:
                    groups[signal_type] = []
                groups[signal_type].append(param)

            # Добавляем группы и параметры
            for signal_type, group_params in sorted(groups.items()):
                # Создаем группу
                group_id = self.tree_all.insert(
                    "", "end",
                    text=signal_type,
                    values=("", f"({len(group_params)} параметров)", "", "")
                )

                # Добавляем параметры в группу
                for param in sorted(group_params, key=lambda x: x.get('signal_code', '')):
                    self.tree_all.insert(
                        group_id, "end",
                        text="",
                        values=(
                            param.get('signal_code', ''),
                            param.get('description', '')[
                                :50] + ("..." if len(param.get('description', '')) > 50 else ""),
                            param.get('line', ''),
                            param.get('wagon', '')
                        ),
                        tags=('parameter',)
                    )

            # Раскрываем все группы
            for item in self.tree_all.get_children():
                self.tree_all.item(item, open=True)

        except Exception as e:
            self.logger.error(f"Ошибка заполнения дерева параметров: {e}")

    def _populate_selected_tree(self):
        """Заполнение дерева выбранных параметров"""
        try:
            # Очищаем дерево
            for item in self.tree_selected.get_children():
                self.tree_selected.delete(item)

            # Добавляем выбранные параметры
            for idx, param in enumerate(self.selected_parameters, 1):
                self.tree_selected.insert(
                    "", "end",
                    text=str(idx),
                    values=(
                        param.get('signal_code', ''),
                        param.get('description', '')[
                            :40] + ("..." if len(param.get('description', '')) > 40 else "")
                    )
                )

            self._update_counters()
            self._notify_selection_changed()

        except Exception as e:
            self.logger.error(f"Ошибка заполнения дерева выбранных: {e}")

    def _filter_parameters_by_search(self, search_text: str):
        """Фильтрация параметров по поисковому запросу"""
        try:
            if not search_text:
                self.filtered_parameters = self.all_parameters.copy()
            else:
                self.filtered_parameters = []
                for param in self.all_parameters:
                    # Поиск в коде сигнала и описании
                    searchable_text = f"{param.get('signal_code', '')} {param.get('description', '')}"
                    if search_text in searchable_text.lower():
                        self.filtered_parameters.append(param)

            self._populate_parameters_tree()
            self._update_counters()

        except Exception as e:
            self.logger.error(f"Ошибка фильтрации по поиску: {e}")

    def _add_selected_parameters(self):
        """Добавление выбранных в дереве параметров к выбранным"""
        try:
            selection = self.tree_all.selection()
            added_count = 0

            for item in selection:
                param_data = self._get_parameter_from_tree_item(item)
                if param_data and self._add_parameter_to_selected(param_data):
                    added_count += 1

            if added_count > 0:
                self._populate_selected_tree()
                self.logger.info(
                    f"Добавлено {added_count} параметров в выбранные")

        except Exception as e:
            self.logger.error(f"Ошибка добавления выбранных параметров: {e}")

    def _add_parameter_to_selected(self, param_data: Dict[str, Any]) -> bool:
        """Добавление одного параметра к выбранным"""
        try:
            # Проверяем, что параметр еще не выбран
            signal_code = param_data.get('signal_code', '')
            for existing in self.selected_parameters:
                if existing.get('signal_code') == signal_code:
                    return False  # Уже выбран

            self.selected_parameters.append(param_data)
            return True

        except Exception as e:
            self.logger.error(f"Ошибка добавления параметра: {e}")
            return False

    def _remove_selected_parameters(self):
        """Удаление выбранных в дереве параметров из выбранных"""
        try:
            selection = self.tree_selected.selection()

            # Получаем индексы для удаления (в обратном порядке)
            indices_to_remove = []
            for item in selection:
                index = self.tree_selected.index(item)
                indices_to_remove.append(index)

            # Удаляем в обратном порядке
            for index in sorted(indices_to_remove, reverse=True):
                if 0 <= index < len(self.selected_parameters):
                    removed = self.selected_parameters.pop(index)
                    self.logger.debug(
                        f"Удален параметр: {removed.get('signal_code')}")

            self._populate_selected_tree()

        except Exception as e:
            self.logger.error(f"Ошибка удаления выбранных параметров: {e}")

    def _clear_all_selections(self):
        """Очистка всех выбранных параметров"""
        try:
            self.selected_parameters.clear()
            self._populate_selected_tree()
            self.logger.info("Очищены все выбранные параметры")
        except Exception as e:
            self.logger.error(f"Ошибка очистки выбранных параметров: {e}")

    def _auto_select_parameters(self):
        """Автоматический выбор первых 10 параметров"""
        try:
            # Очищаем текущий выбор
            self.selected_parameters.clear()

            # Добавляем первые 10 отфильтрованных параметров
            count = 0
            for param in self.filtered_parameters:
                if count >= 10:
                    break
                self.selected_parameters.append(param)
                count += 1

            self._populate_selected_tree()
            self.logger.info(f"Автоматически выбрано {count} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка автовыбора параметров: {e}")

    def _clear_search(self):
        """Очистка поискового запроса"""
        try:
            self.search_var.set("")
        except Exception as e:
            self.logger.error(f"Ошибка очистки поиска: {e}")

    def _get_parameter_from_tree_item(self, item) -> Optional[Dict[str, Any]]:
        """Получение данных параметра из элемента дерева"""
        try:
            # Проверяем, что это элемент параметра, а не группа
            if 'parameter' not in self.tree_all.item(item, 'tags'):
                return None

            values = self.tree_all.item(item, 'values')
            if not values or len(values) < 4:
                return None

            signal_code = values[0]

            # Ищем параметр в отфильтрованном списке
            for param in self.filtered_parameters:
                if param.get('signal_code') == signal_code:
                    return param

            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения параметра из дерева: {e}")
            return None

    def _show_parameter_details(self):
        """Показ детальной информации о параметре"""
        try:
            selection = self.tree_all.selection()
            if not selection:
                return

            param_data = self._get_parameter_from_tree_item(selection[0])
            if not param_data:
                return

            # Создаем окно с деталями
            details_window = tk.Toplevel(self)
            details_window.title(
                f"Детали параметра: {param_data.get('signal_code', 'Unknown')}")
            details_window.geometry("400x300")
            details_window.transient(self)
            details_window.grab_set()

            # Текстовое поле с информацией
            text_widget = tk.Text(
                details_window, wrap=tk.WORD, padx=10, pady=10)
            text_widget.pack(fill=tk.BOTH, expand=True)

            # Заполняем информацией
            details_text = "ИНФОРМАЦИЯ О ПАРАМЕТРЕ\n\n"
            for key, value in param_data.items():
                details_text += f"{key.upper()}: {value}\n"

            text_widget.insert(tk.END, details_text)
            text_widget.config(state=tk.DISABLED)

            # Кнопка закрытия
            ttk.Button(details_window, text="Закрыть",
                       command=details_window.destroy).pack(pady=5)

        except Exception as e:
            self.logger.error(f"Ошибка показа деталей параметра: {e}")

    # === СЛУЖЕБНЫЕ МЕТОДЫ ===

    def _update_counters(self):
        """Обновление счетчиков параметров"""
        try:
            total_count = len(self.all_parameters)
            filtered_count = len(self.filtered_parameters)
            selected_count = len(self.selected_parameters)

            self.total_label.config(text=f"Всего: {total_count}")
            self.filtered_label.config(text=f"Отфильтровано: {filtered_count}")
            self.selected_label.config(text=f"Выбрано: {selected_count}")

        except Exception as e:
            self.logger.error(f"Ошибка обновления счетчиков: {e}")

    def _notify_selection_changed(self):
        """Уведомление об изменении выбора"""
        try:
            if self.on_selection_changed:
                self.on_selection_changed(len(self.selected_parameters))
        except Exception as e:
            self.logger.error(f"Ошибка уведомления об изменении выбора: {e}")

    # === ПУБЛИЧНЫЕ МЕТОДЫ ===

    def get_selected_parameters(self) -> List[Dict[str, Any]]:
        """Получение списка выбранных параметров"""
        return self.selected_parameters.copy()

    def clear_selection(self):
        """Очистка выбора"""
        self._clear_all_selections()

    def update_counters(self, total_count: int, selected_count: int):
        """Обновление счетчиков извне"""
        try:
            self.total_label.config(text=f"Всего: {total_count}")
            self.selected_label.config(text=f"Выбрано: {selected_count}")
        except Exception as e:
            self.logger.error(f"Ошибка обновления счетчиков извне: {e}")

    def set_loading_state(self, loading: bool):
        """Установка состояния загрузки"""
        self.is_loading = loading

        # Отключаем/включаем элементы управления
        state = tk.DISABLED if loading else tk.NORMAL

        widgets_to_disable = [
            self.search_entry, self.tree_all, self.tree_selected
        ]

        for widget in widgets_to_disable:
            if widget:
                widget.config(state=state)

    def enable(self):
        """Включение панели"""
        self.set_loading_state(False)

    def disable(self):
        """Отключение панели"""
        self.set_loading_state(True)

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.all_parameters.clear()
            self.filtered_parameters.clear()
            self.selected_parameters.clear()
            self.controller = None
            self.on_selection_changed = None

            self.logger.info("ParameterPanel очищен")

        except Exception as e:
            self.logger.error(f"Ошибка очистки ParameterPanel: {e}")
