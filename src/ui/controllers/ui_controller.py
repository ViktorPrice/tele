import logging
from typing import Any, Callable, Dict, List, Optional

class UIController:
    """Контроллер для управления UI-компонентами и событиями"""

    def __init__(self, view, event_emitter):
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_emitter = event_emitter  # Функция или объект для эмиссии событий
        self._ui_registry: Dict[str, Any] = {}
        self._ui_search_strategies: Dict[str, List[Callable]] = {}
        self._ui_callbacks: Dict[str, List[Callable]] = {
            "data_loaded": [],
            "parameters_updated": [],
            "filters_applied": [],
            "time_changed": [],
            "changed_params_filter_applied": [],
            "diagnostic_filters_applied": [],
            "plot_requested": [],
        }

    def update_ui_after_data_load(self):
        """Обновление UI после загрузки данных"""
        try:
            self.logger.info("Обновление UI после загрузки данных")

            # Получаем временной диапазон из модели или data_loader
            from_time, to_time = "", ""
            if hasattr(self, "model") and self.model:
                if hasattr(self.model, "get_time_range_fields"):
                    time_fields = self.model.get_time_range_fields()
                    if time_fields:
                        from_time = time_fields.get("from_time", "")
                        to_time = time_fields.get("to_time", "")

            # Обновляем временную панель
            time_panel = self.get_ui_component("time_panel")
            if time_panel and hasattr(time_panel, "update_time_fields"):
                time_panel.update_time_fields(from_time, to_time)

            # Получаем все параметры из модели
            all_params = []
            if hasattr(self, "model") and self.model:
                if hasattr(self.model, "get_parameters"):
                    all_params = self.model.get_parameters()
                elif hasattr(self.model, "get_all_parameters"):
                    all_params = self.model.get_all_parameters()
                elif hasattr(self.model, "data_loader") and hasattr(self.model.data_loader, "get_parameters"):
                    all_params = self.model.data_loader.get_parameters()

            # Обновляем панель параметров
            self.update_parameters(all_params)

            self.logger.info("UI успешно обновлен после загрузки данных")

        except Exception as e:
            self.logger.error(f"Ошибка обновления UI после загрузки данных: {e}")

    def set_ui_components(self, ui_components):
        """Установка UI компонентов"""
        try:
            self.view.ui_components = ui_components
            self.logger.info("UI компоненты установлены в контроллере")
        except Exception as e:
            self.logger.error(f"Ошибка установки UI компонентов: {e}")

    def _setup_component_search_strategies(self, component_name: str):
        """Настройка стратегий поиска для каждого компонента"""
        self._ui_search_strategies[component_name] = [
            lambda name=component_name: (
                getattr(self.view.ui_components, name, None)
                if hasattr(self.view, "ui_components") and self.view.ui_components
                else None
            ),
            lambda name=component_name: getattr(self.view, name, None),
            lambda name=component_name: (
                self.view.get_component(name) if hasattr(self.view, "get_component") else None
            ),
            lambda name=component_name: (
                getattr(self.view.ui_components, f"_{name}", None)
                if hasattr(self.view, "ui_components") and self.view.ui_components
                else None
            ),
            lambda name=component_name: (
                getattr(self.view.ui_components, f"_get_{name}", lambda: None)()
                if hasattr(self.view, "ui_components")
                and self.view.ui_components
                and hasattr(self.view.ui_components, f"_get_{name}")
                else None
            ),
        ]

    def _find_ui_component_unified(self, component_name: str):
        """ЕДИНЫЙ метод поиска UI компонентов"""
        try:
            strategies = self._ui_search_strategies.get(component_name, [])

            for i, strategy in enumerate(strategies):
                try:
                    component = strategy()
                    if component:
                        self.logger.debug(f"Найден {component_name} через стратегию {i+1}")
                        return component
                except Exception as e:
                    self.logger.debug(f"Стратегия {i+1} для {component_name} не сработала: {e}")
                    continue

            self.logger.warning(f"Компонент {component_name} не найден во всех стратегиях")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка поиска компонента {component_name}: {e}")
            return None

    def get_ui_component(self, component_name: str):
        """Публичный метод получения UI компонента"""
        if component_name in self._ui_registry:
            component = self._ui_registry[component_name]
            if component:
                return component

        component = self._find_ui_component_unified(component_name)
        self._ui_registry[component_name] = component
        return component

    def refresh_ui_registry(self):
        """Обновление реестра UI компонентов"""
        try:
            self.logger.info("Обновление реестра UI компонентов")
            self._ui_registry.clear()

            if not hasattr(self.view, "ui_components") or not self.view.ui_components:
                self.logger.debug("UI компоненты еще не созданы, пропускаем инициализацию реестра")
                return

            if (
                not hasattr(self.view.ui_components, "is_initialized")
                or not self.view.ui_components.is_initialized
            ):
                self.logger.debug("UI компоненты не полностью инициализированы, пропускаем")
                return

            ui_components = [
                "time_panel",
                "parameter_panel",
                "filter_panel",
                "action_panel",
                "plot_panel",
                "diagnostic_panel",
            ]

            for component_name in ui_components:
                self._setup_component_search_strategies(component_name)
                component = self._find_ui_component_unified(component_name)
                self._ui_registry[component_name] = component

                if component:
                    self.logger.debug(f"Компонент {component_name} найден и зарегистрирован")
                else:
                    self.logger.debug(f"Компонент {component_name} не найден")

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
                    self.logger.error(f"Ошибка отложенного обновления реестра: {e}")

            if hasattr(self.view, "root") and self.view.root:
                self.view.root.after(delay_ms, refresh_after_delay)
                self.logger.debug(f"Запланировано отложенное обновление реестра через {delay_ms}мс")
            else:
                refresh_after_delay()
                self.logger.debug("Выполнено немедленное обновление реестра (fallback)")

        except Exception as e:
            self.logger.error(f"Ошибка планирования отложенного обновления: {e}")

    def add_ui_callback(self, event_type: str, callback: Callable):
        """Добавление callback для события UI"""
        if event_type not in self._ui_callbacks:
            self._ui_callbacks[event_type] = []
        self._ui_callbacks[event_type].append(callback)

    def emit_event(self, event_type: str, data: Any):
        """Отправка события подписчикам"""
        callbacks = self._ui_callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Ошибка в callback для события {event_type}: {e}")

    def update_parameters(self, parameters: List[Dict[str, Any]], emit_event: bool = True):
        """Единый метод обновления параметров во всех UI компонентах"""
        try:
            self.logger.info(f"Обновление параметров в UI: {len(parameters)} элементов")

            # Обновляем parameter_panel
            parameter_panel = self.get_ui_component("parameter_panel")
            if parameter_panel:
                if hasattr(parameter_panel, "update_parameters"):
                    parameter_panel.update_parameters(parameters)
                    self.logger.info("✅ Параметры обновлены в parameter_panel")
                else:
                    self.logger.warning("parameter_panel не поддерживает update_parameters")

            # Обновляем счетчик параметров в view
            if hasattr(self.view, "update_parameter_count"):
                self.view.update_parameter_count(len(parameters))
                self.logger.info("✅ Счетчик параметров обновлен")

            # Эмитируем событие если нужно
            if emit_event:
                self.emit_event("parameters_updated", {"count": len(parameters)})
                self.logger.info("✅ Событие parameters_updated эмитировано")

        except Exception as e:
            self.logger.error(f"Ошибка обновления параметров в UI: {e}")

    def set_filtering_service(self, filtering_service):
        """Установка сервиса фильтрации"""
        try:
            self.filtering_service = filtering_service
            self.logger.info("Сервис фильтрации установлен в UIController")
        except Exception as e:
            self.logger.error(f"Ошибка установки сервиса фильтрации: {e}")

    def set_plot_manager(self, plot_manager):
        """Установка plot_manager"""
        try:
            self.plot_manager = plot_manager
            self.logger.info("PlotManager установлен в UIController")
        except Exception as e:
            self.logger.error(f"Ошибка установки plot_manager: {e}")

    def set_report_manager(self, report_manager):
        """Установка report_manager"""
        try:
            self.report_manager = report_manager
            self.logger.info("ReportManager установлен в UIController")
        except Exception as e:
            self.logger.error(f"Ошибка установки report_manager: {e}")

    def set_sop_manager(self, sop_manager):
        """Установка sop_manager"""
        try:
            self.sop_manager = sop_manager
            self.logger.info("SOPManager установлен в UIController")
        except Exception as e:
            self.logger.error(f"Ошибка установки sop_manager: {e}")

    def get_time_range(self):
        """Получение временного диапазона из time_panel"""
        try:
            time_panel = self.get_ui_component("time_panel")
            if time_panel and hasattr(time_panel, "get_time_range"):
                return time_panel.get_time_range()
            self.logger.warning("time_panel отсутствует или не поддерживает get_time_range")
            return None, None
        except Exception as e:
            self.logger.error(f"Ошибка получения временного диапазона: {e}")
            return None, None

    def get_selected_parameters(self):
        """Получение выбранных параметров из parameter_panel"""
        try:
            parameter_panel = self.get_ui_component("parameter_panel")
            if parameter_panel:
                if hasattr(parameter_panel, "get_selected_parameters"):
                    return parameter_panel.get_selected_parameters()
                elif hasattr(parameter_panel, "selected_parameters"):
                    return parameter_panel.selected_parameters
                else:
                    self.logger.warning("parameter_panel не имеет выбранных параметров")
                    return []
            else:
                self.logger.warning("parameter_panel не найден")
                return []
        except Exception as e:
            self.logger.error(f"Ошибка получения выбранных параметров: {e}")
            return []
