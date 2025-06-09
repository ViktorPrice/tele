# src/ui/components/ui_components.py - ИСЧЕРПЫВАЮЩЕ ПОЛНАЯ ВЕРСИЯ
"""
Главный менеджер UI компонентов с выбором компактной/стандартной компоновки
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import time

class UIComponents:
    """Главный менеджер UI компонентов с полной интеграцией"""

    def __init__(self, root: tk.Tk, controller):
        self.root = root
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # UI панели
        self.time_panel: Optional[Any] = None
        self.filter_panel: Optional[Any] = None
        self.parameter_panel: Optional[Any] = None
        self.action_panel: Optional[Any] = None
        self.plot_panel: Optional[Any] = None

        # Основные контейнеры
        self.main_content_frame: Optional[ttk.Frame] = None
        self.left_panel_frame: Optional[ttk.Frame] = None
        self.right_panel_frame: Optional[ttk.Frame] = None

        # Состояние UI
        self.is_initialized = False
        self.is_loading = False
        self.use_compact_layout = True  # ПЕРЕКЛЮЧАТЕЛЬ КОМПОНОВКИ
        
        # Кэш для оптимизации обновлений
        self._ui_cache = {}
        self._last_update_time = 0
        
        # Callbacks для координации
        self._event_callbacks: Dict[str, List[Callable]] = {}

        # Инициализация
        self._setup_main_layout()
        self._create_ui_panels()
        self._setup_bindings()
        self._setup_event_system()

        self.is_initialized = True
        self.logger.info("UIComponents полностью инициализированы")

    def _setup_main_layout(self):
        """Создание основного макета приложения"""
        try:
            # Главный контейнер
            self.main_content_frame = ttk.Frame(self.root)
            self.main_content_frame.grid(row=1, column=0, sticky="nsew", padx=3, pady=3)

            # Настройка сетки главного окна
            self.root.grid_rowconfigure(1, weight=1)
            self.root.grid_columnconfigure(0, weight=1)

            if self.use_compact_layout:
                self._setup_compact_layout()
            else:
                self._setup_standard_layout()

            self.logger.info("Основной макет создан")

        except Exception as e:
            self.logger.error(f"Ошибка создания основного макета: {e}")
            raise

    def _setup_compact_layout(self):
        """КОМПАКТНАЯ компоновка - левая панель + правая панель графиков"""
        # Настройка сетки главного контейнера
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)  # Левая панель
        self.main_content_frame.grid_columnconfigure(1, weight=2)  # Правая панель (графики)

        # Левая панель управления (компактная)
        self.left_panel_frame = ttk.Frame(self.main_content_frame)
        self.left_panel_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        self.left_panel_frame.grid_columnconfigure(0, weight=1)

        # Правая панель (для графиков)
        self.right_panel_frame = ttk.Frame(self.main_content_frame)
        self.right_panel_frame.grid(row=0, column=1, sticky="nsew")
        self.right_panel_frame.grid_rowconfigure(0, weight=1)
        self.right_panel_frame.grid_columnconfigure(0, weight=1)

    def _setup_standard_layout(self):
        """СТАНДАРТНАЯ компоновка - только левая панель"""
        # Настройка сетки главного контейнера
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        # Левая панель управления
        self.left_panel_frame = ttk.Frame(self.main_content_frame)
        self.left_panel_frame.grid(row=0, column=0, sticky="nsew")
        self.left_panel_frame.grid_columnconfigure(0, weight=1)

    def _create_ui_panels(self):
        """Создание UI панелей с выбором типа"""
        try:
            if self.use_compact_layout:
                self.logger.info("Создание КОМПАКТНЫХ панелей")
                self._create_compact_panels()
            else:
                self.logger.info("Создание СТАНДАРТНЫХ панелей")
                self._create_standard_panels()

            # Панель визуализации графиков (только для компактного режима)
            if self.use_compact_layout:
                self._create_plot_visualization_panel()

            self.logger.info("Все UI панели созданы")

        except Exception as e:
            self.logger.error(f"Ошибка создания UI панелей: {e}")
            raise

    def _create_compact_panels(self):
        """Создание КОМПАКТНЫХ панелей"""
        try:
            # 1. Компактная панель времени (строка 0)
            self._create_compact_time_panel()

            # 2. Компактная панель фильтров (строка 1)
            self._create_compact_filter_panel()

            # 3. Горизонтальная панель параметров (строка 2)
            self._create_horizontal_parameter_panel()

            # 4. Горизонтальная панель действий (строка 3)
            self._create_horizontal_action_panel()

        except Exception as e:
            self.logger.error(f"Ошибка создания компактных панелей: {e}")
            # Fallback к стандартным панелям
            self.use_compact_layout = False
            self._create_standard_panels()

    def _create_compact_time_panel(self):
        """ИСПРАВЛЕННОЕ создание компактной панели времени"""
        try:
            time_frame = ttk.LabelFrame(
                self.left_panel_frame,
                text="Временной диапазон",
                padding="3"
            )
            time_frame.grid(row=0, column=0, sticky="ew", pady=(0, 3))
            time_frame.grid_columnconfigure(0, weight=1)

            from .compact_time_panel import CompactTimePanel
            self.time_panel = CompactTimePanel(time_frame, self.controller)
            self.time_panel.grid(row=0, column=0, sticky="ew")
            self.logger.info("✅ CompactTimePanel создан принудительно")

        except Exception as e:
            self.logger.error(f"Ошибка создания CompactTimePanel: {e}")
            import traceback
            traceback.print_exc()
            # Fallback к обычному TimePanel
            self._create_fallback_time_panel(time_frame)

    def _create_compact_filter_panel(self):
        """Создание компактной панели фильтров"""
        try:
            filter_frame = ttk.LabelFrame(
                self.left_panel_frame,
                text="Фильтры",
                padding="3"
            )
            filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 3))
            filter_frame.grid_columnconfigure(0, weight=1)

            try:
                from .compact_filter_panel import CompactFilterPanel
                self.filter_panel = CompactFilterPanel(filter_frame, self.controller)
                self.filter_panel.grid(row=0, column=0, sticky="ew")
                self.logger.debug("✅ CompactFilterPanel создан")
            except ImportError:
                self.logger.warning("CompactFilterPanel не найден, используется FilterPanel")
                self._create_fallback_filter_panel(filter_frame)

        except Exception as e:
            self.logger.error(f"Ошибка создания компактной панели фильтров: {e}")
            self._create_filter_panel_placeholder()

    def _create_horizontal_parameter_panel(self):
        """Создание горизонтальной панели параметров"""
        try:
            parameter_frame = ttk.LabelFrame(
                self.left_panel_frame,
                text="Параметры телеметрии",
                padding="3"
            )
            parameter_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 3))
            parameter_frame.grid_columnconfigure(0, weight=1)
            parameter_frame.grid_rowconfigure(0, weight=1)

            # КРИТИЧНО: Устанавливаем вес для растягивания панели параметров
            self.left_panel_frame.grid_rowconfigure(2, weight=1)

            try:
                from .horizontal_parameter_panel import HorizontalParameterPanel
                self.parameter_panel = HorizontalParameterPanel(parameter_frame, self.controller)
                self.parameter_panel.grid(row=0, column=0, sticky="nsew")
                self.logger.info("✅ HorizontalParameterPanel создан")
            except ImportError:
                self.logger.warning("HorizontalParameterPanel не найден, используется ParameterPanel")
                self._create_fallback_parameter_panel(parameter_frame)

        except Exception as e:
            self.logger.error(f"Ошибка создания горизонтальной панели параметров: {e}")
            self._create_parameter_panel_placeholder()

    def _create_horizontal_action_panel(self):
        """Создание горизонтальной панели действий"""
        try:
            action_frame = ttk.LabelFrame(
                self.left_panel_frame,
                text="Действия",
                padding="3"
            )
            action_frame.grid(row=3, column=0, sticky="ew")
            action_frame.grid_columnconfigure(0, weight=1)

            try:
                from .horizontal_action_panel import HorizontalActionPanel
                self.action_panel = HorizontalActionPanel(action_frame, self.controller)
                self.action_panel.grid(row=0, column=0, sticky="ew")
                self.logger.debug("✅ HorizontalActionPanel создан")
            except ImportError:
                self.logger.warning("HorizontalActionPanel не найден, используется ActionPanel")
                self._create_fallback_action_panel(action_frame)

        except Exception as e:
            self.logger.error(f"Ошибка создания горизонтальной панели действий: {e}")
            self._create_action_panel_placeholder()

    def _create_standard_panels(self):
        """Создание СТАНДАРТНЫХ панелей"""
        try:
            # 1. Панель времени
            self._create_standard_time_panel()

            # 2. Панель фильтров
            self._create_standard_filter_panel()

            # 3. Панель параметров (основная)
            self._create_standard_parameter_panel()

            # 4. Панель действий
            self._create_standard_action_panel()

        except Exception as e:
            self.logger.error(f"Ошибка создания стандартных панелей: {e}")
            raise

    def _create_standard_time_panel(self):
        """Создание стандартной панели времени"""
        try:
            time_frame = ttk.LabelFrame(
                self.left_panel_frame,
                text="Временной диапазон",
                padding="8"
            )
            time_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
            time_frame.grid_columnconfigure(0, weight=1)

            self._create_fallback_time_panel(time_frame)

        except Exception as e:
            self.logger.error(f"Ошибка создания стандартной панели времени: {e}")
            self._create_time_panel_placeholder()

    def _create_standard_filter_panel(self):
        """Создание стандартной панели фильтров"""
        try:
            filter_frame = ttk.LabelFrame(
                self.left_panel_frame,
                text="Фильтры параметров",
                padding="8"
            )
            filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
            filter_frame.grid_columnconfigure(0, weight=1)

            self._create_fallback_filter_panel(filter_frame)

        except Exception as e:
            self.logger.error(f"Ошибка создания стандартной панели фильтров: {e}")
            self._create_filter_panel_placeholder()

    def _create_standard_parameter_panel(self):
        """Создание стандартной панели параметров"""
        try:
            parameter_frame = ttk.LabelFrame(
                self.left_panel_frame,
                text="Параметры телеметрии",
                padding="8"
            )
            parameter_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
            parameter_frame.grid_columnconfigure(0, weight=1)
            parameter_frame.grid_rowconfigure(0, weight=1)

            # КРИТИЧНО: Устанавливаем вес для растягивания панели параметров
            self.left_panel_frame.grid_rowconfigure(2, weight=1)

            self._create_fallback_parameter_panel(parameter_frame)

        except Exception as e:
            self.logger.error(f"Ошибка создания стандартной панели параметров: {e}")
            self._create_parameter_panel_placeholder()

    def _create_standard_action_panel(self):
        """Создание стандартной панели действий"""
        try:
            action_frame = ttk.LabelFrame(
                self.left_panel_frame,
                text="Действия",
                padding="8"
            )
            action_frame.grid(row=3, column=0, sticky="ew")
            action_frame.grid_columnconfigure(0, weight=1)

            self._create_fallback_action_panel(action_frame)

        except Exception as e:
            self.logger.error(f"Ошибка создания стандартной панели действий: {e}")
            self._create_action_panel_placeholder()

    # === FALLBACK МЕТОДЫ ===

    def _create_fallback_time_panel(self, parent):
        """Fallback создание TimePanel"""
        try:
            from .time_panel import TimePanel
            self.time_panel = TimePanel(parent, self.controller)
            self.time_panel.grid(row=0, column=0, sticky="ew")
            self.logger.debug("TimePanel создан (fallback)")
        except Exception as e:
            self.logger.error(f"Ошибка создания TimePanel: {e}")
            self._create_time_panel_placeholder()

    def _create_fallback_filter_panel(self, parent):
        """Fallback создание FilterPanel"""
        try:
            from .filter_panel import FilterPanel
            self.filter_panel = FilterPanel(parent, self.controller)
            self.filter_panel.grid(row=0, column=0, sticky="ew")
            self.logger.debug("FilterPanel создан (fallback)")
        except Exception as e:
            self.logger.error(f"Ошибка создания FilterPanel: {e}")
            self._create_filter_panel_placeholder()

    def _create_fallback_parameter_panel(self, parent):
        """Fallback создание ParameterPanel"""
        try:
            from .parameter_panel import ParameterPanel
            self.parameter_panel = ParameterPanel(parent, self.controller)
            self.parameter_panel.grid(row=0, column=0, sticky="nsew")
            self.logger.info("✅ ParameterPanel создан (fallback)")
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания ParameterPanel: {e}")
            import traceback
            traceback.print_exc()
            self._create_parameter_panel_placeholder()

    def _create_fallback_action_panel(self, parent):
        """Fallback создание ActionPanel"""
        try:
            from .action_panel import ActionPanel
            self.action_panel = ActionPanel(parent, self.controller)
            self.action_panel.grid(row=0, column=0, sticky="ew")
            self.logger.debug("ActionPanel создан (fallback)")
        except Exception as e:
            self.logger.error(f"Ошибка создания ActionPanel: {e}")
            self._create_action_panel_placeholder()

    # === PLACEHOLDER МЕТОДЫ ===

    def _create_time_panel_placeholder(self):
        """Создание заглушки панели времени"""
        placeholder_frame = ttk.Frame(self.left_panel_frame)
        placeholder_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        
        ttk.Label(
            placeholder_frame,
            text="Панель времени временно недоступна",
            foreground="gray"
        ).pack()

    def _create_filter_panel_placeholder(self):
        """Создание заглушки панели фильтров"""
        placeholder_frame = ttk.Frame(self.left_panel_frame)
        placeholder_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        
        ttk.Label(
            placeholder_frame,
            text="Панель фильтров временно недоступна",
            foreground="gray"
        ).pack()

    def _create_parameter_panel_placeholder(self):
        """Создание заглушки панели параметров"""
        placeholder_frame = ttk.Frame(self.left_panel_frame)
        placeholder_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        placeholder_frame.grid_columnconfigure(0, weight=1)
        placeholder_frame.grid_rowconfigure(0, weight=1)
        
        # Устанавливаем вес
        self.left_panel_frame.grid_rowconfigure(2, weight=1)
        
        placeholder_text = ttk.Label(
            placeholder_frame,
            text="Панель параметров временно недоступна\nПроверьте логи для деталей",
            foreground="red",
            justify=tk.CENTER
        )
        placeholder_text.pack(expand=True)

    def _create_action_panel_placeholder(self):
        """Создание заглушки панели действий"""
        placeholder_frame = ttk.Frame(self.left_panel_frame)
        placeholder_frame.grid(row=3, column=0, sticky="ew")
        
        ttk.Label(
            placeholder_frame,
            text="Панель действий временно недоступна",
            foreground="gray"
        ).pack()

    def _create_plot_visualization_panel(self):
        """Создание панели визуализации графиков"""
        try:
            # Создаем заголовок для правой панели
            plot_label = ttk.Label(
                self.right_panel_frame,
                text="Графики и визуализация",
                font=('Arial', 10, 'bold')
            )
            plot_label.grid(row=0, column=0, sticky="ew", pady=(0, 5))

            # Контейнер для графиков
            plot_container = ttk.Frame(self.right_panel_frame)
            plot_container.grid(row=1, column=0, sticky="nsew")
            plot_container.grid_rowconfigure(0, weight=1)
            plot_container.grid_columnconfigure(0, weight=1)

            # Настройка веса для правой панели
            self.right_panel_frame.grid_rowconfigure(1, weight=1)

            try:
                # Пытаемся создать PlotVisualizationPanel
                from .plot_visualization_panel import PlotVisualizationPanel
                self.plot_panel = PlotVisualizationPanel(plot_container, self.controller)
                self.plot_panel.grid(row=0, column=0, sticky="nsew")
                
                self.logger.info("✅ Панель визуализации графиков создана")

            except ImportError as e:
                self.logger.warning(f"PlotVisualizationPanel не найден: {e}")
                self._create_plot_panel_placeholder(plot_container)

        except Exception as e:
            self.logger.error(f"Ошибка создания панели визуализации: {e}")
            self._create_plot_panel_placeholder_simple()

    def _create_plot_panel_placeholder(self, container):
        """Создание заглушки панели графиков"""
        placeholder_frame = ttk.Frame(container)
        placeholder_frame.grid(row=0, column=0, sticky="nsew")
        placeholder_frame.grid_rowconfigure(0, weight=1)
        placeholder_frame.grid_columnconfigure(0, weight=1)

        # Информационное сообщение
        info_text = """
        📊 ПАНЕЛЬ ГРАФИКОВ
        
        Здесь будут отображаться:
        • Интерактивные графики телеметрии
        • Визуализация выбранных параметров
        • Инструменты анализа данных
        
        Выберите параметры слева и нажмите
        "Построить график" для начала работы
        """
        
        info_label = tk.Label(
            placeholder_frame,
            text=info_text,
            font=('Arial', 11),
            justify=tk.CENTER,
            fg='#666666',
            bg='#f8f9fa'
        )
        info_label.grid(row=0, column=0, padx=20, pady=20)

    def _create_plot_panel_placeholder_simple(self):
        """Простая заглушка панели графиков"""
        if hasattr(self, 'right_panel_frame') and self.right_panel_frame:
            ttk.Label(
                self.right_panel_frame,
                text="Панель графиков недоступна",
                foreground="gray"
            ).grid(row=0, column=0, padx=20, pady=20)

    def _setup_bindings(self):
        """Настройка связей между компонентами"""
        try:
            # Связь между фильтрами и параметрами
            if self.filter_panel and self.parameter_panel:
                # При изменении фильтров обновляем список параметров
                if hasattr(self.filter_panel, 'on_filter_changed'):
                    self.filter_panel.on_filter_changed = self._on_filters_changed

            # Связь между временной панелью и контроллером
            if self.time_panel:
                if hasattr(self.time_panel, 'on_time_range_changed'):
                    self.time_panel.on_time_range_changed = self._on_time_range_changed

            # Связь между параметрами и действиями
            if self.parameter_panel and self.action_panel:
                if hasattr(self.parameter_panel, 'on_selection_changed'):
                    self.parameter_panel.on_selection_changed = self._on_parameter_selection_changed

            self.logger.debug("Связи между компонентами настроены")

        except Exception as e:
            self.logger.error(f"Ошибка настройки связей: {e}")

    def _setup_event_system(self):
        """Настройка системы событий"""
        try:
            # Инициализация callbacks
            event_types = [
                'parameter_updated', 'filter_changed', 'time_changed',
                'selection_changed', 'data_loaded', 'plot_created'
            ]
            
            for event_type in event_types:
                self._event_callbacks[event_type] = []

            self.logger.debug("Система событий настроена")

        except Exception as e:
            self.logger.error(f"Ошибка настройки системы событий: {e}")

    def register_event_callback(self, event_type: str, callback: Callable):
        """Регистрация callback для события"""
        try:
            if event_type not in self._event_callbacks:
                self._event_callbacks[event_type] = []
            
            self._event_callbacks[event_type].append(callback)
            self.logger.debug(f"Зарегистрирован callback для события: {event_type}")

        except Exception as e:
            self.logger.error(f"Ошибка регистрации callback: {e}")

    def emit_event(self, event_type: str, data: Any = None):
        """Генерация события"""
        try:
            if event_type in self._event_callbacks:
                for callback in self._event_callbacks[event_type]:
                    try:
                        callback(data)
                    except Exception as e:
                        self.logger.error(f"Ошибка в callback {callback}: {e}")

        except Exception as e:
            self.logger.error(f"Ошибка генерации события {event_type}: {e}")

    # === ОБРАБОТЧИКИ СОБЫТИЙ ===

    def _on_filters_changed(self):
        """Обработка изменения фильтров"""
        try:
            if self.controller:
                self.controller.apply_filters()
            
            self.emit_event('filter_changed')

        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения фильтров: {e}")

    def _on_time_range_changed(self, from_time: str, to_time: str):
        """Обработка изменения временного диапазона"""
        try:
            if self.controller:
                self.logger.info(f"Временной диапазон изменен: {from_time} - {to_time}")
            
            self.emit_event('time_changed', {'from_time': from_time, 'to_time': to_time})

        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения времени: {e}")

    def _on_parameter_selection_changed(self, selected_count: int):
        """Обработка изменения выбора параметров"""
        try:
            # Обновляем состояние кнопок действий
            if self.action_panel:
                if hasattr(self.action_panel, 'update_action_buttons_state'):
                    self.action_panel.update_action_buttons_state(selected_count > 0)

            self.emit_event('selection_changed', {'count': selected_count})
            self.logger.debug(f"Выбрано параметров: {selected_count}")

        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения выбора: {e}")

    # === МЕТОДЫ КЭШИРОВАНИЯ ===

    def _should_update_ui(self, key: str, value: Any) -> bool:
        """Проверка необходимости обновления UI с кэшированием"""
        current_time = time.time()
        
        # Обновляем не чаще чем раз в 50мс
        if current_time - self._last_update_time < 0.05:
            return False
        
        # Проверяем изменение значения
        if key in self._ui_cache:
            if self._ui_cache[key] == value:
                return False
        
        return True

    def _cache_ui_value(self, key: str, value: Any):
        """Кэширование значения UI"""
        self._ui_cache[key] = value
        self._last_update_time = time.time()

    # === ПУБЛИЧНЫЕ МЕТОДЫ ДЛЯ КОНТРОЛЛЕРА ===

    def update_parameters(self, parameters: List[Dict[str, Any]]):
        """КРИТИЧНО: Обновление списка параметров во всех панелях"""
        try:
            self.logger.info(f"📊 UIComponents.update_parameters вызван с {len(parameters)} параметрами")

            # Проверяем наличие parameter_panel
            if not self.parameter_panel:
                self.logger.error("❌ parameter_panel не создан!")
                return

            # Проверяем наличие метода update_parameters
            if not hasattr(self.parameter_panel, 'update_parameters'):
                self.logger.error("❌ parameter_panel не имеет метода update_parameters!")
                self.logger.info(f"Доступные методы: {[m for m in dir(self.parameter_panel) if not m.startswith('_')]}")
                return

            # Кэшированное обновление
            params_hash = hash(str(len(parameters)))
            if self._should_update_ui('parameters', params_hash):
                # Обновляем панель параметров
                self.parameter_panel.update_parameters(parameters)
                self.logger.info("✅ parameter_panel.update_parameters выполнен")

                # Обновляем панель фильтров
                if self.filter_panel and hasattr(self.filter_panel, 'update_line_checkboxes'):
                    # Извлекаем уникальные линии
                    lines = list(set(p.get('line', '') for p in parameters if p.get('line')))
                    self.filter_panel.update_line_checkboxes(lines)
                    self.logger.debug(f"Обновлены линии в фильтрах: {len(lines)} элементов")

                self._cache_ui_value('parameters', params_hash)
                self.emit_event('parameter_updated', parameters)

            self.logger.info(f"✅ Параметры обновлены в UI: {len(parameters)} элементов")

        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления параметров: {e}")
            import traceback
            traceback.print_exc()

    def update_time_range(self, from_time: str, to_time: str,
                          duration: str = "", total_records: int = 0, params_count: int = 0):
        """Обновление временного диапазона"""
        try:
            if self.time_panel and hasattr(self.time_panel, 'update_time_fields'):
                self.time_panel.update_time_fields(
                    from_time, to_time, duration, total_records
                )
                self.logger.info(f"Временной диапазон обновлен: {from_time} - {to_time}")
            else:
                self.logger.warning("time_panel недоступен или не имеет метода update_time_fields")

        except Exception as e:
            self.logger.error(f"Ошибка обновления временного диапазона: {e}")

    def get_selected_parameters(self) -> List[Dict[str, Any]]:
        """Получение выбранных параметров"""
        try:
            if self.parameter_panel and hasattr(self.parameter_panel, 'get_selected_parameters'):
                selected = self.parameter_panel.get_selected_parameters()
                self.logger.debug(f"Получено выбранных параметров: {len(selected)}")
                return selected
            else:
                self.logger.warning("parameter_panel недоступен или не имеет метода get_selected_parameters")
                return []
        except Exception as e:
            self.logger.error(f"Ошибка получения выбранных параметров: {e}")
            return []

    def get_filter_criteria(self) -> Dict[str, Any]:
        """Получение критериев фильтрации"""
        try:
            if self.filter_panel and hasattr(self.filter_panel, 'get_selected_filters'):
                criteria = self.filter_panel.get_selected_filters()
                self.logger.debug(f"Получены критерии фильтрации: {list(criteria.keys())}")
                return criteria
            else:
                self.logger.warning("filter_panel недоступен или не имеет метода get_selected_filters")
                return {}
        except Exception as e:
            self.logger.error(f"Ошибка получения критериев фильтрации: {e}")
            return {}

    def get_time_range(self) -> tuple[str, str]:
        """Получение временного диапазона"""
        try:
            if self.time_panel and hasattr(self.time_panel, 'get_time_range'):
                time_range = self.time_panel.get_time_range()
                self.logger.debug(f"Получен временной диапазон: {time_range}")
                return time_range
            else:
                self.logger.warning("time_panel недоступен или не имеет метода get_time_range")
                return "", ""
        except Exception as e:
            self.logger.error(f"Ошибка получения временного диапазона: {e}")
            return "", ""

    def set_loading_state(self, loading: bool):
        """Установка состояния загрузки для всех панелей"""
        try:
            self.is_loading = loading
            
            panels = [
                ('time_panel', self.time_panel),
                ('filter_panel', self.filter_panel),
                ('parameter_panel', self.parameter_panel),
                ('action_panel', self.action_panel),
                ('plot_panel', self.plot_panel)
            ]

            for panel_name, panel in panels:
                if panel and hasattr(panel, 'set_loading_state'):
                    try:
                        panel.set_loading_state(loading)
                        self.logger.debug(f"Состояние загрузки установлено для {panel_name}: {loading}")
                    except Exception as e:
                        self.logger.error(f"Ошибка установки состояния для {panel_name}: {e}")

        except Exception as e:
            self.logger.error(f"Ошибка установки состояния загрузки: {e}")

    def enable_all_panels(self):
        """Включение всех панелей"""
        try:
            panels = [self.time_panel, self.filter_panel, self.parameter_panel, self.action_panel]

            for panel in panels:
                if panel and hasattr(panel, 'enable'):
                    panel.enable()

            self.logger.debug("Все панели включены")

        except Exception as e:
            self.logger.error(f"Ошибка включения панелей: {e}")

    def disable_all_panels(self):
        """Отключение всех панелей"""
        try:
            panels = [self.time_panel, self.filter_panel, self.parameter_panel, self.action_panel]

            for panel in panels:
                if panel and hasattr(panel, 'disable'):
                    panel.disable()

            self.logger.debug("Все панели отключены")

        except Exception as e:
            self.logger.error(f"Ошибка отключения панелей: {e}")

    def reset_all_panels(self):
        """Сброс всех панелей к состоянию по умолчанию"""
        try:
            # Сброс фильтров
            if self.filter_panel and hasattr(self.filter_panel, 'reset_filters'):
                self.filter_panel.reset_filters()

            # Очистка выбора параметров
            if self.parameter_panel and hasattr(self.parameter_panel, 'clear_selection'):
                self.parameter_panel.clear_selection()

            # Очистка полей времени
            if self.time_panel and hasattr(self.time_panel, 'clear_time_fields'):
                self.time_panel.clear_time_fields()

            # Очистка графиков
            if self.plot_panel and hasattr(self.plot_panel, 'clear_all_plots'):
                self.plot_panel.clear_all_plots()

            self.logger.info("Все панели сброшены")

        except Exception as e:
            self.logger.error(f"Ошибка сброса панелей: {e}")

    def update_status_info(self, message: str, params_count: int = 0, selected_count: int = 0):
        """Обновление статусной информации во всех панелях"""
        try:
            # Кэшированное обновление
            status_key = f"status_{message}_{params_count}_{selected_count}"
            if self._should_update_ui('status_info', status_key):
                
                # Обновляем счетчики в панели параметров
                if self.parameter_panel and hasattr(self.parameter_panel, 'update_counters'):
                    self.parameter_panel.update_counters(params_count, selected_count)

                # Обновляем статус в панели действий
                if self.action_panel and hasattr(self.action_panel, 'update_status'):
                    self.action_panel.update_status(message)

                self._cache_ui_value('status_info', status_key)

        except Exception as e:
            self.logger.error(f"Ошибка обновления статусной информации: {e}")

    def show_loading_indicator(self, message: str = "Загрузка..."):
        """Показ индикатора загрузки"""
        try:
            self.set_loading_state(True)
            self.update_status_info(message)

            # Принудительное обновление UI
            self.root.update_idletasks()

        except Exception as e:
            self.logger.error(f"Ошибка показа индикатора загрузки: {e}")

    def hide_loading_indicator(self):
        """Скрытие индикатора загрузки"""
        try:
            self.set_loading_state(False)
            self.update_status_info("Готов")

        except Exception as e:
            self.logger.error(f"Ошибка скрытия индикатора загрузки: {e}")

    # === ДИАГНОСТИЧЕСКИЕ МЕТОДЫ ===

    def diagnose_components(self) -> Dict[str, Any]:
        """Диагностика состояния всех компонентов"""
        try:
            diagnosis = {
                'initialized': self.is_initialized,
                'loading': self.is_loading,
                'compact_layout': self.use_compact_layout,
                'cache_size': len(self._ui_cache),
                'event_callbacks': {k: len(v) for k, v in self._event_callbacks.items()},
                'components': {}
            }

            # Диагностика каждого компонента
            components = {
                'time_panel': self.time_panel,
                'filter_panel': self.filter_panel,
                'parameter_panel': self.parameter_panel,
                'action_panel': self.action_panel,
                'plot_panel': self.plot_panel
            }

            for name, component in components.items():
                diagnosis['components'][name] = {
                    'exists': component is not None,
                    'type': type(component).__name__ if component else None,
                    'methods': [m for m in dir(component) if not m.startswith('_')] if component else []
                }

                # Дополнительная диагностика для parameter_panel
                if name == 'parameter_panel' and component:
                    diagnosis['components'][name].update({
                        'has_update_parameters': hasattr(component, 'update_parameters'),
                        'has_get_selected': hasattr(component, 'get_selected_parameters'),
                        'all_params_count': len(getattr(component, 'all_parameters', [])),
                        'selected_count': len(getattr(component, 'selected_parameters', []))
                    })

            return diagnosis

        except Exception as e:
            self.logger.error(f"Ошибка диагностики: {e}")
            return {'error': str(e)}

    def log_diagnosis(self):
        """Логирование диагностической информации"""
        try:
            diagnosis = self.diagnose_components()
            
            self.logger.info("=== ДИАГНОСТИКА UI КОМПОНЕНТОВ ===")
            self.logger.info(f"Инициализированы: {diagnosis['initialized']}")
            self.logger.info(f"Компактная компоновка: {diagnosis['compact_layout']}")
            self.logger.info(f"Состояние загрузки: {diagnosis['loading']}")
            self.logger.info(f"Размер кэша: {diagnosis['cache_size']}")
            
            for name, info in diagnosis['components'].items():
                self.logger.info(f"{name}: {info['exists']} ({info['type']})")
                if name == 'parameter_panel' and info['exists']:
                    self.logger.info(f"  └─ update_parameters: {info['has_update_parameters']}")
                    self.logger.info(f"  └─ get_selected: {info['has_get_selected']}")
                    self.logger.info(f"  └─ параметров: {info['all_params_count']}")
                    self.logger.info(f"  └─ выбрано: {info['selected_count']}")

        except Exception as e:
            self.logger.error(f"Ошибка логирования диагностики: {e}")

    def force_refresh_all(self):
        """Принудительное обновление всех компонентов"""
        try:
            # Очищаем кэш
            self._ui_cache.clear()
            
            # Принудительное обновление UI
            self.root.update_idletasks()
            
            # Генерируем событие обновления
            self.emit_event('force_refresh')
            
            self.logger.info("Выполнено принудительное обновление всех компонентов")

        except Exception as e:
            self.logger.error(f"Ошибка принудительного обновления: {e}")

    def cleanup(self):
        """Очистка ресурсов UI компонентов"""
        try:
            # Очищаем все панели
            panels = [
                ('time_panel', self.time_panel),
                ('filter_panel', self.filter_panel),
                ('parameter_panel', self.parameter_panel),
                ('action_panel', self.action_panel),
                ('plot_panel', self.plot_panel)
            ]

            for panel_name, panel in panels:
                if panel and hasattr(panel, 'cleanup'):
                    try:
                        panel.cleanup()
                        self.logger.debug(f"Очищен {panel_name}")
                    except Exception as e:
                        self.logger.error(f"Ошибка очистки {panel_name}: {e}")

            # Очищаем кэш и события
            self._ui_cache.clear()
            self._event_callbacks.clear()

            # Обнуляем ссылки
            self.time_panel = None
            self.filter_panel = None
            self.parameter_panel = None
            self.action_panel = None
            self.plot_panel = None
            self.controller = None

            self.is_initialized = False

            self.logger.info("UIComponents полностью очищены")

        except Exception as e:
            self.logger.error(f"Ошибка очистки UIComponents: {e}")

    # === ДОПОЛНИТЕЛЬНЫЕ СЛУЖЕБНЫЕ МЕТОДЫ ===

    def get_component_by_name(self, name: str):
        """Получение компонента по имени"""
        components = {
            'time_panel': self.time_panel,
            'filter_panel': self.filter_panel,
            'parameter_panel': self.parameter_panel,
            'action_panel': self.action_panel,
            'plot_panel': self.plot_panel
        }
        return components.get(name)

    def is_component_ready(self, name: str) -> bool:
        """Проверка готовности компонента"""
        component = self.get_component_by_name(name)
        return component is not None and self.is_initialized

    def get_ui_state(self) -> Dict[str, Any]:
        """Получение состояния UI"""
        return {
            'initialized': self.is_initialized,
            'loading': self.is_loading,
            'compact_layout': self.use_compact_layout,
            'cache_size': len(self._ui_cache),
            'components_ready': {
                name: self.is_component_ready(name)
                for name in ['time_panel', 'filter_panel', 'parameter_panel', 'action_panel', 'plot_panel']
            }
        }

    def switch_layout_mode(self, compact: bool = True):
        """НОВЫЙ: Переключение режима компоновки"""
        try:
            if self.use_compact_layout == compact:
                self.logger.info(f"Режим компоновки уже установлен: {'компактный' if compact else 'стандартный'}")
                return

            self.use_compact_layout = compact
            self.logger.info(f"Переключение на {'компактный' if compact else 'стандартный'} режим")

            # Пересоздаем UI
            self.cleanup()
            self._setup_main_layout()
            self._create_ui_panels()
            self._setup_bindings()

            self.logger.info(f"Режим компоновки изменен на {'компактный' if compact else 'стандартный'}")

        except Exception as e:
            self.logger.error(f"Ошибка переключения режима компоновки: {e}")

    def __str__(self):
        return f"UIComponents(initialized={self.is_initialized}, compact={self.use_compact_layout}, components={sum(1 for p in [self.time_panel, self.filter_panel, self.parameter_panel, self.action_panel, self.plot_panel] if p is not None)})"

    def __repr__(self):
        return self.__str__()
