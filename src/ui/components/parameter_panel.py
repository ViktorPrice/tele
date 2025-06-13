# src/ui/components/parameter_panel.py - ИСПРАВЛЕННАЯ И ОПТИМИЗИРОВАННАЯ ВЕРСИЯ
"""
Панель параметров телеметрии с улучшенной группировкой и функциональностью
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Optional, Callable
import re
from collections import defaultdict

class ParameterPanel(ttk.Frame):
    """ИСПРАВЛЕННАЯ панель параметров телеметрии с полной функциональностью"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Данные параметров
        self.all_parameters: List[Dict[str, Any]] = []
        self.filtered_parameters: List[Dict[str, Any]] = []
        self.selected_parameters: List[Dict[str, Any]] = []

        # Переменные поиска и фильтрации
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_changed)

        # UI элементы
        self.tree_all: Optional[ttk.Treeview] = None
        self.tree_selected: Optional[ttk.Treeview] = None
        self.all_count_label: Optional[ttk.Label] = None
        self.filtered_count_label: Optional[ttk.Label] = None
        self.selected_count_label: Optional[ttk.Label] = None
        self.search_entry: Optional[tk.Entry] = None
        self.grouping_combo: Optional[ttk.Combobox] = None

        # Callbacks
        self.on_selection_changed: Optional[Callable[[int], None]] = None

        # Настройки группировки
        self.grouping_mode = 'signal_type'  # 'signal_type', 'line', 'wagon', 'component'
        self.show_empty_groups = False

        # НОВОЕ: Кэширование для оптимизации
        self._search_cache = {}
        self._group_cache = {}
        self._last_search_term = ""
        self._last_grouping_mode = ""

        self._setup_ui()
        self.logger.info("ParameterPanel инициализирован")

    def _setup_ui(self):
        """ИСПРАВЛЕННАЯ настройка пользовательского интерфейса"""
        try:
            self.logger.info("ParameterPanel: _setup_ui вызван")

            # Настройка сетки
            self.grid_rowconfigure(2, weight=1)  # Основная область с деревьями
            self.grid_columnconfigure(0, weight=1)

            # 1. Секция поиска и группировки
            self._create_search_section()

            # 2. Секция счетчиков
            self._create_counters_section()

            # 3. Основная область с деревьями параметров
            self._create_parameter_trees()

            # 4. Кнопки управления
            self._create_control_buttons()

            self.logger.info("ParameterPanel: _setup_ui завершён")

        except Exception as e:
            self.logger.error(f"Ошибка настройки UI ParameterPanel: {e}")
            import traceback
            traceback.print_exc()

    def _create_search_section(self):
        """ИСПРАВЛЕННОЕ создание секции поиска и группировки"""
        try:
            self.logger.info("ParameterPanel: _create_search_section")

            search_frame = ttk.Frame(self)
            search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
            search_frame.grid_columnconfigure(1, weight=1)

            # Поиск
            ttk.Label(search_frame, text="🔍 Поиск:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky="w")

            self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 9))
            self.search_entry.grid(row=0, column=1, sticky="ew", padx=(5, 5))

            # Кнопка очистки поиска
            clear_btn = ttk.Button(search_frame, text="✕", width=3, command=self._clear_search)
            clear_btn.grid(row=0, column=2)

            # Настройки группировки
            grouping_frame = ttk.Frame(search_frame)
            grouping_frame.grid(row=0, column=3, sticky="e", padx=(10, 0))

            ttk.Label(grouping_frame, text="📂 Группировка:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky="w")

            self.grouping_combo = ttk.Combobox(
                grouping_frame,
                values=["По типу сигнала", "По линии связи", "По вагону", "По компоненту"],
                state="readonly",
                width=15,
                font=('Arial', 9)
            )
            self.grouping_combo.set("По типу сигнала")
            self.grouping_combo.grid(row=0, column=1, padx=(5, 0))
            self.grouping_combo.bind('<<ComboboxSelected>>', self._on_grouping_changed)

            # НОВОЕ: Горячие клавиши для поиска
            self.search_entry.bind('<Control-a>', lambda e: self.search_entry.select_range(0, tk.END))
            self.search_entry.bind('<Escape>', lambda e: self._clear_search())

        except Exception as e:
            self.logger.error(f"Ошибка создания секции поиска: {e}")

    def _create_counters_section(self):
        """ИСПРАВЛЕННОЕ создание секции счетчиков"""
        try:
            self.logger.info("ParameterPanel: _create_counters_section")

            counters_frame = ttk.Frame(self)
            counters_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
            counters_frame.grid_columnconfigure(3, weight=1)  # Растягиваем последний элемент

            # Счетчики с иконками
            self.all_count_label = ttk.Label(
                counters_frame, 
                text="📊 Всего: 0", 
                font=('Arial', 9),
                foreground='gray'
            )
            self.all_count_label.grid(row=0, column=0, sticky="w")

            self.filtered_count_label = ttk.Label(
                counters_frame, 
                text="🔍 Отфильтровано: 0", 
                font=('Arial', 9),
                foreground='blue'
            )
            self.filtered_count_label.grid(row=0, column=1, sticky="w", padx=(20, 0))

            self.selected_count_label = ttk.Label(
                counters_frame, 
                text="✅ Выбрано: 0", 
                font=('Arial', 9),
                foreground='green'
            )
            self.selected_count_label.grid(row=0, column=2, sticky="w", padx=(20, 0))

            # НОВОЕ: Индикатор производительности
            self.performance_label = ttk.Label(
                counters_frame,
                text="⚡ Готов",
                font=('Arial', 8),
                foreground='gray'
            )
            self.performance_label.grid(row=0, column=3, sticky="e")

        except Exception as e:
            self.logger.error(f"Ошибка создания секции счетчиков: {e}")

    def _create_parameter_trees(self):
        """ИСПРАВЛЕННОЕ создание деревьев параметров с компоновкой 50/50"""
        try:
            self.logger.info("ParameterPanel: _create_parameter_trees")

            # Основной контейнер для деревьев с PanedWindow для 50/50
            trees_container = ttk.Frame(self)
            trees_container.grid(row=2, column=0, sticky="nsew", pady=(0, 5))
            trees_container.grid_rowconfigure(0, weight=1)
            trees_container.grid_columnconfigure(0, weight=1)

            # ИСПРАВЛЕНО: Используем PanedWindow для настраиваемой компоновки 50/50
            self.paned_window = ttk.PanedWindow(trees_container, orient=tk.HORIZONTAL)
            self.paned_window.grid(row=0, column=0, sticky="nsew")

            # Левая панель - все параметры
            self._create_all_parameters_tree()

            # Правая панель - выбранные параметры
            self._create_selected_parameters_tree()

            # НОВОЕ: Настраиваем начальную компоновку 50/50
            self.after(100, self._configure_initial_split)

        except Exception as e:
            self.logger.error(f"Ошибка создания деревьев параметров: {e}")

    def _configure_initial_split(self):
        """НОВЫЙ МЕТОД: Настройка начальной компоновки 50/50"""
        try:
            total_width = self.paned_window.winfo_width()
            if total_width > 100:
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
                self.after(100, lambda: self.configure_split_layout(split_ratio))
                
        except Exception as e:
            self.logger.error(f"Ошибка настройки компоновки: {e}")

    def _create_all_parameters_tree(self):
        """ИСПРАВЛЕННОЕ создание дерева всех параметров"""
        try:
            all_frame = ttk.LabelFrame(self.paned_window, text="📋 Все параметры", padding="5")
            all_frame.grid_rowconfigure(0, weight=1)
            all_frame.grid_columnconfigure(0, weight=1)

            # Определяем столбцы
            columns = ("signal_code", "description", "line", "wagon")
            
            self.tree_all = ttk.Treeview(
                all_frame,
                columns=columns,
                show="tree headings",
                height=15
            )

            # Настройка заголовков с иконками
            self.tree_all.heading("#0", text="📂 Группа", anchor=tk.W)
            self.tree_all.heading("signal_code", text="🔢 Код сигнала", anchor=tk.W)
            self.tree_all.heading("description", text="📝 Описание", anchor=tk.W)
            self.tree_all.heading("line", text="🔗 Линия", anchor=tk.W)
            self.tree_all.heading("wagon", text="🚃 Вагон", anchor=tk.W)

            # ИСПРАВЛЕНО: Оптимальные ширины столбцов
            self.tree_all.column("#0", width=100, minwidth=80)
            self.tree_all.column("signal_code", width=120, minwidth=100)
            self.tree_all.column("description", width=250, minwidth=200)
            self.tree_all.column("line", width=80, minwidth=60)
            self.tree_all.column("wagon", width=60, minwidth=50)

            # Прокрутка
            scrollbar_all = ttk.Scrollbar(all_frame, orient="vertical", command=self.tree_all.yview)
            self.tree_all.configure(yscrollcommand=scrollbar_all.set)

            # Размещение
            self.tree_all.grid(row=0, column=0, sticky="nsew")
            scrollbar_all.grid(row=0, column=1, sticky="ns")

            # События
            self.tree_all.bind("<Double-1>", self._on_all_double_click)
            self.tree_all.bind("<Button-3>", self._on_all_right_click)
            self.tree_all.bind("<<TreeviewSelect>>", self._on_all_tree_select)
            self.tree_all.bind("<Return>", self._on_all_enter_key)

            # Добавляем в PanedWindow
            self.paned_window.add(all_frame, weight=1)

        except Exception as e:
            self.logger.error(f"Ошибка создания дерева всех параметров: {e}")

    def _create_selected_parameters_tree(self):
        """ИСПРАВЛЕННОЕ создание дерева выбранных параметров"""
        try:
            selected_frame = ttk.LabelFrame(self.paned_window, text="✅ Выбранные параметры", padding="5")
            selected_frame.grid_rowconfigure(0, weight=1)
            selected_frame.grid_columnconfigure(0, weight=1)

            # Дерево выбранных параметров
            columns = ("signal_code", "description", "line")
            
            self.tree_selected = ttk.Treeview(
                selected_frame,
                columns=columns,
                show="tree headings",
                height=15
            )

            # Настройка заголовков
            self.tree_selected.heading("#0", text="№", anchor=tk.W)
            self.tree_selected.heading("signal_code", text="🔢 Код сигнала", anchor=tk.W)
            self.tree_selected.heading("description", text="📝 Описание", anchor=tk.W)
            self.tree_selected.heading("line", text="🔗 Линия", anchor=tk.W)

            # ИСПРАВЛЕНО: Оптимальные ширины столбцов
            self.tree_selected.column("#0", width=40, minwidth=30)
            self.tree_selected.column("signal_code", width=120, minwidth=100)
            self.tree_selected.column("description", width=250, minwidth=200)
            self.tree_selected.column("line", width=80, minwidth=60)

            # Прокрутка
            scrollbar_selected = ttk.Scrollbar(selected_frame, orient="vertical", command=self.tree_selected.yview)
            self.tree_selected.configure(yscrollcommand=scrollbar_selected.set)

            # Размещение
            self.tree_selected.grid(row=0, column=0, sticky="nsew")
            scrollbar_selected.grid(row=0, column=1, sticky="ns")

            # События
            self.tree_selected.bind("<Double-1>", self._on_selected_double_click)
            self.tree_selected.bind("<Delete>", self._on_delete_selected)
            self.tree_selected.bind("<Button-3>", self._on_selected_right_click)
            self.tree_selected.bind("<Return>", self._on_selected_enter_key)

            # Добавляем в PanedWindow
            self.paned_window.add(selected_frame, weight=1)

        except Exception as e:
            self.logger.error(f"Ошибка создания дерева выбранных параметров: {e}")

    def _create_control_buttons(self):
        """ИСПРАВЛЕННОЕ создание кнопок управления"""
        try:
            self.logger.info("ParameterPanel: _create_control_buttons")

            buttons_frame = ttk.Frame(self)
            buttons_frame.grid(row=3, column=0, sticky="ew", pady=(5, 0))

            # Левая группа кнопок - управление выбором
            left_buttons = ttk.Frame(buttons_frame)
            left_buttons.pack(side=tk.LEFT)

            ttk.Button(left_buttons, text="➤ Добавить", command=self._add_selected, width=12).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(left_buttons, text="⬅ Удалить", command=self._remove_selected, width=12).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(left_buttons, text="🗑 Очистить все", command=self._clear_all_selected, width=12).pack(side=tk.LEFT, padx=(0, 5))

            # Центральная группа - сортировка
            center_buttons = ttk.Frame(buttons_frame)
            center_buttons.pack(side=tk.LEFT, padx=(20, 0))

            ttk.Button(center_buttons, text="⬆ Вверх", command=self._move_selected_up, width=10).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(center_buttons, text="⬇ Вниз", command=self._move_selected_down, width=10).pack(side=tk.LEFT, padx=(0, 5))

            # Правая группа кнопок - управление деревом
            right_buttons = ttk.Frame(buttons_frame)
            right_buttons.pack(side=tk.RIGHT)

            ttk.Button(right_buttons, text="📂 Развернуть", command=self._expand_all, width=12).pack(side=tk.RIGHT, padx=(5, 0))
            ttk.Button(right_buttons, text="📁 Свернуть", command=self._collapse_all, width=12).pack(side=tk.RIGHT, padx=(5, 0))

        except Exception as e:
            self.logger.error(f"Ошибка создания кнопок управления: {e}")

    # === ОБРАБОТЧИКИ СОБЫТИЙ ===

    def _on_search_changed(self, *args):
        """ОПТИМИЗИРОВАННАЯ обработка изменения поискового запроса"""
        try:
            search_text = self.search_var.get().strip().lower()
            
            # Оптимизация: не обновляем если поиск не изменился
            if search_text == self._last_search_term:
                return
                
            self._last_search_term = search_text
            self._update_performance_indicator("🔍 Поиск...")
            
            # Используем кэш для быстрого поиска
            if search_text in self._search_cache:
                self.filtered_parameters = self._search_cache[search_text].copy()
            else:
                self._filter_parameters_by_search(search_text)
                # Кэшируем результат (ограничиваем размер кэша)
                if len(self._search_cache) < 50:
                    self._search_cache[search_text] = self.filtered_parameters.copy()
            
            self._populate_parameters_tree()
            self._update_counters()
            self._update_performance_indicator("⚡ Готов")
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска: {e}")
            self._update_performance_indicator("❌ Ошибка")

    def _on_grouping_changed(self, event):
        """ОПТИМИЗИРОВАННАЯ обработка изменения режима группировки"""
        try:
            combo = event.widget
            selection = combo.get()
            
            grouping_map = {
                "По типу сигнала": "signal_type",
                "По линии связи": "line",
                "По вагону": "wagon",
                "По компоненту": "component"
            }
            
            new_mode = grouping_map.get(selection, "signal_type")
            
            # Оптимизация: не обновляем если режим не изменился
            if new_mode == self._last_grouping_mode:
                return
                
            self._last_grouping_mode = new_mode
            self.grouping_mode = new_mode
            
            self.logger.info(f"Изменен режим группировки: {self.grouping_mode}")
            
            # Очищаем кэш групп при изменении режима
            self._group_cache.clear()
            
            self._update_performance_indicator("📂 Группировка...")
            self._populate_parameters_tree()
            self._update_performance_indicator("⚡ Готов")
            
        except Exception as e:
            self.logger.error(f"Ошибка изменения группировки: {e}")
            self._update_performance_indicator("❌ Ошибка")

    def _on_all_double_click(self, event):
        """ИСПРАВЛЕННЫЙ двойной клик по дереву всех параметров"""
        try:
            selection = self.tree_all.selection()
            if selection:
                item = selection[0]
                if self._is_parameter_item(item):
                    param_data = self._get_param_from_tree_item(item)
                    if param_data:
                        if self._add_param_to_selected(param_data):
                            self._populate_selected_tree()
                            self.logger.debug(f"Добавлен параметр: {param_data.get('signal_code', 'Unknown')}")
        except Exception as e:
            self.logger.error(f"Ошибка двойного клика: {e}")

    def _on_all_enter_key(self, event):
        """НОВЫЙ МЕТОД: Обработка клавиши Enter в дереве всех параметров"""
        self._on_all_double_click(event)

    def _on_selected_enter_key(self, event):
        """НОВЫЙ МЕТОД: Обработка клавиши Enter в дереве выбранных параметров"""
        self._on_selected_double_click(event)

    def _on_all_right_click(self, event):
        """ИСПРАВЛЕННЫЙ правый клик по дереву всех параметров"""
        try:
            item = self.tree_all.identify_row(event.y)
            if item:
                self.tree_all.selection_set(item)
                
                context_menu = tk.Menu(self, tearoff=0)
                
                if self._is_parameter_item(item):
                    context_menu.add_command(label="➤ Добавить в выбранные", command=self._add_selected)
                    context_menu.add_command(label="ℹ️ Показать детали", command=self._show_parameter_details)
                else:
                    context_menu.add_command(label="📂 Развернуть группу", command=lambda: self.tree_all.item(item, open=True))
                    context_menu.add_command(label="📁 Свернуть группу", command=lambda: self.tree_all.item(item, open=False))
                    context_menu.add_separator()
                    context_menu.add_command(label="➤➤ Добавить всю группу", command=lambda: self._add_group_to_selected(item))
                
                context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.logger.error(f"Ошибка контекстного меню: {e}")

    def _on_all_tree_select(self, event):
        """ОПТИМИЗИРОВАННЫЙ выбор элемента в дереве всех параметров"""
        try:
            selection = self.tree_all.selection()
            if selection:
                item = selection[0]
                if not self._is_parameter_item(item):
                    children_count = len(self.tree_all.get_children(item))
                    group_name = self.tree_all.item(item, 'text')
                    self._update_performance_indicator(f"📂 {group_name} ({children_count})")
                else:
                    param_data = self._get_param_from_tree_item(item)
                    if param_data:
                        signal_code = param_data.get('signal_code', 'Unknown')
                        self._update_performance_indicator(f"🔢 {signal_code}")
        except Exception as e:
            self.logger.error(f"Ошибка выбора в дереве: {e}")

    def _on_selected_double_click(self, event):
        """ИСПРАВЛЕННЫЙ двойной клик по дереву выбранных параметров"""
        try:
            self._remove_selected()
        except Exception as e:
            self.logger.error(f"Ошибка двойного клика по выбранным: {e}")

    def _on_selected_right_click(self, event):
        """ИСПРАВЛЕННЫЙ правый клик по дереву выбранных параметров"""
        try:
            item = self.tree_selected.identify_row(event.y)
            if item:
                self.tree_selected.selection_set(item)
                
                context_menu = tk.Menu(self, tearoff=0)
                context_menu.add_command(label="⬅ Удалить из выбранных", command=self._remove_selected)
                context_menu.add_command(label="ℹ️ Показать детали", command=self._show_selected_details)
                context_menu.add_separator()
                context_menu.add_command(label="⬆ Переместить вверх", command=self._move_selected_up)
                context_menu.add_command(label="⬇ Переместить вниз", command=self._move_selected_down)
                context_menu.add_separator()
                context_menu.add_command(label="🗑 Очистить все", command=self._clear_all_selected)
                
                context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.logger.error(f"Ошибка контекстного меню выбранных: {e}")

    def _on_delete_selected(self, event):
        """ИСПРАВЛЕННОЕ удаление выбранных параметров по клавише Delete"""
        try:
            self._remove_selected()
        except Exception as e:
            self.logger.error(f"Ошибка удаления по Delete: {e}")

    # === МЕТОДЫ УПРАВЛЕНИЯ ДАННЫМИ ===

    def update_parameters(self, parameters: List[Dict[str, Any]]):
        """ИСПРАВЛЕННОЕ И ОПТИМИЗИРОВАННОЕ обновление списка всех параметров"""
        try:
            self.logger.info(f"📊 update_parameters вызван с {len(parameters)} параметрами")
            
            if not parameters:
                self.logger.warning("⚠️ Получен пустой список параметров!")
                self._clear_all_data()
                return
            
            # Диагностика первого параметра
            if parameters:
                first_param = parameters[0]
                self.logger.debug(f"📋 Первый параметр: {first_param}")
            
            # Очищаем кэш при обновлении данных
            self._clear_cache()
            
            self._update_performance_indicator("💾 Загрузка...")
            
            self.all_parameters = parameters.copy()
            self.filtered_parameters = parameters.copy()
            
            self.logger.info(f"💾 Данные сохранены: all={len(self.all_parameters)}, filtered={len(self.filtered_parameters)}")
            
            # Проверяем tree_all
            if not self.tree_all:
                self.logger.error("❌ tree_all не инициализировано!")
                return
            
            self._populate_parameters_tree()
            self._update_counters()
            
            # Проверяем результат
            tree_items = len(self.tree_all.get_children())
            self.logger.info(f"🌳 Элементов в дереве после заполнения: {tree_items}")
            
            self._update_performance_indicator("⚡ Готов")
            self.logger.info(f"✅ update_parameters завершен успешно: {len(parameters)} элементов")

        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления параметров: {e}")
            self._update_performance_indicator("❌ Ошибка")
            import traceback
            traceback.print_exc()

    def _populate_parameters_tree(self):
        """ОПТИМИЗИРОВАННОЕ заполнение дерева параметров с кэшированием"""
        try:
            # Очищаем дерево
            for item in self.tree_all.get_children():
                self.tree_all.delete(item)

            if not self.filtered_parameters:
                self.logger.warning("Нет отфильтрованных параметров для отображения")
                return

            # Используем кэш групп для оптимизации
            cache_key = f"{self.grouping_mode}_{len(self.filtered_parameters)}_{hash(str(sorted([p.get('signal_code', '') for p in self.filtered_parameters[:10]])))}"
            
            if cache_key in self._group_cache:
                groups = self._group_cache[cache_key]
            else:
                groups = self._group_parameters_by_mode()
                if len(self._group_cache) < 20:  # Ограничиваем размер кэша
                    self._group_cache[cache_key] = groups

            self.logger.debug(f"Группировка параметров ({self.grouping_mode}): {[(k, len(v)) for k, v in groups.items()]}")

            # Добавляем группы и параметры
            for group_name, group_params in sorted(groups.items()):
                if not group_params and not self.show_empty_groups:
                    continue
                    
                # Создаем группу с улучшенным отображением
                group_display = f"{group_name} ({len(group_params)} параметров)"
                group_id = self.tree_all.insert(
                    "", "end", 
                    text=group_display, 
                    values=("", "", "", ""),
                    tags=('group',)
                )
                
                # Добавляем параметры в группу
                for param in sorted(group_params, key=lambda x: x.get('signal_code', '')):
                    description = param.get('description', '')
                    if len(description) > 45:  # Оптимизируем длину
                        description = description[:45] + "..."
                    
                    self.tree_all.insert(
                        group_id, "end",
                        text="",
                        values=(
                            param.get('signal_code', ''),
                            description,
                            param.get('line', ''),
                            param.get('wagon', '')
                        ),
                        tags=('parameter',)
                    )
            
            # ОПТИМИЗАЦИЯ: Умное раскрытие групп
            self._smart_expand_groups()
                
            tree_items = len(self.tree_all.get_children())
            self.logger.debug(f"✅ Дерево заполнено: {tree_items} групп, {len(self.filtered_parameters)} параметров")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка заполнения дерева параметров: {e}")
            import traceback
            traceback.print_exc()

    def _smart_expand_groups(self):
        """НОВЫЙ МЕТОД: Умное раскрытие групп"""
        try:
            total_groups = len(self.tree_all.get_children())
            
            for item in self.tree_all.get_children():
                children_count = len(self.tree_all.get_children(item))
                
                # Раскрываем группы с небольшим количеством элементов
                # или если общее количество групп невелико
                if children_count <= 15 or (total_groups <= 3 and children_count <= 50):
                    self.tree_all.item(item, open=True)
                else:
                    self.tree_all.item(item, open=False)
                    
        except Exception as e:
            self.logger.error(f"Ошибка умного раскрытия групп: {e}")

    def _group_parameters_by_mode(self) -> Dict[str, List[Dict[str, Any]]]:
        """ОПТИМИЗИРОВАННАЯ группировка параметров с использованием defaultdict"""
        groups = defaultdict(list)
        
        for param in self.filtered_parameters:
            if self.grouping_mode == 'signal_type':
                signal_code = param.get('signal_code', '')
                if signal_code:
                    signal_type = signal_code[0] if signal_code else 'Unknown'
                    group_key = f"Тип {signal_type}"
                else:
                    group_key = "Неизвестный тип"
                    
            elif self.grouping_mode == 'line':
                line = param.get('line', '')
                group_key = f"Линия {line}" if line else "Без линии"
                
            elif self.grouping_mode == 'wagon':
                wagon = param.get('wagon', '')
                group_key = f"Вагон {wagon}" if wagon else "Без вагона"
                
            elif self.grouping_mode == 'component':
                signal_code = param.get('signal_code', '')
                component = self._extract_component_from_signal(signal_code)
                group_key = f"Компонент {component}" if component else "Неизвестный компонент"
                
            else:
                group_key = "Все параметры"
            
            groups[group_key].append(param)
        
        return dict(groups)

    def _extract_component_from_signal(self, signal_code: str) -> str:
        """ОПТИМИЗИРОВАННОЕ извлечение компонента из кода сигнала"""
        try:
            if not signal_code:
                return "Unknown"
            
            # Кэшируем результаты извлечения компонентов
            if not hasattr(self, '_component_cache'):
                self._component_cache = {}
                
            if signal_code in self._component_cache:
                return self._component_cache[signal_code]
            
            # Паттерны для извлечения компонента
            patterns = [
                r'S_([A-Z]+)_',  # S_I_AKB_1 -> I
                r'([A-Z]+)_',    # AKB_VOLTAGE -> AKB
                r'^([A-Z]+)',    # TEMP123 -> TEMP
            ]
            
            result = "Unknown"
            for pattern in patterns:
                match = re.search(pattern, signal_code)
                if match:
                    result = match.group(1)
                    break
            
            if result == "Unknown":
                # Fallback - первые 3 символа
                result = signal_code[:3] if len(signal_code) >= 3 else signal_code
            
            # Кэшируем результат
            if len(self._component_cache) < 1000:
                self._component_cache[signal_code] = result
                
            return result
            
        except Exception:
            return "Unknown"

    def _filter_parameters_by_search(self, search_text: str):
        """ОПТИМИЗИРОВАННАЯ фильтрация параметров по поисковому запросу"""
        try:
            if not search_text:
                self.filtered_parameters = self.all_parameters.copy()
                return
                
            self.filtered_parameters = []
            search_lower = search_text.lower()
            
            # Оптимизация: предварительная компиляция регулярного выражения для сложного поиска
            if len(search_text) > 2 and any(c in search_text for c in ['*', '?', '+']):
                try:
                    search_pattern = re.compile(search_text.replace('*', '.*').replace('?', '.'), re.IGNORECASE)
                    use_regex = True
                except re.error:
                    use_regex = False
            else:
                use_regex = False
            
            for param in self.all_parameters:
                # Поиск по различным полям
                searchable_fields = [
                    param.get('signal_code', ''),
                    param.get('description', ''),
                    param.get('line', ''),
                    param.get('wagon', ''),
                ]
                
                searchable_text = ' '.join(str(field) for field in searchable_fields).lower()
                
                if use_regex:
                    if search_pattern.search(searchable_text):
                        self.filtered_parameters.append(param)
                else:
                    if search_lower in searchable_text:
                        self.filtered_parameters.append(param)
            
        except Exception as e:
            self.logger.error(f"Ошибка фильтрации по поиску: {e}")
            # В случае ошибки показываем все параметры
            self.filtered_parameters = self.all_parameters.copy()

    def _clear_search(self):
        """ИСПРАВЛЕННАЯ очистка поискового запроса"""
        try:
            self.search_var.set("")
            self.search_entry.focus_set()  # Возвращаем фокус в поле поиска
        except Exception as e:
            self.logger.error(f"Ошибка очистки поиска: {e}")

    # === МЕТОДЫ УПРАВЛЕНИЯ ВЫБОРОМ ===

    def _add_selected(self):
        """ОПТИМИЗИРОВАННОЕ добавление выбранных параметров"""
        try:
            selection = self.tree_all.selection()
            if not selection:
                self.logger.warning("Выберите параметры для добавления")
                return
                
            added_count = 0
            
            for item in selection:
                if self._is_parameter_item(item):
                    param_data = self._get_param_from_tree_item(item)
                    if param_data and self._add_param_to_selected(param_data):
                        added_count += 1
            
            if added_count > 0:
                self._populate_selected_tree()
                self.logger.info(f"Добавлено {added_count} параметров к выбранным")
            else:
                self.logger.warning("Параметры уже добавлены или выберите корректные элементы")
                
        except Exception as e:
            self.logger.error(f"Ошибка добавления параметров: {e}")

    def _add_group_to_selected(self, group_item):
        """НОВЫЙ МЕТОД: Добавление всей группы в выбранные"""
        try:
            added_count = 0
            
            for child_item in self.tree_all.get_children(group_item):
                if self._is_parameter_item(child_item):
                    param_data = self._get_param_from_tree_item(child_item)
                    if param_data and self._add_param_to_selected(param_data):
                        added_count += 1
            
            if added_count > 0:
                self._populate_selected_tree()
                group_name = self.tree_all.item(group_item, 'text')
                self.logger.info(f"Добавлена группа '{group_name}': {added_count} параметров")
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления группы: {e}")

    def _add_param_to_selected(self, param_data: Dict[str, Any]) -> bool:
        """ОПТИМИЗИРОВАННОЕ добавление одного параметра к выбранным"""
        try:
            signal_code = param_data.get('signal_code', '')
            
            # Оптимизация: используем set для быстрой проверки дубликатов
            if not hasattr(self, '_selected_codes_set'):
                self._selected_codes_set = set()
                
            if signal_code in self._selected_codes_set:
                return False
            
            self.selected_parameters.append(param_data)
            self._selected_codes_set.add(signal_code)
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления параметра: {e}")
            return False

    def _remove_selected(self):
        """ОПТИМИЗИРОВАННОЕ удаление выбранных параметров"""
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
                    
                    # Обновляем set выбранных кодов
                    if hasattr(self, '_selected_codes_set'):
                        signal_code = removed_param.get('signal_code', '')
                        self._selected_codes_set.discard(signal_code)
                    
                    removed_count += 1
                    self.logger.debug(f"Удален параметр: {removed_param.get('signal_code', 'Unknown')}")
            
            if removed_count > 0:
                self._populate_selected_tree()
                self.logger.info(f"Удалено {removed_count} параметров")
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления выбранных параметров: {e}")

    def _clear_all_selected(self):
        """ОПТИМИЗИРОВАННАЯ очистка всех выбранных параметров"""
        try:
            if not self.selected_parameters:
                self.logger.info("Нет параметров для очистки")
                return
                
            count = len(self.selected_parameters)
            self.selected_parameters.clear()
            
            # Очищаем set выбранных кодов
            if hasattr(self, '_selected_codes_set'):
                self._selected_codes_set.clear()
                
            self._populate_selected_tree()
            self.logger.info(f"Очищено {count} параметров")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки параметров: {e}")

    def _populate_selected_tree(self):
        """ОПТИМИЗИРОВАННОЕ заполнение дерева выбранных параметров"""
        try:
            # Очищаем дерево
            for item in self.tree_selected.get_children():
                self.tree_selected.delete(item)
            
            # Добавляем выбранные параметры
            for idx, param in enumerate(self.selected_parameters, 1):
                description = param.get('description', '')
                if len(description) > 45:  # Оптимизируем длину
                    description = description[:45] + "..."
                
                self.tree_selected.insert(
                    "", "end",
                    text=str(idx),
                    values=(
                        param.get('signal_code', ''),
                        description,
                        param.get('line', '')
                    )
                )
            
            self._update_counters()
            self._notify_selection_changed()
            
        except Exception as e:
            self.logger.error(f"Ошибка заполнения дерева выбранных: {e}")

    def _move_selected_up(self):
        """ИСПРАВЛЕННОЕ перемещение выбранного параметра вверх"""
        try:
            selection = self.tree_selected.selection()
            if not selection:
                return
            
            index = self.tree_selected.index(selection[0])
            if index > 0:
                # Меняем местами в списке
                self.selected_parameters[index], self.selected_parameters[index-1] = \
                    self.selected_parameters[index-1], self.selected_parameters[index]
                
                self._populate_selected_tree()
                
                # Восстанавливаем выбор
                new_item = self.tree_selected.get_children()[index-1]
                self.tree_selected.selection_set(new_item)
                self.tree_selected.focus(new_item)
                
        except Exception as e:
            self.logger.error(f"Ошибка перемещения вверх: {e}")

    def _move_selected_down(self):
        """ИСПРАВЛЕННОЕ перемещение выбранного параметра вниз"""
        try:
            selection = self.tree_selected.selection()
            if not selection:
                return
            
            index = self.tree_selected.index(selection[0])
            if index < len(self.selected_parameters) - 1:
                # Меняем местами в списке
                self.selected_parameters[index], self.selected_parameters[index+1] = \
                    self.selected_parameters[index+1], self.selected_parameters[index]
                
                self._populate_selected_tree()
                
                # Восстанавливаем выбор
                new_item = self.tree_selected.get_children()[index+1]
                self.tree_selected.selection_set(new_item)
                self.tree_selected.focus(new_item)
                
        except Exception as e:
            self.logger.error(f"Ошибка перемещения вниз: {e}")

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def _is_parameter_item(self, item) -> bool:
        """НОВЫЙ МЕТОД: Проверка, является ли элемент параметром"""
        try:
            tags = self.tree_all.item(item, 'tags')
            return tags and 'parameter' in tags
        except Exception:
            return False

    def _get_param_from_tree_item(self, item) -> Optional[Dict[str, Any]]:
        """ОПТИМИЗИРОВАННОЕ получение данных параметра из элемента дерева"""
        try:
            if not self._is_parameter_item(item):
                return None
            
            values = self.tree_all.item(item, 'values')
            if not values:
                return None
            
            signal_code = values[0]
            
            # Оптимизация: используем словарь для быстрого поиска
            if not hasattr(self, '_params_dict'):
                self._params_dict = {p.get('signal_code', ''): p for p in self.filtered_parameters}
            
            return self._params_dict.get(signal_code)
            
        except Exception as e:
            self.logger.error(f"Ошибка получения параметра из дерева: {e}")
            return None

    def _show_parameter_details(self):
        """ИСПРАВЛЕННЫЙ показ деталей выбранного параметра"""
        try:
            selection = self.tree_all.selection()
            if not selection:
                return
            
            param_data = self._get_param_from_tree_item(selection[0])
            if not param_data:
                return
            
            self._show_details_window(param_data, "Детали параметра")
            
        except Exception as e:
            self.logger.error(f"Ошибка показа деталей параметра: {e}")

    def _show_selected_details(self):
        """ИСПРАВЛЕННЫЙ показ деталей выбранного параметра из списка выбранных"""
        try:
            selection = self.tree_selected.selection()
            if not selection:
                return
            
            index = self.tree_selected.index(selection[0])
            if 0 <= index < len(self.selected_parameters):
                param_data = self.selected_parameters[index]
                self._show_details_window(param_data, "Детали выбранного параметра")
                
        except Exception as e:
            self.logger.error(f"Ошибка показа деталей выбранного: {e}")

    def _show_details_window(self, param_data: Dict[str, Any], title: str):
        """УЛУЧШЕННОЕ окно с деталями параметра"""
        try:
            details_window = tk.Toplevel(self)
            details_window.title(title)
            details_window.geometry("600x500")
            details_window.transient(self)
            details_window.grab_set()
            
            # Заголовок окна
            header_frame = ttk.Frame(details_window)
            header_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(
                header_frame,
                text=f"ℹ️ {title}",
                font=('Arial', 14, 'bold')
            ).pack()
            
            # Основная информация
            info_frame = ttk.LabelFrame(details_window, text="Основная информация", padding="10")
            info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Создаем прокручиваемый текст
            text_frame = ttk.Frame(info_frame)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 10))
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Заполняем информацией
            details_text = f"ИНФОРМАЦИЯ О ПАРАМЕТРЕ\n{'='*60}\n\n"
            
            # Основные поля
            main_fields = ['signal_code', 'description', 'line', 'wagon']
            for field in main_fields:
                if field in param_data:
                    value = param_data[field]
                    field_name = field.upper().replace('_', ' ')
                    details_text += f"{field_name:20}: {value}\n"
            
            details_text += "\n" + "="*60 + "\nВСЕ ПОЛЯ:\n" + "="*60 + "\n\n"
            
            # Все остальные поля
            for key, value in sorted(param_data.items()):
                if key not in main_fields:
                    if isinstance(value, list):
                        value_str = ', '.join(str(v) for v in value)
                    else:
                        value_str = str(value)
                    
                    field_name = key.upper().replace('_', ' ')
                    details_text += f"{field_name:20}: {value_str}\n"
            
            text_widget.insert(tk.END, details_text)
            text_widget.config(state=tk.DISABLED)
            
            # Кнопки
            button_frame = ttk.Frame(details_window)
            button_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Button(
                button_frame, 
                text="📋 Копировать", 
                command=lambda: self._copy_to_clipboard(details_text)
            ).pack(side=tk.LEFT, padx=(0, 5))
            
            ttk.Button(
                button_frame, 
                text="Закрыть", 
                command=details_window.destroy
            ).pack(side=tk.RIGHT)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания окна деталей: {e}")

    def _copy_to_clipboard(self, text: str):
        """НОВЫЙ МЕТОД: Копирование текста в буфер обмена"""
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._update_performance_indicator("📋 Скопировано")
            self.after(2000, lambda: self._update_performance_indicator("⚡ Готов"))
        except Exception as e:
            self.logger.error(f"Ошибка копирования в буфер: {e}")

    def _expand_all(self):
        """ИСПРАВЛЕННОЕ разворачивание всех групп"""
        try:
            for item in self.tree_all.get_children():
                self.tree_all.item(item, open=True)
            self._update_performance_indicator("📂 Развернуто")
            self.after(1000, lambda: self._update_performance_indicator("⚡ Готов"))
        except Exception as e:
            self.logger.error(f"Ошибка разворачивания групп: {e}")

    def _collapse_all(self):
        """ИСПРАВЛЕННОЕ сворачивание всех групп"""
        try:
            for item in self.tree_all.get_children():
                self.tree_all.item(item, open=False)
            self._update_performance_indicator("📁 Свернуто")
            self.after(1000, lambda: self._update_performance_indicator("⚡ Готов"))
        except Exception as e:
            self.logger.error(f"Ошибка сворачивания групп: {e}")

    def _update_counters(self):
        """ИСПРАВЛЕННОЕ обновление счетчиков"""
        try:
            all_count = len(self.all_parameters)
            filtered_count = len(self.filtered_parameters)
            selected_count = len(self.selected_parameters)
            
            if self.all_count_label:
                self.all_count_label.config(text=f"📊 Всего: {all_count}")
            if self.filtered_count_label:
                self.filtered_count_label.config(text=f"🔍 Отфильтровано: {filtered_count}")
            if self.selected_count_label:
                self.selected_count_label.config(text=f"✅ Выбрано: {selected_count}")
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления счетчиков: {e}")

    def _update_performance_indicator(self, message: str):
        """НОВЫЙ МЕТОД: Обновление индикатора производительности"""
        try:
            if self.performance_label:
                self.performance_label.config(text=message)
                self.update_idletasks()
        except Exception as e:
            self.logger.error(f"Ошибка обновления индикатора: {e}")

    def _notify_selection_changed(self):
        """ИСПРАВЛЕННОЕ уведомление об изменении выбора"""
        try:
            count = len(self.selected_parameters)
            if self.on_selection_changed:
                self.on_selection_changed(count)
                
            # Также уведомляем контроллер если есть
            if self.controller and hasattr(self.controller, '_on_parameter_selection_changed'):
                self.controller._on_parameter_selection_changed(count)
                
        except Exception as e:
            self.logger.error(f"Ошибка уведомления об изменении выбора: {e}")

    def _clear_cache(self):
        """НОВЫЙ МЕТОД: Очистка всех кэшей"""
        try:
            self._search_cache.clear()
            self._group_cache.clear()
            if hasattr(self, '_component_cache'):
                self._component_cache.clear()
            if hasattr(self, '_params_dict'):
                delattr(self, '_params_dict')
            if hasattr(self, '_selected_codes_set'):
                self._selected_codes_set.clear()
            self.logger.debug("Кэш очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки кэша: {e}")

    def _clear_all_data(self):
        """НОВЫЙ МЕТОД: Очистка всех данных"""
        try:
            self.all_parameters.clear()
            self.filtered_parameters.clear()
            self.selected_parameters.clear()
            self._clear_cache()
            
            # Очищаем деревья
            if self.tree_all:
                for item in self.tree_all.get_children():
                    self.tree_all.delete(item)
            
            if self.tree_selected:
                for item in self.tree_selected.get_children():
                    self.tree_selected.delete(item)
            
            self._update_counters()
            self._update_performance_indicator("🗑 Очищено")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки данных: {e}")

    # === ПУБЛИЧНЫЕ МЕТОДЫ ===

    def get_selected_parameters(self) -> List[Dict[str, Any]]:
        """Получение списка выбранных параметров"""
        return [param.copy() for param in self.selected_parameters]

    def clear_selection(self):
        """Очистка выбора"""
        self._clear_all_selected()

    def set_grouping_mode(self, mode: str):
        """Установка режима группировки"""
        if mode in ['signal_type', 'line', 'wagon', 'component']:
            self.grouping_mode = mode
            self._group_cache.clear()  # Очищаем кэш групп
            self._populate_parameters_tree()

    def update_counters(self, all_count: int, selected_count: int):
        """Обновление счетчиков (внешний вызов)"""
        try:
            if self.all_count_label:
                self.all_count_label.config(text=f"📊 Всего: {all_count}")
            if self.selected_count_label:
                self.selected_count_label.config(text=f"✅ Выбрано: {selected_count}")
        except Exception as e:
            self.logger.error(f"Ошибка внешнего обновления счетчиков: {e}")

    def set_loading_state(self, loading: bool):
        """Установка состояния загрузки"""
        try:
            state = tk.DISABLED if loading else tk.NORMAL
            
            widgets = [self.tree_all, self.tree_selected, self.search_entry, self.grouping_combo]
            for widget in widgets:
                if widget:
                    widget.config(state=state)
                    
            if loading:
                self._update_performance_indicator("⏳ Загрузка...")
            else:
                self._update_performance_indicator("⚡ Готов")
                    
        except Exception as e:
            self.logger.error(f"Ошибка установки состояния загрузки: {e}")

    def cleanup(self):
        """ИСПРАВЛЕННАЯ очистка ресурсов"""
        try:
            # Очищаем все данные
            self._clear_all_data()
            
            # Очищаем callbacks
            self.on_selection_changed = None
            
            # Очищаем ссылку на контроллер
            self.controller = None
            
            # Очищаем кэш для освобождения памяти
            self._clear_cache()
            
            # Обнуляем UI элементы
            self.tree_all = None
            self.tree_selected = None
            self.search_entry = None
            self.grouping_combo = None
            self.all_count_label = None
            self.filtered_count_label = None
            self.selected_count_label = None
            self.performance_label = None
            
            # Очищаем переменные поиска
            if hasattr(self, 'search_var'):
                self.search_var = None
                
            # Очищаем PanedWindow
            if hasattr(self, 'paned_window'):
                self.paned_window = None
            
            self.logger.info("ParameterPanel успешно очищен")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки ParameterPanel: {e}")
            # В случае ошибки все равно пытаемся очистить основные данные
            try:
                self.all_parameters.clear()
                self.selected_parameters.clear()
                self.filtered_parameters.clear()
            except:
                pass

    def __str__(self):
        return f"ParameterPanel(all={len(self.all_parameters)}, filtered={len(self.filtered_parameters)}, selected={len(self.selected_parameters)})"

    def __repr__(self):
        return self.__str__()

