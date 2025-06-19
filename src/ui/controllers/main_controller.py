import logging
from typing import Dict, List, Any, Optional, Tuple, Callable, Type, TypeVar, Generic

T = TypeVar('T')

class ControllerError(Exception):
    """Базовый класс для ошибок контроллера"""
    pass

class ControllerNotInitializedError(ControllerError):
    """Исключение при попытке использовать неинициализированный контроллер"""
    pass

class StateError(ControllerError):
    """Исключение при попытке выполнить операцию в неверном состоянии"""
    pass

class MainController:
    """
    Главный контроллер приложения для координации работы подконтроллеров
    
    Отвечает за:
    - Координацию взаимодействия между подконтроллерами
    - Делегирование операций соответствующим подконтроллерам
    - Управление состоянием приложения
    - Обработку ошибок и логирование
    """
    
    def __init__(self, model: Any, view: Any):
        """
        Инициализация главного контроллера
        
        Args:
            model: Модель данных приложения
            view: Представление приложения
        """
        self.model = model
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Подконтроллеры
        self.data_loader_controller = None
        self.filter_controller = None
        self.diagnostic_controller = None
        self.ui_controller = None
        self.plot_controller = None
        self.report_controller = None
        self.state_controller = None
        
        # Состояние
        self.is_processing = False
        self.is_loading = False
        self.current_file_path: Optional[str] = None
        
        # События
        self._event_handlers: Dict[str, List[Callable]] = {}

        # Добавлено для совместимости с _ui_callbacks
        self._ui_callbacks = self._event_handlers
        
        self.logger.info("MainController инициализирован")

    def _check_state(self) -> None:
        """Проверка состояния контроллера перед выполнением операций"""
        if self.is_processing:
            raise StateError("Контроллер занят обработкой другой операции")
        if self.is_loading:
            raise StateError("Идет загрузка данных")

    def _set_controller(self, controller_name: str, controller: Any, controller_type: Optional[Type] = None) -> None:
        """
        Универсальный метод установки подконтроллера
        
        Args:
            controller_name: Имя устанавливаемого контроллера
            controller: Экземпляр контроллера
            controller_type: Ожидаемый тип контроллера (опционально)
        
        Raises:
            ValueError: Если контроллер уже установлен
            TypeError: Если тип контроллера не соответствует ожидаемому
        """
        if getattr(self, controller_name) is not None:
            self.logger.warning(f"{controller_name} уже установлен")
            raise ValueError(f"{controller_name} уже установлен")
            
        if controller_type and not isinstance(controller, controller_type):
            raise TypeError(f"Контроллер {controller_name} должен быть типа {controller_type}")
            
        setattr(self, controller_name, controller)
        self.logger.info(f"{controller_name} установлен")

    # === Методы внедрения зависимостей ===
    def set_data_loader_controller(self, controller: Any) -> None:
        """Установка контроллера загрузки данных"""
        self._set_controller("data_loader_controller", controller)

    def set_filter_controller(self, controller: Any) -> None:
        """Установка контроллера фильтрации"""
        self._set_controller("filter_controller", controller)

    def set_diagnostic_controller(self, controller: Any) -> None:
        """Установка контроллера диагностики"""
        self._set_controller("diagnostic_controller", controller)

    def set_ui_controller(self, controller: Any) -> None:
        """Установка контроллера UI"""
        self._set_controller("ui_controller", controller)

    def set_plot_controller(self, controller: Any) -> None:
        """Установка контроллера графиков"""
        self._set_controller("plot_controller", controller)

    def set_report_controller(self, controller: Any) -> None:
        """Установка контроллера отчетов"""
        self._set_controller("report_controller", controller)

    def set_state_controller(self, controller: Any) -> None:
        """Установка контроллера состояния"""
        self._set_controller("state_controller", controller)

    # === Методы управления сервисами UI ===
    def set_service(self, service_type: str, service: Any) -> None:
        """
        Универсальный метод установки сервиса в UI контроллер
        
        Args:
            service_type: Тип сервиса ('filtering', 'plot', 'report', 'sop')
            service: Экземпляр сервиса
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
            
        service_setters = {
            'filtering': self.ui_controller.set_filtering_service,
            'plot': self.ui_controller.set_plot_manager,
            'report': self.ui_controller.set_report_manager,
            'sop': self.ui_controller.set_sop_manager
        }
        
        if service_type not in service_setters:
            raise ValueError(f"Неизвестный тип сервиса: {service_type}")
            
        service_setters[service_type](service)
        self.logger.info(f"Сервис {service_type} установлен")

    # === Делегирующие методы для DataLoaderController ===
    def upload_csv(self) -> None:
        """
        Делегирование загрузки CSV файла
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
            StateError: Если контроллер занят
        """
        self._check_state()
        if not self.data_loader_controller:
            raise ControllerNotInitializedError("DataLoaderController не инициализирован")
        
        try:
            self.is_loading = True
            self.data_loader_controller.upload_csv()
        finally:
            self.is_loading = False

    def load_csv_file(self, file_path: str) -> None:
        """
        Делегирование загрузки конкретного CSV файла
        
        Args:
            file_path: Путь к CSV файлу
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
            StateError: Если контроллер занят
        """
        self._check_state()
        if not self.data_loader_controller:
            raise ControllerNotInitializedError("DataLoaderController не инициализирован")
        
        try:
            self.is_loading = True
            self.data_loader_controller.load_csv_file(file_path)
            self.current_file_path = file_path
            self.logger.info(f"CSV файл загружен: {file_path}")
            # Обновление UI после загрузки данных
            self.update_ui_after_data_load()
        finally:
            self.is_loading = False

    # === Делегирующие методы для FilterController ===
    def apply_filters(self, changed_only: bool = False, **kwargs) -> None:
        """
        Делегирование применения фильтров
        
        Args:
            changed_only: Флаг фильтрации только по изменённым параметрам
            **kwargs: Дополнительные параметры фильтрации
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
            StateError: Если контроллер занят
        """
        self._check_state()
        if not self.filter_controller:
            raise ControllerNotInitializedError("FilterController не инициализирован")
        
        try:
            self.is_processing = True
            self.filter_controller.apply_filters(changed_only, **kwargs)
        finally:
            self.is_processing = False

    def clear_all_filters(self) -> None:
        """
        Делегирование очистки всех фильтров
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.filter_controller:
            raise ControllerNotInitializedError("FilterController не инициализирован")
        self.filter_controller.clear_all_filters()

    def apply_changed_parameters_filter(self, auto_recalc: bool = False) -> None:
        """
        Применение фильтра изменяемых параметров с приоритетом
        
        Args:
            auto_recalc: Флаг автоматического пересчета
        """
        self.logger.info(f"apply_changed_parameters_filter вызван с auto_recalc={auto_recalc}")
        self.apply_filters(changed_only=True, auto_recalc=auto_recalc)

    # === Делегирующие методы для DiagnosticController ===
    def apply_diagnostic_filters(self, diagnostic_criteria: Dict[str, List[str]]) -> None:
        """
        Делегирование применения диагностических фильтров
        
        Args:
            diagnostic_criteria: Критерии диагностической фильтрации
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.diagnostic_controller:
            raise ControllerNotInitializedError("DiagnosticController не инициализирован")
        self.diagnostic_controller.apply_diagnostic_filters(diagnostic_criteria)

    def reset_diagnostic_filters(self) -> None:
        """
        Делегирование сброса диагностических фильтров
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.diagnostic_controller:
            raise ControllerNotInitializedError("DiagnosticController не инициализирован")
        self.diagnostic_controller.reset_diagnostic_filters()

    def perform_diagnostic_analysis(self) -> None:
        """
        Делегирование выполнения диагностического анализа
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
            StateError: Если контроллер занят
        """
        self._check_state()
        if not self.diagnostic_controller:
            raise ControllerNotInitializedError("DiagnosticController не инициализирован")
        
        try:
            self.is_processing = True
            self.diagnostic_controller.perform_diagnostic_analysis()
        finally:
            self.is_processing = False

    def diagnose_changed_params_issue(self) -> None:
        """
        Делегирование диагностики проблем с изменяемыми параметрами
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.diagnostic_controller:
            raise ControllerNotInitializedError("DiagnosticController не инициализирован")
        self.diagnostic_controller.diagnose_changed_params_issue()

    def diagnose_time_range_analysis(self, start_time_str: str, end_time_str: str) -> bool:
        """
        Делегирование диагностики временного диапазона
        
        Args:
            start_time_str: Начальное время в строковом формате
            end_time_str: Конечное время в строковом формате
            
        Returns:
            bool: Результат диагностики
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.diagnostic_controller:
            raise ControllerNotInitializedError("DiagnosticController не инициализирован")
        return self.diagnostic_controller.diagnose_time_range_analysis(start_time_str, end_time_str)

    # === Делегирующие методы для UIController ===
    def get_ui_component(self, component_name: str) -> Any:
        """
        Делегирование получения UI компонента
        
        Args:
            component_name: Имя компонента
            
        Returns:
            Any: UI компонент или None
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        return self.ui_controller.get_ui_component(component_name)

    def refresh_ui_registry(self) -> None:
        """
        Делегирование обновления реестра UI компонентов
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        self.ui_controller.refresh_ui_registry()

    def delayed_refresh_ui_registry(self, delay_ms: int = 100) -> None:
        """
        Делегирование отложенного обновления реестра UI
        
        Args:
            delay_ms: Задержка в миллисекундах
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        self.ui_controller.delayed_refresh_ui_registry(delay_ms)

    def get_selected_parameters(self) -> List[Dict[str, Any]]:
        """
        Делегирование получения выбранных параметров
        
        Returns:
            List[Dict[str, Any]]: Список выбранных параметров
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        return self.ui_controller.get_selected_parameters()

    def get_time_range(self) -> Tuple[str, str]:
        """
        Делегирование получения временного диапазона
        
        Returns:
            Tuple[str, str]: Кортеж (начальное_время, конечное_время)
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        return self.ui_controller.get_time_range()

    def update_time_range(self, from_time: str, to_time: str) -> bool:
        """
        Делегирование обновления временного диапазона
        
        Args:
            from_time: Начальное время
            to_time: Конечное время
            
        Returns:
            bool: Успешность операции
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        return self.ui_controller.update_time_range(from_time, to_time)

    def reset_time_range(self) -> bool:
        """
        Делегирование сброса временного диапазона
        
        Returns:
            bool: Успешность операции
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        return self.ui_controller.reset_time_range()

    def get_filter_statistics(self) -> Dict[str, Any]:
        """
        Делегирование получения статистики фильтров
        
        Returns:
            Dict[str, Any]: Статистика фильтров
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        return self.ui_controller.get_filter_statistics()

    def get_application_info(self) -> Dict[str, Any]:
        """
        Делегирование получения информации о приложении
        
        Returns:
            Dict[str, Any]: Информация о приложении
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        return self.ui_controller.get_application_info()

    # === Делегирующие методы для PlotController ===
    def build_plot(self) -> None:
        """
        Делегирование построения графиков
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
            StateError: Если контроллер занят
        """
        self._check_state()
        if not self.plot_controller:
            raise ControllerNotInitializedError("PlotController не инициализирован")
        
        try:
            self.is_processing = True
            plot_type = 'line'  # Значение по умолчанию, можно изменить при необходимости
            parameters = self.get_selected_parameters()
            self.plot_controller.build_plot(plot_type, parameters)
        finally:
            self.is_processing = False

    def plot_selected_parameters(self) -> None:
        """
        Делегирование построения графиков для выбранных параметров
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
            StateError: Если контроллер занят
        """
        self._check_state()
        if not self.plot_controller:
            raise ControllerNotInitializedError("PlotController не инициализирован")
        
        try:
            self.is_processing = True
            self.plot_controller.plot_selected_parameters()
        finally:
            self.is_processing = False

    def export_all_plots(self) -> None:
        """
        Делегирование экспорта всех графиков
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.plot_controller:
            raise ControllerNotInitializedError("PlotController не инициализирован")
        self.plot_controller.export_all_plots()

    def clear_all_plots(self) -> None:
        """
        Делегирование очистки всех графиков
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.plot_controller:
            raise ControllerNotInitializedError("PlotController не инициализирован")
        self.plot_controller.clear_all_plots()

    # === Делегирующие методы для ReportController ===
    def generate_report(self) -> None:
        """
        Делегирование генерации отчета
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
            StateError: Если контроллер занят
        """
        self._check_state()
        if not self.report_controller:
            raise ControllerNotInitializedError("ReportController не инициализирован")
        
        try:
            self.is_processing = True
            self.report_controller.generate_report()
        finally:
            self.is_processing = False

    # === Делегирующие методы для StateController ===
    def force_clear_all_caches(self) -> None:
        """
        Делегирование принудительной очистки всех кэшей
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.state_controller:
            raise ControllerNotInitializedError("StateController не инициализирован")
        self.state_controller.force_clear_all_caches()

    def cleanup(self) -> None:
        """
        Делегирование финальной очистки ресурсов
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.state_controller:
            raise ControllerNotInitializedError("StateController не инициализирован")
        self.state_controller.cleanup()

    # === Общие утилитные методы ===
    def update_parameters(self, parameters: List[Dict[str, Any]]) -> None:
        """
        Делегирование обновления списка параметров во всех панелях
        
        Args:
            parameters: Список параметров для обновления
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        self.ui_controller.update_parameters(parameters)

    def disable_changed_only_checkbox(self) -> None:
        """
        Делегирование отключения чекбокса 'только изменяемые'
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        self.ui_controller.disable_changed_only_checkbox()

    def select_all_parameters(self) -> None:
        """
        Делегирование выбора всех параметров
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        self.ui_controller.select_all_parameters()

    def deselect_all_parameters(self) -> None:
        """
        Делегирование отмены выбора всех параметров
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        self.ui_controller.deselect_all_parameters()

    def get_selected_count(self) -> int:
        """
        Делегирование получения количества выбранных параметров
        
        Returns:
            int: Количество выбранных параметров
            
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.ui_controller:
            raise ControllerNotInitializedError("UIController не инициализирован")
        return self.ui_controller.get_selected_count()

    def update_ui_after_data_load(self) -> None:
        """
        Делегирование обновления UI после загрузки данных
        
        Raises:
            ControllerNotInitializedError: Если контроллер не инициализирован
        """
        if not self.data_loader_controller:
            raise ControllerNotInitializedError("DataLoaderController не инициализирован")
        self.data_loader_controller.update_ui_after_data_load()

    def set_ui_components(self, ui_components: Any) -> None:
        """
        Установка UI компонентов в контроллере
        
        Args:
            ui_components: Компоненты пользовательского интерфейса
        """
        self.ui_components = ui_components
        self.logger.info("UI компоненты установлены")

    # === Устаревшие методы для обратной совместимости ===
    def set_filtering_service(self, service: Any) -> None:
        """Устаревший метод. Используйте set_service('filtering', service)"""
        self.logger.warning("set_filtering_service устарел, используйте set_service('filtering', service)")
        self.set_service('filtering', service)

    def set_plot_manager(self, service: Any) -> None:
        """Устаревший метод. Используйте set_service('plot', service)"""
        self.logger.warning("set_plot_manager устарел, используйте set_service('plot', service)")
        self.set_service('plot', service)

    def set_report_generator(self, service: Any) -> None:
        """Устаревший метод. Используйте set_service('report', service)"""
        self.logger.warning("set_report_generator устарел, используйте set_service('report', service)")
        self.set_service('report', service)

    def set_report_manager(self, service: Any) -> None:
        """Устаревший метод. Используйте set_service('report', service)"""
        self.logger.warning("set_report_manager устарел, используйте set_service('report', service)")
        self.set_service('report', service)

    def set_sop_manager(self, service: Any) -> None:
        """Устаревший метод. Используйте set_service('sop', service)"""
        self.logger.warning("set_sop_manager устарел, используйте set_service('sop', service)")
        self.set_service('sop', service)

    # === Методы работы с событиями ===
    def subscribe(self, event_name: str, handler: Callable) -> None:
        """
        Подписка на событие
        
        Args:
            event_name: Имя события
            handler: Обработчик события
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)
        self.logger.debug(f"Добавлен обработчик для события {event_name}")

    def emit_event(self, event_name: str, event_data: Any) -> None:
        """
        Эмиссия события
        
        Args:
            event_name: Имя события
            event_data: Данные события
        """
        # Ограничение длины вывода event_data до 200 символов
        event_data_str = str(event_data)
        if len(event_data_str) > 200:
            event_data_str = event_data_str[:200] + "..."
        self.logger.info(f"Эмиссия события: {event_name}, данные: {event_data_str}")
        if event_name in self._event_handlers:
            for handler in self._event_handlers[event_name]:
                try:
                    handler(event_data)
                except Exception as e:
                    self.logger.error(f"Ошибка в обработчике события {event_name}: {e}")

    def __str__(self) -> str:
        """Строковое представление контроллера"""
        return (f"MainController(file={self.current_file_path}, "
                f"processing={self.is_processing}, loading={self.is_loading})")

    def __repr__(self) -> str:
        return self.__str__()

    def __del__(self) -> None:
        """Деструктор с очисткой ресурсов"""
        try:
            if hasattr(self, "logger"):
                self.logger.info("MainController удаляется из памяти")
            if hasattr(self, "_event_handlers"):
                self._event_handlers.clear()
        except:
            pass  # Игнорируем ошибки в деструкторе

    def _update_parameter_display(self):
        """Заглушка метода _update_parameter_display для совместимости"""
        if hasattr(self, "logger"):
            self.logger.warning("_update_parameter_display вызван, но не реализован")

    def _matches_system_filter(self, parameter):
        """Заглушка метода _matches_system_filter для совместимости"""
        if hasattr(self, "logger"):
            self.logger.warning("_matches_system_filter вызван, но не реализован")
        return True
