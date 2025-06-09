# src/ui/components/parameter_panel.py - ИСЧЕРПЫВАЮЩЕ ПОЛНАЯ ВЕРСИЯ
"""
Панель параметров телеметрии с улучшенной группировкой и функциональностью
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Optional, Callable
import re

class ParameterPanel(ttk.Frame):
    """Панель параметров телеметрии с полной функциональностью"""

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

        # Callbacks
        self.on_selection_changed: Optional[Callable[[int], None]] = None

        # Настройки группировки
        self.grouping_mode = 'signal_type'  # 'signal_type', 'line', 'wagon', 'component'
        self.show_empty_groups = False

        self._setup_ui()
        self.logger.info("ParameterPanel инициализирован")

    def _setup_ui(self):
        """Настройка пользовательского интерфейса"""
        try:
            self.logger.info("ParameterPanel: _setup_ui вызван")

            # Настройка сетки
            self.grid_rowconfigure(2, weight=1)  # Основная область с деревьями
            self.grid_columnconfigure(0, weight=1)

            # 1. Секция поиска
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
        """Создание секции поиска"""
        try:
            self.logger.info("ParameterPanel: _create_search_section")

            search_frame = ttk.Frame(self)
            search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
            search_frame.grid_columnconfigure(1, weight=1)

            # Поиск
            ttk.Label(search_frame, text="Поиск:", font=('Arial', 9)).grid(row=0, column=0, sticky="w")

            search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 9))
            search_entry.grid(row=0, column=1, sticky="ew", padx=(5, 5))

            # Кнопка очистки поиска
            clear_btn = ttk.Button(search_frame, text="✕", width=3, command=self._clear_search)
            clear_btn.grid(row=0, column=2)

            # Настройки группировки
            grouping_frame = ttk.Frame(search_frame)
            grouping_frame.grid(row=0, column=3, sticky="e", padx=(10, 0))

            ttk.Label(grouping_frame, text="Группировка:", font=('Arial', 9)).grid(row=0, column=0, sticky="w")

            grouping_combo = ttk.Combobox(
                grouping_frame,
                values=["По типу сигнала", "По линии связи", "По вагону", "По компоненту"],
                state="readonly",
                width=15,
                font=('Arial', 9)
            )
            grouping_combo.set("По типу сигнала")
            grouping_combo.grid(row=0, column=1, padx=(5, 0))
            grouping_combo.bind('<<ComboboxSelected>>', self._on_grouping_changed)

        except Exception as e:
            self.logger.error(f"Ошибка создания секции поиска: {e}")

    def _create_counters_section(self):
        """Создание секции счетчиков"""
        try:
            self.logger.info("ParameterPanel: _create_counters_section")

            counters_frame = ttk.Frame(self)
            counters_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))

            # Счетчики
            self.all_count_label = ttk.Label(
                counters_frame, 
                text="Всего: 0", 
                font=('Arial', 9),
                foreground='gray'
            )
            self.all_count_label.grid(row=0, column=0, sticky="w")

            self.filtered_count_label = ttk.Label(
                counters_frame, 
                text="Отфильтровано: 0", 
                font=('Arial', 9),
                foreground='blue'
            )
            self.filtered_count_label.grid(row=0, column=1, sticky="w", padx=(20, 0))

            self.selected_count_label = ttk.Label(
                counters_frame, 
                text="Выбрано: 0", 
                font=('Arial', 9),
                foreground='green'
            )
            self.selected_count_label.grid(row=0, column=2, sticky="w", padx=(20, 0))

        except Exception as e:
            self.logger.error(f"Ошибка создания секции счетчиков: {e}")

    def _create_parameter_trees(self):
        """Создание деревьев параметров"""
        try:
            self.logger.info("ParameterPanel: _create_parameter_trees")

            # Основной контейнер для деревьев
            trees_frame = ttk.Frame(self)
            trees_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 5))
            trees_frame.grid_rowconfigure(0, weight=1)
            trees_frame.grid_columnconfigure(0, weight=1)
            trees_frame.grid_columnconfigure(1, weight=1)

            # Левая часть - все параметры
            self._create_all_parameters_tree(trees_frame)

            # Правая часть - выбранные параметры
            self._create_selected_parameters_tree(trees_frame)

        except Exception as e:
            self.logger.error(f"Ошибка создания деревьев параметров: {e}")

    def _create_all_parameters_tree(self, parent):
        """Создание дерева всех параметров"""
        try:
            all_frame = ttk.LabelFrame(parent, text="Все параметры", padding="5")
            all_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
            all_frame.grid_rowconfigure(0, weight=1)
            all_frame.grid_columnconfigure(0, weight=1)

            # Определяем столбцы в зависимости от режима группировки
            columns = ("signal_code", "description", "line", "wagon")
            
            self.tree_all = ttk.Treeview(
                all_frame,
                columns=columns,
                show="tree headings",
                height=15
            )

            # Настройка заголовков
            self.tree_all.heading("#0", text="Группа", anchor=tk.W)
            self.tree_all.heading("signal_code", text="Код сигнала", anchor=tk.W)
            self.tree_all.heading("description", text="Описание", anchor=tk.W)
            self.tree_all.heading("line", text="Линия", anchor=tk.W)
            self.tree_all.heading("wagon", text="Вагон", anchor=tk.W)

            # Настройка ширины столбцов
            self.tree_all.column("#0", width=80, minwidth=60)
            self.tree_all.column("signal_code", width=120, minwidth=100)
            self.tree_all.column("description", width=200, minwidth=150)
            self.tree_all.column("line", width=100, minwidth=80)
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

        except Exception as e:
            self.logger.error(f"Ошибка создания дерева всех параметров: {e}")

    def _create_selected_parameters_tree(self, parent):
        """Создание дерева выбранных параметров"""
        try:
            selected_frame = ttk.LabelFrame(parent, text="Выбранные параметры", padding="5")
            selected_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0))
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
            self.tree_selected.heading("signal_code", text="Код сигнала", anchor=tk.W)
            self.tree_selected.heading("description", text="Описание", anchor=tk.W)
            self.tree_selected.heading("line", text="Линия", anchor=tk.W)

            # Настройка ширины столбцов
            self.tree_selected.column("#0", width=30, minwidth=30)
            self.tree_selected.column("signal_code", width=120, minwidth=100)
            self.tree_selected.column("description", width=200, minwidth=150)
            self.tree_selected.column("line", width=100, minwidth=80)

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

        except Exception as e:
            self.logger.error(f"Ошибка создания дерева выбранных параметров: {e}")

    def _create_control_buttons(self):
        """Создание кнопок управления"""
        try:
            self.logger.info("ParameterPanel: _create_control_buttons")

            buttons_frame = ttk.Frame(self)
            buttons_frame.grid(row=3, column=0, sticky="ew", pady=(5, 0))

            # Левая группа кнопок
            left_buttons = ttk.Frame(buttons_frame)
            left_buttons.pack(side=tk.LEFT)

            ttk.Button(left_buttons, text="→ Добавить", command=self._add_selected).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(left_buttons, text="← Удалить", command=self._remove_selected).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(left_buttons, text="Очистить все", command=self._clear_all_selected).pack(side=tk.LEFT, padx=(0, 5))

            # Правая группа кнопок
            right_buttons = ttk.Frame(buttons_frame)
            right_buttons.pack(side=tk.RIGHT)

            ttk.Button(right_buttons, text="Развернуть все", command=self._expand_all).pack(side=tk.RIGHT, padx=(5, 0))
            ttk.Button(right_buttons, text="Свернуть все", command=self._collapse_all).pack(side=tk.RIGHT, padx=(5, 0))

        except Exception as e:
            self.logger.error(f"Ошибка создания кнопок управления: {e}")

    # === ОБРАБОТЧИКИ СОБЫТИЙ ===

    def _on_search_changed(self, *args):
        """Обработка изменения поискового запроса"""
        try:
            search_text = self.search_var.get().strip().lower()
            self._filter_parameters_by_search(search_text)
        except Exception as e:
            self.logger.error(f"Ошибка поиска: {e}")

    def _on_grouping_changed(self, event):
        """Обработка изменения режима группировки"""
        try:
            combo = event.widget
            selection = combo.get()
            
            grouping_map = {
                "По типу сигнала": "signal_type",
                "По линии связи": "line",
                "По вагону": "wagon",
                "По компоненту": "component"
            }
            
            self.grouping_mode = grouping_map.get(selection, "signal_type")
            self.logger.info(f"Изменен режим группировки: {self.grouping_mode}")
            
            # Перестраиваем дерево
            self._populate_parameters_tree()
            
        except Exception as e:
            self.logger.error(f"Ошибка изменения группировки: {e}")

    def _on_all_double_click(self, event):
        """Двойной клик по дереву всех параметров"""
        try:
            selection = self.tree_all.selection()
            if selection:
                item = selection[0]
                # Проверяем, что это параметр, а не группа
                if self.tree_all.item(item, 'tags') and 'parameter' in self.tree_all.item(item, 'tags'):
                    param_data = self._get_param_from_tree_item(item)
                    if param_data:
                        self._add_param_to_selected(param_data)
        except Exception as e:
            self.logger.error(f"Ошибка двойного клика: {e}")

    def _on_all_right_click(self, event):
        """Правый клик по дереву всех параметров"""
        try:
            item = self.tree_all.identify_row(event.y)
            if item:
                self.tree_all.selection_set(item)
                
                # Создаем контекстное меню
                context_menu = tk.Menu(self, tearoff=0)
                
                if self.tree_all.item(item, 'tags') and 'parameter' in self.tree_all.item(item, 'tags'):
                    context_menu.add_command(label="Добавить в выбранные", command=self._add_selected)
                    context_menu.add_command(label="Показать детали", command=self._show_parameter_details)
                else:
                    context_menu.add_command(label="Развернуть группу", command=lambda: self.tree_all.item(item, open=True))
                    context_menu.add_command(label="Свернуть группу", command=lambda: self.tree_all.item(item, open=False))
                
                context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.logger.error(f"Ошибка контекстного меню: {e}")

    def _on_all_tree_select(self, event):
        """Выбор элемента в дереве всех параметров"""
        try:
            selection = self.tree_all.selection()
            if selection:
                item = selection[0]
                # Если выбрана группа, показываем информацию о ней
                if not (self.tree_all.item(item, 'tags') and 'parameter' in self.tree_all.item(item, 'tags')):
                    children_count = len(self.tree_all.get_children(item))
                    group_name = self.tree_all.item(item, 'text')
                    self.logger.debug(f"Выбрана группа '{group_name}' с {children_count} параметрами")
        except Exception as e:
            self.logger.error(f"Ошибка выбора в дереве: {e}")

    def _on_selected_double_click(self, event):
        """Двойной клик по дереву выбранных параметров"""
        try:
            self._remove_selected()
        except Exception as e:
            self.logger.error(f"Ошибка двойного клика по выбранным: {e}")

    def _on_selected_right_click(self, event):
        """Правый клик по дереву выбранных параметров"""
        try:
            item = self.tree_selected.identify_row(event.y)
            if item:
                self.tree_selected.selection_set(item)
                
                context_menu = tk.Menu(self, tearoff=0)
                context_menu.add_command(label="Удалить из выбранных", command=self._remove_selected)
                context_menu.add_command(label="Показать детали", command=self._show_selected_details)
                context_menu.add_separator()
                context_menu.add_command(label="Переместить вверх", command=self._move_selected_up)
                context_menu.add_command(label="Переместить вниз", command=self._move_selected_down)
                
                context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.logger.error(f"Ошибка контекстного меню выбранных: {e}")

    def _on_delete_selected(self, event):
        """Удаление выбранных параметров по клавише Delete"""
        try:
            self._remove_selected()
        except Exception as e:
            self.logger.error(f"Ошибка удаления по Delete: {e}")

    # === МЕТОДЫ УПРАВЛЕНИЯ ДАННЫМИ ===

    def update_parameters(self, parameters: List[Dict[str, Any]]):
        """ИСПРАВЛЕННОЕ обновление списка всех параметров"""
        try:
            self.logger.info(f"📊 update_parameters вызван с {len(parameters)} параметрами")
            
            if not parameters:
                self.logger.warning("⚠️ Получен пустой список параметров!")
                return
            
            # Диагностика первого параметра
            if parameters:
                first_param = parameters[0]
                self.logger.info(f"📋 Первый параметр: {first_param}")
                self.logger.info(f"🔑 Ключи параметра: {list(first_param.keys())}")
            
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
            
            self.logger.info(f"✅ update_parameters завершен успешно: {len(parameters)} элементов")

        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления параметров: {e}")
            import traceback
            traceback.print_exc()

    def _populate_parameters_tree(self):
        """ИСПРАВЛЕННОЕ заполнение дерева параметров с улучшенной группировкой"""
        try:
            # Очищаем дерево
            for item in self.tree_all.get_children():
                self.tree_all.delete(item)

            if not self.filtered_parameters:
                self.logger.warning("Нет отфильтрованных параметров для отображения")
                return

            # ИСПРАВЛЕНИЕ: Улучшенная группировка
            groups = self._group_parameters_by_mode()

            self.logger.info(f"Группировка параметров ({self.grouping_mode}): {[(k, len(v)) for k, v in groups.items()]}")

            # Добавляем группы и параметры
            for group_name, group_params in sorted(groups.items()):
                if not group_params and not self.show_empty_groups:
                    continue
                    
                # Создаем группу
                group_id = self.tree_all.insert(
                    "", "end", 
                    text=group_name, 
                    values=("", f"({len(group_params)} параметров)", "", ""),
                    tags=('group',)
                )
                
                # Добавляем параметры в группу
                for param in sorted(group_params, key=lambda x: x.get('signal_code', '')):
                    description = param.get('description', '')
                    if len(description) > 50:
                        description = description[:50] + "..."
                    
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
            
            # Раскрываем группы с небольшим количеством параметров
            for item in self.tree_all.get_children():
                children_count = len(self.tree_all.get_children(item))
                if children_count <= 20:  # Автоматически раскрываем группы до 20 элементов
                    self.tree_all.item(item, open=True)
                
            tree_items = len(self.tree_all.get_children())
            self.logger.info(f"✅ Дерево заполнено: {tree_items} групп, {len(self.filtered_parameters)} параметров")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка заполнения дерева параметров: {e}")
            import traceback
            traceback.print_exc()

    def _group_parameters_by_mode(self) -> Dict[str, List[Dict[str, Any]]]:
        """Группировка параметров в зависимости от режима"""
        groups = {}
        
        for param in self.filtered_parameters:
            if self.grouping_mode == 'signal_type':
                # Группировка по типу сигнала (первая буква signal_code)
                signal_code = param.get('signal_code', '')
                if signal_code:
                    signal_type = signal_code[0] if signal_code else 'Unknown'
                    group_key = f"Тип {signal_type}"
                else:
                    group_key = "Неизвестный тип"
                    
            elif self.grouping_mode == 'line':
                # Группировка по линии связи
                line = param.get('line', '')
                group_key = line if line else "Без линии"
                
            elif self.grouping_mode == 'wagon':
                # Группировка по вагону
                wagon = param.get('wagon', '')
                group_key = f"Вагон {wagon}" if wagon else "Без вагона"
                
            elif self.grouping_mode == 'component':
                # Группировка по компоненту (извлекаем из signal_code)
                signal_code = param.get('signal_code', '')
                component = self._extract_component_from_signal(signal_code)
                group_key = f"Компонент {component}" if component else "Неизвестный компонент"
                
            else:
                group_key = "Все параметры"
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(param)
        
        return groups

    def _extract_component_from_signal(self, signal_code: str) -> str:
        """Извлечение компонента из кода сигнала"""
        try:
            if not signal_code:
                return "Unknown"
            
            # Паттерны для извлечения компонента
            patterns = [
                r'S_([A-Z]+)_',  # S_I_AKB_1 -> I
                r'([A-Z]+)_',    # AKB_VOLTAGE -> AKB
                r'^([A-Z]+)',    # TEMP123 -> TEMP
            ]
            
            for pattern in patterns:
                match = re.search(pattern, signal_code)
                if match:
                    return match.group(1)
            
            # Fallback - первые 3 символа
            return signal_code[:3] if len(signal_code) >= 3 else signal_code
            
        except Exception:
            return "Unknown"

    def _filter_parameters_by_search(self, search_text: str):
        """Фильтрация параметров по поисковому запросу"""
        try:
            if not search_text:
                self.filtered_parameters = self.all_parameters.copy()
            else:
                self.filtered_parameters = []
                search_lower = search_text.lower()
                
                for param in self.all_parameters:
                    # Поиск по различным полям
                    searchable_fields = [
                        param.get('signal_code', ''),
                        param.get('description', ''),
                        param.get('line', ''),
                        param.get('wagon', ''),
                    ]
                    
                    searchable_text = ' '.join(str(field) for field in searchable_fields).lower()
                    
                    if search_lower in searchable_text:
                        self.filtered_parameters.append(param)
            
            self._populate_parameters_tree()
            self._update_counters()
            
        except Exception as e:
            self.logger.error(f"Ошибка фильтрации по поиску: {e}")

    def _clear_search(self):
        """Очистка поискового запроса"""
        try:
            self.search_var.set("")
        except Exception as e:
            self.logger.error(f"Ошибка очистки поиска: {e}")

    # === МЕТОДЫ УПРАВЛЕНИЯ ВЫБОРОМ ===

    def _add_selected(self):
        """Добавление выбранных параметров к выбранным"""
        try:
            selection = self.tree_all.selection()
            added_count = 0
            
            for item in selection:
                if self.tree_all.item(item, 'tags') and 'parameter' in self.tree_all.item(item, 'tags'):
                    param_data = self._get_param_from_tree_item(item)
                    if param_data and self._add_param_to_selected(param_data):
                        added_count += 1
            
            if added_count > 0:
                self._populate_selected_tree()
                self.logger.info(f"Добавлено {added_count} параметров к выбранным")
                
        except Exception as e:
            self.logger.error(f"Ошибка добавления параметров: {e}")

    def _add_param_to_selected(self, param_data: Dict[str, Any]) -> bool:
        """Добавление одного параметра к выбранным"""
        try:
            signal_code = param_data.get('signal_code', '')
            
            # Проверяем дубликаты
            for existing in self.selected_parameters:
                if existing.get('signal_code') == signal_code:
                    return False
            
            self.selected_parameters.append(param_data)
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления параметра: {e}")
            return False

    def _remove_selected(self):
        """Удаление выбранных параметров из списка выбранных"""
        try:
            selection = self.tree_selected.selection()
            indices_to_remove = []
            
            for item in selection:
                index = self.tree_selected.index(item)
                indices_to_remove.append(index)
            
            # Удаляем в обратном порядке
            for index in sorted(indices_to_remove, reverse=True):
                if 0 <= index < len(self.selected_parameters):
                    removed_param = self.selected_parameters.pop(index)
                    self.logger.debug(f"Удален параметр: {removed_param.get('signal_code', 'Unknown')}")
            
            self._populate_selected_tree()
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления выбранных параметров: {e}")

    def _clear_all_selected(self):
        """Очистка всех выбранных параметров"""
        try:
            self.selected_parameters.clear()
            self._populate_selected_tree()
            self.logger.info("Все выбранные параметры очищены")
        except Exception as e:
            self.logger.error(f"Ошибка очистки выбранных параметров: {e}")

    def _populate_selected_tree(self):
        """Заполнение дерева выбранных параметров"""
        try:
            # Очищаем дерево
            for item in self.tree_selected.get_children():
                self.tree_selected.delete(item)
            
            # Добавляем выбранные параметры
            for idx, param in enumerate(self.selected_parameters, 1):
                description = param.get('description', '')
                if len(description) > 50:
                    description = description[:50] + "..."
                
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
        """Перемещение выбранного параметра вверх"""
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
                
        except Exception as e:
            self.logger.error(f"Ошибка перемещения вверх: {e}")

    def _move_selected_down(self):
        """Перемещение выбранного параметра вниз"""
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
                
        except Exception as e:
            self.logger.error(f"Ошибка перемещения вниз: {e}")

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def _get_param_from_tree_item(self, item) -> Optional[Dict[str, Any]]:
        """Получение данных параметра из элемента дерева"""
        try:
            if not (self.tree_all.item(item, 'tags') and 'parameter' in self.tree_all.item(item, 'tags')):
                return None
            
            values = self.tree_all.item(item, 'values')
            if not values:
                return None
            
            signal_code = values[0]
            
            # Поиск в отфильтрованных параметрах
            for param in self.filtered_parameters:
                if param.get('signal_code') == signal_code:
                    return param
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения параметра из дерева: {e}")
            return None

    def _show_parameter_details(self):
        """Показ деталей выбранного параметра"""
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
        """Показ деталей выбранного параметра из списка выбранных"""
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
        """Показ окна с деталями параметра"""
        try:
            details_window = tk.Toplevel(self)
            details_window.title(title)
            details_window.geometry("500x400")
            details_window.transient(self)
            details_window.grab_set()
            
            # Создаем прокручиваемый текст
            text_frame = ttk.Frame(details_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 10))
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Заполняем информацией
            details_text = f"ИНФОРМАЦИЯ О ПАРАМЕТРЕ\n{'='*50}\n\n"
            
            for key, value in param_data.items():
                if isinstance(value, list):
                    value_str = ', '.join(str(v) for v in value)
                else:
                    value_str = str(value)
                
                details_text += f"{key.upper().replace('_', ' ')}: {value_str}\n"
            
            text_widget.insert(tk.END, details_text)
            text_widget.config(state=tk.DISABLED)
            
            # Кнопка закрытия
            ttk.Button(details_window, text="Закрыть", command=details_window.destroy).pack(pady=5)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания окна деталей: {e}")

    def _expand_all(self):
        """Развернуть все группы"""
        try:
            for item in self.tree_all.get_children():
                self.tree_all.item(item, open=True)
        except Exception as e:
            self.logger.error(f"Ошибка разворачивания групп: {e}")

    def _collapse_all(self):
        """Свернуть все группы"""
        try:
            for item in self.tree_all.get_children():
                self.tree_all.item(item, open=False)
        except Exception as e:
            self.logger.error(f"Ошибка сворачивания групп: {e}")

    def _update_counters(self):
        """Обновление счетчиков"""
        try:
            all_count = len(self.all_parameters)
            filtered_count = len(self.filtered_parameters)
            selected_count = len(self.selected_parameters)
            
            if self.all_count_label:
                self.all_count_label.config(text=f"Всего: {all_count}")
            if self.filtered_count_label:
                self.filtered_count_label.config(text=f"Отфильтровано: {filtered_count}")
            if self.selected_count_label:
                self.selected_count_label.config(text=f"Выбрано: {selected_count}")
                
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
        self._clear_all_selected()

    def set_grouping_mode(self, mode: str):
        """Установка режима группировки"""
        if mode in ['signal_type', 'line', 'wagon', 'component']:
            self.grouping_mode = mode
            self._populate_parameters_tree()

    def update_counters(self, all_count: int, selected_count: int):
        """Обновление счетчиков (внешний вызов)"""
        try:
            if self.all_count_label:
                self.all_count_label.config(text=f"Всего: {all_count}")
            if self.selected_count_label:
                self.selected_count_label.config(text=f"Выбрано: {selected_count}")
        except Exception as e:
            self.logger.error(f"Ошибка внешнего обновления счетчиков: {e}")

    def set_loading_state(self, loading: bool):
        """Установка состояния загрузки"""
        try:
            state = tk.DISABLED if loading else tk.NORMAL
            
            widgets = [self.tree_all, self.tree_selected]
            for widget in widgets:
                if widget:
                    widget.config(state=state)
                    
        except Exception as e:
            self.logger.error(f"Ошибка установки состояния загрузки: {e}")

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

    def __str__(self):
        return f"ParameterPanel(all={len(self.all_parameters)}, filtered={len(self.filtered_parameters)}, selected={len(self.selected_parameters)})"

    def __repr__(self):
        return self.__str__()
