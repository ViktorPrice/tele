# src/ui/components/horizontal_parameter_panel.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Горизонтальная панель параметров с компоновкой 50/50 и улучшенным интерфейсом
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Optional, Callable

class HorizontalParameterPanel(ttk.Frame):
    """ИСПРАВЛЕННАЯ горизонтальная панель параметров с компоновкой 50/50"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Данные параметров
        self.all_parameters: List[Dict[str, Any]] = []
        self.selected_parameters: List[Dict[str, Any]] = []
        self.filtered_parameters: List[Dict[str, Any]] = []

        # UI элементы
        self.tree_all = None
        self.tree_selected = None
        self.selection_info = None
        self.filtered_count_label = None
        
        # НОВОЕ: Элементы для компоновки 50/50
        self.paned_window = None
        self.left_frame = None
        self.right_frame = None
        self.control_frame = None

        # Callbacks
        self.on_selection_changed: Optional[Callable] = None

        # ИСПРАВЛЕНО: Убираем информацию о поезде из панели параметров
        self._setup_horizontal_ui()
        self.logger.info("HorizontalParameterPanel инициализирован")

    def _setup_horizontal_ui(self):
        """ИСПРАВЛЕННАЯ настройка горизонтального UI с компоновкой 50/50"""
        try:
            # Основная настройка сетки
            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(0, weight=1)

            # НОВОЕ: Создаем PanedWindow для настраиваемой компоновки 50/50
            self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
            self.paned_window.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

            # Левая панель - все параметры (50%)
            self.left_frame = ttk.Frame(self.paned_window)
            self.left_frame.grid_rowconfigure(0, weight=1)
            self.left_frame.grid_columnconfigure(0, weight=1)

            # Правая панель - выбранные параметры (50%)
            self.right_frame = ttk.Frame(self.paned_window)
            self.right_frame.grid_rowconfigure(0, weight=1)
            self.right_frame.grid_columnconfigure(0, weight=1)

            # Добавляем панели в PanedWindow с равными весами
            self.paned_window.add(self.left_frame, weight=1)
            self.paned_window.add(self.right_frame, weight=1)

            # Создаем секции
            self._create_all_parameters_section()
            self._create_selected_parameters_section()
            self._create_control_buttons()

            # НОВОЕ: Настраиваем начальную компоновку 50/50
            self.after(100, self._configure_initial_split)

        except Exception as e:
            self.logger.error(f"Ошибка настройки UI: {e}")

    def _configure_initial_split(self):
        """НОВЫЙ МЕТОД: Настройка начальной компоновки 50/50"""
        try:
            # Получаем общую ширину
            total_width = self.paned_window.winfo_width()
            if total_width > 100:  # Проверяем, что виджет отрисован
                split_position = total_width // 2
                self.paned_window.sashpos(0, split_position)
                self.logger.debug(f"Установлена компоновка 50/50: {split_position}px")
        except Exception as e:
            self.logger.error(f"Ошибка настройки компоновки: {e}")

    def configure_split_layout(self, split_ratio: float = 0.5):
        """НОВЫЙ МЕТОД: Настройка соотношения панелей"""
        try:
            if not 0.1 <= split_ratio <= 0.9:
                split_ratio = 0.5
                
            total_width = self.paned_window.winfo_width()
            if total_width > 100:
                split_position = int(total_width * split_ratio)
                self.paned_window.sashpos(0, split_position)
                self.logger.info(f"Компоновка изменена на {int(split_ratio*100)}/{int((1-split_ratio)*100)}")
            else:
                # Если виджет еще не отрисован, планируем на потом
                self.after(100, lambda: self.configure_split_layout(split_ratio))
                
        except Exception as e:
            self.logger.error(f"Ошибка настройки компоновки: {e}")

    def _create_all_parameters_section(self):
        """ИСПРАВЛЕННОЕ создание секции всех параметров"""
        try:
            # Контейнер для всех параметров
            all_container = ttk.Frame(self.left_frame)
            all_container.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
            all_container.grid_rowconfigure(1, weight=1)
            all_container.grid_columnconfigure(0, weight=1)

            # Заголовок с счетчиком
            header_frame = ttk.Frame(all_container)
            header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 3))
            header_frame.grid_columnconfigure(0, weight=1)

            ttk.Label(
                header_frame, 
                text="📋 Все параметры", 
                font=('Arial', 10, 'bold')
            ).grid(row=0, column=0, sticky="w")

            self.filtered_count_label = ttk.Label(
                header_frame,
                text="(0 параметров)",
                font=('Arial', 9),
                foreground='gray'
            )
            self.filtered_count_label.grid(row=0, column=1, sticky="e")

            # Фрейм для дерева и скроллбара
            tree_frame = ttk.Frame(all_container)
            tree_frame.grid(row=1, column=0, sticky="nsew")
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Дерево всех параметров
            self.tree_all = ttk.Treeview(
                tree_frame,
                columns=("description", "line", "wagon"),
                show="tree headings",
                height=12
            )
            self.tree_all.heading("#0", text="Код", anchor=tk.W)
            self.tree_all.heading("description", text="Описание", anchor=tk.W)
            self.tree_all.heading("line", text="Линия", anchor=tk.W)
            self.tree_all.heading("wagon", text="Вагон", anchor=tk.W)
            self.tree_all.column("#0", width=100, minwidth=80)
            self.tree_all.column("description", width=250, minwidth=150)
            self.tree_all.column("line", width=80, minwidth=60)
            self.tree_all.column("wagon", width=60, minwidth=50)

            # Скроллбар для всех параметров
            scrollbar_all = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_all.yview)
            self.tree_all.configure(yscrollcommand=scrollbar_all.set)

            self.tree_all.grid(row=0, column=0, sticky="nsew")
            scrollbar_all.grid(row=0, column=1, sticky="ns")

            # События
            self.tree_all.bind("<Double-1>", self._on_all_double_click)
            self.tree_all.bind("<Button-3>", self._on_all_right_click)

        except Exception as e:
            self.logger.error(f"Ошибка создания секции всех параметров: {e}")

    def _create_selected_parameters_section(self):
        """ИСПРАВЛЕННОЕ создание секции выбранных параметров"""
        try:
            # Контейнер для выбранных параметров
            selected_container = ttk.Frame(self.right_frame)
            selected_container.grid(row=0, column=0, sticky="nsew", padx=(2, 0))
            selected_container.grid_rowconfigure(1, weight=1)
            selected_container.grid_columnconfigure(0, weight=1)

            # Заголовок с счетчиком
            header_frame = ttk.Frame(selected_container)
            header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 3))
            header_frame.grid_columnconfigure(0, weight=1)

            ttk.Label(
                header_frame, 
                text="✅ Выбранные параметры", 
                font=('Arial', 10, 'bold')
            ).grid(row=0, column=0, sticky="w")

            self.selection_info = ttk.Label(
                header_frame,
                text="(0 выбрано)",
                font=('Arial', 9),
                foreground='green'
            )
            self.selection_info.grid(row=0, column=1, sticky="e")

            # Фрейм для дерева и скроллбара
            tree_frame = ttk.Frame(selected_container)
            tree_frame.grid(row=1, column=0, sticky="nsew")
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Дерево выбранных параметров
            self.tree_selected = ttk.Treeview(
                tree_frame,
                columns=("code", "description", "line", "wagon"),
                show="tree headings",
                height=12
            )
            self.tree_selected.heading("#0", text="№", anchor=tk.W)
            self.tree_selected.heading("code", text="Код", anchor=tk.W)
            self.tree_selected.heading("description", text="Описание", anchor=tk.W)
            self.tree_selected.heading("line", text="Линия", anchor=tk.W)
            self.tree_selected.heading("wagon", text="Вагон", anchor=tk.W)
            self.tree_selected.column("#0", width=30, minwidth=30)
            self.tree_selected.column("code", width=80, minwidth=60)
            self.tree_selected.column("description", width=200, minwidth=150)
            self.tree_selected.column("line", width=80, minwidth=60)
            self.tree_selected.column("wagon", width=60, minwidth=50)

            # Скроллбар для выбранных параметров
            scrollbar_selected = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_selected.yview)
            self.tree_selected.configure(yscrollcommand=scrollbar_selected.set)

            self.tree_selected.grid(row=0, column=0, sticky="nsew")
            scrollbar_selected.grid(row=0, column=1, sticky="ns")

            # События
            self.tree_selected.bind("<Double-1>", self._on_selected_double_click)
            self.tree_selected.bind("<Button-3>", self._on_selected_right_click)
            self.tree_selected.bind("<<TreeviewSelect>>", self._on_selection_changed_event)
            self.tree_selected.bind("<Delete>", self._on_delete_key)

        except Exception as e:
            self.logger.error(f"Ошибка создания секции выбранных параметров: {e}")

    def _create_control_buttons(self):
        """ИСПРАВЛЕННОЕ создание кнопок управления в нижней части"""
        try:
            # Контейнер для кнопок управления в нижней части левой панели
            control_container = ttk.Frame(self.left_frame)
            control_container.grid(row=1, column=0, sticky="ew", padx=(0, 2), pady=(3, 0))
            control_container.grid_columnconfigure(0, weight=1)
            control_container.grid_columnconfigure(1, weight=1)
            control_container.grid_columnconfigure(2, weight=1)
            control_container.grid_columnconfigure(3, weight=1)

            # Кнопки добавления
            add_btn = ttk.Button(
                control_container,
                text="➤ Добавить",
                command=self._add_selected_parameters
            )
            add_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

            add_all_btn = ttk.Button(
                control_container,
                text="➤➤ Все",
                command=self._add_all_parameters
            )
            add_all_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

            # Кнопки удаления в правой панели
            remove_container = ttk.Frame(self.right_frame)
            remove_container.grid(row=1, column=0, sticky="ew", padx=(2, 0), pady=(3, 0))
            remove_container.grid_columnconfigure(0, weight=1)
            remove_container.grid_columnconfigure(1, weight=1)
            remove_container.grid_columnconfigure(2, weight=1)
            remove_container.grid_columnconfigure(3, weight=1)

            remove_btn = ttk.Button(
                remove_container,
                text="✖ Удалить",
                command=self._remove_selected_parameters
            )
            remove_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

            remove_all_btn = ttk.Button(
                remove_container,
                text="🗑 Очистить",
                command=self._remove_all_parameters
            )
            remove_all_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

            # Кнопки сортировки
            sort_up_btn = ttk.Button(
                remove_container,
                text="⬆ Вверх",
                command=self._move_parameter_up
            )
            sort_up_btn.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

            sort_down_btn = ttk.Button(
                remove_container,
                text="⬇ Вниз",
                command=self._move_parameter_down
            )
            sort_down_btn.grid(row=0, column=3, padx=2, pady=2, sticky="ew")

        except Exception as e:
            self.logger.error(f"Ошибка создания кнопок управления: {e}")

    def _add_selected_parameters(self):
        """ИСПРАВЛЕННОЕ добавление выбранных параметров"""
        try:
            selection = self.tree_all.selection()
            if not selection:
                self.logger.warning("Выберите параметры для добавления")
                return

            added_count = 0
            for item in selection:
                # Проверяем, что это параметр, а не группа
                signal_code = self.tree_all.item(item, 'text')
                if signal_code and not self.tree_all.get_children(item):  # Листовой узел
                    param_data = self._find_parameter_by_code(signal_code)
                    if param_data and self._add_param_to_selected(param_data):
                        added_count += 1

            if added_count > 0:
                self._populate_selected_tree()
                self._update_selection_info()
                self._notify_selection_changed()
                self.logger.info(f"Добавлено {added_count} параметров")
            else:
                self.logger.warning("Параметры уже добавлены или выберите корректные элементы")

        except Exception as e:
            self.logger.error(f"Ошибка добавления параметров: {e}")

    def _add_all_parameters(self):
        """ИСПРАВЛЕННОЕ добавление всех видимых параметров"""
        try:
            added_count = 0
            current_params = self.filtered_parameters if self.filtered_parameters else self.all_parameters

            for param in current_params:
                if self._add_param_to_selected(param):
                    added_count += 1

            if added_count > 0:
                self._populate_selected_tree()
                self._update_selection_info()
                self._notify_selection_changed()
                self.logger.info(f"Добавлено всех параметров: {added_count}")
            else:
                self.logger.info("Все параметры уже добавлены")

        except Exception as e:
            self.logger.error(f"Ошибка добавления всех параметров: {e}")

    def _remove_selected_parameters(self):
        """ИСПРАВЛЕННОЕ удаление выбранных параметров"""
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
            removed_count = 0
            for index in sorted(indices_to_remove, reverse=True):
                if 0 <= index < len(self.selected_parameters):
                    removed_param = self.selected_parameters.pop(index)
                    removed_count += 1
                    self.logger.debug(f"Удален: {removed_param.get('signal_code', 'Unknown')}")

            if removed_count > 0:
                self._populate_selected_tree()
                self._update_selection_info()
                self._notify_selection_changed()
                self.logger.info(f"Удалено {removed_count} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка удаления параметров: {e}")

    def _remove_all_parameters(self):
        """ИСПРАВЛЕННАЯ очистка всех выбранных параметров"""
        try:
            if not self.selected_parameters:
                self.logger.info("Нет параметров для очистки")
                return

            count = len(self.selected_parameters)
            self.selected_parameters.clear()
            self._populate_selected_tree()
            self._update_selection_info()
            self._notify_selection_changed()
            self.logger.info(f"Очищено {count} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка очистки параметров: {e}")

    def _move_parameter_up(self):
        """ИСПРАВЛЕННОЕ перемещение параметра вверх"""
        try:
            selection = self.tree_selected.selection()
            if not selection:
                self.logger.warning("Выберите параметр для перемещения")
                return

            index = self.tree_selected.index(selection[0])
            if index > 0:
                # Меняем местами
                self.selected_parameters[index], self.selected_parameters[index-1] = \
                    self.selected_parameters[index-1], self.selected_parameters[index]

                self._populate_selected_tree()
                self._notify_selection_changed()

                # Восстанавливаем выбор
                new_item = self.tree_selected.get_children()[index-1]
                self.tree_selected.selection_set(new_item)
                self.tree_selected.focus(new_item)

        except Exception as e:
            self.logger.error(f"Ошибка перемещения вверх: {e}")

    def _move_parameter_down(self):
        """ИСПРАВЛЕННОЕ перемещение параметра вниз"""
        try:
            selection = self.tree_selected.selection()
            if not selection:
                self.logger.warning("Выберите параметр для перемещения")
                return

            index = self.tree_selected.index(selection[0])
            if index < len(self.selected_parameters) - 1:
                # Меняем местами
                self.selected_parameters[index], self.selected_parameters[index+1] = \
                    self.selected_parameters[index+1], self.selected_parameters[index]

                self._populate_selected_tree()
                self._notify_selection_changed()

                # Восстанавливаем выбор
                new_item = self.tree_selected.get_children()[index+1]
                self.tree_selected.selection_set(new_item)
                self.tree_selected.focus(new_item)

        except Exception as e:
            self.logger.error(f"Ошибка перемещения вниз: {e}")

    def _find_parameter_by_code(self, signal_code: str) -> Optional[Dict[str, Any]]:
        """ИСПРАВЛЕННЫЙ поиск параметра по коду"""
        # Сначала ищем в отфильтрованных параметрах
        search_list = self.filtered_parameters if self.filtered_parameters else self.all_parameters
        
        for param in search_list:
            if param.get('signal_code') == signal_code:
                return param
        return None

    def _add_param_to_selected(self, param_data: Dict[str, Any]) -> bool:
        """ИСПРАВЛЕННОЕ добавление параметра в выбранные (без дубликатов)"""
        signal_code = param_data.get('signal_code', '')

        # Проверяем дубликаты
        for existing in self.selected_parameters:
            if existing.get('signal_code') == signal_code:
                return False

        self.selected_parameters.append(param_data.copy())
        return True

    def _update_selection_info(self):
        """ИСПРАВЛЕННОЕ обновление информации о выборе"""
        try:
            count = len(self.selected_parameters)
            if self.selection_info:
                self.selection_info.config(text=f"({count} выбрано)")

        except Exception as e:
            self.logger.error(f"Ошибка обновления информации: {e}")

    def _notify_selection_changed(self):
        """НОВЫЙ МЕТОД: Уведомление об изменении выбора"""
        try:
            count = len(self.selected_parameters)
            
            # Уведомляем через callback
            if self.on_selection_changed:
                self.on_selection_changed(count)
            
            # Уведомляем контроллер
            if self.controller and hasattr(self.controller, '_on_parameter_selection_changed'):
                self.controller._on_parameter_selection_changed(count)

        except Exception as e:
            self.logger.error(f"Ошибка уведомления об изменении: {e}")

    def _on_selection_changed_event(self, event):
        """Обработка события изменения выбора в дереве"""
        self._update_selection_info()

    def _on_all_double_click(self, event):
        """ИСПРАВЛЕННЫЙ двойной клик - добавить в выбранные"""
        try:
            selection = self.tree_all.selection()
            if selection:
                item = selection[0]
                signal_code = self.tree_all.item(item, 'text')

                # Проверяем, что это параметр, а не группа
                if signal_code and not self.tree_all.get_children(item):
                    param_data = self._find_parameter_by_code(signal_code)
                    if param_data and self._add_param_to_selected(param_data):
                        self._populate_selected_tree()
                        self._update_selection_info()
                        self._notify_selection_changed()
                        self.logger.debug(f"Добавлен параметр: {signal_code}")

        except Exception as e:
            self.logger.error(f"Ошибка двойного клика: {e}")

    def _on_selected_double_click(self, event):
        """ИСПРАВЛЕННЫЙ двойной клик - удалить из выбранных"""
        try:
            selection = self.tree_selected.selection()
            if selection:
                item = selection[0]
                index = self.tree_selected.index(item)
                
                if 0 <= index < len(self.selected_parameters):
                    removed_param = self.selected_parameters.pop(index)
                    self._populate_selected_tree()
                    self._update_selection_info()
                    self._notify_selection_changed()
                    self.logger.debug(f"Удален параметр: {removed_param.get('signal_code', 'Unknown')}")

        except Exception as e:
            self.logger.error(f"Ошибка двойного клика на выбранном: {e}")

    def _on_delete_key(self, event):
        """НОВЫЙ МЕТОД: Обработка клавиши Delete"""
        self._remove_selected_parameters()

    def _on_all_right_click(self, event):
        """НОВЫЙ МЕТОД: Контекстное меню для всех параметров"""
        try:
            # Определяем элемент под курсором
            item = self.tree_all.identify_row(event.y)
            if item:
                self.tree_all.selection_set(item)
                
                # Создаем контекстное меню
                context_menu = tk.Menu(self, tearoff=0)
                context_menu.add_command(label="➤ Добавить", command=self._add_selected_parameters)
                context_menu.add_command(label="➤➤ Добавить все", command=self._add_all_parameters)
                
                context_menu.tk_popup(event.x_root, event.y_root)

        except Exception as e:
            self.logger.error(f"Ошибка контекстного меню: {e}")

    def _on_selected_right_click(self, event):
        """НОВЫЙ МЕТОД: Контекстное меню для выбранных параметров"""
        try:
            # Определяем элемент под курсором
            item = self.tree_selected.identify_row(event.y)
            if item:
                self.tree_selected.selection_set(item)
                
                # Создаем контекстное меню
                context_menu = tk.Menu(self, tearoff=0)
                context_menu.add_command(label="✖ Удалить", command=self._remove_selected_parameters)
                context_menu.add_command(label="🗑 Очистить все", command=self._remove_all_parameters)
                context_menu.add_separator()
                context_menu.add_command(label="⬆ Переместить вверх", command=self._move_parameter_up)
                context_menu.add_command(label="⬇ Переместить вниз", command=self._move_parameter_down)
                
                context_menu.tk_popup(event.x_root, event.y_root)

        except Exception as e:
            self.logger.error(f"Ошибка контекстного меню выбранных: {e}")

    def update_parameters(self, parameters: List[Dict[str, Any]]):
        """ИСПРАВЛЕННОЕ обновление списка параметров"""
        try:
            self.all_parameters = parameters.copy()
            self.filtered_parameters = []  # Сбрасываем фильтр
            self._populate_all_tree()
            self._update_filtered_count()
            self.logger.info(f"HorizontalParameterPanel: обновлено {len(parameters)} параметров")
        except Exception as e:
            self.logger.error(f"Ошибка обновления параметров: {e}")

    def update_filtered_count(self, count: int):
        """НОВЫЙ МЕТОД: Обновление счетчика отфильтрованных параметров"""
        try:
            if self.filtered_count_label:
                self.filtered_count_label.config(text=f"({count} параметров)")
        except Exception as e:
            self.logger.error(f"Ошибка обновления счетчика: {e}")

    def update_counters(self, all_count: int, selected_count: int):
        """НОВЫЙ МЕТОД: Обновление обоих счетчиков"""
        try:
            if self.filtered_count_label:
                self.filtered_count_label.config(text=f"({all_count} параметров)")
            if self.selection_info:
                self.selection_info.config(text=f"({selected_count} выбрано)")
        except Exception as e:
            self.logger.error(f"Ошибка обновления счетчиков: {e}")

    def _update_filtered_count(self):
        """ИСПРАВЛЕННОЕ обновление счетчика отфильтрованных параметров"""
        try:
            count = len(self.filtered_parameters) if self.filtered_parameters else len(self.all_parameters)
            if self.filtered_count_label:
                self.filtered_count_label.config(text=f"({count} параметров)")
        except Exception as e:
            self.logger.error(f"Ошибка обновления счетчика: {e}")

    def _populate_all_tree(self):
        """ИСПРАВЛЕННОЕ заполнение дерева всех параметров"""
        try:
            # Очищаем дерево
            for item in self.tree_all.get_children():
                self.tree_all.delete(item)

            # Определяем какие параметры показывать
            params_to_show = self.filtered_parameters if self.filtered_parameters else self.all_parameters

            if not params_to_show:
                return

            # Группировка по типу сигнала
            groups = {}
            for param in params_to_show:
                signal_code = param.get('signal_code', '')
                if signal_code:
                    signal_type = signal_code[0] if signal_code else 'Unknown'
                    group_key = f"Тип {signal_type}"
                else:
                    group_key = "Без типа"

                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(param)

            # Добавляем группы
            for group_name, group_params in sorted(groups.items()):
                group_id = self.tree_all.insert("", "end", text=group_name,
                                               values=(f"({len(group_params)} параметров)", "", ""),
                                               tags=('group',))

                for param in sorted(group_params, key=lambda x: x.get('signal_code', '')):
                    description = param.get('description', '')[:60]
                    line = param.get('line', '')
                    wagon = param.get('wagon', '')
                    self.tree_all.insert(group_id, "end",
                                         text=param.get('signal_code', ''),
                                         values=(description, line, wagon),
                                         tags=('parameter',))

            # Раскрываем все группы
            for item in self.tree_all.get_children():
                self.tree_all.item(item, open=True)

        except Exception as e:
            self.logger.error(f"Ошибка заполнения дерева всех параметров: {e}")

    def _populate_selected_tree(self):
        """ИСПРАВЛЕННОЕ заполнение дерева выбранных параметров"""
        try:
            # Очищаем дерево
            for item in self.tree_selected.get_children():
                self.tree_selected.delete(item)

            # Добавляем выбранные параметры
            for idx, param in enumerate(self.selected_parameters, start=1):
                signal_code = param.get('signal_code', '')
                description = param.get('description', '')[:50]
                line = param.get('line', '')
                wagon = param.get('wagon', '')
                self.tree_selected.insert("", "end",
                                          text=str(idx),
                                          values=(signal_code, description, line, wagon))

        except Exception as e:
            self.logger.error(f"Ошибка заполнения дерева выбранных параметров: {e}")

    def apply_filter(self, filtered_params: List[Dict[str, Any]]):
        """НОВЫЙ МЕТОД: Применение фильтра к параметрам"""
        try:
            self.filtered_parameters = filtered_params.copy()
            self._populate_all_tree()
            self._update_filtered_count()
            self.logger.debug(f"Применен фильтр: {len(filtered_params)} параметров")
        except Exception as e:
            self.logger.error(f"Ошибка применения фильтра: {e}")

    def clear_filter(self):
        """НОВЫЙ МЕТОД: Очистка фильтра"""
        try:
            self.filtered_parameters = []
            self._populate_all_tree()
            self._update_filtered_count()
            self.logger.debug("Фильтр очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки фильтра: {e}")

    def get_selected_parameters(self) -> List[Dict[str, Any]]:
        """ИСПРАВЛЕННОЕ получение выбранных параметров"""
        return [param.copy() for param in self.selected_parameters]

    def set_selected_parameters(self, parameters: List[Dict[str, Any]]):
        """НОВЫЙ МЕТОД: Установка выбранных параметров"""
        try:
            self.selected_parameters = [param.copy() for param in parameters]
            self._populate_selected_tree()
            self._update_selection_info()
            self._notify_selection_changed()
            self.logger.info(f"Установлено {len(parameters)} выбранных параметров")
        except Exception as e:
            self.logger.error(f"Ошибка установки выбранных параметров: {e}")

    def get_all_parameters_count(self) -> int:
        """НОВЫЙ МЕТОД: Получение количества всех параметров"""
        return len(self.filtered_parameters) if self.filtered_parameters else len(self.all_parameters)

    def get_selected_parameters_count(self) -> int:
        """НОВЫЙ МЕТОД: Получение количества выбранных параметров"""
        return len(self.selected_parameters)

    def set_controller(self, controller):
        """ИСПРАВЛЕННАЯ установка контроллера"""
        try:
            self.controller = controller
            self.logger.debug("Контроллер установлен в HorizontalParameterPanel")
        except Exception as e:
            self.logger.error(f"Ошибка установки контроллера: {e}")

    def cleanup(self):
        """ИСПРАВЛЕННАЯ очистка ресурсов"""
        try:
            # Очищаем данные
            self.all_parameters.clear()
            self.selected_parameters.clear()
            self.filtered_parameters.clear()
            
            # Очищаем деревья
            if self.tree_all:
                for item in self.tree_all.get_children():
                    self.tree_all.delete(item)
            
            if self.tree_selected:
                for item in self.tree_selected.get_children():
                    self.tree_selected.delete(item)
            
            # Обнуляем ссылки
            self.controller = None
            self.on_selection_changed = None
            
            self.logger.info("HorizontalParameterPanel очищен")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки HorizontalParameterPanel: {e}")

    def __str__(self):
        return f"HorizontalParameterPanel(all={len(self.all_parameters)}, selected={len(self.selected_parameters)})"

    def __repr__(self):
        return self.__str__()
