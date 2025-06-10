# src/ui/components/diagnostic_filter_panel.py
"""
UI панель диагностических фильтров для анализа телеметрии
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, List, Any, Callable, Optional

from ...config.diagnostic_filters_config import (
    CRITICAL_FILTERS, SYSTEM_FILTERS, FUNCTIONAL_FILTERS, SEVERITY_LEVELS
)
from src.core.domain.entities.signal_classifier import (
    SignalCriticality, 
    SignalSystem
)

class DiagnosticFilterPanel(ttk.Frame):
    """Панель диагностических фильтров"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Переменные фильтров
        self.critical_vars: Dict[str, tk.BooleanVar] = {}
        self.system_vars: Dict[str, tk.BooleanVar] = {}
        self.functional_vars: Dict[str, tk.BooleanVar] = {}
        
        # Состояние панели
        self.is_expanded = tk.BooleanVar(value=True)
        self.active_filters_count = tk.StringVar(value="Фильтры: 0")
        
        # Callbacks
        self.on_filter_changed: Optional[Callable] = None
        
        self._setup_diagnostic_ui()
        self.logger.info("DiagnosticFilterPanel инициализирован")

    def _setup_diagnostic_ui(self):
        """Настройка UI диагностических фильтров"""
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)
        
        # Заголовок с кнопкой сворачивания
        self._create_header()
        
        # Основной контейнер фильтров
        self.filters_container = ttk.Frame(self)
        self.filters_container.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        self.filters_container.grid_columnconfigure(0, weight=1)
        
        # Создание фильтров
        self._create_critical_filters()
        self._create_system_filters() 
        self._create_functional_filters()
        self._create_control_buttons()
        
        # Привязка к переменной сворачивания
        self.is_expanded.trace('w', self._on_expand_changed)

    def _create_header(self):
        """Создание заголовка панели"""
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        # Кнопка сворачивания
        expand_btn = ttk.Checkbutton(
            header_frame,
            text="🔍",
            variable=self.is_expanded,
            style="Toolbutton"
        )
        expand_btn.grid(row=0, column=0, sticky="w")

        # Заголовок
        title_label = ttk.Label(
            header_frame,
            text="Диагностические фильтры",
            font=('Arial', 10, 'bold')
        )
        title_label.grid(row=0, column=1, sticky="w", padx=(5, 0))

        # Счетчик активных фильтров
        count_label = ttk.Label(
            header_frame,
            textvariable=self.active_filters_count,
            font=('Arial', 8),
            foreground='gray'
        )
        count_label.grid(row=0, column=2, sticky="e")

    def _create_critical_filters(self):
        """Создание фильтров критичности"""
        critical_frame = ttk.LabelFrame(
            self.filters_container,
            text="🚨 Критичность",
            padding="3"
        )
        critical_frame.grid(row=0, column=0, sticky="ew", pady=(0, 3))
        critical_frame.grid_columnconfigure(0, weight=1)

        # Контейнер для кнопок
        buttons_frame = ttk.Frame(critical_frame)
        buttons_frame.grid(row=0, column=0, sticky="ew")

        # Создание кнопок критичности
        critical_configs = [
            ("🆘 Аварии", "emergency", CRITICAL_FILTERS["emergency"]["color"]),
            ("⚠️ Безопасность", "safety", CRITICAL_FILTERS["safety"]["color"]),
            ("⚡ Энергосистема", "power_critical", CRITICAL_FILTERS["power_critical"]["color"]),
            ("🛑 Тормоза", "brake_critical", CRITICAL_FILTERS["brake_critical"]["color"])
        ]

        for i, (text, filter_key, color) in enumerate(critical_configs):
            var = tk.BooleanVar()
            self.critical_vars[filter_key] = var
            
            btn = ttk.Checkbutton(
                buttons_frame,
                text=text,
                variable=var,
                command=self._on_critical_filter_changed
            )
            btn.grid(row=0, column=i, sticky="w", padx=2)

    def _create_system_filters(self):
        """Создание фильтров по системам"""
        systems_frame = ttk.LabelFrame(
            self.filters_container,
            text="⚙️ Системы",
            padding="3"
        )
        systems_frame.grid(row=1, column=0, sticky="ew", pady=(0, 3))
        systems_frame.grid_columnconfigure(0, weight=1)

        # Контейнер для кнопок систем
        buttons_frame = ttk.Frame(systems_frame)
        buttons_frame.grid(row=0, column=0, sticky="ew")

        # Создание кнопок систем
        system_configs = [
            ("🚂 Тяга", "traction"),
            ("🛑 Тормоза", "brakes"), 
            ("🚪 Двери", "doors"),
            ("⚡ Питание", "power"),
            ("🌡️ Климат", "climate"),
            ("📺 Инфо", "info_systems"),
            ("📡 Связь", "communication")
        ]

        for i, (text, system_key) in enumerate(system_configs):
            var = tk.BooleanVar()
            self.system_vars[system_key] = var
            
            btn = ttk.Checkbutton(
                buttons_frame,
                text=text,
                variable=var,
                command=self._on_system_filter_changed
            )
            btn.grid(row=0, column=i, sticky="w", padx=2)

    def _create_functional_filters(self):
        """Создание функциональных фильтров"""
        func_frame = ttk.LabelFrame(
            self.filters_container,
            text="🔧 Функции",
            padding="3"
        )
        func_frame.grid(row=2, column=0, sticky="ew", pady=(0, 3))
        func_frame.grid_columnconfigure(0, weight=1)

        # Контейнер для кнопок функций
        buttons_frame = ttk.Frame(func_frame)
        buttons_frame.grid(row=0, column=0, sticky="ew")

        # Создание кнопок функций
        functional_configs = [
            ("❌ Ошибки", "faults"),
            ("📊 Измерения", "measurements"),
            ("🔘 Состояния", "states"),
            ("⚙️ Управление", "controls"),
            ("🔧 Диагностика", "diagnostics")
        ]

        for i, (text, func_key) in enumerate(functional_configs):
            var = tk.BooleanVar()
            self.functional_vars[func_key] = var
            
            btn = ttk.Checkbutton(
                buttons_frame,
                text=text,
                variable=var,
                command=self._on_functional_filter_changed
            )
            btn.grid(row=0, column=i, sticky="w", padx=2)

    def _create_control_buttons(self):
        """Создание кнопок управления"""
        control_frame = ttk.Frame(self.filters_container)
        control_frame.grid(row=3, column=0, sticky="ew", pady=(5, 0))

        # Кнопки управления
        ttk.Button(
            control_frame,
            text="Все критичные",
            command=self._select_all_critical,
            width=12
        ).grid(row=0, column=0, padx=2)

        ttk.Button(
            control_frame,
            text="Только ошибки",
            command=self._select_only_faults,
            width=12
        ).grid(row=0, column=1, padx=2)

        ttk.Button(
            control_frame,
            text="Сбросить",
            command=self._reset_all_filters,
            width=12
        ).grid(row=0, column=2, padx=2)

        # Кнопка анализа
        ttk.Button(
            control_frame,
            text="🔍 Анализ",
            command=self._perform_diagnostic_analysis,
            width=12
        ).grid(row=0, column=3, padx=2)

    def _on_expand_changed(self, *args):
        """Обработка сворачивания/разворачивания"""
        if self.is_expanded.get():
            self.filters_container.grid()
        else:
            self.filters_container.grid_remove()

    def _on_critical_filter_changed(self):
        """Обработка изменения фильтров критичности"""
        self._update_active_filters_count()
        self._apply_diagnostic_filters()

    def _on_system_filter_changed(self):
        """Обработка изменения системных фильтров"""
        self._update_active_filters_count()
        self._apply_diagnostic_filters()

    def _on_functional_filter_changed(self):
        """Обработка изменения функциональных фильтров"""
        self._update_active_filters_count()
        self._apply_diagnostic_filters()

    def _apply_diagnostic_filters(self):
        """Применение диагностических фильтров"""
        try:
            # Собираем активные фильтры
            filters = self.get_active_diagnostic_filters()
            
            # Применяем через контроллер
            if self.controller and hasattr(self.controller, 'apply_diagnostic_filters'):
                self.controller.apply_diagnostic_filters(filters)
            
            # Вызываем callback
            if self.on_filter_changed:
                self.on_filter_changed(filters)
                
        except Exception as e:
            self.logger.error(f"Ошибка применения диагностических фильтров: {e}")

    def _update_active_filters_count(self):
        """Обновление счетчика активных фильтров"""
        try:
            count = 0
            
            # Считаем активные фильтры
            for var in self.critical_vars.values():
                if var.get():
                    count += 1
            
            for var in self.system_vars.values():
                if var.get():
                    count += 1
            
            for var in self.functional_vars.values():
                if var.get():
                    count += 1
            
            self.active_filters_count.set(f"Фильтры: {count}")
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления счетчика фильтров: {e}")

    def _select_all_critical(self):
        """Выбор всех критичных фильтров"""
        for filter_key in ['emergency', 'safety', 'power_critical', 'brake_critical']:
            if filter_key in self.critical_vars:
                self.critical_vars[filter_key].set(True)
        
        # Выбираем фильтр ошибок
        if 'faults' in self.functional_vars:
            self.functional_vars['faults'].set(True)
        
        self._update_active_filters_count()
        self._apply_diagnostic_filters()

    def _select_only_faults(self):
        """Выбор только ошибок"""
        # Сбрасываем все
        self._reset_all_filters_internal()
        
        # Включаем только фильтр ошибок
        if 'faults' in self.functional_vars:
            self.functional_vars['faults'].set(True)
        
        self._update_active_filters_count()
        self._apply_diagnostic_filters()

    def _reset_all_filters(self):
        """Сброс всех фильтров"""
        self._reset_all_filters_internal()
        self._update_active_filters_count()
        self._apply_diagnostic_filters()

    def _reset_all_filters_internal(self):
        """Внутренний сброс фильтров"""
        for var in self.critical_vars.values():
            var.set(False)
        for var in self.system_vars.values():
            var.set(False)
        for var in self.functional_vars.values():
            var.set(False)

    def _perform_diagnostic_analysis(self):
        """Выполнение диагностического анализа"""
        try:
            if self.controller and hasattr(self.controller, 'perform_diagnostic_analysis'):
                self.controller.perform_diagnostic_analysis()
            else:
                self.logger.warning("Диагностический анализ недоступен")
                
        except Exception as e:
            self.logger.error(f"Ошибка выполнения диагностического анализа: {e}")

    # === ПУБЛИЧНЫЕ МЕТОДЫ ===

    def get_active_diagnostic_filters(self) -> Dict[str, List[str]]:
        """Получение активных диагностических фильтров"""
        try:
            filters = {
                'criticality': [],
                'systems': [],
                'functions': []
            }
            
            # Собираем активные фильтры критичности
            for filter_key, var in self.critical_vars.items():
                if var.get():
                    filters['criticality'].append(filter_key)
            
            # Собираем активные системные фильтры
            for filter_key, var in self.system_vars.items():
                if var.get():
                    filters['systems'].append(filter_key)
            
            # Собираем активные функциональные фильтры
            for filter_key, var in self.functional_vars.items():
                if var.get():
                    filters['functions'].append(filter_key)
            
            return filters
            
        except Exception as e:
            self.logger.error(f"Ошибка получения фильтров: {e}")
            return {'criticality': [], 'systems': [], 'functions': []}

    def set_diagnostic_filters(self, filters: Dict[str, List[str]]):
        """Установка диагностических фильтров"""
        try:
            # Сначала сбрасываем все
            self._reset_all_filters_internal()
            
            # Устанавливаем фильтры критичности
            for filter_key in filters.get('criticality', []):
                if filter_key in self.critical_vars:
                    self.critical_vars[filter_key].set(True)
            
            # Устанавливаем системные фильтры
            for filter_key in filters.get('systems', []):
                if filter_key in self.system_vars:
                    self.system_vars[filter_key].set(True)
            
            # Устанавливаем функциональные фильтры
            for filter_key in filters.get('functions', []):
                if filter_key in self.functional_vars:
                    self.functional_vars[filter_key].set(True)
            
            self._update_active_filters_count()
            
        except Exception as e:
            self.logger.error(f"Ошибка установки фильтров: {e}")

    def highlight_critical_signals(self, signal_codes: List[str]):
        """Подсветка критичных сигналов"""
        try:
            # Здесь можно добавить логику подсветки в UI
            # Например, изменение цвета кнопок фильтров
            self.logger.info(f"Подсветка {len(signal_codes)} критичных сигналов")
            
        except Exception as e:
            self.logger.error(f"Ошибка подсветки сигналов: {e}")

    def show_diagnostic_results(self, results: Dict[str, Any]):
        """Отображение результатов диагностики"""
        try:
            # Создаем окно с результатами
            self._create_results_window(results)
            
        except Exception as e:
            self.logger.error(f"Ошибка отображения результатов: {e}")

    def _create_results_window(self, results: Dict[str, Any]):
        """Создание окна с результатами диагностики"""
        try:
            results_window = tk.Toplevel(self)
            results_window.title("Результаты диагностического анализа")
            results_window.geometry("800x600")
            results_window.transient(self)
            
            # Создаем прокручиваемый текст
            text_frame = ttk.Frame(results_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 10))
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Заполняем результатами
            results_text = self._format_diagnostic_results(results)
            text_widget.insert(tk.END, results_text)
            text_widget.config(state=tk.DISABLED)
            
            # Кнопка закрытия
            ttk.Button(
                results_window,
                text="Закрыть",
                command=results_window.destroy
            ).pack(pady=5)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания окна результатов: {e}")

    def _format_diagnostic_results(self, results: Dict[str, Any]) -> str:
        """Форматирование результатов диагностики"""
        try:
            text = "РЕЗУЛЬТАТЫ ДИАГНОСТИЧЕСКОГО АНАЛИЗА\n"
            text += "=" * 50 + "\n\n"
            
            # Общий статус
            if 'overall_status' in results:
                status = results['overall_status'].upper()
                text += f"ОБЩИЙ СТАТУС СИСТЕМЫ: {status}\n\n"
            
            # Критичные неисправности
            if 'critical_faults' in results and results['critical_faults']:
                text += "КРИТИЧНЫЕ НЕИСПРАВНОСТИ:\n"
                for fault in results['critical_faults']:
                    text += f"  • {fault}\n"
                text += "\n"
            
            # Статус систем
            if 'systems_status' in results:
                text += "СТАТУС СИСТЕМ:\n"
                for system, status in results['systems_status'].items():
                    fault_count = status.get('fault_count', 0)
                    system_status = status.get('status', 'unknown')
                    text += f"  • {system}: {system_status.upper()} (неисправностей: {fault_count})\n"
                text += "\n"
            
            # Рекомендации
            if 'recommendations' in results and results['recommendations']:
                text += "РЕКОМЕНДАЦИИ:\n"
                for i, rec in enumerate(results['recommendations'], 1):
                    text += f"  {i}. {rec}\n"
            
            return text
            
        except Exception as e:
            self.logger.error(f"Ошибка форматирования результатов: {e}")
            return "Ошибка отображения результатов"

    def cleanup(self):
        """Очистка ресурсов"""
        self.controller = None
        self.on_filter_changed = None
        self.logger.info("DiagnosticFilterPanel очищен")
