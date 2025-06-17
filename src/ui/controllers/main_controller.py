"""
Главный контроллер приложения без дублирований с приоритетной логикой изменяемых параметров
ИСПРАВЛЕННАЯ ВЕРСИЯ с поддержкой диагностических фильтров
"""
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
import time
import threading
from pathlib import Path

# Импорты Use Cases
try:
    from ...core.application.use_cases.filter_parameters_use_case import (
        FilterParametersUseCase, FilterParametersRequest,
        FindChangedParametersUseCase, FindChangedParametersRequest,
        TimeRangeInitUseCase, TimeRangeInitRequest
    )
    from ...core.application.dto.filter_dto import FilterDTO
    USE_CASES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Use Cases не доступны: {e}")
    USE_CASES_AVAILABLE = False

# НОВЫЙ ИМПОРТ: Диагностические фильтры
try:
    from ...config.diagnostic_filters_config import (
        CRITICAL_FILTERS, SYSTEM_FILTERS, FUNCTIONAL_FILTERS, COMPONENT_MAPPING
    )
    DIAGNOSTIC_FILTERS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Диагностические фильтры не доступны: {e}")
    DIAGNOSTIC_FILTERS_AVAILABLE = False


class MainController:
    """Главный контроллер приложения без дублирований с поддержкой диагностики"""

    def build_plot(self):
        """Метод для поддержки построения графиков из HorizontalActionPanel"""
        self.plot_selected_parameters()

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)



        # Текущие значения МЦД для сохранения состояния
        self._current_line_mcd = ""
        self._current_route = ""
        self._current_train = ""
        self._current_leading_unit = ""

        # Сервисы (внедряются извне)
        self.filtering_service = None
        self.plot_manager = None
        self.report_generator = None
        self.sop_manager = None

        # Use Cases (если доступны)
        self.filter_parameters_use_case: Optional[FilterParametersUseCase] = None
        self.find_changed_params_use_case: Optional[FindChangedParametersUseCase] = None
        self.time_range_init_use_case: Optional[TimeRangeInitUseCase] = None

        # UI компоненты
        self.ui_components = None

        # ЕДИНЫЙ реестр UI компонентов (устраняет все дублирования)
        self._ui_registry: Dict[str, Any] = {}
        self._ui_search_strategies: Dict[str, List[Callable]] = {}

        # Кэш для оптимизации
        self._filter_criteria_cache: Optional[Dict[str, Any]] = None
        self._last_filter_update = 0
        self._ui_update_cache: Dict[str, Any] = {}
        self._last_ui_update = 0

        # Состояние
        self.is_processing = False
        self.is_loading = False
        self.current_file_path: Optional[str] = None

        # Callbacks для UI событий
        self._ui_callbacks: Dict[str, List[Callable]] = {
            'data_loaded': [],
            'parameters_updated': [],
            'filters_applied': [],
            'time_changed': [],
            'changed_params_filter_applied': [],  # Приоритетный callback
            'diagnostic_filters_applied': [],     # НОВЫЙ: Диагностические фильтры
            'plot_requested': []                   # НОВЫЙ: Запрос на построение графиков
        }

        # Инициализация
        self._setup_use_cases()

        self.logger.info(
            "MainController инициализирован с поддержкой диагностики")

    # === МЕТОДЫ НАСТРОЙКИ ===

    def _setup_use_cases(self):
        """Настройка Use Cases"""
        if not USE_CASES_AVAILABLE:
            self.logger.warning(
                "Use Cases недоступны, используется fallback режим")
            return

        try:
            # Инициализация Use Cases если модель поддерживает
            if hasattr(self.model, 'parameter_repository') and hasattr(self.model, 'filtering_service'):
                self.filter_parameters_use_case = FilterParametersUseCase(
                    self.model.parameter_repository,
                    self.model.filtering_service
                )

            if hasattr(self.model, 'data_model'):
                self.find_changed_params_use_case = FindChangedParametersUseCase(
                    self.model.data_model
                )
                self.time_range_init_use_case = TimeRangeInitUseCase(
                    self.model.data_model
                )

            self.logger.info("Use Cases инициализированы")

        except Exception as e:
            self.logger.error(f"Ошибка инициализации Use Cases: {e}")

    def _setup_unified_ui_registry(self):
        """ЕДИНАЯ настройка реестра UI компонентов с дополнительными проверками"""
        try:
            ui_components = [
                'time_panel', 'parameter_panel', 'filter_panel',
                'action_panel', 'plot_panel', 'diagnostic_panel'
            ]

            for component_name in ui_components:
                # Настраиваем стратегии поиска
                self._setup_component_search_strategies(component_name)

                # Ищем компонент
                component = self._find_ui_component_unified(component_name)

                # Регистрируем в реестре (даже если None для отслеживания)
                self._ui_registry[component_name] = component

                if component:
                    self.logger.debug(
                        f"✅ Компонент {component_name} найден и зарегистрирован")
                else:
                    self.logger.debug(
                        f"⚠️ Компонент {component_name} не найден (возможно, еще не создан)")

            self.logger.info(
                f"Реестр UI компонентов настроен: {len([c for c in self._ui_registry.values() if c])} из {len(ui_components)} найдено")

        except Exception as e:
            self.logger.error(f"Ошибка настройки реестра UI компонентов: {e}")

    def _setup_component_search_strategies(self, component_name: str):
        """Настройка стратегий поиска для каждого компонента"""
        self._ui_search_strategies[component_name] = [
            # Стратегия 1: Через ui_components (если установлен)
            lambda name=component_name: getattr(self.view.ui_components, name, None) if hasattr(
                self.view, 'ui_components') and self.view.ui_components else None,

            # Стратегия 2: Прямой доступ через view
            lambda name=component_name: getattr(self.view, name, None),

            # Стратегия 3: Через get_component
            lambda name=component_name: self.view.get_component(
                name) if hasattr(self.view, 'get_component') else None,

            # Стратегия 4: Через приватные методы ui_components
            lambda name=component_name: getattr(self.view.ui_components, f'_{name}', None) if hasattr(
                self.view, 'ui_components') and self.view.ui_components else None,

            # Стратегия 5: Через метод _get_*
            lambda name=component_name: getattr(self.view.ui_components, f'_get_{name}', lambda: None)() if hasattr(
                self.view, 'ui_components') and self.view.ui_components and hasattr(self.view.ui_components, f'_get_{name}') else None
        ]

    # === ЕДИНАЯ СИСТЕМА ДОСТУПА К UI КОМПОНЕНТАМ ===

    def _find_ui_component_unified(self, component_name: str):
        """ЕДИНЫЙ метод поиска UI компонентов (устраняет все дублирования)"""
        try:
            strategies = self._ui_search_strategies.get(component_name, [])

            for i, strategy in enumerate(strategies):
                try:
                    component = strategy()
                    if component:
                        self.logger.debug(
                            f"Найден {component_name} через стратегию {i+1}")
                        return component
                except Exception as e:
                    self.logger.debug(
                        f"Стратегия {i+1} для {component_name} не сработала: {e}")
                    continue

            self.logger.warning(
                f"Компонент {component_name} не найден во всех стратегиях")
            return None

        except Exception as e:
            self.logger.error(
                f"Ошибка поиска компонента {component_name}: {e}")
            return None

    def get_ui_component(self, component_name: str):
        """ЕДИНЫЙ публичный метод получения UI компонента"""
        # Проверяем кэш
        if component_name in self._ui_registry:
            component = self._ui_registry[component_name]
            if component:
                return component

        # Если компонент не найден или устарел, ищем заново
        component = self._find_ui_component_unified(component_name)
        self._ui_registry[component_name] = component
        return component

    def refresh_ui_registry(self):
        """Обновление реестра UI компонентов с проверками"""
        try:
            self.logger.info("Обновление реестра UI компонентов")
            self._ui_registry.clear()

            # КРИТИЧЕСКАЯ ПРОВЕРКА: UI компоненты должны быть созданы
            if not hasattr(self.view, 'ui_components') or not self.view.ui_components:
                self.logger.debug(
                    "UI компоненты еще не созданы, пропускаем инициализацию реестра")
                return

            # Проверяем, что ui_components инициализирован
            if not hasattr(self.view.ui_components, 'is_initialized') or not self.view.ui_components.is_initialized:
                self.logger.debug(
                    "UI компоненты не полностью инициализированы, пропускаем")
                return

            self._setup_unified_ui_registry()
            self.logger.info("Реестр UI компонентов успешно обновлен")

        except Exception as e:
            self.logger.error(f"Ошибка обновления реестра UI: {e}")

    def delayed_refresh_ui_registry(self, delay_ms: int = 100):
        """Отложенное обновление реестра UI компонентов"""
        try:
            def refresh_after_delay():
                try:
                    self.refresh_ui_registry()
                except Exception as e:
                    self.logger.error(
                        f"Ошибка отложенного обновления реестра: {e}")

            # Планируем обновление через указанное время
            if hasattr(self.view, 'root') and self.view.root:
                self.view.root.after(delay_ms, refresh_after_delay)
                self.logger.debug(
                    f"Запланировано отложенное обновление реестра через {delay_ms}мс")
            else:
                # Fallback - обновляем сразу
                refresh_after_delay()
                self.logger.debug(
                    "Выполнено немедленное обновление реестра (fallback)")

        except Exception as e:
            self.logger.error(
                f"Ошибка планирования отложенного обновления: {e}")

    # === МЕТОДЫ ДЛЯ ВНЕДРЕНИЯ СЕРВИСОВ ===

    def set_filtering_service(self, service):
        """Установка сервиса фильтрации"""
        self.filtering_service = service
        self.logger.info("Фильтрационный сервис установлен")

    def set_plot_manager(self, service):
        """Установка менеджера графиков"""
        self.plot_manager = service
        self.logger.info("PlotManager установлен")

    def set_report_generator(self, service):
        """Установка генератора отчетов"""
        self.report_generator = service
        self.logger.info("ReportGenerator установлен")

    def set_report_manager(self, service):
        """Установка менеджера отчетов (алиас для совместимости)"""
        self.set_report_generator(service)

    def set_ui_components(self, ui_components):
        """Установка UI компонентов с автоматическим обновлением реестра"""
        try:
            self.ui_components = ui_components

            # Ждем полной инициализации UI компонентов
            if hasattr(ui_components, 'is_initialized') and ui_components.is_initialized:
                # Обновляем реестр после установки новых компонентов
                self.refresh_ui_registry()
                self.logger.info("UIComponents установлен и реестр обновлен")
                # Настраиваем синхронизацию changed_only между time_panel и filter_panel
                self._setup_changed_only_sync()
            else:
                self.logger.info(
                    "UIComponents установлен, ожидание полной инициализации")

        except Exception as e:
            self.logger.error(f"Ошибка установки UI компонентов: {e}")

    def _setup_changed_only_sync(self):
        """Настройка двунаправленной синхронизации changed_only между time_panel и filter_panel"""
        try:
            time_panel = self.get_ui_component('time_panel')
            filter_panel = self.get_ui_component('filter_panel')

            if not time_panel or not filter_panel:
                self.logger.warning(
                    "Не найдены time_panel или filter_panel для синхронизации changed_only")
                return

            # Callback для изменения changed_only в time_panel
            def on_time_panel_changed_only_toggled(is_enabled: bool):
                try:
                    self.logger.info(
                        f"Событие changed_only из time_panel: {is_enabled}")
                    if hasattr(filter_panel, 'sync_changed_only_state'):
                        filter_panel.sync_changed_only_state(is_enabled)
                    else:
                        self.logger.warning(
                            "filter_panel не имеет метода sync_changed_only_state")
                except Exception as e:
                    self.logger.error(
                        f"Ошибка в on_time_panel_changed_only_toggled: {e}")

            # Устанавливаем callback в time_panel
            if hasattr(time_panel, 'on_changed_only_toggle'):
                time_panel.on_changed_only_toggle = on_time_panel_changed_only_toggled
                self.logger.info(
                    "Установлен callback on_changed_only_toggle в time_panel")
            else:
                self.logger.warning(
                    "time_panel не имеет атрибута on_changed_only_toggle")

            # Подписка на изменения changed_only в filter_panel через observer
            if hasattr(filter_panel, 'observer') and hasattr(filter_panel.observer, 'subscribe'):
                def on_filter_panel_state_changed(state):
                    try:
                        if hasattr(state, 'changed_only'):
                            is_enabled = state.changed_only
                        elif isinstance(state, dict) and 'changed_only' in state:
                            is_enabled = state['changed_only']
                        else:
                            return
                        self.logger.info(
                            f"Событие changed_only из filter_panel: {is_enabled}")
                        # Обновляем changed_only_var в time_panel
                        if hasattr(time_panel, 'changed_only_var'):
                            current = time_panel.changed_only_var.get()
                            if current != is_enabled:
                                time_panel.changed_only_var.set(is_enabled)
                    except Exception as e:
                        self.logger.error(
                            f"Ошибка в on_filter_panel_state_changed: {e}")

                filter_panel.observer.subscribe(on_filter_panel_state_changed)
                self.logger.info(
                    "Подписка на observer filter_panel для changed_only установлена")
            else:
                self.logger.warning(
                    "filter_panel не имеет observer с методом subscribe")

        except Exception as e:
            self.logger.error(
                f"Ошибка настройки синхронизации changed_only: {e}")

    def set_sop_manager(self, service):
        """Установка менеджера SOP"""
        self.sop_manager = service
        self.logger.info("SOPManager установлен")

    # === МЕТОДЫ ПОЛУЧЕНИЯ ПАРАМЕТРОВ ===

    def _get_selected_parameters_unified(self) -> List[Dict[str, Any]]:
        """ЕДИНЫЙ метод получения выбранных параметров"""
        try:
            # Способ 1: Через parameter_panel
            parameter_panel = self.get_ui_component('parameter_panel')
            if parameter_panel:
                if hasattr(parameter_panel, 'get_selected_parameters'):
                    selected = parameter_panel.get_selected_parameters()
                    if selected:
                        self.logger.debug(
                            f"Получено {len(selected)} выбранных параметров через parameter_panel")
                        return selected
                elif hasattr(parameter_panel, 'get_checked_parameters'):
                    selected = parameter_panel.get_checked_parameters()
                    if selected:
                        self.logger.debug(
                            f"Получено {len(selected)} выбранных параметров через get_checked_parameters")
                        return selected

            # Способ 2: Через view
            if hasattr(self.view, 'get_selected_parameters'):
                selected = self.view.get_selected_parameters()
                if selected:
                    self.logger.debug(
                        f"Получено {len(selected)} выбранных параметров через view")
                    return selected

            # Способ 3: Через ui_components
            if (hasattr(self.view, 'ui_components') and
                self.view.ui_components and
                    hasattr(self.view.ui_components, 'get_selected_parameters')):
                selected = self.view.ui_components.get_selected_parameters()
                if selected:
                    self.logger.debug(
                        f"Получено {len(selected)} выбранных параметров через ui_components")
                    return selected

            self.logger.warning("Не удалось получить выбранные параметры")
            return []

        except Exception as e:
            self.logger.error(f"Ошибка получения выбранных параметров: {e}")
            return []

    def get_selected_parameters(self) -> List[Dict[str, Any]]:
        """ПУБЛИЧНЫЙ метод для внешнего доступа к выбранным параметрам"""
        return self._get_selected_parameters_unified()

    def _get_all_parameters(self) -> List[Dict[str, Any]]:
        """Получение всех параметров"""
        try:
            if hasattr(self.model, 'get_all_parameters'):
                params = self.model.get_all_parameters()
            elif hasattr(self.model, 'data_loader') and hasattr(self.model.data_loader, 'get_parameters'):
                params = self.model.data_loader.get_parameters()
            else:
                self.logger.warning("Не удалось получить параметры из модели")
                return []

            # Преобразуем в словари если нужно
            if params and hasattr(params[0], 'to_dict'):
                return [param.to_dict() for param in params]
            return params or []

        except Exception as e:
            self.logger.error(f"Ошибка получения всех параметров: {e}")
            return []

    # === МЕТОДЫ РАБОТЫ СО ВРЕМЕНЕМ ===

    def _get_time_range_unified(self) -> Tuple[str, str]:
        """ЕДИНЫЙ метод получения временного диапазона"""
        try:
            # Способ 1: Через time_panel
            time_panel = self.get_ui_component('time_panel')
            if time_panel and hasattr(time_panel, 'get_time_range'):
                result = time_panel.get_time_range()
                if result[0] and result[1]:
                    self.logger.debug(
                        f"Время получено через time_panel: {result}")
                    return result

            # Способ 2: Через модель данных
            if hasattr(self.model, 'get_time_range_fields'):
                time_fields = self.model.get_time_range_fields()
                if time_fields and time_fields.get('from_time') and time_fields.get('to_time'):
                    result = (time_fields['from_time'], time_fields['to_time'])
                    self.logger.debug(f"Время получено через модель: {result}")
                    return result

            # Способ 3: Через data_loader
            if (hasattr(self.model, 'data_loader') and
                self.model.data_loader and
                hasattr(self.model.data_loader, 'min_timestamp') and
                    hasattr(self.model.data_loader, 'max_timestamp')):

                result = (self.model.data_loader.min_timestamp,
                          self.model.data_loader.max_timestamp)
                if result[0] and result[1]:
                    self.logger.debug(
                        f"Время получено через data_loader: {result}")
                    return result

            # Fallback - текущее время
            now = datetime.now()
            start = now - timedelta(hours=1)
            result = (
                start.strftime('%Y-%m-%d %H:%M:%S'),
                now.strftime('%Y-%m-%d %H:%M:%S')
            )
            self.logger.warning(f"Использовано fallback время: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Ошибка получения временного диапазона: {e}")
            return ("", "")

    def get_time_range(self) -> Tuple[str, str]:
        """Публичный метод получения временного диапазона"""
        return self._get_time_range_unified()

    def update_time_range(self, from_time: str, to_time: str):
        """Обновление временного диапазона"""
        try:
            self.logger.info(
                f"Обновление временного диапазона: {from_time} - {to_time}")

            # Валидация времени
            if not self._validate_time_range(from_time, to_time):
                return False

            # Обновляем в time_panel
            time_panel = self.get_ui_component('time_panel')
            if time_panel:
                if hasattr(time_panel, 'set_time_range'):
                    time_panel.set_time_range(from_time, to_time)
                    self.logger.info(
                        "Временной диапазон обновлен в time_panel")
                elif hasattr(time_panel, 'update_time_fields'):
                    time_panel.update_time_fields(
                        from_time=from_time, to_time=to_time)
                    self.logger.info(
                        "Временной диапазон обновлен через update_time_fields")

            # Уведомляем о изменении времени
            self._emit_event('time_changed', {
                'from_time': from_time,
                'to_time': to_time
            })

            # Синхронизируем фильтры с панелью времени
            self._sync_with_time_panel()

            return True

        except Exception as e:
            self.logger.error(f"Ошибка обновления временного диапазона: {e}")
            return False

    def reset_time_range(self):
        """Сброс временного диапазона к значениям по умолчанию"""
        try:
            if self._has_data():
                # Используем диапазон из данных
                time_fields = self._get_time_fields_from_model(
                ) or self._get_time_fields_from_data_loader()
                if time_fields:
                    self.update_time_range(
                        time_fields['from_time'], time_fields['to_time'])
                    self.logger.info(
                        "Временной диапазон сброшен к значениям из данных")
                    return True

            # Fallback - текущее время
            now = datetime.now()
            start = now - timedelta(hours=1)
            self.update_time_range(
                start.strftime('%Y-%m-%d %H:%M:%S'),
                now.strftime('%Y-%m-%d %H:%M:%S')
            )
            self.logger.info("Временной диапазон сброшен к текущему времени")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка сброса временного диапазона: {e}")
            return False

    def _get_time_fields_from_model(self) -> Optional[Dict[str, str]]:
        """Получение временных полей из модели"""
        try:
            if hasattr(self.model, 'get_time_range_fields'):
                return self.model.get_time_range_fields()
            return None
        except Exception as e:
            self.logger.error(
                f"Ошибка получения временных полей из модели: {e}")
            return None

    def _get_time_fields_from_data_loader(self) -> Optional[Dict[str, str]]:
        """Получение временных полей из data_loader"""
        try:
            if (hasattr(self.model, 'data_loader') and
                self.model.data_loader and
                hasattr(self.model.data_loader, 'min_timestamp') and
                    hasattr(self.model.data_loader, 'max_timestamp')):
                return {
                    'from_time': self.model.data_loader.min_timestamp,
                    'to_time': self.model.data_loader.max_timestamp
                }
            return None
        except Exception as e:
            self.logger.error(
                f"Ошибка получения временных полей из data_loader: {e}")
            return None

    def _validate_time_range(self, from_time: str, to_time: str) -> bool:
        """Валидация временного диапазона"""
        try:
            start = datetime.strptime(from_time, '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(to_time, '%Y-%m-%d %H:%M:%S')

            if start >= end:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(
                        "Время начала должно быть меньше времени окончания")
                return False

            return True

        except ValueError as e:
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Неверный формат времени: {e}")
            return False

    def apply_diagnostic_filters(self, diagnostic_criteria: Dict[str, List[str]]):
        """Применение диагностических фильтров с использованием конфигурации"""
        try:
            self.logger.info(
                f"Применение диагностических фильтров: {diagnostic_criteria}")

            if not self._has_data():
                self.logger.warning(
                    "Нет данных для диагностической фильтрации")
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning(
                        "Нет данных для диагностического анализа")
                return

            all_params = self._get_all_parameters()

            # Используем конфигурацию из diagnostic_filters_config.py
            from src.config.diagnostic_filters_config import CRITICAL_FILTERS, SYSTEM_FILTERS, FUNCTIONAL_FILTERS

            def matches_patterns(param, patterns):
                text = f"{param.get('signal_code', '').upper()} {param.get('description', '').upper()}"
                return any(pat in text for pat in patterns)

            filtered = []

            for param in all_params:
                match = False

                # Проверка критичности
                for crit_key in diagnostic_criteria.get('criticality', []):
                    crit_conf = CRITICAL_FILTERS.get(crit_key)
                    if crit_conf and matches_patterns(param, crit_conf['patterns']):
                        match = True
                        break

                # Проверка систем
                if not match:
                    for sys_key in diagnostic_criteria.get('systems', []):
                        sys_conf = SYSTEM_FILTERS.get(sys_key)
                        if sys_conf and matches_patterns(param, sys_conf['patterns']):
                            match = True
                            break

                # Проверка функций
                if not match:
                    for func_key in diagnostic_criteria.get('functions', []):
                        func_conf = FUNCTIONAL_FILTERS.get(func_key)
                        if func_conf and matches_patterns(param, func_conf['patterns']):
                            match = True
                            break

                if match:
                    filtered.append(param)

            self._update_ui_with_filtered_params(filtered)
            self._emit_event('diagnostic_filters_applied', {
                'count': len(filtered),
                'criteria': diagnostic_criteria
            })

            self.logger.info(
                f"Диагностическая фильтрация завершена: {len(filtered)} параметров")

        except Exception as e:
            self.logger.error(
                f"Ошибка применения диагностических фильтров: {e}")

    def reset_diagnostic_filters(self):
        """Сброс диагностических фильтров и показ всех параметров"""
        try:
            self.logger.info("Сброс диагностических фильтров")

            if self._has_data():
                all_params = self._get_all_parameters()
                self._update_ui_with_filtered_params(all_params)

            self._emit_event('diagnostic_filters_applied', {
                'count': 0,
                'criteria': {}
            })

            self.logger.info("Диагностические фильтры сброшены")

        except Exception as e:
            self.logger.error(f"Ошибка сброса диагностических фильтров: {e}")

    def perform_diagnostic_analysis(self):
        """Выполнение диагностического анализа с использованием конфигурации"""
        try:
            self.logger.info("Выполнение диагностического анализа")

            if not self._has_data():
                self.logger.warning("Нет данных для диагностического анализа")
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning("Нет данных для анализа")
                return

            all_params = self._get_all_parameters()

            critical_faults = []
            systems_status = {}
            recommendations = []

            from src.config.diagnostic_filters_config import CRITICAL_FILTERS, COMPONENT_MAPPING

            # Анализ критичных неисправностей
            for param in all_params:
                text = f"{param.get('signal_code', '').upper()} {param.get('description', '').upper()}"
                for crit_key, crit_conf in CRITICAL_FILTERS.items():
                    if any(pat in text for pat in crit_conf['patterns']):
                        critical_faults.append(param.get('signal_code', ''))
                        break

            # Анализ состояния систем (пример)
            for sys_key in SYSTEM_FILTERS.keys():
                count_faults = sum(
                    1 for param in all_params
                    if any(pat in f"{param.get('signal_code', '').upper()} {param.get('description', '').upper()}"
                           for pat in SYSTEM_FILTERS[sys_key]['patterns'])
                )
                systems_status[sys_key] = {
                    'fault_count': count_faults,
                    'status': 'critical' if count_faults > 0 else 'normal'
                }

            # Формирование рекомендаций (пример)
            if critical_faults:
                recommendations.append(
                    "Проверьте критичные неисправности и примите меры.")
            else:
                recommendations.append("Система работает в нормальном режиме.")

            results = {
                'total_parameters': len(all_params),
                'critical_faults': critical_faults,
                'systems_status': systems_status,
                'recommendations': recommendations,
                'overall_status': 'critical' if critical_faults else 'normal',
                'timestamp': datetime.now().isoformat()
            }

            # Отображение результатов через view
            if hasattr(self.view, 'show_info'):
                message = f"Диагностический анализ завершен. Статус: {results['overall_status'].upper()}"
                self.view.show_info("Диагностический анализ", message)

            self._emit_event('diagnostic_analysis_completed', results)
            self.logger.info(
                f"Диагностический анализ завершен: {results['overall_status']}")

        except Exception as e:
            self.logger.error(f"Ошибка диагностического анализа: {e}")

    # Добавляем недостающие методы в MainController:
    def _matches_criticality_filter(self, signal_code: str, description: str, filter_type: str) -> bool:
        """ИНТЕГРАЦИЯ: Проверка соответствия фильтру критичности"""
        combined_text = f"{signal_code} {description}".upper()

        critical_patterns = {
            'emergency': ['FAULT', 'FAIL', 'EMERGENCY', 'ALARM', 'BCU_FAULT', 'EB_TRAINLINE'],
            'safety': ['WSP_FAULT', 'R_PRESSURE_LOW', 'DIRECT_BRAKE_FAULT', 'ERRC1_CODE_44'],
            'power_critical': ['KPSN175_GENERAL_ERR', 'IGBTSTATUS', 'FAIL_POWER'],
            'brake_critical': ['BCU_', 'BRAKE_', 'PRESSURE_', 'SLIDING_']
        }

        patterns = critical_patterns.get(filter_type, [])
        return any(pattern in combined_text for pattern in patterns)

    def _matches_system_filter(self, signal_code: str, description: str, filter_type: str) -> bool:
        """ИНТЕГРАЦИЯ: Проверка соответствия системному фильтру"""
        system_patterns = {
            'traction': ['PST_', 'INV', 'TRACTION_', 'MOTOR_', 'EFFORT_'],
            'brakes': ['BCU_', 'BRAKE_', 'PRESSURE_', 'SLIDING_'],
            'doors': ['BUD', 'DOOR_', 'HINDRANCE'],
            'power': ['PSN_', 'QF', 'VOLTAGE', 'CURRENT', 'KPSN'],
            'climate': ['SOM_', 'KSK_', 'GOR_', 'TEMP'],
            'info_systems': ['BIM', 'BUIK_', 'ANNOUNCEMENT'],
            'communication': ['BST_', 'RADIO_', 'GSM_', 'ETHERNET_']
        }

        patterns = system_patterns.get(filter_type, [])
        return any(pattern in signal_code.upper() for pattern in patterns)

    def _matches_function_filter(self, signal_code: str, description: str, filter_type: str) -> bool:
        """ИНТЕГРАЦИЯ: Проверка соответствия функциональному фильтру"""
        combined_text = f"{signal_code} {description}".upper()

        function_patterns = {
            'faults': ['FAULT', 'FAIL', 'ERROR', 'ERR_', 'ERRC1_'],
            'measurements': ['TEMP', 'PRESSURE', 'VOLTAGE', 'CURRENT', 'SPEED'],
            'states': ['STATE', 'STATUS', 'MODE', 'READY', 'OK', 'ISCLOSED', 'ISOPENED'],
            'controls': ['CTRL', 'COMMAND', 'SET', 'RESET', 'ENABLE'],
            'diagnostics': ['HEARTBEAT', 'VERSION', 'AVAIL', 'CONNECT', 'CALC_RDY']
        }

        patterns = function_patterns.get(filter_type, [])
        return any(pattern in combined_text for pattern in patterns)

    def _update_parameter_display(self, parameters: List[Dict[str, Any]]):
        """ИНТЕГРАЦИЯ: Обновление отображения параметров"""
        try:
            self._update_ui_with_filtered_params(parameters)
            self.logger.debug(
                f"Отображение параметров обновлено: {len(parameters)}")
        except Exception as e:
            self.logger.error(f"Ошибка обновления отображения параметров: {e}")

    def _simple_diagnostic_filter(self, parameters: List[Dict[str, Any]],
                                  criteria: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Простая диагностическая фильтрация без конфигурационных файлов"""
        try:
            filtered = []

            # Простые паттерны для диагностики
            diagnostic_patterns = {
                'critical': ['EMERGENCY', 'FAULT', 'FAIL', 'ERROR', 'ALARM'],
                'faults': ['FAULT', 'FAIL', 'ERROR', 'ERR_'],
                'diagnostics': ['DIAG', 'STATUS', 'HEARTBEAT', 'VERSION']
            }

            for param in parameters:
                signal_code = param.get('signal_code', '').upper()
                description = param.get('description', '').upper()

                matches = False

                for category, patterns in diagnostic_patterns.items():
                    if category in criteria.get('functions', []) or category in criteria.get('criticality', []):
                        if any(pattern in signal_code or pattern in description for pattern in patterns):
                            matches = True
                            break

                if matches:
                    filtered.append(param)

            return filtered

        except Exception as e:
            self.logger.error(
                f"Ошибка простой диагностической фильтрации: {e}")
            return parameters

    def reset_diagnostic_filters(self):
        """НОВЫЙ МЕТОД: Сброс диагностических фильтров"""
        try:
            self.logger.info("Сброс диагностических фильтров")

            # Показываем все параметры
            if self._has_data():
                all_params = self._get_all_parameters()
                self._update_ui_with_filtered_params(all_params)

            self.logger.info("Диагностические фильтры сброшены")

        except Exception as e:
            self.logger.error(f"Ошибка сброса диагностических фильтров: {e}")

    def perform_diagnostic_analysis(self):
        """НОВЫЙ МЕТОД: Выполнение диагностического анализа"""
        try:
            self.logger.info("Выполнение диагностического анализа")

            if not self._has_data():
                self.logger.warning("Нет данных для диагностического анализа")
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning("Нет данных для анализа")
                return

            # Получаем все параметры
            all_params = self._get_all_parameters()

            # Ищем критичные параметры
            critical_params = []
            fault_params = []

            for param in all_params:
                signal_code = param.get('signal_code', '').upper()
                description = param.get('description', '').upper()

                # Проверяем на критичные паттерны
                critical_patterns = ['EMERGENCY', 'FAULT',
                                     'FAIL', 'ERR_', 'ALARM', 'FIRE']
                if any(pattern in signal_code or pattern in description for pattern in critical_patterns):
                    critical_params.append(param)

                # Проверяем на ошибки
                fault_patterns = ['FAULT', 'FAIL', 'ERROR', 'ERR_']
                if any(pattern in signal_code or pattern in description for pattern in fault_patterns):
                    fault_params.append(param)

            # Формируем результаты анализа
            analysis_results = {
                'total_parameters': len(all_params),
                'critical_count': len(critical_params),
                'fault_count': len(fault_params),
                'critical_parameters': [p.get('signal_code', '') for p in critical_params[:10]],
                'fault_parameters': [p.get('signal_code', '') for p in fault_params[:10]],
                'overall_status': 'critical' if critical_params else ('warning' if fault_params else 'healthy'),
                'timestamp': datetime.now().isoformat()
            }

            # Показываем результаты
            self._show_diagnostic_results(analysis_results)

            self.logger.info(
                f"Диагностический анализ завершен: {analysis_results['overall_status']}")

        except Exception as e:
            self.logger.error(f"Ошибка диагностического анализа: {e}")

    def _show_diagnostic_results(self, results: Dict[str, Any]):
        """НОВЫЙ МЕТОД: Показ результатов диагностического анализа"""
        try:
            if hasattr(self.view, 'show_info'):
                message = f"""РЕЗУЛЬТАТЫ ДИАГНОСТИЧЕСКОГО АНАЛИЗА

                        Общий статус: {results['overall_status'].upper()}

                        Всего параметров: {results['total_parameters']}
                        Критичных: {results['critical_count']}
                        С ошибками: {results['fault_count']}

                        Критичные параметры:
                        {chr(10).join(results['critical_parameters'][:5])}

                        Параметры с ошибками:
                        {chr(10).join(results['fault_parameters'][:5])}"""

                self.view.show_info("Диагностический анализ", message)

        except Exception as e:
            self.logger.error(f"Ошибка показа результатов анализа: {e}")

    # === МЕТОДЫ ЗАГРУЗКИ CSV ===

    def upload_csv(self):
        """Загрузка CSV файла через диалог выбора"""
        try:
            from tkinter import filedialog

            file_path = filedialog.askopenfilename(
                title="Выберите CSV файл",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ]
            )

            if file_path:
                self.load_csv_file(file_path)
            else:
                self.logger.info("Загрузка файла отменена пользователем")

        except Exception as e:
            self.logger.error(f"Ошибка выбора CSV файла: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка выбора файла: {e}")

    def load_csv_file(self, file_path: str):
        """Загрузка CSV файла"""
        try:
            self.logger.info(f"Начало загрузки CSV файла: {file_path}")

            if self.is_loading:
                self.logger.warning("Загрузка уже выполняется")
                return

            self._start_loading("Загрузка CSV файла...")
            self.current_file_path = file_path

            def load_file():
                try:
                    success = self._load_csv_file(file_path)
                    if hasattr(self.view, 'root'):
                        self.view.root.after(
                            0, lambda: self._handle_file_load_result(success, file_path))
                except Exception as e:
                    self.logger.error(f"Ошибка в потоке загрузки: {e}")
                    if hasattr(self.view, 'root'):
                        self.view.root.after(
                            0, lambda: self._handle_file_load_error(e))

            thread = threading.Thread(target=load_file, daemon=True)
            thread.start()

        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV файла: {e}")
            self._stop_loading()

    def _load_csv_file(self, file_path: str) -> bool:
        """Внутренний метод загрузки CSV файла"""
        try:
            # Проверяем существование файла
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Файл не найден: {file_path}")

            # Загружаем через модель
            if hasattr(self.model, 'load_csv'):
                success = self.model.load_csv(file_path)
            elif hasattr(self.model, 'data_loader') and hasattr(self.model.data_loader, 'load_csv'):
                success = self.model.data_loader.load_csv(file_path)
            else:
                raise AttributeError("Модель не поддерживает загрузку CSV")

            if success:
                self.logger.info(f"CSV файл успешно загружен: {file_path}")
                return True
            else:
                self.logger.error(
                    f"Не удалось загрузить CSV файл: {file_path}")
                return False

        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV файла {file_path}: {e}")
            raise

    def _handle_file_load_result(self, success: bool, file_path: str):
        """ИСПРАВЛЕННАЯ обработка результата загрузки файла с передачей данных в DataModel"""
        try:
            self._stop_loading()

            if success:
                self.logger.info(f"Файл успешно загружен: {file_path}")

                # Получаем количество записей и параметров
                records_count = getattr(self.model.data_loader, 'records_count', 0) if hasattr(
                    self.model, 'data_loader') else 0
                all_params = self._get_all_parameters()
                params_count = len(all_params)

                # КРИТИЧНО: Извлекаем МЦД информацию
                mcd_info = None
                if hasattr(self.model, 'data_loader') and self.model.data_loader:
                    mcd_info = self.model.data_loader.extract_and_update_mcd_info(
                        file_path)
                    self.logger.info(
                        f"🔍 МЦД информация из data_loader: {mcd_info}")

                # ПРИНУДИТЕЛЬНО обновляем информационную панель с МЦД данными
                file_name = Path(file_path).name

                if mcd_info and hasattr(self.view, 'update_telemetry_info'):
                    self.logger.info(
                        f"🔄 Передача в update_telemetry_info: file_name={file_name}, params_count={params_count}, selected_count=0, mcd_info={mcd_info}")
                    self.view.update_telemetry_info(
                        file_name=file_name,
                        params_count=params_count,
                        selected_count=0,
                        line_mcd=mcd_info.get('line_mcd', ''),
                        route=mcd_info.get('route', ''),
                        train=mcd_info.get('train', ''),
                        leading_unit=mcd_info.get('leading_unit', '')
                    )
                    self.logger.info(
                        f"✅ Панель обновлена с МЦД: МЦД-{mcd_info.get('line_mcd')}, маршрут {mcd_info.get('route')}, состав {mcd_info.get('train')}, вагон {mcd_info.get('leading_unit')}")

                    # Принудительно обновляем root для отображения изменений
                    if hasattr(self.view, 'root'):
                        self.view.root.update_idletasks()

                else:
                    self.logger.warning(
                        "❌ МЦД информация не найдена или метод update_telemetry_info недоступен")
                    if hasattr(self.view, 'update_telemetry_info'):
                        self.view.update_telemetry_info(
                            file_name=file_name,
                            params_count=params_count,
                            selected_count=0
                        )

                # КРИТИЧНО: Передаем данные в DataModel
                if hasattr(self.model, 'data_model') and self.model.data_model:
                    # Передаем телеметрические данные
                    if (hasattr(self.model, 'data_loader') and
                        self.model.data_loader and
                            hasattr(self.model.data_loader, 'data')):

                        telemetry_data = self.model.data_loader.data
                        if telemetry_data is not None and not telemetry_data.empty:
                            if hasattr(self.model.data_model, 'set_telemetry_data'):
                                self.model.data_model.set_telemetry_data(
                                    telemetry_data)
                                self.logger.info(
                                    f"✅ Телеметрия передана в DataModel: {len(telemetry_data)} записей")
                            elif hasattr(self.model.data_model, 'load_data'):
                                self.model.data_model.load_data(telemetry_data)
                                self.logger.info(
                                    f"✅ Данные загружены в DataModel: {len(telemetry_data)} записей")

                    # Передаем параметры
                    if all_params:
                        if hasattr(self.model.data_model, 'set_parameters_for_analysis'):
                            self.model.data_model.set_parameters_for_analysis(
                                all_params)
                            self.logger.info(
                                f"✅ Параметры переданы в DataModel: {len(all_params)}")
                        elif hasattr(self.model.data_model, 'load_parameters'):
                            self.model.data_model.load_parameters(all_params)
                            self.logger.info(
                                f"✅ Параметры загружены в DataModel: {len(all_params)}")

                # Остальная логика...
                self._update_ui_after_data_load()

                # Уведомляем о загрузке данных
                self._emit_event('data_loaded', {
                    'file_path': file_path,
                    'records_count': records_count,
                    'mcd_info': mcd_info,
                    'timestamp': datetime.now()
                })

                if hasattr(self.view, 'show_info'):
                    self.view.show_info(
                        "Загрузка", f"Файл загружен: {Path(file_path).name}")

            else:
                self.logger.error(f"Не удалось загрузить файл: {file_path}")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(
                        f"Не удалось загрузить файл: {Path(file_path).name}")

        except Exception as e:
            self.logger.error(f"Ошибка обработки результата загрузки: {e}")

    def _handle_file_load_error(self, error: Exception):
        """Обработка ошибки загрузки файла"""
        try:
            self._stop_loading()
            self.logger.error(f"Ошибка загрузки файла: {error}")

            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка загрузки файла: {error}")

        except Exception as e:
            self.logger.error(f"Ошибка обработки ошибки загрузки: {e}")

    def _update_ui_after_data_load(self):
        """ИСПРАВЛЕННОЕ обновление UI после загрузки данных с обновлением SmartFilterPanel"""
        try:
            # Инициализируем временной диапазон
            self._init_time_range_after_load()

            # Загружаем все параметры
            all_params = self._get_all_parameters()

            # КРИТИЧНО: Обновляем SmartFilterPanel с данными из CSV
            self._update_smart_filter_panel_with_data(all_params)

            # Остальная логика...
            self._update_ui_with_filtered_params(all_params)

            self.logger.info(
                f"UI обновлен после загрузки данных: {len(all_params)} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка обновления UI после загрузки: {e}")

    def _update_smart_filter_panel_with_data(self, parameters: List[Dict[str, Any]]):
        """ИСПРАВЛЕННОЕ обновление SmartFilterPanel с данными из CSV"""
        try:
            filter_panel = self.get_ui_component('filter_panel')
            if not filter_panel:
                self.logger.warning("SmartFilterPanel не найден")
                return

            # Извлекаем уникальные типы сигналов
            signal_types = list(
                set(param.get('signal_type', 'Unknown') for param in parameters))
            signal_types = [
                st for st in signal_types if st and st != 'Unknown']

            # Извлекаем уникальные линии
            lines = list(set(param.get('line', 'Unknown')
                         for param in parameters))
            lines = [line for line in lines if line and line != 'Unknown']

            # КРИТИЧНО: Извлекаем реальные номера вагонов
            wagons = list(set(param.get('wagon', 'Unknown')
                          for param in parameters))
            wagons = [str(wagon)
                      for wagon in wagons if wagon and str(wagon) != 'Unknown']

            # КРИТИЧНО: Сортируем для стабильного отображения
            signal_types = sorted(signal_types)
            lines = sorted(lines)
            wagons = sorted(wagons)

            self.logger.info(f"📡 Найдено данных для SmartFilterPanel:")
            self.logger.info(f"   📊 Типы сигналов: {len(signal_types)}")
            self.logger.info(f"   📡 Линии: {len(lines)}")
            self.logger.info(f"   🚃 Вагоны: {wagons}")

            # Обновляем SmartFilterPanel
            if hasattr(filter_panel, 'update_signal_type_checkboxes'):
                filter_panel.update_signal_type_checkboxes(signal_types)
                self.logger.info(
                    "✅ Типы сигналов обновлены в SmartFilterPanel")

            if hasattr(filter_panel, 'update_line_checkboxes'):
                filter_panel.update_line_checkboxes(lines)
                self.logger.info("✅ Линии обновлены в SmartFilterPanel")

            # ВАЖНО: Вагоны обновляются отдельно с учетом маппинга
            if hasattr(filter_panel, 'update_wagon_checkboxes'):
                filter_panel.update_wagon_checkboxes(wagons)
                self.logger.info(
                    "✅ Вагоны обновлены в SmartFilterPanel с маппингом")

        except Exception as e:
            self.logger.error(f"Ошибка обновления SmartFilterPanel: {e}")

    def update_ui_after_data_load(self):
        """ИСПРАВЛЕННОЕ обновление UI после загрузки данных"""
        try:
            # Инициализируем временной диапазон
            self._init_time_range_after_load()

            # Загружаем все параметры
            all_params = self._get_all_parameters()

            # ИСПРАВЛЕНО: Применяем правильный маппинг к параметрам
            self._update_ui_with_filtered_params(all_params)

            self.logger.info(
                f"UI обновлен после загрузки данных: {len(all_params)} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка обновления UI после загрузки: {e}")

    def _init_time_range_after_load(self):
        """Инициализация временного диапазона после загрузки данных"""
        try:
            # Используем Use Case если доступен
            if self.time_range_init_use_case:
                request = TimeRangeInitRequest()
                response = self.time_range_init_use_case.execute(request)
                if response.success:
                    self.update_time_range(
                        response.from_time, response.to_time)
                    return

            # Fallback - получаем из модели
            time_fields = self._get_time_fields_from_model(
            ) or self._get_time_fields_from_data_loader()
            if time_fields:
                self.update_time_range(
                    time_fields['from_time'], time_fields['to_time'])
                self.logger.info(
                    "Временной диапазон инициализирован из данных")
            else:
                self.reset_time_range()
                self.logger.info(
                    "Временной диапазон сброшен к значениям по умолчанию")

        except Exception as e:
            self.logger.error(
                f"Ошибка инициализации временного диапазона: {e}")

    # === МЕТОДЫ ФИЛЬТРАЦИИ ===

    def apply_filters(self, changed_only: bool = False, **kwargs):
        """ИСПРАВЛЕННЫЙ метод применения фильтров с поддержкой приоритетного режима"""
        try:
            self.logger.info(
                f"🔄 Применение фильтров (changed_only={changed_only}): {kwargs}")

            if not self._has_data():
                self._show_no_data_message()
                return

            # КРИТИЧНО: Проверяем состояние приоритетного чекбокса
            priority_mode_active = self._is_priority_mode_active()

            if changed_only or priority_mode_active:
                self.logger.info(
                    "🔥 Приоритетный режим активен, применяем фильтр изменяемых параметров")

                # Получаем filter_panel
                filter_panel = self.get_ui_component('filter_panel')
                if filter_panel and hasattr(filter_panel, 'get_selected_filters'):
                    selected_filters = filter_panel.get_selected_filters()
                    # Объединяем с kwargs, объединяя списки фильтров
                    combined_criteria = kwargs.copy()

                    def merge_lists(key):
                        vals1 = set(combined_criteria.get(key, []))
                        vals2 = set(selected_filters.get(key, []))
                        combined_criteria[key] = list(vals1.union(vals2))

                    for key in ['signal_types', 'lines', 'wagons']:
                        merge_lists(key)

                else:
                    combined_criteria = kwargs

                self.logger.info(
                    f"🔥 Приоритетные фильтры: {combined_criteria}")

                self._apply_priority_filters_with_criteria(combined_criteria)
                return

            # Обычная фильтрация только если приоритетный режим не активен
            self.logger.info("📊 Применение обычных фильтров")
            all_params = self._get_all_parameters()
            filtered_params = self._detailed_filter_parameters(
                all_params, kwargs)
            self._update_ui_with_filtered_params(filtered_params)

            self.logger.info(
                f"✅ Обычная фильтрация завершена: {len(filtered_params)} из {len(all_params)} параметров")

        except Exception as e:
            self.logger.error(f"❌ Ошибка применения фильтров: {e}")

    def _is_priority_mode_active(self) -> bool:
        """НОВЫЙ МЕТОД: Проверка активности приоритетного режима"""
        try:
            # Проверяем в SmartFilterPanel
            filter_panel = self.get_ui_component('filter_panel')
            if filter_panel:
                # Способ 1: Через метод is_changed_only_active (если есть)
                if hasattr(filter_panel, 'is_changed_only_active'):
                    return filter_panel.is_changed_only_active()

                # Способ 2: Через прямой доступ к чекбоксу
                if hasattr(filter_panel, 'changed_only_var'):
                    return filter_panel.changed_only_var.get()

                # Способ 3: Через состояние фильтра
                if hasattr(filter_panel, 'state') and hasattr(filter_panel.state, 'changed_only'):
                    return filter_panel.state.changed_only

            # Проверяем в time_panel
            time_panel = self.get_ui_component('time_panel')
            if time_panel:
                if hasattr(time_panel, 'is_changed_only_enabled'):
                    return time_panel.is_changed_only_enabled()

                if hasattr(time_panel, 'changed_only_var'):
                    return time_panel.changed_only_var.get()

            self.logger.debug("🔍 Приоритетный режим не активен")
            return False

        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки приоритетного режима: {e}")
            return False

    def _apply_priority_filters_with_criteria(self, filter_criteria: Dict[str, Any]):
        """НОВЫЙ МЕТОД: Применение приоритетных фильтров с дополнительными критериями"""
        try:
            self.logger.info(
                f"🔥 Применение приоритетных фильтров с критериями: {filter_criteria}")

            # Получаем временной диапазон
            start_time, end_time = self._get_time_range_unified()
            if not start_time or not end_time:
                self._show_time_error()
                return

            # Получаем session_id
            session_id = self.get_session_id()

            # Получаем изменяемые параметры
            changed_params = self._get_changed_parameters(
                start_time, end_time, session_id)
            if not changed_params:
                self.logger.warning("⚠️ Изменяемые параметры не найдены")
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning(
                        "Изменяемые параметры не найдены в указанном диапазоне")
                return

            self.logger.info(
                f"🔍 Найдено {len(changed_params)} изменяемых параметров")

            # КРИТИЧНО: Применяем дополнительные фильтры к изменяемым параметрам
            if filter_criteria:
                filtered_changed_params = self._detailed_filter_parameters(
                    changed_params, filter_criteria)
                self.logger.info(
                    f"🎯 После применения фильтров: {len(filtered_changed_params)} из {len(changed_params)} параметров")
            else:
                filtered_changed_params = changed_params

            self.logger.info(
                f"🎯 Отфильтрованные параметры: {filtered_changed_params}")

            # Обновляем UI
            self._update_ui_with_filtered_params(filtered_changed_params)

            # Убираем автоматическое добавление в selected_parameters
            # Ранее здесь был код обновления selected_parameters, он удален

            # Генерируем событие
            self._emit_event('changed_params_filter_applied', {
                'count': len(filtered_changed_params),
                'total_changed': len(changed_params),
                'time_range': {'start': start_time, 'end': end_time},
                'filter_criteria': filter_criteria
            })

            self.logger.info(
                f"✅ Приоритетная фильтрация завершена: {len(filtered_changed_params)} параметров")

        except Exception as e:
            self.logger.error(
                f"❌ Ошибка приоритетной фильтрации с критериями: {e}")

    def _get_changed_parameters(self, start_time: str, end_time: str, session_id: str) -> List[Dict[str, Any]]:
        """НОВЫЙ МЕТОД: Получение изменяемых параметров"""
        try:
            # Способ 1: Через Use Case
            if self.find_changed_params_use_case:
                request = FindChangedParametersRequest(
                    session_id=session_id,
                    from_time=start_time,
                    to_time=end_time
                )
                response = self.find_changed_params_use_case.execute(request)

                if response.success and response.changed_parameters:
                    self.logger.info(
                        f"✅ Use Case: найдено {len(response.changed_parameters)} изменяемых параметров")
                    return response.changed_parameters

            # Способ 2: Через data_loader
            if (hasattr(self.model, 'data_loader') and
                self.model.data_loader and
                    hasattr(self.model.data_loader, 'filter_changed_params')):

                changed_params = self.model.data_loader.filter_changed_params(
                    start_time, end_time)
                if changed_params:
                    self.logger.info(
                        f"✅ CSV Loader: найдено {len(changed_params)} изменяемых параметров")
                    return changed_params

            # Способ 3: Через DataModel
            if (hasattr(self.model, 'data_model') and
                    hasattr(self.model.data_model, 'find_changed_parameters_in_range')):

                changed_params = self.model.data_model.find_changed_parameters_in_range(
                    start_time, end_time)
                if changed_params:
                    self.logger.info(
                        f"✅ DataModel: найдено {len(changed_params)} изменяемых параметров")
                    return changed_params

            self.logger.warning(
                "❌ Все методы поиска изменяемых параметров не сработали")
            return []

        except Exception as e:
            self.logger.error(f"❌ Ошибка получения изменяемых параметров: {e}")
            return []

    def _detailed_filter_parameters(self, parameters: List[Dict[str, Any]],
                                    criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """НОВЫЙ МЕТОД: Детальная фильтрация параметров с логированием"""
        try:
            filtered = parameters.copy()
            original_count = len(filtered)

            # Фильтр по типам сигналов
            if criteria.get('signal_types'):
                signal_types = set(criteria['signal_types'])
                self.logger.info(f"🔍 Фильтр по типам сигналов: {signal_types}")

                before_count = len(filtered)
                filtered = [p for p in filtered if p.get(
                    'signal_type') in signal_types]
                after_count = len(filtered)

                self.logger.info(
                    f"📊 Фильтр по типам: {before_count} → {after_count} параметров")

            # Фильтр по линиям
            if criteria.get('lines'):
                lines = set(criteria['lines'])
                self.logger.info(f"🔍 Фильтр по линиям: {len(lines)} линий")

                before_count = len(filtered)
                filtered = [p for p in filtered if p.get('line') in lines]
                after_count = len(filtered)

                self.logger.info(
                    f"📡 Фильтр по линиям: {before_count} → {after_count} параметров")

            # Фильтр по вагонам
            if criteria.get('wagons'):
                wagons = set(str(w) for w in criteria['wagons'])
                self.logger.info(f"🔍 Фильтр по вагонам: {wagons}")

                before_count = len(filtered)
                filtered = [p for p in filtered if str(
                    p.get('wagon', '')) in wagons]
                after_count = len(filtered)

                self.logger.info(
                    f"🚃 Фильтр по вагонам: {before_count} → {after_count} параметров")

            self.logger.info(
                f"🎯 Итоговая фильтрация: {original_count} → {len(filtered)} параметров")
            self.logger.info(f"🎯 Отфильтрованные параметры: {filtered}")
            return filtered

        except Exception as e:
            self.logger.error(f"❌ Ошибка детальной фильтрации: {e}")
            return parameters

    def get_session_id(self) -> str:
        """Получение session_id для приоритетных операций"""
        import uuid
        # Можно реализовать получение session_id из модели или сгенерировать новый
        if hasattr(self.model, 'session_id'):
            return self.model.session_id
        # Генерируем новый UUID для сессии
        return str(uuid.uuid4())

    def apply_changed_parameters_filter(self, auto_recalc: bool = False, session_id: str = None):
        """ИСПРАВЛЕННЫЙ метод для изменяемых параметров с сохранением состояния фильтров"""
        try:
            if auto_recalc:
                self.logger.info(
                    "🔥 Автоматический пересчет изменяемых параметров")
            else:
                self.logger.info(
                    "🔥 ПРИОРИТЕТНОЕ применение фильтра изменяемых параметров")

            if not self._has_data():
                self._show_no_data_message()
                return

            # Получаем временной диапазон
            start_time, end_time = self._get_time_range_unified()
            if not start_time or not end_time:
                self._show_time_error()
                return

            # Диагностика временного диапазона
            self.diagnose_time_range_analysis(start_time, end_time)

            # ВАЖНО: Получаем текущие фильтры из SmartFilterPanel до пересчета
            filter_panel = self.get_ui_component('filter_panel')
            current_filters = {}
            if filter_panel and hasattr(filter_panel, 'get_selected_filters'):
                current_filters = filter_panel.get_selected_filters()
                self.logger.info(f"📋 Текущие фильтры: {current_filters}")

            # Очищаем кэш для принудительного пересчета
            if not auto_recalc:
                self.force_clear_all_caches()

            # Если session_id не передан, пытаемся получить из контроллера
            if not session_id:
                session_id = self.get_session_id()

            # Получаем изменяемые параметры через Use Case или CSV loader
            changed_params = []

            # Способ 1: Через Use Case
            if self.find_changed_params_use_case:
                request = FindChangedParametersRequest(
                    session_id=session_id,
                    from_time=start_time,
                    to_time=end_time
                )
                response = self.find_changed_params_use_case.execute(request)
                if response.success and response.changed_parameters:
                    changed_params = response.changed_parameters
                    self.logger.info(
                        f"✅ Use Case: найдено {len(changed_params)} изменяемых параметров")

            # Способ 2: Через CSV loader (если Use Case не сработал)
            if not changed_params and hasattr(self.model, 'data_loader') and \
               self.model.data_loader and hasattr(self.model.data_loader, 'filter_changed_params'):
                changed_params = self.model.data_loader.filter_changed_params(
                    start_time, end_time)
                if changed_params:
                    self.logger.info(
                        f"✅ CSV Loader: найдено {len(changed_params)} изменяемых параметров")

            if not changed_params:
                self.logger.warning(
                    "❌ Не удалось получить изменяемые параметры")
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning(
                        "Не удалось найти изменяемые параметры в указанном диапазоне")
                return

            # КРИТИЧНО: Применяем текущие фильтры к изменяемым параметрам
            if current_filters:
                filtered_changed_params = self._detailed_filter_parameters(
                    changed_params, current_filters)
                self.logger.info(
                    f"🎯 После применения фильтров: {len(filtered_changed_params)} из {len(changed_params)}")
            else:
                filtered_changed_params = changed_params

            # Обновляем UI с отфильтрованными параметрами
            self._update_ui_with_filtered_params(filtered_changed_params)

            # Генерируем событие с учетом фильтров
            self._emit_event('changed_params_filter_applied', {
                'count': len(filtered_changed_params),
                'total_changed': len(changed_params),
                'time_range': {'start': start_time, 'end': end_time},
                'filter_criteria': current_filters
            })

            self.logger.info(
                f"✅ Пересчет завершен с сохранением фильтров: {len(filtered_changed_params)} параметров")

        except Exception as e:
            self.logger.error(
                f"Ошибка применения фильтра изменяемых параметров: {e}")

    def _simple_filter_parameters(self, parameters: List[Dict[str, Any]],
                                  criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Простая фильтрация параметров"""
        try:
            filtered = parameters.copy()

            # Фильтр по типам сигналов
            if criteria.get('signal_types'):
                signal_types = set(criteria['signal_types'])
                filtered = [p for p in filtered if p.get(
                    'signal_type') in signal_types]

            # Фильтр по линиям
            if criteria.get('lines'):
                lines = set(criteria['lines'])
                filtered = [p for p in filtered if p.get('line') in lines]

            # Фильтр по вагонам
            if criteria.get('wagons'):
                wagons = set(str(w) for w in criteria['wagons'])
                filtered = [p for p in filtered if str(
                    p.get('wagon', '')) in wagons]

            return filtered

        except Exception as e:
            self.logger.error(f"Ошибка простой фильтрации: {e}")
            return parameters

    # === МЕТОДЫ УПРАВЛЕНИЯ СОСТОЯНИЕМ ===

    def _start_loading(self, message: str = "Загрузка..."):
        """Начало индикации загрузки"""
        try:
            self.is_loading = True

            if hasattr(self.view, 'ui_components') and self.view.ui_components:
                self.view.ui_components.start_processing(message)

            self.logger.debug(f"Начата загрузка: {message}")

        except Exception as e:
            self.logger.error(f"Ошибка начала загрузки: {e}")

    def _stop_loading(self):
        """Завершение индикации загрузки"""
        try:
            self.is_loading = False

            if hasattr(self.view, 'ui_components') and self.view.ui_components:
                self.view.ui_components.stop_processing()

            self.logger.debug("Загрузка завершена")

        except Exception as e:
            self.logger.error(f"Ошибка завершения загрузки: {e}")

    def _start_processing(self, message: str = "Обработка..."):
        """Начало индикации обработки"""
        try:
            self.is_processing = True

            if hasattr(self.view, 'ui_components') and self.view.ui_components:
                self.view.ui_components.start_processing(message)

            self.logger.debug(f"Начата обработка: {message}")

        except Exception as e:
            self.logger.error(f"Ошибка начала обработки: {e}")

    def _stop_processing(self):
        """Завершение индикации обработки"""
        try:
            self.is_processing = False

            if hasattr(self.view, 'ui_components') and self.view.ui_components:
                self.view.ui_components.stop_processing()

            self.logger.debug("Обработка завершена")

        except Exception as e:
            self.logger.error(f"Ошибка завершения обработки: {e}")

    def _has_data(self) -> bool:
        """Проверка наличия загруженных данных"""
        try:
            if hasattr(self.model, 'data_loader') and self.model.data_loader:
                return hasattr(self.model.data_loader, 'data') and self.model.data_loader.data is not None
            return False
        except Exception as e:
            self.logger.error(f"Ошибка проверки данных: {e}")
            return False

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Отправка события подписчикам"""
        try:
            callbacks = self._ui_callbacks.get(event_type, [])
            for callback in callbacks:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(
                        f"Ошибка в callback для события {event_type}: {e}")

        except Exception as e:
            self.logger.error(f"Ошибка отправки события {event_type}: {e}")

    def _show_no_data_message(self):
        """Показ сообщения об отсутствии данных"""
        if hasattr(self.view, 'show_warning'):
            self.view.show_warning(
                "Нет загруженных данных. Загрузите CSV файл.")

    def _show_time_error(self):
        """Показ ошибки времени"""
        if hasattr(self.view, 'show_error'):
            self.view.show_error("Ошибка получения временного диапазона")

    # === МЕТОДЫ ПОСТРОЕНИЯ ГРАФИКОВ ===

    def plot_selected_parameters(self):
        """ОСНОВНОЙ метод построения графиков выбранных параметров"""
        try:
            self.logger.info("🔄 plot_selected_parameters вызван")

            # Проверяем наличие данных
            if not self._has_data():
                self._show_no_data_message()
                return

            # Получаем выбранные параметры
            selected_params = self._get_selected_parameters_unified()
            if not selected_params:
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning("Выберите параметры для построения графиков")
                return

            # Получаем временной диапазон
            start_time, end_time = self._get_time_range_unified()
            if not start_time or not end_time:
                self._show_time_error()
                return

            self.logger.info(f"📊 Построение графиков для {len(selected_params)} параметров")

            # Проверяем plot_manager
            if not self.plot_manager:
                self.logger.error("❌ PlotManager не инициализирован")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("PlotManager не инициализирован")
                return

            # Получаем plot_panel
            plot_panel = self.get_ui_component('plot_panel')
            if not plot_panel:
                self.logger.error("❌ PlotVisualizationPanel не найден")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Панель графиков не найдена")
                return

            self._start_processing("Построение графиков...")

            try:
                # Преобразуем время если нужно
                if isinstance(start_time, str):
                    from datetime import datetime
                    start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                else:
                    start_dt = start_time

                if isinstance(end_time, str):
                    from datetime import datetime
                    end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                else:
                    end_dt = end_time

                # Вызываем построение через plot_panel
                if hasattr(plot_panel, 'build_plots_for_parameters'):
                    plot_panel.build_plots_for_parameters(selected_params, start_dt, end_dt)
                    self.logger.info("✅ Графики переданы в PlotVisualizationPanel")
                else:
                    # Fallback через plot_manager
                    success = self.plot_manager.plot_parameters(
                        parameters=selected_params,
                        start_time=start_time if isinstance(start_time, str) else start_time.strftime('%Y-%m-%d %H:%M:%S'),
                        end_time=end_time if isinstance(end_time, str) else end_time.strftime('%Y-%m-%d %H:%M:%S')
                    )
                    
                    if success:
                        self.logger.info("✅ Графики построены через PlotManager")
                        if hasattr(self.view, 'show_info'):
                            self.view.show_info("Графики построены успешно")
                    else:
                        self.logger.error("❌ Не удалось построить графики")
                        if hasattr(self.view, 'show_error'):
                            self.view.show_error("Не удалось построить графики")

            except Exception as e:
                self.logger.error(f"❌ Ошибка построения графиков: {e}")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(f"Ошибка построения графиков: {e}")
            finally:
                self._stop_processing()

        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка plot_selected_parameters: {e}")
            self._stop_processing()
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Критическая ошибка: {e}")

    def _handle_plot_result(self, success: bool):
        """Обработка результата построения графиков"""
        try:
            self._stop_processing()

            if success:
                self.logger.info("Графики успешно построены")
                if hasattr(self.view, 'show_info'):
                    self.view.show_info("Графики", "Графики успешно построены")
            else:
                self.logger.error("Не удалось построить графики")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Не удалось построить графики")

        except Exception as e:
            self.logger.error(
                f"Ошибка обработки результата построения графиков: {e}")

    def _handle_plot_error(self, error: Exception):
        """Обработка ошибки построения графиков"""
        try:
            self._stop_processing()
            self.logger.error(f"Ошибка построения графиков: {error}")

            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка построения графиков: {error}")

        except Exception as e:
            self.logger.error(
                f"Ошибка обработки ошибки построения графиков: {e}")

    # === МЕТОДЫ ГЕНЕРАЦИИ ОТЧЕТОВ ===

    def generate_report(self):
        """Генерация отчета"""
        try:
            if not self.report_generator:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(
                        "Генератор отчетов не инициализирован")
                return

            # Получаем данные для отчета
            selected_params = self._get_selected_parameters_unified()
            start_time, end_time = self._get_time_range_unified()

            if not selected_params:
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning("Выберите параметры для отчета")
                return

            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("HTML files", "*.html")],
                title="Сохранить отчет"
            )

            if file_path:
                self._start_processing("Генерация отчета...")

                try:
                    success = self.report_generator.generate_full_report(
                        parameters=selected_params,
                        start_time=start_time,
                        end_time=end_time,
                        output_path=file_path
                    )

                    if success:
                        self.logger.info(f"Отчет создан: {file_path}")
                        if hasattr(self.view, 'show_info'):
                            self.view.show_info(
                                "Отчет", f"Отчет сохранен: {file_path}")
                    else:
                        if hasattr(self.view, 'show_error'):
                            self.view.show_error("Ошибка создания отчета")

                finally:
                    self._stop_processing()

        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета: {e}")
            self._stop_processing()
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка генерации отчета: {e}")

    def export_all_plots(self):
        """Экспорт всех графиков"""
        try:
            if not self.plot_manager:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("PlotManager не инициализирован")
                return

            from tkinter import filedialog
            directory = filedialog.askdirectory(
                title="Выберите папку для экспорта графиков")

            if directory:
                success = self.plot_manager.export_all_plots(directory)
                if success:
                    self.logger.info(f"Графики экспортированы в: {directory}")
                    if hasattr(self.view, 'show_info'):
                        self.view.show_info(
                            "Экспорт", f"Графики сохранены в: {directory}")
                else:
                    if hasattr(self.view, 'show_error'):
                        self.view.show_error("Ошибка экспорта графиков")

        except Exception as e:
            self.logger.error(f"Ошибка экспорта графиков: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка экспорта: {e}")

    # === МЕТОДЫ УПРАВЛЕНИЯ ВЫБОРОМ ПАРАМЕТРОВ ===

    def select_all_parameters(self):
        """Выбор всех параметров"""
        try:
            parameter_panel = self.get_ui_component('parameter_panel')
            if parameter_panel:
                if hasattr(parameter_panel, 'select_all'):
                    parameter_panel.select_all()
                    self.logger.info("Все параметры выбраны")
                elif hasattr(parameter_panel, 'select_all_parameters'):
                    parameter_panel.select_all_parameters()
                    self.logger.info(
                        "Все параметры выбраны через select_all_parameters")
                else:
                    self.logger.warning(
                        "Метод выбора всех параметров не найден")
            else:
                self.logger.warning(
                    "parameter_panel не найден для выбора всех параметров")
        except Exception as e:
            self.logger.error(f"Ошибка выбора всех параметров: {e}")

    def deselect_all_parameters(self):
        """Отмена выбора всех параметров"""
        try:
            parameter_panel = self.get_ui_component('parameter_panel')
            if parameter_panel:
                if hasattr(parameter_panel, 'deselect_all'):
                    parameter_panel.deselect_all()
                    self.logger.info("Выбор всех параметров отменен")
                elif hasattr(parameter_panel, 'clear_selection'):
                    parameter_panel.clear_selection()
                    self.logger.info("Выбор очищен через clear_selection")
                else:
                    self.logger.warning(
                        "Метод отмены выбора параметров не найден")
            else:
                self.logger.warning(
                    "parameter_panel не найден для отмены выбора")
        except Exception as e:
            self.logger.error(f"Ошибка отмены выбора параметров: {e}")

    def get_selected_count(self) -> int:
        """Получение количества выбранных параметров"""
        try:
            selected_params = self._get_selected_parameters_unified()
            return len(selected_params)
        except Exception as e:
            self.logger.error(
                f"Ошибка получения количества выбранных параметров: {e}")
            return 0

    # === МЕТОДЫ ОЧИСТКИ ===

    def clear_all_filters(self):
        """Очистка всех фильтров"""
        try:
            self.logger.info("Очистка всех фильтров")

            filter_panel = self.get_ui_component('filter_panel')
            if filter_panel:
                if hasattr(filter_panel, 'clear_all_filters'):
                    filter_panel.clear_all_filters()
                elif hasattr(filter_panel, 'reset_filters'):
                    filter_panel.reset_filters()
                else:
                    self.logger.warning("Метод очистки фильтров не найден")

            # Очищаем кэш
            self._filter_criteria_cache = None

            # Показываем все параметры
            all_params = self._get_all_parameters()
            self._update_ui_with_filtered_params(all_params)

            self.logger.info(
                f"Фильтры очищены, показано {len(all_params)} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка очистки фильтров: {e}")

    def clear_all_plots(self):
        """Очистка всех графиков"""
        try:
            plot_panel = self.get_ui_component('plot_panel')
            if plot_panel:
                if hasattr(plot_panel, 'clear_all_plots'):
                    plot_panel.clear_all_plots()
                    self.logger.info("Все графики очищены через plot_panel")
                elif hasattr(plot_panel, 'clear_plots'):
                    plot_panel.clear_plots()
                    self.logger.info("Графики очищены через clear_plots")
                else:
                    self.logger.warning(
                        "Метод очистки графиков не найден в plot_panel")

            # Также очищаем через plot_manager если есть
            if self.plot_manager and hasattr(self.plot_manager, 'clear_all_plots'):
                self.plot_manager.clear_all_plots()
                self.logger.info("Графики очищены через plot_manager")

        except Exception as e:
            self.logger.error(f"Ошибка очистки графиков: {e}")

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def _update_ui_with_filtered_params(self, parameters: List[Dict[str, Any]]):
        """ИСПРАВЛЕННОЕ обновление UI с правильным маппингом вагонов"""
        try:
            # Получаем filter_panel для доступа к маппингу вагонов
            filter_panel = self.get_ui_component('filter_panel')
            wagon_mapping = {}

            if filter_panel and hasattr(filter_panel, 'wagon_mapping'):
                wagon_mapping = filter_panel.wagon_mapping
                self.logger.info(
                    f"🔄 Используется маппинг из filter_panel: {wagon_mapping}")
            else:
                self.logger.warning(
                    "⚠️ Маппинг вагонов не найден в filter_panel")

            # ИСПРАВЛЕНО: Преобразуем номера вагонов в параметрах
            transformed_params = []
            for param in parameters:
                new_param = param.copy()
                original_wagon = param.get('wagon', '')

                # КРИТИЧНО: Применяем ПРЯМОЙ маппинг (логический -> реальный)
                if original_wagon and str(original_wagon).isdigit():
                    logical_wagon = int(original_wagon)
                    if logical_wagon in wagon_mapping:
                        real_wagon = wagon_mapping[logical_wagon]
                        new_param['wagon'] = real_wagon
                        self.logger.debug(
                            f"🔄 Маппинг вагона: логический {logical_wagon} → реальный {real_wagon}")
                    else:
                        # Если логический номер не найден в маппинге, оставляем как есть
                        new_param['wagon'] = str(original_wagon)
                        self.logger.debug(
                            f"⚠️ Логический вагон {logical_wagon} не найден в маппинге, оставляем: {original_wagon}")
                else:
                    # Если это не число или пустое значение, оставляем как есть
                    new_param['wagon'] = str(
                        original_wagon) if original_wagon else ''
                    self.logger.debug(
                        f"ℹ️ Нечисловой вагон оставлен как есть: {original_wagon}")

                transformed_params.append(new_param)

            # Обновляем parameter_panel с преобразованными параметрами
            parameter_panel = self.get_ui_component('parameter_panel')
            if parameter_panel:
                if hasattr(parameter_panel, 'update_parameters'):
                    parameter_panel.update_parameters(transformed_params)
                    self.logger.info(
                        f"✅ Параметры обновлены с маппингом: {len(transformed_params)} элементов")
                elif hasattr(parameter_panel, 'set_parameters'):
                    parameter_panel.set_parameters(transformed_params)
                    self.logger.info(
                        f"✅ Параметры установлены с маппингом: {len(transformed_params)} элементов")
            else:
                self.logger.error("❌ parameter_panel не найден")

            # Обновляем статистику в главном окне
            if hasattr(self.view, 'update_parameter_count'):
                self.view.update_parameter_count(len(parameters))

            # Обновляем счетчики выбранных параметров
            selected_count = len(self._get_selected_parameters_unified())
            if hasattr(self.view, 'update_telemetry_info'):
                # Получаем текущую информацию для обновления счетчика
                current_filename = getattr(self, 'current_file_path', '')
                if current_filename:
                    filename = Path(current_filename).name
                    # Передаем текущие сохранённые МЦД параметры, чтобы не затирать их
                    line_mcd = getattr(self.view, '_current_line_mcd', '')
                    route = getattr(self.view, '_current_route', '')
                    train = getattr(self.view, '_current_train', '')
                    leading_unit = getattr(
                        self.view, '_current_leading_unit', '')
                    self.view.update_telemetry_info(
                        file_name=filename,
                        params_count=len(parameters),
                        selected_count=selected_count,
                        line_mcd=line_mcd,
                        route=route,
                        train=train,
                        leading_unit=leading_unit
                    )

            self.logger.info(
                f"✅ UI обновлен с правильным маппингом вагонов: {len(parameters)} → {len(transformed_params)} параметров")

        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления UI с параметрами: {e}")
            import traceback
            traceback.print_exc()

    def handle_file_load_result(self, success: bool, file_path: str):
        """ИСПРАВЛЕННАЯ обработка результата загрузки с полной синхронизацией маппинга"""
        try:
            self._stop_loading()

            if success:
                # Получаем количество записей и параметров
                all_params = self._get_all_parameters()
                params_count = len(all_params)

                # КРИТИЧНО: Извлекаем МЦД информацию
                mcd_info = None
                if hasattr(self.model, 'data_loader') and self.model.data_loader:
                    mcd_info = self.model.data_loader.extract_and_update_mcd_info(
                        file_path)
                    self.logger.info(f"🔍 МЦД информация: {mcd_info}")

                # КРИТИЧНО: Сначала обновляем SmartFilterPanel с правильным ведущим вагоном
                filter_panel = self.get_ui_component('filter_panel')
                if filter_panel and mcd_info and mcd_info.get('leading_unit'):
                    try:
                        leading_unit = int(mcd_info['leading_unit'])

                        # Принудительно обновляем ведущий вагон и маппинг
                        filter_panel.leading_wagon = leading_unit
                        filter_panel._create_wagon_mapping(leading_unit)

                        # Извлекаем реальные номера вагонов из данных
                        real_wagons = list(
                            set(str(param.get('wagon', '')) for param in all_params))
                        real_wagons = [
                            wagon for wagon in real_wagons if wagon and wagon != 'Unknown']

                        # Обновляем filter_panel с реальными данными о вагонах
                        if hasattr(filter_panel, 'update_wagon_checkboxes'):
                            filter_panel.update_wagon_checkboxes(real_wagons)
                            self.logger.info(
                                f"✅ Вагоны обновлены в SmartFilterPanel: {real_wagons}")

                        self.logger.info(
                            f"✅ SmartFilterPanel синхронизирован с ведущим вагоном: {leading_unit}")
                        self.logger.info(
                            f"✅ Маппинг вагонов: {filter_panel.wagon_mapping}")

                    except ValueError:
                        self.logger.error(
                            f"❌ Неверный формат ведущего вагона: {mcd_info['leading_unit']}")

                # ВАЖНО: Обновляем заголовок ПОСЛЕ установки маппинга
                file_name = Path(file_path).name
                if mcd_info and hasattr(self.view, 'update_telemetry_info'):
                    self.view.update_telemetry_info(
                        file_name=file_name,
                        params_count=params_count,
                        selected_count=0,
                        line_mcd=mcd_info.get('line_mcd', ''),
                        route=mcd_info.get('route', ''),
                        train=mcd_info.get('train', ''),
                        leading_unit=mcd_info.get('leading_unit', '')
                    )
                    self.logger.info(f"✅ Заголовок обновлен с МЦД данными")

                # КРИТИЧНО: Теперь обновляем UI с параметрами (применится правильный маппинг)
                self.update_ui_after_data_load()

                # Обновляем SmartFilterPanel с данными из CSV
                self._update_smart_filter_panel_with_data(all_params)

                # Принудительно обновляем интерфейс
                if hasattr(self.view, 'root'):
                    self.view.root.update_idletasks()

                self.logger.info(
                    f"✅ Файл успешно загружен с правильным маппингом: {file_path}")

                if hasattr(self.view, 'show_info'):
                    self.view.show_info(
                        "Успешно", f"Файл {Path(file_path).name} загружен")

            else:
                self.logger.error(f"❌ Ошибка загрузки файла: {file_path}")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(
                        "Ошибка", f"Не удалось загрузить файл {Path(file_path).name}")

        except Exception as e:
            self.logger.error(f"❌ Ошибка обработки результата загрузки: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error("Ошибка", f"Ошибка обработки файла: {e}")

    def update_parameters(self, parameters: List[Dict[str, Any]]):
        """ЕДИНСТВЕННЫЙ метод обновления списка параметров во всех панелях"""
        try:
            self.logger.info(
                f"📊 update_parameters вызван с {len(parameters)} параметрами")

            if not hasattr(self.view, 'ui_components') or not self.view.ui_components:
                self.logger.error("❌ ui_components не создан!")
                return

            # Обновляем панель параметров
            if hasattr(self.view.ui_components, 'update_parameters'):
                self.view.ui_components.update_parameters(parameters)
                self.logger.info("✅ ui_components.update_parameters выполнен")

            # Генерируем событие
            self._emit_event('parameters_updated', {'count': len(parameters)})

            self.logger.info(
                f"✅ Параметры обновлены в UI: {len(parameters)} элементов")

        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления параметров: {e}")
            import traceback
            traceback.print_exc()

    def disable_changed_only_checkbox(self):
        """ЕДИНСТВЕННЫЙ метод отключения чекбокса 'только изменяемые' в SmartFilterPanel"""
        try:
            filter_panel = self.get_ui_component('filter_panel')
            if filter_panel and hasattr(filter_panel, 'disable_changed_only_checkbox'):
                filter_panel.disable_changed_only_checkbox()
                self.logger.debug("Чекбокс 'только изменяемые' отключен")
            else:
                self.logger.warning(
                    "Метод disable_changed_only_checkbox не найден в filter_panel")
        except Exception as e:
            self.logger.error(f"Ошибка отключения чекбокса: {e}")

    def _sync_with_time_panel(self):
        """Синхронизация с панелью времени"""
        try:
            filter_panel = self.get_ui_component('filter_panel')
            if filter_panel and hasattr(filter_panel, '_sync_with_time_panel'):
                filter_panel._sync_with_time_panel()
                self.logger.debug("Синхронизация с time_panel выполнена")
            else:
                self.logger.debug(
                    "Метод _sync_with_time_panel не найден в filter_panel")
        except Exception as e:
            self.logger.error(f"Ошибка синхронизации с time_panel: {e}")

    # === МЕТОДЫ СТАТИСТИКИ ===

    def get_filter_statistics(self) -> Dict[str, Any]:
        """Получение статистики по фильтрам"""
        try:
            all_params = self._get_all_parameters()
            if not all_params:
                return {}

            stats = {
                'total_parameters': len(all_params),
                'lines': {},
                'wagons': {},
                'signal_types': {},
                'data_types': {}
            }

            for param in all_params:
                # Статистика по линиям
                line = param.get('line', 'Unknown')
                stats['lines'][line] = stats['lines'].get(line, 0) + 1

                # Статистика по вагонам
                wagon = param.get('wagon', 'Unknown')
                stats['wagons'][wagon] = stats['wagons'].get(wagon, 0) + 1

                # Статистика по типам сигналов
                signal_type = param.get('signal_type', 'Unknown')
                stats['signal_types'][signal_type] = stats['signal_types'].get(
                    signal_type, 0) + 1

                # Статистика по типам данных
                data_type = param.get('data_type', 'Unknown')
                stats['data_types'][data_type] = stats['data_types'].get(
                    data_type, 0) + 1

            return stats

        except Exception as e:
            self.logger.error(f"Ошибка получения статистики фильтров: {e}")
            return {}

    def get_application_info(self) -> Dict[str, Any]:
        """Получение информации о приложении"""
        try:
            info = {
                'controller_version': '2.0.0',
                'current_file': self.current_file_path,
                'has_data': self._has_data(),
                'parameters_count': len(self._get_all_parameters()) if self._has_data() else 0,
                'selected_count': self.get_selected_count(),
                'is_processing': self.is_processing,
                'is_loading': self.is_loading,
                'use_cases_available': USE_CASES_AVAILABLE,
                'diagnostic_filters_available': DIAGNOSTIC_FILTERS_AVAILABLE,
                'services': {
                    'filtering_service': self.filtering_service is not None,
                    'plot_manager': self.plot_manager is not None,
                    'report_generator': self.report_generator is not None,
                    'sop_manager': self.sop_manager is not None
                },
                'ui_components': {
                    'time_panel': self.get_ui_component('time_panel') is not None,
                    'parameter_panel': self.get_ui_component('parameter_panel') is not None,
                    'filter_panel': self.get_ui_component('filter_panel') is not None,
                    'action_panel': self.get_ui_component('action_panel') is not None,
                    'plot_panel': self.get_ui_component('plot_panel') is not None,
                    'diagnostic_panel': self.get_ui_component('diagnostic_panel') is not None
                },
                'cache_info': {
                    'filter_cache_size': len(self._filter_criteria_cache) if self._filter_criteria_cache else 0,
                    'ui_cache_size': len(self._ui_update_cache),
                    'callbacks_count': sum(len(callbacks) for callbacks in self._ui_callbacks.values())
                },
                'time_range': self._get_time_range_unified(),
                'filter_stats': self.get_filter_statistics()
            }

            return info

        except Exception as e:
            self.logger.error(f"Ошибка получения информации о приложении: {e}")
            return {}

    # === ДИАГНОСТИЧЕСКИЕ МЕТОДЫ ===

    def diagnose_changed_params_issue(self):
        """Диагностика проблем с поиском изменяемых параметров"""
        try:
            self.logger.info(
                "=== ДИАГНОСТИКА ПОИСКА ИЗМЕНЯЕМЫХ ПАРАМЕТРОВ ===")

            # Проверяем Use Case
            if self.find_changed_params_use_case:
                self.logger.info("✅ FindChangedParametersUseCase доступен")
            else:
                self.logger.error("❌ FindChangedParametersUseCase НЕ доступен")

            # Проверяем DataModel
            if hasattr(self.model, 'data_model') and self.model.data_model:
                self.logger.info("✅ DataModel доступен")

                # Проверяем методы DataModel
                if hasattr(self.model.data_model, 'find_changed_parameters'):
                    self.logger.info(
                        "✅ DataModel.find_changed_parameters доступен")
                else:
                    self.logger.error(
                        "❌ DataModel.find_changed_parameters НЕ доступен")
            else:
                self.logger.error("❌ DataModel НЕ доступен")

            # Проверяем данные
            if self._has_data():
                all_params = self._get_all_parameters()
                self.logger.info(
                    f"✅ Данные загружены: {len(all_params)} параметров")
            else:
                self.logger.error("❌ Данные НЕ загружены")

            # Проверяем временной диапазон
            start_time, end_time = self._get_time_range_unified()
            if start_time and end_time:
                self.logger.info(
                    f"✅ Временной диапазон: {start_time} - {end_time}")
            else:
                self.logger.error("❌ Временной диапазон НЕ доступен")

        except Exception as e:
            self.logger.error(f"Ошибка диагностики: {e}")

    def diagnose_time_range_analysis(self, start_time_str: str, end_time_str: str) -> bool:
        """Диагностика анализа временного диапазона"""
        try:
            from datetime import datetime

            start_dt = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            end_dt = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
            duration_seconds = (end_dt - start_dt).total_seconds()

            self.logger.info(f"=== ДИАГНОСТИКА ВРЕМЕННОГО АНАЛИЗА ===")
            self.logger.info(f"Диапазон: {start_time_str} - {end_time_str}")
            self.logger.info(f"Длительность: {duration_seconds} секунд")

            if duration_seconds <= 1:
                self.logger.warning(
                    "⚠️ ОЧЕНЬ КОРОТКИЙ диапазон (≤1 сек) - параметры скорее всего НЕ изменяются")
                return False
            elif duration_seconds <= 5:
                self.logger.warning(
                    "⚠️ Короткий диапазон (≤5 сек) - мало изменений ожидается")
                return False
            else:
                self.logger.info(
                    "✅ Достаточный диапазон для анализа изменений")
                return True

        except Exception as e:
            self.logger.error(f"Ошибка диагностики: {e}")
            return False

    def force_clear_all_caches(self):
        """Принудительная очистка всех кэшей системы"""
        try:
            self.logger.info("=== ПРИНУДИТЕЛЬНАЯ ОЧИСТКА ВСЕХ КЭШЕЙ ===")

            # Очищаем кэш Use Case
            if self.find_changed_params_use_case and hasattr(self.find_changed_params_use_case, 'clear_cache'):
                self.find_changed_params_use_case.clear_cache()
                self.logger.info("🔄 Кэш FindChangedParametersUseCase очищен")

            if self.filter_parameters_use_case and hasattr(self.filter_parameters_use_case, 'clear_cache'):
                self.filter_parameters_use_case.clear_cache()
                self.logger.info("🔄 Кэш FilterParametersUseCase очищен")

            # Очищаем кэш сервиса фильтрации
            if self.filtering_service and hasattr(self.filtering_service, 'clear_cache'):
                self.filtering_service.clear_cache()
                self.logger.info("🔄 Кэш ParameterFilteringService очищен")

            # Очищаем локальные кэши контроллера
            self._filter_criteria_cache = None
            self._ui_update_cache.clear()
            self.logger.info("🔄 Локальные кэши контроллера очищены")

            # Очищаем кэш DataModel если есть
            if hasattr(self.model, 'data_model') and self.model.data_model:
                if hasattr(self.model.data_model, 'clear_cache'):
                    self.model.data_model.clear_cache()
                    self.logger.info("🔄 Кэш DataModel очищен")

            self.logger.info("✅ Все кэши системы очищены")

        except Exception as e:
            self.logger.error(f"Ошибка очистки кэшей: {e}")

    def cleanup(self):
        """Финальная очистка ресурсов контроллера"""
        try:
            self.logger.info("Начало финальной очистки MainController")

            # Останавливаем все процессы
            self.is_processing = False
            self.is_loading = False

            # Очищаем все кэши
            self.force_clear_all_caches()

            # Очищаем callbacks
            self._ui_callbacks.clear()

            # Обнуляем ссылки на сервисы
            self.filtering_service = None
            self.plot_manager = None
            self.report_generator = None
            self.sop_manager = None

            # Обнуляем Use Cases
            self.filter_parameters_use_case = None
            self.find_changed_params_use_case = None
            self.time_range_init_use_case = None

            # Очищаем UI реестр
            self._ui_registry.clear()
            self._ui_search_strategies.clear()

            # Обнуляем ссылки на модель и view
            self.ui_components = None
            self.model = None
            self.view = None

            self.logger.info("MainController полностью очищен")

        except Exception as e:
            self.logger.error(f"Ошибка финальной очистки MainController: {e}")

    def __str__(self):
        return f"MainController(file={self.current_file_path}, processing={self.is_processing}, loading={self.is_loading})"

    def __repr__(self):
        return self.__str__()

    def __del__(self):
        """Деструктор"""
        try:
            if hasattr(self, 'logger'):
                self.logger.info("MainController удаляется из памяти")
        except:
            pass  # Игнорируем ошибки в деструкторе

    def update_parameters(self, parameters: List[Dict[str, Any]]):
        """Обновление списка параметров во всех панелях"""
        try:
            self.logger.info(
                f"📊 UIComponents.update_parameters вызван с {len(parameters)} параметрами")

            if not hasattr(self.view, 'ui_components') or not self.view.ui_components:
                self.logger.error("❌ ui_components не создан!")
                return

            # Обновляем панель параметров
            if hasattr(self.view.ui_components, 'update_parameters'):
                self.view.ui_components.update_parameters(parameters)
                self.logger.info("✅ ui_components.update_parameters выполнен")

            # Генерируем событие
            self._emit_event('parameter_updated', {'count': len(parameters)})

            self.logger.info(
                f"✅ Параметры обновлены в UI: {len(parameters)} элементов")

        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления параметров: {e}")
            import traceback
            traceback.print_exc()

    def disable_changed_only_checkbox(self):
        """Отключение чекбокса 'только изменяемые' в SmartFilterPanel"""
        try:
            filter_panel = self.get_ui_component('filter_panel')
            if filter_panel and hasattr(filter_panel, 'disable_changed_only_checkbox'):
                filter_panel.disable_changed_only_checkbox()
                self.logger.debug("Чекбокс 'только изменяемые' отключен")
            else:
                self.logger.warning(
                    "Метод disable_changed_only_checkbox не найден в filter_panel")
        except Exception as e:
            self.logger.error(f"Ошибка отключения чекбокса: {e}")

    def _sync_with_time_panel(self):
        """Синхронизация с панелью времени"""
        try:
            filter_panel = self.get_ui_component('filter_panel')
            if filter_panel and hasattr(filter_panel, '_sync_with_time_panel'):
                filter_panel._sync_with_time_panel()
                self.logger.debug("Синхронизация с time_panel выполнена")
            else:
                self.logger.debug(
                    "Метод _sync_with_time_panel не найден в filter_panel")
        except Exception as e:
            self.logger.error(f"Ошибка синхронизации с time_panel: {e}")

    def _update_parameter_display(self, parameters: List[Dict[str, Any]]):
        """Обновление отображения параметров"""
        try:
            self._update_ui_with_filtered_params(parameters)
            self.logger.debug(
                f"Отображение параметров обновлено: {len(parameters)}")
        except Exception as e:
            self.logger.error(f"Ошибка обновления отображения параметров: {e}")

    def _matches_system_filter(self, parameter: Dict[str, Any], system_filter: str) -> bool:
        """Проверка соответствия параметра системному фильтру"""
        try:
            signal_code = parameter.get('signal_code', '').upper()
            description = parameter.get('description', '').upper()

            # Системные фильтры
            system_patterns = {
                'traction': ['TRACTION', 'MOTOR', 'INV', 'DRIVE'],
                'brake': ['BRAKE', 'BCU', 'PRESSURE', 'STOP'],
                'door': ['DOOR', 'GATE', 'LOCK'],
                'hvac': ['HVAC', 'TEMP', 'CLIMATE', 'FAN'],
                'lighting': ['LIGHT', 'LED', 'LAMP'],
                'safety': ['SAFETY', 'EMERGENCY', 'ALARM', 'FIRE'],
                'communication': ['COMM', 'RADIO', 'GSM', 'WIFI'],
                'diagnostic': ['DIAG', 'STATUS', 'HEARTBEAT', 'VERSION']
            }

            patterns = system_patterns.get(system_filter.lower(), [])
            return any(pattern in signal_code or pattern in description for pattern in patterns)

        except Exception as e:
            self.logger.error(f"Ошибка проверки системного фильтра: {e}")
            return False
