"""
Иерархия UI компонентов с базовым классом и специализированными наследниками
ИСПРАВЛЕННАЯ ВЕРСИЯ с интеграцией SmartFilterPanel
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import time
from abc import ABC, abstractmethod

class UIComponentsBase(ABC):
    """Базовый класс для всех UI компонентов"""

    def __init__(self, root: tk.Tk, controller):
        self.root = root
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Общие UI панели
        self.time_panel: Optional[Any] = None
        self.filter_panel: Optional[Any] = None
        self.parameter_panel: Optional[Any] = None
        self.action_panel: Optional[Any] = None
        self.plot_panel: Optional[Any] = None
        self.diagnostic_panel: Optional[Any] = None

        # Основные контейнеры
        self.main_content_frame: Optional[ttk.Frame] = None
        self.left_panel_frame: Optional[ttk.Frame] = None
        self.right_panel_frame: Optional[ttk.Frame] = None

        # Общее состояние UI
        self.is_initialized = False
        self.is_loading = False

        # Кэш для оптимизации обновлений
        self._ui_cache = {}
        self._last_update_time = 0

        # Callbacks для координации
        self._event_callbacks: Dict[str, List[Callable]] = {}

    @abstractmethod
    def _setup_main_layout(self):
        """Абстрактный метод настройки основного макета"""
        pass

    @abstractmethod
    def _create_ui_panels(self):
        """Абстрактный метод создания UI панелей"""
        pass

    def _setup_bindings(self):
        """Общая настройка связей между компонентами"""
        try:
            # Связь времени с параметрами
            if self.time_panel and hasattr(self.time_panel, 'on_time_range_changed'):
                self.time_panel.on_time_range_changed = self._on_time_range_changed

            # Связь между фильтрами и параметрами
            if self.filter_panel and self.parameter_panel:
                if hasattr(self.filter_panel, 'observer'):
                    # Подписываемся на изменения фильтров через Observer
                    self.filter_panel.observer.subscribe(self._on_filters_changed)

            # Связь между параметрами и действиями
            if self.parameter_panel and self.action_panel:
                if hasattr(self.parameter_panel, 'on_selection_changed'):
                    self.parameter_panel.on_selection_changed = self._on_parameter_selection_changed

            # Связь с диагностической панелью
            if self.diagnostic_panel and hasattr(self.diagnostic_panel, 'on_diagnostic_filter_changed'):
                self.diagnostic_panel.on_diagnostic_filter_changed = self._on_diagnostic_filters_changed

            self.logger.info("Связи между компонентами настроены")

        except Exception as e:
            self.logger.error(f"Ошибка настройки связей: {e}")

    def _setup_event_system(self):
        """Общая настройка системы событий"""
        try:
            event_types = [
                'parameter_updated', 'filter_changed', 'time_changed',
                'selection_changed', 'data_loaded', 'plot_created',
                'diagnostic_filter_changed'
            ]

            for event_type in event_types:
                self._event_callbacks[event_type] = []

            self.logger.info("Система событий настроена")

        except Exception as e:
            self.logger.error(f"Ошибка настройки системы событий: {e}")

    # === ОБЩИЕ ОБРАБОТЧИКИ СОБЫТИЙ ===

    def _on_filters_changed(self, filter_state):
        """Обработка изменения фильтров через SmartFilterPanel"""
        try:
            if self.controller:
                # SmartFilterPanel уже применяет фильтры через свой observer
                pass
            self.emit_event('filter_changed', filter_state.to_dict())
        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения фильтров: {e}")

    def _on_time_range_changed(self, from_time: str, to_time: str):
        """Обработка изменения временного диапазона"""
        try:
            self.logger.info(f"Временной диапазон изменен: {from_time} - {to_time}")
            self.emit_event('time_changed', {'from_time': from_time, 'to_time': to_time})
        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения времени: {e}")

    def _on_parameter_selection_changed(self, selected_count: int):
        """Обработка изменения выбора параметров"""
        try:
            if self.action_panel and hasattr(self.action_panel, 'update_action_buttons_state'):
                self.action_panel.update_action_buttons_state(selected_count > 0)

            self.emit_event('selection_changed', {'count': selected_count})
            self.logger.debug(f"Выбрано параметров: {selected_count}")
        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения выбора: {e}")

    def _on_diagnostic_filters_changed(self, diagnostic_filters: Dict[str, List[str]]):
        """Обработка изменения диагностических фильтров"""
        try:
            self.logger.info(f"Диагностические фильтры изменены: {diagnostic_filters}")
            
            if self.controller and hasattr(self.controller, 'apply_diagnostic_filters'):
                self.controller.apply_diagnostic_filters(diagnostic_filters)
            
            self.emit_event('diagnostic_filter_changed', {'filters': diagnostic_filters})
        except Exception as e:
            self.logger.error(f"Ошибка обработки диагностических фильтров: {e}")

    # === ОБЩИЕ МЕТОДЫ СОБЫТИЙ ===

    def emit_event(self, event_type: str, data: Any = None):
        """Генерация события"""
        try:
            if event_type in self._event_callbacks:
                callback_count = len(self._event_callbacks[event_type])
                if callback_count > 0:
                    self.logger.debug(f"Генерация события '{event_type}' для {callback_count} подписчиков")
                
                for callback in self._event_callbacks[event_type]:
                    try:
                        callback(data)
                    except Exception as e:
                        self.logger.error(f"Ошибка в callback {callback}: {e}")
        except Exception as e:
            self.logger.error(f"Ошибка генерации события {event_type}: {e}")

    def register_event_callback(self, event_type: str, callback: Callable):
        """Регистрация callback для события"""
        try:
            if event_type not in self._event_callbacks:
                self._event_callbacks[event_type] = []
            
            self._event_callbacks[event_type].append(callback)
            self.logger.debug(f"Зарегистрирован callback для события '{event_type}'")
        except Exception as e:
            self.logger.error(f"Ошибка регистрации callback: {e}")

    # === ОБЩИЕ ПУБЛИЧНЫЕ МЕТОДЫ ===

    def set_controller(self, controller):
        """Установка контроллера во всех панелях"""
        try:
            self.controller = controller

            panels_order = [
                ('time_panel', self.time_panel),
                ('filter_panel', self.filter_panel),
                ('parameter_panel', self.parameter_panel),
                ('action_panel', self.action_panel),
                ('diagnostic_panel', self.diagnostic_panel)
            ]

            for panel_name, panel in panels_order:
                if panel and hasattr(panel, 'set_controller'):
                    panel.set_controller(controller)
                    self.logger.debug(f"Контроллер установлен в {panel_name}")

            self.logger.info("Контроллер обновлен во всех панелях")

        except Exception as e:
            self.logger.error(f"Ошибка установки контроллера: {e}")

    def update_parameters(self, parameters: List[Dict[str, Any]]):
        """Обновление списка параметров во всех панелях"""
        try:
            self.logger.info(f"📊 UIComponents.update_parameters вызван с {len(parameters)} параметрами")

            if not self.parameter_panel:
                self.logger.error("❌ parameter_panel не создан!")
                return

            if not hasattr(self.parameter_panel, 'update_parameters'):
                self.logger.error("❌ parameter_panel не имеет метода update_parameters!")
                return

            # Обновляем панель параметров
            self.parameter_panel.update_parameters(parameters)
            self.logger.info("✅ parameter_panel.update_parameters выполнен")

            # Обновляем SmartFilterPanel
            if self.filter_panel:
                # Извлекаем уникальные типы сигналов
                signal_types = list(set(p.get('signal_type', '') for p in parameters if p.get('signal_type')))
                if hasattr(self.filter_panel, 'update_signal_type_checkboxes'):
                    self.filter_panel.update_signal_type_checkboxes(signal_types)
                    self.logger.debug(f"Обновлены типы сигналов: {len(signal_types)} элементов")

                # Извлекаем уникальные линии
                lines = list(set(p.get('line', '') for p in parameters if p.get('line')))
                if hasattr(self.filter_panel, 'update_line_checkboxes'):
                    self.filter_panel.update_line_checkboxes(lines)
                    self.logger.debug(f"Обновлены линии: {len(lines)} элементов")

                # Извлекаем номера вагонов
                wagons = list(set(str(p.get('wagon', '')) for p in parameters if p.get('wagon')))
                if hasattr(self.filter_panel, 'update_wagon_checkboxes'):
                    self.filter_panel.update_wagon_checkboxes(wagons)
                    self.logger.debug(f"Обновлены вагоны: {len(wagons)} элементов")

            # Обновляем диагностическую панель (если есть отдельная)
            if self.diagnostic_panel and hasattr(self.diagnostic_panel, 'update_parameters'):
                self.diagnostic_panel.update_parameters(parameters)
                self.logger.debug("Обновлены параметры в диагностической панели")

            # Генерируем событие
            self.emit_event('parameter_updated', {'count': len(parameters)})

            self.logger.info(f"✅ Параметры обновлены в UI: {len(parameters)} элементов")

        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления параметров: {e}")
            import traceback
            traceback.print_exc()

    def get_selected_parameters(self) -> List[Dict[str, Any]]:
        """Получение выбранных параметров"""
        try:
            if self.parameter_panel and hasattr(self.parameter_panel, 'get_selected_parameters'):
                return self.parameter_panel.get_selected_parameters()
            return []
        except Exception as e:
            self.logger.error(f"Ошибка получения выбранных параметров: {e}")
            return []

    def start_processing(self, message: str = "Обработка..."):
        """Индикация начала обработки"""
        try:
            self.is_loading = True
            
            panels = [self.time_panel, self.filter_panel, self.action_panel]
            for panel in panels:
                if panel and hasattr(panel, 'disable'):
                    panel.disable()

            if hasattr(self.root, 'config'):
                self.root.config(cursor="wait")

            self.logger.debug(f"Начата обработка: {message}")

        except Exception as e:
            self.logger.error(f"Ошибка индикации обработки: {e}")

    def stop_processing(self):
        """Завершение индикации обработки"""
        try:
            self.is_loading = False
            
            panels = [self.time_panel, self.filter_panel, self.action_panel]
            for panel in panels:
                if panel and hasattr(panel, 'enable'):
                    panel.enable()

            if hasattr(self.root, 'config'):
                self.root.config(cursor="")

            self.logger.debug("Обработка завершена")

        except Exception as e:
            self.logger.error(f"Ошибка завершения индикации обработки: {e}")

    def get_component(self, component_name: str):
        """Универсальный доступ к компонентам"""
        try:
            component_mapping = {
                'time_panel': self.time_panel,
                'filter_panel': self.filter_panel,
                'parameter_panel': self.parameter_panel,
                'action_panel': self.action_panel,
                'plot_panel': self.plot_panel,
                'diagnostic_panel': self.diagnostic_panel
            }
            
            return component_mapping.get(component_name)
            
        except Exception as e:
            self.logger.error(f"Ошибка получения компонента {component_name}: {e}")
            return None

    def cleanup(self):
        """Очистка ресурсов UI компонентов"""
        try:
            self.logger.info("Начало очистки UIComponents")

            self.stop_processing()

            panels = [
                ('diagnostic_panel', self.diagnostic_panel),
                ('plot_panel', self.plot_panel),
                ('action_panel', self.action_panel),
                ('parameter_panel', self.parameter_panel),
                ('filter_panel', self.filter_panel),
                ('time_panel', self.time_panel)
            ]

            for panel_name, panel in panels:
                if panel and hasattr(panel, 'cleanup'):
                    try:
                        panel.cleanup()
                        self.logger.debug(f"Очищен {panel_name}")
                    except Exception as e:
                        self.logger.error(f"Ошибка очистки {panel_name}: {e}")

            self._ui_cache.clear()
            self._event_callbacks.clear()

            # Обнуляем ссылки
            self.time_panel = None
            self.filter_panel = None
            self.parameter_panel = None
            self.action_panel = None
            self.plot_panel = None
            self.diagnostic_panel = None
            self.controller = None

            self.is_initialized = False

            self.logger.info("UIComponents полностью очищены")

        except Exception as e:
            self.logger.error(f"Ошибка очистки UIComponents: {e}")

    # === ОБЩИЕ FALLBACK МЕТОДЫ ===

    def _create_fallback_time_panel(self, parent):
        """Fallback создание TimePanel"""
        try:
            from .time_panel import TimePanel
            self.time_panel = TimePanel(parent, self.controller)
            self.time_panel.grid(row=0, column=0, sticky="ew")
            self.logger.info("✅ TimePanel создан (fallback)")
        except Exception as e:
            self.logger.error(f"Ошибка создания TimePanel: {e}")

    def _create_fallback_filter_panel(self, parent):
        """Fallback создание FilterPanel"""
        try:
            # Удален fallback импорт старой панели filter_panel, чтобы избежать ошибки импорта
            self.logger.warning("Fallback FilterPanel отключен, используйте SmartFilterPanel")
            # Можно добавить альтернативный код или оставить пустым
        except Exception as e:
            self.logger.error(f"Ошибка создания FilterPanel: {e}")

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

    def _create_fallback_action_panel(self, parent):
        """Fallback создание ActionPanel"""
        try:
            from .action_panel import ActionPanel
            self.action_panel = ActionPanel(parent, self.controller)
            self.action_panel.grid(row=0, column=0, sticky="ew")
            self.logger.info("✅ ActionPanel создан (fallback)")
        except Exception as e:
            self.logger.error(f"Ошибка создания ActionPanel: {e}")

class UIComponentsCompact(UIComponentsBase):
    """ИСПРАВЛЕННЫЙ компактный режим UI с интеграцией SmartFilterPanel"""

    def __init__(self, root: tk.Tk, controller):
        super().__init__(root, controller)

        # Инициализация только компактного режима
        self._setup_main_layout()
        self._create_ui_panels()
        self._setup_bindings()
        self._setup_event_system()

        self.is_initialized = True
        self.logger.info("UIComponentsCompact инициализирован с SmartFilterPanel")

    def _setup_main_layout(self):
        """Создание компактного макета приложения"""
        try:
            # Создаем PanedWindow для горизонтального разделения
            self.main_content_frame = ttk.PanedWindow(
                self.root, orient=tk.HORIZONTAL)
            self.main_content_frame.grid(
                row=1, column=0, sticky="nsew", padx=3, pady=3)
            self.root.grid_rowconfigure(1, weight=1)
            self.root.grid_columnconfigure(0, weight=1)

            # Левая панель управления (компактная)
            self.left_panel_frame = ttk.Frame(self.main_content_frame)
            self.left_panel_frame.grid_columnconfigure(0, weight=1)

            # Правая панель (для графиков)
            self.right_panel_frame = ttk.Frame(self.main_content_frame)
            self.right_panel_frame.grid_rowconfigure(0, weight=1)
            self.right_panel_frame.grid_columnconfigure(0, weight=1)

            # Добавляем панели в PanedWindow
            self.main_content_frame.add(self.left_panel_frame, weight=1)
            self.main_content_frame.add(self.right_panel_frame, weight=3)

            self.logger.info("Компактный макет создан")

        except Exception as e:
            self.logger.error(f"Ошибка создания компактного макета: {e}")
            raise

    def _create_ui_panels(self):
        """ИСПРАВЛЕННОЕ создание UI панелей с SmartFilterPanel"""
        try:
            self.logger.info("Создание компактных панелей с SmartFilterPanel")
            
            # КРИТИЧНО: Правильные веса для отображения панели параметров
            self.left_panel_frame.grid_rowconfigure(0, weight=0)  # time_panel
            self.left_panel_frame.grid_rowconfigure(1, weight=0)  # smart_filter_panel
            self.left_panel_frame.grid_rowconfigure(2, weight=1)  # parameter_panel ✅
            self.left_panel_frame.grid_rowconfigure(3, weight=0)  # action_panel

            # 1. Компактная панель времени (строка 0)
            self._create_compact_time_panel()

            # 2. НОВАЯ SmartFilterPanel (строка 1) - заменяет 3 старые панели
            self._create_smart_filter_panel()

            # 3. Горизонтальная панель параметров (строка 2) - ИСПРАВЛЕНА
            self._create_horizontal_parameter_panel()

            # 4. Горизонтальная панель действий (строка 3)
            self._create_horizontal_action_panel()

            # 5. Панель визуализации графиков
            self._create_plot_visualization_panel()

            self.logger.info("Все компактные панели созданы с SmartFilterPanel")

        except Exception as e:
            self.logger.error(f"Ошибка создания компактных панелей: {e}")
            raise

    def _create_compact_time_panel(self):
        """Создание компактной панели времени"""
        try:
            time_frame = ttk.LabelFrame(
                self.left_panel_frame,
                text="⏰ Временной диапазон",
                padding="3"
            )
            time_frame.grid(row=0, column=0, sticky="ew", pady=(0, 3))
            time_frame.grid_columnconfigure(0, weight=1)

            try:
                from .compact_time_panel import CompactTimePanel
                self.time_panel = CompactTimePanel(time_frame, self.controller)
                self.time_panel.grid(row=0, column=0, sticky="ew")
                self.logger.info("✅ CompactTimePanel создан")
            except ImportError:
                self._create_fallback_time_panel(time_frame)

        except Exception as e:
            self.logger.error(f"Ошибка создания компактной панели времени: {e}")

    def _create_smart_filter_panel(self):
        """НОВОЕ: Создание революционно компактной SmartFilterPanel"""
        try:
            filter_frame = ttk.LabelFrame(
                self.left_panel_frame,
                text="🔍 Умные фильтры",
                padding="3"
            )
            filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 3))
            filter_frame.grid_columnconfigure(0, weight=1)

            try:
                from .smart_filter_panel import SmartFilterPanel
                self.filter_panel = SmartFilterPanel(filter_frame, self.controller)
                self.filter_panel.grid(row=0, column=0, sticky="ew")
                self.logger.info("✅ SmartFilterPanel создан - заменил 3 старые панели")
            except ImportError as e:
                self.logger.warning(f"SmartFilterPanel недоступен: {e}")
                # Fallback к CompactFilterPanel
                try:
                    from .compact_filter_panel import CompactFilterPanel
                    self.filter_panel = CompactFilterPanel(filter_frame, self.controller)
                    self.filter_panel.grid(row=0, column=0, sticky="ew")
                    self.logger.info("✅ CompactFilterPanel создан (fallback)")
                except ImportError:
                    self._create_fallback_filter_panel(filter_frame)

        except Exception as e:
            self.logger.error(f"Ошибка создания SmartFilterPanel: {e}")

    def _create_horizontal_parameter_panel(self):
        """КРИТИЧНО ИСПРАВЛЕННОЕ создание панели параметров"""
        try:
            parameter_frame = ttk.LabelFrame(
                self.left_panel_frame,
                text="📊 Параметры телеметрии",
                padding="3"
            )
            parameter_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 3))
            parameter_frame.grid_columnconfigure(0, weight=1)
            parameter_frame.grid_rowconfigure(0, weight=1)

            # КРИТИЧНО: Этот вес уже установлен выше в _create_ui_panels()
            # self.left_panel_frame.grid_rowconfigure(2, weight=1)

            try:
                from .horizontal_parameter_panel import HorizontalParameterPanel
                self.parameter_panel = HorizontalParameterPanel(parameter_frame, self.controller)
                self.parameter_panel.grid(row=0, column=0, sticky="nsew")
                self.logger.info("✅ HorizontalParameterPanel создан")
            except ImportError:
                self._create_fallback_parameter_panel(parameter_frame)

            # ДОПОЛНИТЕЛЬНО: Принудительное обновление компоновки
            parameter_frame.update_idletasks()
            self.left_panel_frame.update_idletasks()

            self.logger.info("✅ Панель параметров создана с правильными весами")

        except Exception as e:
            self.logger.error(f"Ошибка создания панели параметров: {e}")

    def _create_horizontal_action_panel(self):
        """Создание горизонтальной панели действий"""
        try:
            action_frame = ttk.LabelFrame(
                self.left_panel_frame,
                text="🚀 Действия",
                padding="3"
            )
            action_frame.grid(row=3, column=0, sticky="ew", pady=(0, 3))
            action_frame.grid_columnconfigure(0, weight=1)

            try:
                from .horizontal_action_panel import HorizontalActionPanel
                self.action_panel = HorizontalActionPanel(action_frame, self.controller)
                self.action_panel.grid(row=0, column=0, sticky="ew")
                self.logger.info("✅ HorizontalActionPanel создан")
            except ImportError:
                self._create_fallback_action_panel(action_frame)

        except Exception as e:
            self.logger.error(f"Ошибка создания горизонтальной панели действий: {e}")

    def _create_plot_visualization_panel(self):
        """Создание панели визуализации графиков"""
        try:
            # Создаем заголовок для правой панели
            plot_label = ttk.Label(
                self.right_panel_frame,
                text="📊 Графики и визуализация",
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
                from .plot_visualization_panel import PlotVisualizationPanel
                self.plot_panel = PlotVisualizationPanel(plot_container, self.controller)
                self.plot_panel.grid(row=0, column=0, sticky="nsew")
                self.logger.info("✅ Панель визуализации графиков создана")
            except ImportError:
                self._create_plot_panel_placeholder(plot_container)

        except Exception as e:
            self.logger.error(f"Ошибка создания панели визуализации: {e}")

    def _create_plot_panel_placeholder(self, container):
        """Создание заглушки панели графиков"""
        placeholder_frame = ttk.Frame(container)
        placeholder_frame.grid(row=0, column=0, sticky="nsew")
        placeholder_frame.grid_rowconfigure(0, weight=1)
        placeholder_frame.grid_columnconfigure(0, weight=1)

        info_text = """📊 ПАНЕЛЬ ГРАФИКОВ
        
Здесь будут отображаться:
• Интерактивные графики телеметрии
• Визуализация выбранных параметров
• Инструменты анализа данных

Выберите параметры слева и нажмите
"Построить график" для начала работы"""

        info_label = tk.Label(
            placeholder_frame,
            text=info_text,
            font=('Arial', 11),
            justify=tk.CENTER,
            fg='#666666',
            bg='#f8f9fa'
        )
        info_label.grid(row=0, column=0, padx=20, pady=20)

    def __str__(self):
        return f"UIComponentsCompact(initialized={self.is_initialized}, smart_filter=True)"


# ОСНОВНОЙ КЛАСС ДЛЯ ИСПОЛЬЗОВАНИЯ
class UIComponents(UIComponentsCompact):
    """Главный класс UI компонентов - наследует от компактного режима с SmartFilterPanel"""
    
    def __init__(self, root: tk.Tk, controller):
        super().__init__(root, controller)
        self.logger.info("UIComponents инициализирован с SmartFilterPanel (революционный режим)")

    def __str__(self):
        return f"UIComponents(mode=smart_compact, initialized={self.is_initialized})"
