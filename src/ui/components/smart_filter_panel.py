"""
Революционно компактная панель фильтров с вкладками для 11-вагонного состава
ИСПРАВЛЕННАЯ ВЕРСИЯ с динамическим маппингом вагонов
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class FilterState:
    """Централизованное состояние всех фильтров"""
    signal_types: set = field(default_factory=set)
    wagons: set = field(default_factory=set)
    lines: set = field(default_factory=set)
    criticality: set = field(default_factory=set)
    systems: set = field(default_factory=set)
    changed_only: bool = False
    diagnostic_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_types': list(self.signal_types),
            'wagons': list(self.wagons),
            'lines': list(self.lines),
            'criticality': list(self.criticality),
            'systems': list(self.systems),
            'changed_only': self.changed_only,
            'diagnostic_mode': self.diagnostic_mode
        }

class FilterObserver:
    """Реактивная система обновлений фильтров"""
    def __init__(self):
        self._subscribers: List[Callable] = []
    
    def subscribe(self, callback: Callable):
        self._subscribers.append(callback)
    
    def notify(self, state: FilterState):
        for callback in self._subscribers:
            try:
                callback(state)
            except Exception as e:
                logging.error(f"Ошибка в callback фильтра: {e}")

class SmartFilterPanel(ttk.Frame):
    """ИСПРАВЛЕННАЯ революционно компактная панель фильтров с вкладками"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Реактивная система
        self.state = FilterState()
        self.observer = FilterObserver()
        
        # UI состояние
        self.is_updating = False
        
        # ИСПРАВЛЕНО: Инициализируем диагностические переменные
        self.diag_vars = {}
        
        # Данные для фильтрации
        self.all_signal_types = []
        self.all_lines = []
        
        # НОВОЕ: Динамический маппинг вагонов
        self.leading_wagon = 1  # По умолчанию
        self.wagon_mapping = {}  # Сквозная → Реальная
        self.reverse_wagon_mapping = {}  # Реальная → Сквозная
        self.real_wagons_in_data = set()  # Реальные номера из данных
        self._wagon_ui_needs_update = False  # Флаг для обновления UI
        
        # UI элементы
        self.stats_label = None
        self.wagon_buttons = {}
        self.wagon_vars = {}
        
        # ИСПРАВЛЕНО: Используем вкладки вместо аккордеона
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="ew")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # Создаем вкладки для разделов фильтров
        self.tabs = {}
        
        self._setup_smart_ui()
        self.logger.info("SmartFilterPanel инициализирован с вкладками и динамическим маппингом")

    def _setup_smart_ui(self):
        """Настройка революционно компактного UI с вкладками"""
        try:
            self.grid_columnconfigure(0, weight=1)
            
            # Компактный заголовок с живой статистикой
            self._create_compact_header()
            
            # Создаем вкладки с основными фильтрами
            self._create_tabs()
            
            # Горизонтальная панель быстрых действий
            self._create_quick_actions_bar()
            
            self.logger.info("Компактный UI с вкладками создан")
            
        except Exception as e:
            self.logger.error(f"Ошибка создания компактного UI: {e}")

    def _create_tabs(self):
        """Создание вкладок для разделов фильтров"""
        tab_definitions = [
            ("signals", "📊 Сигналы", self._create_signals_content),
            ("wagons", "🚃 Вагоны", self._create_wagons_content),
            ("lines", "📡 Линии", self._create_lines_content),
            ("diagnostic", "🚨 Диагностика", self._create_diagnostic_content)
        ]
        
        for tab_id, title, content_creator in tab_definitions:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=title)
            self.tabs[tab_id] = {
                'frame': frame,
                'creator': content_creator,
                'initialized': False
            }

    def _on_tab_changed(self, event):
        """ИСПРАВЛЕННАЯ обработка переключения вкладок"""
        try:
            selected_tab = event.widget.select()
            for tab_id, tab_info in self.tabs.items():
                if str(tab_info['frame']) == selected_tab:
                    if not tab_info['initialized']:
                        tab_info['creator'](tab_info['frame'])
                        tab_info['initialized'] = True
                    # При переключении на вкладку вагонов обновляем UI если нужно
                    if tab_id == 'wagons' and self._wagon_ui_needs_update:
                        self._update_wagon_ui_with_mapping()
                        self._wagon_ui_needs_update = False
                    break
        except Exception as e:
            self.logger.error(f"Ошибка переключения вкладок: {e}")

    def _create_compact_header(self):
        """Сверхкомпактный заголовок с живой статистикой"""
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        header.grid_columnconfigure(1, weight=1)
        
        # Иконка-кнопка (без функционала сворачивания для вкладок)
        self.collapse_btn = ttk.Button(
            header, 
            text="🔍", 
            width=3,
            command=self._toggle_main_section
        )
        self.collapse_btn.grid(row=0, column=0)
        
        # Живая статистика
        self.stats_label = ttk.Label(
            header, 
            text="Фильтры: 0/0", 
            font=('Arial', 8)
        )
        self.stats_label.grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        # Индикатор режима
        self.mode_label = ttk.Label(
            header, 
            text="●", 
            foreground="gray", 
            font=('Arial', 8)
        )
        self.mode_label.grid(row=0, column=2)

    def _toggle_main_section(self):
        """ИСПРАВЛЕНО: Переключение видимости вкладок"""
        try:
            if self.notebook.winfo_viewable():
                self.notebook.grid_remove()
                self.collapse_btn.config(text="🔍▼")
            else:
                self.notebook.grid(row=1, column=0, sticky="ew")
                self.collapse_btn.config(text="🔍▲")
        except Exception as e:
            self.logger.error(f"Ошибка переключения основной секции: {e}")

    def _create_signals_content(self, parent):
        """Компактный контент для типов сигналов с чекбоксами для множественного выбора"""
        signals_frame = ttk.Frame(parent)
        signals_frame.pack(fill="x", pady=2)
        
        ttk.Label(signals_frame, text="Типы:", font=('Arial', 8)).pack(anchor="w")
        
        # Словарь для хранения переменных чекбоксов
        self.signal_type_vars = {}
        
        # Категории сигналов для чекбоксов (убраны слова "сигналы" из описания)
        categories = [
            ("BY_ (Байт)", lambda s: s.startswith('BY_') or s == 'BY'),
            ("F_ (Float)", lambda s: s.startswith('F_')),
            ("S_ (S)", lambda s: s.startswith('S_') or s == 'S'),
            ("B_ (Bool)", lambda s: (s.startswith('B_') or s == 'B') and not s.startswith('Banner')),
            ("DW_ (DWord)", lambda s: s.startswith('DW_') or s == 'DW'),
            ("W_ (Word)", lambda s: s.startswith('W_') or s == 'W'),
            ("Banner", lambda s: s.startswith('Banner') or 'Banner#' in s),
            ("Другие", lambda s: not any([
                s.startswith(prefix) or s == prefix for prefix in
                ['BY_', 'BY', 'F_', 'S_', 'S', 'B_', 'B', 'DW_', 'DW', 'W_', 'W']
            ]) and not (s.startswith('Banner') or 'Banner#' in s))
        ]
        
        # Фрейм для чекбоксов
        checkbox_frame = ttk.Frame(signals_frame)
        checkbox_frame.pack(fill="x", pady=2)
        
        for text, filter_func in categories:
            var = tk.BooleanVar(value=True)
            self.signal_type_vars[text] = (var, filter_func)
            cb = ttk.Checkbutton(
                checkbox_frame,
                text=text,
                variable=var,
                command=self._on_signal_checkboxes_changed
            )
            cb.pack(side="left", padx=5, pady=1)

    def _create_wagons_content(self, parent):
        """ИСПРАВЛЕННЫЙ контент для вагонов с немедленным созданием кнопок"""
        wagons_frame = ttk.Frame(parent)
        wagons_frame.pack(fill="x", pady=2)
        
        # Динамический заголовок с информацией о составе
        if hasattr(self, 'wagon_mapping') and self.wagon_mapping:
            composition_text = f"Ведущий: {self.leading_wagon}, Состав: {'-'.join([self.wagon_mapping.get(i, str(i)) for i in range(1, 12)])}"
        else:
            composition_text = "11-вагонный состав"
            
        ttk.Label(wagons_frame, text=composition_text, font=('Arial', 7)).pack(anchor="w")
        
        # Контейнер для кнопок вагонов
        self.wagon_container = ttk.Frame(wagons_frame)
        self.wagon_container.pack(fill="x", pady=2)
        
        # ИСПРАВЛЕНИЕ: Создаем кнопки немедленно если маппинг уже есть
        if hasattr(self, 'wagon_mapping') and self.wagon_mapping and hasattr(self, 'real_wagons_in_data'):
            self._create_wagon_buttons_immediately()
        
        # Кнопки группового выбора
        group_frame = ttk.Frame(wagons_frame)
        group_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Button(group_frame, text="Все", width=6, command=self._select_all_wagons).pack(side="left", padx=1)
        ttk.Button(group_frame, text="Нет", width=6, command=self._deselect_all_wagons).pack(side="left", padx=1)
        ttk.Button(group_frame, text="Г+М", width=6, command=self._select_head_motor).pack(side="left", padx=1)

    def _create_wagon_buttons_immediately(self):
        """ИСПРАВЛЕННОЕ создание кнопок вагонов с правильными callback"""
        try:
            # Очищаем существующие кнопки
            for widget in self.wagon_container.winfo_children():
                widget.destroy()
            
            self.wagon_buttons = {}
            self.wagon_vars = {}
            
            # Создаем кнопки для каждого сквозного номера
            buttons_frame = ttk.Frame(self.wagon_container)
            buttons_frame.pack(fill="x", pady=2)
            
            for logical_num in range(1, 12):  # Сквозная нумерация 1-11
                real_wagon = self.wagon_mapping.get(logical_num, str(logical_num))
                
                # Проверяем, есть ли этот реальный вагон в данных
                wagon_exists = real_wagon in self.real_wagons_in_data
                
                # ИСПРАВЛЕНО: Правильная инициализация состояния
                var = tk.BooleanVar(value=wagon_exists and real_wagon in self.state.wagons)
                self.wagon_vars[logical_num] = var
                
                # ИСПРАВЛЕНО: Создаем отдельную функцию для каждой кнопки
                def create_toggle_function(logical_number):
                    return lambda: self._toggle_wagon_with_mapping(logical_number)
                
                # Кнопка с реальным номером вагона
                btn = ttk.Checkbutton(
                    buttons_frame,
                    text=real_wagon,  # Показываем реальный номер
                    variable=var,
                    command=create_toggle_function(logical_num),
                    width=4,
                    state="normal" if wagon_exists else "disabled"
                )
                btn.pack(side="left", padx=1)
                self.wagon_buttons[logical_num] = btn
                
            self.logger.info(f"✅ Кнопки вагонов созданы с правильными callback: {list(self.wagon_mapping.values())}")
            
        except Exception as e:
            self.logger.error(f"Ошибка создания кнопок вагонов: {e}")

    def _create_lines_content(self, parent):
        """Компактный контент для линий с автодополнением"""
        lines_frame = ttk.Frame(parent)
        lines_frame.pack(fill="x", pady=2)
        
        ttk.Label(lines_frame, text="Поиск:", font=('Arial', 8)).pack(side="left")
        
        self.lines_entry = ttk.Entry(lines_frame, width=20, font=('Arial', 8))
        self.lines_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.lines_entry.bind('<KeyRelease>', self._on_lines_search)
        
        # Мини-список с результатами (максимум 3 строки)
        self.lines_listbox = tk.Listbox(lines_frame, height=3, font=('Arial', 8))
        self.lines_listbox.pack(fill="x", pady=(2, 0))
        self.lines_listbox.bind('<Double-Button-1>', self._on_line_selected)

    def _create_diagnostic_content(self, parent):
        """ИСПРАВЛЕННОЕ создание без проблемных опций"""
        diag_frame = ttk.Frame(parent)
        diag_frame.pack(fill="x", pady=2)
        
        self.diag_vars = {}
        
        # ИСПРАВЛЕНО: Убираем font из LabelFrame
        crit_frame = ttk.LabelFrame(diag_frame, text="Критичность")
        crit_frame.pack(fill="x", pady=2)
        
        critical_options = [
            ("🚨 Аварийные", "emergency"),
            ("⚠️ Безопасность", "safety"),
            ("⚡ Энергосистема", "power_critical"),
            ("🛑 Тормоза", "brake_critical")
        ]
        
        for text, key in critical_options:
            var = tk.BooleanVar()
            self.diag_vars[key] = var
            ttk.Checkbutton(crit_frame, text=text, variable=var, 
                        command=self._on_diagnostic_changed).pack(side="left", padx=2)
        
        # Системы
        sys_frame = ttk.LabelFrame(diag_frame, text="Системы")
        sys_frame.pack(fill="x", pady=2)
        
        system_options = [
            ("🚂 Тяга", "traction"),
            ("🛑 Тормоза", "brakes"),
            ("🚪 Двери", "doors"),
            ("⚡ Энергия", "power"),
            ("🌡️ Климат", "climate"),
            ("📡 Связь", "communication")
        ]
        
        for text, key in system_options:
            var = tk.BooleanVar()
            self.diag_vars[f"sys_{key}"] = var
            ttk.Checkbutton(sys_frame, text=text, variable=var,
                        command=self._on_diagnostic_changed).pack(side="left", padx=2)
        
        # Функции
        func_frame = ttk.LabelFrame(diag_frame, text="Функции")
        func_frame.pack(fill="x", pady=2)
        
        function_options = [
            ("❌ Неисправности", "faults"),
            ("📊 Измерения", "measurements"),
            ("🔧 Состояния", "states"),
            ("🚨 Диагностика", "diagnostics")
        ]
        
        for text, key in function_options:
            var = tk.BooleanVar()
            self.diag_vars[f"func_{key}"] = var
            ttk.Checkbutton(func_frame, text=text, variable=var,
                        command=self._on_diagnostic_changed).pack(side="left", padx=2)

    def _create_quick_actions_bar(self):
        """Горизонтальная панель быстрых действий"""
        actions_bar = ttk.Frame(self)
        actions_bar.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        
        # Специальные режимы
        self.changed_only_var = tk.BooleanVar()
        self.changed_only_checkbox = ttk.Checkbutton(
            actions_bar,
            text="🔥 Изменяемые",
            variable=self.changed_only_var,
            command=self._on_changed_only_toggle
        )
        self.changed_only_checkbox.pack(side="left")
        
        # Разделитель
        ttk.Separator(actions_bar, orient="vertical").pack(side="left", fill="y", padx=5)
        
        # Быстрые пресеты
        presets = [
            ("Все", self._preset_all),
            ("Тяга", self._preset_traction),
            ("Тормоза", self._preset_brakes),
            ("Сброс", self._preset_reset)
        ]
        
        for text, command in presets:
            ttk.Button(
                actions_bar,
                text=text,
                width=6,
                command=command
            ).pack(side="left", padx=1)

    # === НОВЫЕ МЕТОДЫ ДИНАМИЧЕСКОГО МАППИНГА ===

    def _get_leading_wagon_from_controller(self) -> int:
        """Получение ведущего вагона из контроллера"""
        try:
            if (self.controller and 
                hasattr(self.controller, 'model') and 
                hasattr(self.controller.model, 'data_loader')):
                
                data_loader = self.controller.model.data_loader
                if hasattr(data_loader, 'get_controlling_wagon'):
                    leading_wagon = data_loader.get_controlling_wagon()
                    self.logger.info(f"🔍 Ведущий вагон из data_loader: {leading_wagon}")
                    return leading_wagon
                elif hasattr(data_loader, 'leading_wagon'):
                    leading_wagon = data_loader.leading_wagon
                    self.logger.info(f"🔍 Ведущий вагон из атрибута: {leading_wagon}")
                    return leading_wagon
                    
            self.logger.warning("⚠️ Не удалось получить ведущий вагон, используем 1")
            return 1
            
        except Exception as e:
            self.logger.error(f"Ошибка получения ведущего вагона: {e}")
            return 1

    def _create_wagon_mapping(self, leading_wagon: int):
        """ИСПРАВЛЕННОЕ создание маппинга на основе ведущего вагона из CSVDataLoader"""
        try:
            # Используем ту же логику что и в CSVDataLoader
            if leading_wagon == 1:
                self.wagon_mapping = {
                    1: "1г", 2: "11бо", 3: "2м", 4: "3нм", 5: "6м",
                    6: "8м", 7: "7нм", 8: "12м", 9: "13бо", 10: "10м", 11: "9г"
                }
                self.logger.info("Применена карта вагонов для ведущего вагона 1")
            elif leading_wagon == 9:
                self.wagon_mapping = {
                    11: "1г", 10: "11бо", 9: "2м", 8: "3нм", 7: "6м",
                    6: "8м", 5: "7нм", 4: "12м", 3: "13бо", 2: "10м", 1: "9г"
                }
                self.logger.info("Применена карта вагонов для ведущего вагона 9")
            else:
                # Fallback для других ведущих вагонов
                self.wagon_mapping = {i: str(i) for i in range(1, 12)}
                self.logger.info(f"Применена карта по умолчанию для ведущего вагона {leading_wagon}")
                
            # Создаем обратный маппинг
            self.reverse_wagon_mapping = {v: k for k, v in self.wagon_mapping.items()}
            
            self.logger.info(f"🔄 Создан маппинг для ведущего вагона {leading_wagon}")
            self.logger.info(f"📋 Маппинг: {self.wagon_mapping}")
            
        except Exception as e:
            self.logger.error(f"Ошибка создания маппинга вагонов: {e}")
            # Fallback
            self.wagon_mapping = {i: str(i) for i in range(1, 12)}
            self.reverse_wagon_mapping = {str(i): i for i in range(1, 12)}

    def _update_wagon_ui_with_mapping(self):
        """ИСПРАВЛЕННОЕ обновление UI вагонов с проверкой существования контейнера"""
        try:
            # Проверяем, существует ли контейнер
            if not hasattr(self, 'wagon_container') or not self.wagon_container.winfo_exists():
                self.logger.warning("wagon_container не существует, пропускаем обновление")
                return
            
            # Если кнопки уже созданы, просто обновляем их состояние
            if hasattr(self, 'wagon_buttons') and self.wagon_buttons:
                self._update_existing_wagon_buttons()
                return
            
            # Создаем кнопки если их нет
            self._create_wagon_buttons_immediately()
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления UI вагонов: {e}")

    def _update_existing_wagon_buttons(self):
        """ИСПРАВЛЕННОЕ обновление существующих кнопок вагонов"""
        try:
            for logical_num, var in self.wagon_vars.items():
                real_wagon = self.wagon_mapping.get(logical_num)
                if real_wagon:
                    # ИСПРАВЛЕНО: Синхронизируем с текущим состоянием фильтра
                    is_selected = real_wagon in self.state.wagons
                    var.set(is_selected)
                    
                    # Обновляем доступность кнопки
                    if logical_num in self.wagon_buttons:
                        btn = self.wagon_buttons[logical_num]
                        wagon_exists = real_wagon in self.real_wagons_in_data
                        btn.config(state="normal" if wagon_exists else "disabled")
                        
            self.logger.debug("Существующие кнопки вагонов синхронизированы с состоянием")
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления существующих кнопок: {e}")

    def _force_update_wagon_ui(self):
        """ИСПРАВЛЕННЫЙ метод: Принудительное обновление UI вагонов для вкладок"""
        try:
            # Проверяем, активна ли вкладка вагонов
            current_tab = self.notebook.select()
            wagon_tab = None
            
            for tab_id, tab_info in self.tabs.items():
                if tab_id == 'wagons':
                    wagon_tab = tab_info
                    break
            
            if wagon_tab and str(wagon_tab['frame']) == current_tab:
                # Вкладка вагонов активна, обновляем немедленно
                self._update_wagon_ui_with_mapping()
            else:
                # Вкладка не активна, помечаем для обновления
                self._wagon_ui_needs_update = True
                
            self.logger.info("UI вагонов принудительно обновлен")
            
        except Exception as e:
            self.logger.error(f"Ошибка принудительного обновления UI вагонов: {e}")

    def _toggle_wagon_with_mapping(self, logical_num: int):
        """ИСПРАВЛЕННОЕ переключение вагона с синхронизацией состояния"""
        try:
            var = self.wagon_vars[logical_num]
            real_wagon = self.wagon_mapping.get(logical_num)
            
            if not real_wagon or real_wagon not in self.real_wagons_in_data:
                self.logger.warning(f"Вагон {logical_num} -> {real_wagon} не найден в данных")
                # ИСПРАВЛЕНО: Возвращаем чекбокс в предыдущее состояние
                var.set(real_wagon in self.state.wagons)
                return
            
            # ИСПРАВЛЕНО: Синхронизируем состояние с UI
            checkbox_state = var.get()
            
            if checkbox_state:
                # Добавляем реальный номер вагона
                self.state.wagons.add(real_wagon)
                self.logger.debug(f"✅ Добавлен вагон: {logical_num} -> {real_wagon}")
            else:
                # Удаляем реальный номер вагона
                self.state.wagons.discard(real_wagon)
                self.logger.debug(f"❌ Удален вагон: {logical_num} -> {real_wagon}")
            
            # ИСПРАВЛЕНО: Обновляем статистику и уведомляем
            self._update_statistics()
            self._notify_state_changed()
            
        except Exception as e:
            self.logger.error(f"Ошибка переключения вагона {logical_num}: {e}")

    # === ОБРАБОТЧИКИ СОБЫТИЙ ===

    def _on_signal_checkboxes_changed(self):
        """Обработка изменения выбора чекбоксов сигналов"""
        try:
            selected_signal_types = set()
            for text, (var, filter_func) in self.signal_type_vars.items():
                if var.get():
                    filtered = filter(filter_func, self.all_signal_types)
                    selected_signal_types.update(filtered)
            self.state.signal_types = selected_signal_types
            self.logger.info(f"✅ Выбрано типов сигналов: {len(selected_signal_types)}")
            self._notify_state_changed()
        except Exception as e:
            self.logger.error(f"Ошибка обработки чекбоксов сигналов: {e}")

    def _on_lines_search(self, event=None):
        """Обработка поиска по линиям"""
        try:
            search_text = self.lines_entry.get().lower()
            
            # Фильтруем линии по поисковому запросу
            if search_text:
                filtered_lines = [line for line in self.all_lines if search_text in line.lower()]
            else:
                filtered_lines = self.all_lines[:10]  # Показываем первые 10
            
            # Обновляем listbox
            self.lines_listbox.delete(0, tk.END)
            for line in filtered_lines[:10]:  # Максимум 10 результатов
                self.lines_listbox.insert(tk.END, line)
                
        except Exception as e:
            self.logger.error(f"Ошибка поиска линий: {e}")

    def _on_line_selected(self, event=None):
        """Обработка выбора линии"""
        try:
            selection = self.lines_listbox.curselection()
            if selection:
                line = self.lines_listbox.get(selection[0])
                
                if line in self.state.lines:
                    self.state.lines.remove(line)
                else:
                    self.state.lines.add(line)
                
                self._notify_state_changed()
                
        except Exception as e:
            self.logger.error(f"Ошибка выбора линии: {e}")

    def _on_diagnostic_changed(self):
        """ИСПРАВЛЕННАЯ обработка диагностических фильтров"""
        try:
            # Проверяем, что diag_vars инициализирован
            if not hasattr(self, 'diag_vars') or not self.diag_vars:
                self.logger.warning("diag_vars не инициализирован")
                return
                
            # Собираем выбранные критерии
            diagnostic_criteria = {
                'criticality': [],
                'systems': [],
                'functions': []
            }
            
            for key, var in self.diag_vars.items():
                if var.get():
                    if key in ['emergency', 'safety', 'power_critical', 'brake_critical']:
                        diagnostic_criteria['criticality'].append(key)
                    elif key.startswith('sys_'):
                        diagnostic_criteria['systems'].append(key[4:])
                    elif key.startswith('func_'):
                        diagnostic_criteria['functions'].append(key[5:])
            
            # Применяем через контроллер
            if self.controller and hasattr(self.controller, 'apply_diagnostic_filters'):
                self.controller.apply_diagnostic_filters(diagnostic_criteria)
            
            self.logger.info(f"🚨 Применены диагностические фильтры: {diagnostic_criteria}")
            
        except Exception as e:
            self.logger.error(f"Ошибка диагностических фильтров: {e}")

    def _on_changed_only_toggle(self):
        """Обработка переключения режима 'только изменяемые'"""
        try:
            self.state.changed_only = self.changed_only_var.get()
            
            if self.state.changed_only:
                # Отключаем диагностический режим
                self.state.diagnostic_mode = False
                self.mode_label.config(text="🔥", foreground="red")
                
                # Применяем через контроллер
                if self.controller and hasattr(self.controller, 'apply_changed_parameters_filter'):
                    self.controller.apply_changed_parameters_filter()
            else:
                self.mode_label.config(text="●", foreground="gray")
                self._notify_state_changed()
                
        except Exception as e:
            self.logger.error(f"Ошибка переключения режима: {e}")

    # === БЫСТРЫЕ ПРЕСЕТЫ С МАППИНГОМ ===

    def _preset_all(self):
        """Пресет: выбрать все"""
        self.state.signal_types = set(self.all_signal_types)
        self.state.wagons = self.real_wagons_in_data.copy()
        self.state.lines = set(self.all_lines)
        self.signals_combo.set("Все")
        self._update_wagon_buttons()
        self._notify_state_changed()

    def _preset_traction(self):
        """ИНТЕГРАЦИЯ реального пресета тяговых систем"""
        try:
            # Реальные тяговые сигналы из анализа
            traction_signal_types = {s for s in self.all_signal_types 
                                if any(pattern in s.upper() for pattern in 
                                        ['PST_', 'INV', 'EFFORT_', 'MOTOR_', 'TRACTION_'])}
            
            # Моторные вагоны
            motor_real = set()
            for logical_num, real_wagon in self.wagon_mapping.items():
                if real_wagon in self.real_wagons_in_data and 'м' in real_wagon:
                    motor_real.add(real_wagon)
            
            self.state.signal_types = traction_signal_types
            self.state.wagons = motor_real
            
            # Обновляем UI
            self.signals_combo.set("S_ сигналы (Системные)")
            self._update_wagon_buttons()
            self._notify_state_changed()
            
            self.logger.info(f"🚂 Пресет тяговые: {len(traction_signal_types)} сигналов, {len(motor_real)} вагонов")
            
        except Exception as e:
            self.logger.error(f"Ошибка пресета тяговых систем: {e}")

    def _preset_brakes(self):
        """ИНТЕГРАЦИЯ реального пресета тормозных систем"""
        try:
            # Реальные тормозные сигналы из анализа
            brake_signal_types = {s for s in self.all_signal_types 
                                if any(pattern in s.upper() for pattern in 
                                    ['BCU_', 'BRAKE_', 'PRESSURE_', 'VALVE_', 'KNORR'])}
            
            self.state.signal_types = brake_signal_types
            self.state.wagons = self.real_wagons_in_data.copy()  # Все вагоны
            
            # Обновляем UI
            self.signals_combo.set("BY_ сигналы (Байт)")
            self._update_wagon_buttons()
            self._notify_state_changed()
            
            self.logger.info(f"🛑 Пресет тормозные: {len(brake_signal_types)} сигналов")
            
        except Exception as e:
            self.logger.error(f"Ошибка пресета тормозных систем: {e}")

    def _preset_reset(self):
        """ИСПРАВЛЕННЫЙ пресет: сброс"""
        try:
            self.state.signal_types = set(self.all_signal_types)
            self.state.wagons = self.real_wagons_in_data.copy()
            self.state.lines = set(self.all_lines)
            self.state.criticality.clear()
            self.state.systems.clear()
            
            self.signals_combo.set("Все")
            self.changed_only_var.set(False)
            for var in self.diag_vars.values():
                var.set(False)
            self._update_wagon_buttons()
            self._notify_state_changed()
            
        except Exception as e:
            self.logger.error(f"Ошибка сброса: {e}")

    # === МЕТОДЫ УПРАВЛЕНИЯ ВАГОНАМИ С МАППИНГОМ ===

    def _select_all_wagons(self):
        """ИСПРАВЛЕННЫЙ выбор всех вагонов с синхронизацией UI"""
        try:
            # Обновляем состояние фильтра
            self.state.wagons = self.real_wagons_in_data.copy()
            
            # ИСПРАВЛЕНО: Синхронизируем UI с новым состоянием
            for logical_num, var in self.wagon_vars.items():
                real_wagon = self.wagon_mapping.get(logical_num)
                is_selected = real_wagon in self.state.wagons
                var.set(is_selected)
            
            self._update_statistics()
            self._notify_state_changed()
            self.logger.info(f"✅ Выбраны все вагоны: {self.state.wagons}")
            
        except Exception as e:
            self.logger.error(f"Ошибка выбора всех вагонов: {e}")

    def _deselect_all_wagons(self):
        """ИСПРАВЛЕННАЯ отмена выбора всех вагонов с синхронизацией UI"""
        try:
            # Очищаем состояние фильтра
            self.state.wagons.clear()
            
            # ИСПРАВЛЕНО: Синхронизируем UI с новым состоянием
            for var in self.wagon_vars.values():
                var.set(False)
            
            self._update_statistics()
            self._notify_state_changed()
            self.logger.info("❌ Отменен выбор всех вагонов")
            
        except Exception as e:
            self.logger.error(f"Ошибка отмены выбора вагонов: {e}")

    def _select_head_motor(self):
        """ИСПРАВЛЕННЫЙ выбор головных и моторных вагонов с синхронизацией UI"""
        try:
            # Находим головные и моторные вагоны по реальным номерам
            head_motor_real = set()
            
            for logical_num, real_wagon in self.wagon_mapping.items():
                if real_wagon in self.real_wagons_in_data:
                    # Головные (содержат 'г') и моторные (содержат 'м')
                    if 'г' in real_wagon or 'м' in real_wagon:
                        head_motor_real.add(real_wagon)
            
            # Обновляем состояние фильтра
            self.state.wagons = head_motor_real
            
            # ИСПРАВЛЕНО: Синхронизируем UI с новым состоянием
            for logical_num, var in self.wagon_vars.items():
                real_wagon = self.wagon_mapping.get(logical_num)
                is_selected = real_wagon in head_motor_real
                var.set(is_selected)
            
            self._update_statistics()
            self._notify_state_changed()
            self.logger.info(f"🚃 Выбраны головные+моторные: {head_motor_real}")
            
        except Exception as e:
            self.logger.error(f"Ошибка выбора головных и моторных: {e}")

    def _update_wagon_buttons(self):
        """ИСПРАВЛЕННОЕ обновление состояния кнопок вагонов"""
        try:
            # ИСПРАВЛЕНО: Принудительная синхронизация всех кнопок
            for logical_num, var in self.wagon_vars.items():
                real_wagon = self.wagon_mapping.get(logical_num)
                if real_wagon:
                    is_selected = real_wagon in self.state.wagons
                    # Обновляем только если состояние изменилось
                    if var.get() != is_selected:
                        var.set(is_selected)
                        
            self.logger.debug("Состояние кнопок вагонов синхронизировано")
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления кнопок вагонов: {e}")

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def _notify_state_changed(self):
        """ИСПРАВЛЕННОЕ уведомление об изменении состояния"""
        try:
            if not self.is_updating:
                self._update_statistics()
                self.observer.notify(self.state)
                
                # ИСПРАВЛЕНО: Принудительно применяем фильтры через контроллер
                if self.controller and not self.state.changed_only:
                    filters = self.state.to_dict()
                    self.logger.info(f"🔄 Применение фильтров: {filters}")
                    
                    if hasattr(self.controller, 'apply_filters'):
                        self.controller.apply_filters(**filters)
                        self.logger.info("✅ Фильтры применены через контроллер")
                    else:
                        self.logger.error("❌ Метод apply_filters не найден в контроллере")
                        
        except Exception as e:
            self.logger.error(f"Ошибка уведомления об изменении: {e}")

    def _update_statistics(self):
        """ИСПРАВЛЕННОЕ обновление статистики с реальными номерами"""
        try:
            total_real_wagons = len(self.real_wagons_in_data)
            selected_real_wagons = len(self.state.wagons)
            
            total = len(self.all_signal_types) + len(self.all_lines) + total_real_wagons
            selected = len(self.state.signal_types) + len(self.state.lines) + selected_real_wagons
            
            stats_text = f"Фильтры: {selected}/{total}"
            if self.stats_label:
                self.stats_label.config(text=stats_text)
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления статистики: {e}")

    # === НЕДОСТАЮЩИЕ МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ ===

    def disable_changed_only_checkbox(self):
        """Отключение чекбокса 'только изменяемые'"""
        try:
            if hasattr(self, 'changed_only_var'):
                self.changed_only_var.set(False)
                # Отключаем чекбокс если есть ссылка на виджет
                if hasattr(self, 'changed_only_checkbox'):
                    self.changed_only_checkbox.config(state='disabled')
            self.logger.debug("Чекбокс 'только изменяемые' отключен")
        except Exception as e:
            self.logger.error(f"Ошибка отключения чекбокса: {e}")

    def _sync_with_time_panel(self):
        """Синхронизация с панелью времени"""
        try:
            # Получаем временной диапазон из контроллера
            if self.controller:
                time_range = self.controller.get_time_range()
                if time_range[0] and time_range[1]:
                    self.logger.debug(f"Синхронизация с временным диапазоном: {time_range}")
            self.logger.debug("Синхронизация с time_panel выполнена")
        except Exception as e:
            self.logger.error(f"Ошибка синхронизации с time_panel: {e}")

    # === ПУБЛИЧНЫЕ МЕТОДЫ ===

    def update_signal_type_checkboxes(self, signal_types: List[str]):
        """ИНТЕГРАЦИЯ реального анализа типов сигналов из предыдущего диалога"""
        try:
            self.logger.info(f"🔄 Получены типы сигналов для анализа: {len(signal_types)}")
            self.logger.info(f"📊 Типы: {signal_types[:10]}...")
            
            # КРИТИЧНО: Сохраняем все типы сигналов
            self.all_signal_types = signal_types
            self.state.signal_types = set(signal_types)
            
            # ИНТЕГРАЦИЯ: Реальный анализ из предыдущего диалога
            if signal_types:
                categories = ["Все"]
                
                # Анализируем реальные типы сигналов на основе нашего исследования
                signal_groups = {
                    'BY_ сигналы (Байт)': [],      # uint8_t
                    'F_ сигналы (Float)': [],      # float32
                    'S_ сигналы (Системные)': [],  # system status
                    'B_ сигналы (Bool)': [],       # boolean
                    'DW_ сигналы (DWord)': [],     # uint32_t
                    'W_ сигналы (Word)': [],       # uint16_t
                    'Banner сигналы': [],          # Banner#xxx
                    'Другие': []
                }
                
                # РЕАЛЬНАЯ КАТЕГОРИЗАЦИЯ на основе анализа
                for signal_type in signal_types:
                    if signal_type.startswith('BY_') or signal_type == 'BY':
                        signal_groups['BY_ сигналы (Байт)'].append(signal_type)
                    elif signal_type.startswith('F_'):
                        signal_groups['F_ сигналы (Float)'].append(signal_type)
                    elif signal_type.startswith('S_') or signal_type == 'S':
                        signal_groups['S_ сигналы (Системные)'].append(signal_type)
                    elif signal_type.startswith('B_') or signal_type == 'B':
                        signal_groups['B_ сигналы (Bool)'].append(signal_type)
                    elif signal_type.startswith('DW_') or signal_type == 'DW':
                        signal_groups['DW_ сигналы (DWord)'].append(signal_type)
                    elif signal_type.startswith('W_') or signal_type == 'W':
                        signal_groups['W_ сигналы (Word)'].append(signal_type)
                    elif signal_type.startswith('Banner') or 'Banner#' in signal_type:
                        signal_groups['Banner сигналы'].append(signal_type)
                    else:
                        signal_groups['Другие'].append(signal_type)
                
                # Добавляем категории с количеством (только если есть сигналы)
                for group_name, types in signal_groups.items():
                    if types:
                        categories.append(f"{group_name} ({len(types)})")
                
                # Обновляем комбобокс
                if hasattr(self, 'signals_combo'):
                    self.signals_combo['values'] = categories
                    self.signals_combo.set("Все")
                    self.logger.info(f"🔄 Созданы реальные категории: {categories}")
            
            self._update_statistics()
            self.logger.info(f"✅ Типы сигналов проанализированы и категоризированы")
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа типов сигналов: {e}")


    def update_line_checkboxes(self, lines: List[str]):
        """Обновление линий"""
        try:
            self.all_lines = lines
            self.state.lines = set(lines)  # По умолчанию все выбраны
            self._update_statistics()
            self.logger.info(f"Обновлены линии: {len(lines)}")
        except Exception as e:
            self.logger.error(f"Ошибка обновления линий: {e}")

    def update_wagon_checkboxes(self, wagons: List[str]):
        """ИСПРАВЛЕННОЕ обновление с полной синхронизацией UI"""
        try:
            # Сохраняем реальные номера из данных
            self.real_wagons_in_data = set(wagons)
            
            # Получаем ведущий вагон из контроллера
            leading_wagon = self._get_leading_wagon_from_controller()
            self.leading_wagon = leading_wagon
            
            # Создаем маппинг на основе ведущего вагона
            self._create_wagon_mapping(leading_wagon)
            
            # ИСПРАВЛЕНО: Инициализируем состояние только реальными вагонами
            self.state.wagons = self.real_wagons_in_data.copy()
            
            # КРИТИЧНО: Принудительно обновляем UI
            self._force_update_wagon_ui()
            
            # ИСПРАВЛЕНО: Синхронизируем состояние после создания UI
            if hasattr(self, 'wagon_vars') and self.wagon_vars:
                self._update_existing_wagon_buttons()
            
            self._update_statistics()
            self.logger.info(f"✅ Вагоны обновлены и синхронизированы для ведущего {leading_wagon}: {wagons}")
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления вагонов: {e}")

    def get_selected_filters(self) -> Dict[str, Any]:
        """Получение выбранных фильтров"""
        return self.state.to_dict()

    def set_controller(self, controller):
        """Установка контроллера"""
        self.controller = controller
        self.logger.info("Контроллер установлен в SmartFilterPanel")

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.observer._subscribers.clear()
            self.controller = None
            self.logger.info("SmartFilterPanel очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки SmartFilterPanel: {e}")

    def __str__(self):
        return f"SmartFilterPanel(tabs=True, leading_wagon={self.leading_wagon}, mapping={len(self.wagon_mapping)})"
