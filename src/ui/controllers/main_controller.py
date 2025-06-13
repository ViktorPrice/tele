"""
Главный контроллер приложения без дублирований с приоритетной логикой изменяемых параметров
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


class MainController:
    """Главный контроллер приложения без дублирований"""

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)

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
            'changed_params_filter_applied': []  # Приоритетный callback
        }

        # Инициализация
        self._setup_use_cases()
        # УБИРАЕМ: self._setup_unified_ui_registry()  # UI компоненты еще не созданы!

        self.logger.info("MainController инициализирован без дублирований")


    # === МЕТОДЫ НАСТРОЙКИ ===

    def _setup_use_cases(self):
        """Настройка Use Cases"""
        if not USE_CASES_AVAILABLE:
            self.logger.warning("Use Cases недоступны, используется fallback режим")
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
                    self.logger.debug(f"✅ Компонент {component_name} найден и зарегистрирован")
                else:
                    self.logger.debug(f"⚠️ Компонент {component_name} не найден (возможно, еще не создан)")
                    
            self.logger.info(f"Реестр UI компонентов настроен: {len([c for c in self._ui_registry.values() if c])} из {len(ui_components)} найдено")
            
        except Exception as e:
            self.logger.error(f"Ошибка настройки реестра UI компонентов: {e}")


    def _setup_component_search_strategies(self, component_name: str):
        """Настройка стратегий поиска для каждого компонента"""
        self._ui_search_strategies[component_name] = [
            # Стратегия 1: Через ui_components (если установлен)
            lambda name=component_name: getattr(self.view.ui_components, name, None) if hasattr(self.view, 'ui_components') and self.view.ui_components else None,
            
            # Стратегия 2: Прямой доступ через view
            lambda name=component_name: getattr(self.view, name, None),
            
            # Стратегия 3: Через get_component
            lambda name=component_name: self.view.get_component(name) if hasattr(self.view, 'get_component') else None,
            
            # Стратегия 4: Через приватные методы ui_components
            lambda name=component_name: getattr(self.view.ui_components, f'_{name}', None) if hasattr(self.view, 'ui_components') and self.view.ui_components else None,
            
            # Стратегия 5: Через метод _get_*
            lambda name=component_name: getattr(self.view.ui_components, f'_get_{name}', lambda: None)() if hasattr(self.view, 'ui_components') and self.view.ui_components and hasattr(self.view.ui_components, f'_get_{name}') else None
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
                self.logger.debug("UI компоненты еще не созданы, пропускаем инициализацию реестра")
                return
            
            # Проверяем, что ui_components инициализирован
            if not hasattr(self.view.ui_components, 'is_initialized') or not self.view.ui_components.is_initialized:
                self.logger.debug("UI компоненты не полностью инициализированы, пропускаем")
                return
                
            self._setup_unified_ui_registry()
            self.logger.info("Реестр UI компонентов успешно обновлен")
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления реестра UI: {e}")


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
            else:
                self.logger.info("UIComponents установлен, ожидание полной инициализации")
                
        except Exception as e:
            self.logger.error(f"Ошибка установки UI компонентов: {e}")


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
                        self.logger.debug(f"Получено {len(selected)} выбранных параметров через parameter_panel")
                        return selected
                elif hasattr(parameter_panel, 'get_checked_parameters'):
                    selected = parameter_panel.get_checked_parameters()
                    if selected:
                        self.logger.debug(f"Получено {len(selected)} выбранных параметров через get_checked_parameters")
                        return selected

            # Способ 2: Через view
            if hasattr(self.view, 'get_selected_parameters'):
                selected = self.view.get_selected_parameters()
                if selected:
                    self.logger.debug(f"Получено {len(selected)} выбранных параметров через view")
                    return selected

            # Способ 3: Через ui_components
            if (hasattr(self.view, 'ui_components') and 
                self.view.ui_components and 
                hasattr(self.view.ui_components, 'get_selected_parameters')):
                selected = self.view.ui_components.get_selected_parameters()
                if selected:
                    self.logger.debug(f"Получено {len(selected)} выбранных параметров через ui_components")
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
                    self.logger.debug(f"Время получено через time_panel: {result}")
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
                
                result = (self.model.data_loader.min_timestamp, self.model.data_loader.max_timestamp)
                if result[0] and result[1]:
                    self.logger.debug(f"Время получено через data_loader: {result}")
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
            self.logger.info(f"Обновление временного диапазона: {from_time} - {to_time}")
            
            # Валидация времени
            if not self._validate_time_range(from_time, to_time):
                return False

            # Обновляем в time_panel
            time_panel = self.get_ui_component('time_panel')
            if time_panel:
                if hasattr(time_panel, 'set_time_range'):
                    time_panel.set_time_range(from_time, to_time)
                    self.logger.info("Временной диапазон обновлен в time_panel")
                elif hasattr(time_panel, 'update_time_fields'):
                    time_panel.update_time_fields(from_time=from_time, to_time=to_time)
                    self.logger.info("Временной диапазон обновлен через update_time_fields")

            # Уведомляем о изменении времени
            self._emit_event('time_changed', {
                'from_time': from_time,
                'to_time': to_time
            })

            return True

        except Exception as e:
            self.logger.error(f"Ошибка обновления временного диапазона: {e}")
            return False

    def reset_time_range(self):
        """Сброс временного диапазона к значениям по умолчанию"""
        try:
            if self._has_data():
                # Используем диапазон из данных
                time_fields = self._get_time_fields_from_model() or self._get_time_fields_from_data_loader()
                if time_fields:
                    self.update_time_range(time_fields['from_time'], time_fields['to_time'])
                    self.logger.info("Временной диапазон сброшен к значениям из данных")
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
            self.logger.error(f"Ошибка получения временных полей из модели: {e}")
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
            self.logger.error(f"Ошибка получения временных полей из data_loader: {e}")
            return None

    def _validate_time_range(self, from_time: str, to_time: str) -> bool:
        """Валидация временного диапазона"""
        try:
            start = datetime.strptime(from_time, '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(to_time, '%Y-%m-%d %H:%M:%S')
            
            if start >= end:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Время начала должно быть меньше времени окончания")
                return False
                
            return True
            
        except ValueError as e:
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Неверный формат времени: {e}")
            return False

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
                        self.view.root.after(0, lambda: self._handle_file_load_result(success, file_path))
                except Exception as e:
                    self.logger.error(f"Ошибка в потоке загрузки: {e}")
                    if hasattr(self.view, 'root'):
                        self.view.root.after(0, lambda: self._handle_file_load_error(e))
            
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
                self.logger.error(f"Не удалось загрузить CSV файл: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV файла {file_path}: {e}")
            raise

    def _handle_file_load_result(self, success: bool, file_path: str):
        """Обработка результата загрузки файла с интеграцией МЦД информации"""
        try:
            self._stop_loading()
            
            if success:
                self.logger.info(f"Файл успешно загружен: {file_path}")
                
                # Извлекаем информацию о МЦД из CSV загрузчика
                mcd_info = None
                if hasattr(self.model, 'data_loader') and self.model.data_loader:
                    # Используем метод из csv_loader.py для извлечения МЦД информации
                    mcd_info = self.model.data_loader.extract_and_update_mcd_info(file_path)
                    
                    # Если метод возвращает None, пытаемся извлечь из view
                    if not mcd_info and hasattr(self.view, 'extract_and_update_mcd_info'):
                        self.view.extract_and_update_mcd_info(file_path)
                
                # Обновляем информацию о файле в view
                records_count = 0
                if hasattr(self.model, 'data_loader') and self.model.data_loader:
                    records_count = getattr(self.model.data_loader, 'records_count', 0)
                elif hasattr(self.model, 'records_count'):
                    records_count = self.model.records_count
                
                # Обновляем информацию о файле с автоматическим извлечением МЦД
                if hasattr(self.view, 'update_file_info'):
                    self.view.update_file_info(file_path, records_count)
                
                # Если МЦД информация была извлечена в data_loader, передаем в view
                if mcd_info and hasattr(self.view, 'update_mcd_info'):
                    self.view.update_mcd_info(
                        line_mcd=mcd_info.get('line_mcd', ''),
                        route=mcd_info.get('route', ''),
                        train=mcd_info.get('train', ''),
                        leading_unit=mcd_info.get('leading_unit', '')
                    )
                
                # Логируем параметры для диагностики
                self.logger.info(f"Передача в update_telemetry_info: file_name={Path(file_path).name}, params_count={len(self._get_all_parameters())}, selected_count=0, mcd_info={mcd_info}")
                
                # ПРИНУДИТЕЛЬНО обновляем информационную панель
                if hasattr(self.view, 'update_telemetry_info'):
                    self.view.update_telemetry_info(
                        file_name=Path(file_path).name,
                        params_count=len(self._get_all_parameters()),
                        selected_count=0,
                        line_mcd=mcd_info.get('line_mcd', '') if mcd_info else '',
                        route=mcd_info.get('route', '') if mcd_info else '',
                        train=mcd_info.get('train', '') if mcd_info else '',
                        leading_unit=mcd_info.get('leading_unit', '') if mcd_info else ''
                    )
                
                # Обновляем UI после загрузки данных
                self._update_ui_after_data_load()
                
                # Уведомляем о загрузке данных
                self._emit_event('data_loaded', {
                    'file_path': file_path,
                    'records_count': records_count,
                    'mcd_info': mcd_info,
                    'timestamp': datetime.now()
                })
                
                # Обновляем статус подключения на "телеметрия активна"
                if hasattr(self.view, 'update_connection_status'):
                    if mcd_info and any(mcd_info.values()):
                        self.view.update_connection_status("telemetry", "#3498db")
                    else:
                        self.view.update_connection_status("connected", "#27ae60")
                
                # Показываем информационное сообщение
                if hasattr(self.view, 'show_info'):
                    file_name = Path(file_path).name
                    message = f"Файл загружен: {file_name}"
                    if records_count > 0:
                        message += f"\nЗаписей: {records_count:,}"
                    if mcd_info and any(mcd_info.values()):
                        mcd_parts = []
                        if mcd_info.get('line_mcd'):
                            mcd_parts.append(f"МЦД-{mcd_info['line_mcd']}")
                        if mcd_info.get('route'):
                            mcd_parts.append(f"Маршрут: {mcd_info['route']}")
                        if mcd_info.get('train'):
                            mcd_parts.append(f"Состав: {mcd_info['train']}")
                        if mcd_parts:
                            message += f"\n{', '.join(mcd_parts)}"
                    
                    self.view.show_info("Загрузка завершена", message)
                    
            else:
                self.logger.error(f"Не удалось загрузить файл: {file_path}")
                
                # Сбрасываем информацию о файле
                if hasattr(self.view, 'update_file_info'):
                    self.view.update_file_info()
                
                # Сбрасываем информацию о телеметрии
                if hasattr(self.view, 'update_telemetry_info'):
                    self.view.update_telemetry_info()
                
                # Обновляем статус на ошибку
                if hasattr(self.view, 'update_connection_status'):
                    self.view.update_connection_status("error", "#e74c3c")
                
                # Показываем ошибку
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(f"Не удалось загрузить файл: {Path(file_path).name}")
                    
        except Exception as e:
            self.logger.error(f"Ошибка обработки результата загрузки: {e}")
            
            # В случае ошибки обработки результата
            if hasattr(self.view, 'update_connection_status'):
                self.view.update_connection_status("error", "#e74c3c")
            
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка обработки загруженного файла: {e}")


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
        """Обновление UI после загрузки данных"""
        try:
            # Инициализируем временной диапазон
            self._init_time_range_after_load()
            
            # Загружаем все параметры
            all_params = self._get_all_parameters()
            self._update_ui_with_filtered_params(all_params)
            
            # Обновляем статистику
            if hasattr(self.view, 'update_statistics'):
                stats = self.get_filter_statistics()
                self.view.update_statistics(stats)
                
            self.logger.info(f"UI обновлен после загрузки данных: {len(all_params)} параметров")
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления UI после загрузки: {e}")

    def _init_time_range_after_load(self):
        """Инициализация временного диапазона после загрузки данных"""
        try:
            # Используем Use Case если доступен
            if self.time_range_init_use_case:
                request = TimeRangeInitRequest(session_id="current_session")
                response = self.time_range_init_use_case.execute(request)
                
                if response.success:
                    self.update_time_range(response.from_time, response.to_time)
                    self.logger.info(f"Временной диапазон инициализирован через Use Case: {response.from_time} - {response.to_time}")
                    return
            
            # Fallback - получаем из данных
            time_fields = self._get_time_fields_from_model() or self._get_time_fields_from_data_loader()
            if time_fields:
                self.update_time_range(time_fields['from_time'], time_fields['to_time'])
                self.logger.info(f"Временной диапазон инициализирован из данных: {time_fields['from_time']} - {time_fields['to_time']}")
            else:
                self.reset_time_range()
                self.logger.warning("Временной диапазон сброшен к значениям по умолчанию")
                
        except Exception as e:
            self.logger.error(f"Ошибка инициализации временного диапазона: {e}")
            self.reset_time_range()

    # === МЕТОДЫ УПРАВЛЕНИЯ СОСТОЯНИЕМ ===

    def _start_loading(self, message: str = "Загрузка..."):
        """Начало процесса загрузки"""
        try:
            self.is_loading = True
            if hasattr(self.view, 'start_loading'):
                self.view.start_loading(message)
            elif hasattr(self.view, 'update_status'):
                self.view.update_status(message)
            self.logger.debug(f"Начата загрузка: {message}")
        except Exception as e:
            self.logger.error(f"Ошибка начала загрузки: {e}")

    def _stop_loading(self):
        """Завершение процесса загрузки"""
        try:
            self.is_loading = False
            if hasattr(self.view, 'stop_loading'):
                self.view.stop_loading()
            elif hasattr(self.view, 'update_status'):
                self.view.update_status("Готов")
            self.logger.debug("Загрузка завершена")
        except Exception as e:
            self.logger.error(f"Ошибка завершения загрузки: {e}")

    def _start_processing(self, message: str = "Обработка..."):
        """Начало процесса обработки"""
        try:
            self.is_processing = True
            if hasattr(self.view, 'start_processing'):
                self.view.start_processing(message)
            elif hasattr(self.view, 'update_status'):
                self.view.update_status(message)
            self.logger.debug(f"Начата обработка: {message}")
        except Exception as e:
            self.logger.error(f"Ошибка начала обработки: {e}")

    def _stop_processing(self):
        """Завершение процесса обработки"""
        try:
            self.is_processing = False
            if hasattr(self.view, 'stop_processing'):
                self.view.stop_processing()
            elif hasattr(self.view, 'update_status'):
                self.view.update_status("Готов")
            self.logger.debug("Обработка завершена")
        except Exception as e:
            self.logger.error(f"Ошибка завершения обработки: {e}")

    def _has_data(self) -> bool:
        """Проверка наличия загруженных данных"""
        try:
            if hasattr(self.model, 'has_data'):
                return self.model.has_data()
            elif hasattr(self.model, 'data_loader') and self.model.data_loader:
                return hasattr(self.model.data_loader, 'data') and self.model.data_loader.data is not None
            elif hasattr(self.model, 'data'):
                return self.model.data is not None
            return False
        except Exception as e:
            self.logger.error(f"Ошибка проверки наличия данных: {e}")
            return False

    # === ПРИОРИТЕТНЫЕ МЕТОДЫ ДЛЯ ИЗМЕНЯЕМЫХ ПАРАМЕТРОВ ===

    def apply_changed_parameters_filter(self, **kwargs):
        """ПРИОРИТЕТНЫЙ метод для фильтрации изменяемых параметров"""
        try:
            self.logger.info("=== ПРИОРИТЕТНАЯ ФИЛЬТРАЦИЯ ИЗМЕНЯЕМЫХ ПАРАМЕТРОВ ===")
            
            if self.is_processing:
                self.logger.warning("Фильтрация уже выполняется, пропускаем")
                return

            self.is_processing = True

            try:
                # Проверяем наличие данных
                if not self._has_data():
                    self.logger.warning("Нет данных для фильтрации изменяемых параметров")
                    self._show_no_data_message()
                    return

                # Получаем временной диапазон
                start_time_str, end_time_str = self._get_time_range_unified()
                
                if not start_time_str or not end_time_str:
                    self.logger.error("Не удалось получить временной диапазон для изменяемых параметров")
                    self._show_time_error()
                    return

                # Применяем фильтр изменяемых параметров
                changed_params = self._execute_changed_params_filter(start_time_str, end_time_str, **kwargs)
                
                # Обновляем UI
                self._update_ui_with_filtered_params(changed_params)
                
                # Уведомляем о применении приоритетного фильтра
                self._emit_event('changed_params_filter_applied', {
                    'count': len(changed_params),
                    'time_range': (start_time_str, end_time_str)
                })
                
                self.logger.info(f"✅ Приоритетная фильтрация завершена: {len(changed_params)} изменяемых параметров")

            finally:
                self.is_processing = False

        except Exception as e:
            self.logger.error(f"Ошибка приоритетной фильтрации изменяемых параметров: {e}")
            self.is_processing = False

    def _execute_changed_params_filter(self, start_time_str: str, end_time_str: str, **kwargs) -> List[Dict[str, Any]]:
        """Выполнение фильтрации изменяемых параметров с приоритетом Use Case"""
        try:
            # Приоритет 1: Use Case
            if self.find_changed_params_use_case:
                return self._apply_changed_params_with_use_case(start_time_str, end_time_str, **kwargs)
            
            # Приоритет 2: Сервис фильтрации
            if self.filtering_service and hasattr(self.filtering_service, 'filter_changed_params'):
                changed_params = self.filtering_service.filter_changed_params(start_time_str, end_time_str)
                self.logger.info(f"Найдено {len(changed_params)} изменяемых параметров через сервис")
                return changed_params
            
            # Приоритет 3: Модель данных
            if hasattr(self.model, 'find_changed_parameters_in_range'):
                changed_params = self.model.find_changed_parameters_in_range(start_time_str, end_time_str)
                changed_params_dicts = [param.to_dict() if hasattr(param, 'to_dict') else param for param in changed_params]
                self.logger.info(f"Найдено {len(changed_params_dicts)} изменяемых параметров через модель")
                return changed_params_dicts
            
            # Приоритет 4: Data loader
            if (hasattr(self.model, 'data_loader') and 
                hasattr(self.model.data_loader, 'filter_changed_params')):
                changed_params = self.model.data_loader.filter_changed_params(start_time_str, end_time_str)
                self.logger.info(f"Найдено {len(changed_params)} изменяемых параметров через data_loader")
                return changed_params
            
            # Fallback: эвристика
            self.logger.warning("Используется эвристический метод для изменяемых параметров")
            all_params = self._get_all_parameters()
            # Простая эвристика - первые 30% параметров считаем изменяемыми
            changed_count = max(1, len(all_params) // 3)
            return all_params[:changed_count]
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения фильтрации изменяемых параметров: {e}")
            return []

    def _apply_changed_params_with_use_case(self, start_time_str: str, end_time_str: str, **kwargs) -> List[Dict[str, Any]]:
        """Применение фильтра изменяемых параметров через Use Case"""
        try:
            request = FindChangedParametersRequest(
                session_id="current_session",
                from_time=start_time_str,
                to_time=end_time_str,
                threshold=kwargs.get('threshold', 0.1),
                include_timestamp_params=kwargs.get('include_timestamp_params', False),
                include_problematic_params=kwargs.get('include_problematic_params', True)
            )

            response = self.find_changed_params_use_case.execute(request)

            # Преобразуем DTO обратно в словари для UI
            changed_params = [self._dto_to_dict(dto) for dto in response.changed_parameters]

            self.logger.info(f"✅ Use Case: найдено {len(changed_params)} изменяемых параметров ({response.execution_time_ms:.1f}ms)")
            return changed_params

        except Exception as e:
            self.logger.error(f"Ошибка Use Case для изменяемых параметров: {e}")
            raise

    def _dto_to_dict(self, dto) -> Dict[str, Any]:
        """Преобразование DTO в словарь"""
        try:
            if hasattr(dto, 'to_dict'):
                return dto.to_dict()
            elif hasattr(dto, '__dict__'):
                return dto.__dict__
            else:
                return {'data': str(dto)}
        except Exception as e:
            self.logger.error(f"Ошибка преобразования DTO в словарь: {e}")
            return {'error': str(e)}

    # === МЕТОДЫ ФИЛЬТРАЦИИ ===

    def apply_filters(self):
        """Применение фильтров параметров"""
        try:
            self.logger.info("Применение фильтров параметров")
            
            if self.is_processing:
                self.logger.warning("Фильтрация уже выполняется")
                return

            self._start_processing("Применение фильтров...")
            
            try:
                # Получаем критерии фильтрации
                criteria = self._get_filter_criteria()
                
                if not criteria:
                    self.logger.warning("Нет критериев фильтрации")
                    all_params = self._get_all_parameters()
                    self._update_ui_with_filtered_params(all_params)
                    return

                # Применяем фильтры
                filtered_params = self._execute_parameter_filter(criteria)
                
                # Обновляем UI
                self._update_ui_with_filtered_params(filtered_params)
                
                # Уведомляем о применении фильтров
                self._emit_event('filters_applied', {
                    'count': len(filtered_params),
                    'criteria': criteria
                })
                
                self.logger.info(f"Фильтры применены: {len(filtered_params)} параметров")

            finally:
                self._stop_processing()

        except Exception as e:
            self.logger.error(f"Ошибка применения фильтров: {e}")
            self._stop_processing()

    def _execute_parameter_filter(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Выполнение фильтрации параметров"""
        try:
            # Приоритет 1: Use Case
            if self.filter_parameters_use_case:
                return self._apply_filters_with_use_case(criteria)
            
            # Приоритет 2: Сервис фильтрации
            if self.filtering_service and hasattr(self.filtering_service, 'filter_parameters'):
                return self.filtering_service.filter_parameters(criteria)
            
            # Приоритет 3: Модель данных
            if hasattr(self.model, 'filter_parameters'):
                return self.model.filter_parameters(criteria)
            
            # Fallback: простая фильтрация
            return self._simple_parameter_filter(criteria)
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения фильтрации параметров: {e}")
            return []

    def _apply_filters_with_use_case(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Применение фильтров через Use Case"""
        try:
            # Преобразуем критерии в DTO
            filter_dto = FilterDTO(**criteria)
            
            request = FilterParametersRequest(
                session_id="current_session",
                filter_criteria=filter_dto
            )

            response = self.filter_parameters_use_case.execute(request)

            # Преобразуем DTO обратно в словари для UI
            filtered_params = [self._dto_to_dict(dto) for dto in response.filtered_parameters]

            self.logger.info(f"✅ Use Case: отфильтровано {len(filtered_params)} параметров ({response.execution_time_ms:.1f}ms)")
            return filtered_params

        except Exception as e:
            self.logger.error(f"Ошибка Use Case для фильтрации: {e}")
            raise

    def _simple_parameter_filter(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Простая фильтрация параметров"""
        try:
            all_params = self._get_all_parameters()
            filtered_params = []
            
            for param in all_params:
                match = True
                
                # Фильтр по линии
                if criteria.get('line') and param.get('line') != criteria['line']:
                    match = False
                
                # Фильтр по вагону
                if criteria.get('wagon') and param.get('wagon') != criteria['wagon']:
                    match = False
                
                # Фильтр по типу сигнала
                if criteria.get('signal_type') and param.get('signal_type') != criteria['signal_type']:
                    match = False
                
                # Текстовый поиск
                if criteria.get('search_text'):
                    search_text = criteria['search_text'].lower()
                    signal_code = param.get('signal_code', '').lower()
                    description = param.get('description', '').lower()
                    
                    if search_text not in signal_code and search_text not in description:
                        match = False
                
                if match:
                    filtered_params.append(param)
            
            self.logger.info(f"Простая фильтрация: {len(filtered_params)} из {len(all_params)} параметров")
            return filtered_params
            
        except Exception as e:
            self.logger.error(f"Ошибка простой фильтрации: {e}")
            return []

    def _get_filter_criteria(self) -> Dict[str, Any]:
        """Получение критериев фильтрации"""
        try:
            # Проверяем кэш
            if self._filter_criteria_cache and (time.time() - self._last_filter_update) < 1.0:
                return self._filter_criteria_cache

            criteria = {}
            
            # Получаем критерии из filter_panel
            filter_panel = self.get_ui_component('filter_panel')
            if filter_panel and hasattr(filter_panel, 'get_filter_criteria'):
                criteria = filter_panel.get_filter_criteria()
            
            # Кэшируем результат
            self._filter_criteria_cache = criteria
            self._last_filter_update = time.time()
            
            return criteria
            
        except Exception as e:
            self.logger.error(f"Ошибка получения критериев фильтрации: {e}")
            return {}

    # === МЕТОДЫ ПОСТРОЕНИЯ ГРАФИКОВ ===

    def build_plots(self):
        """Построение графиков для выбранных параметров"""
        try:
            self.logger.info("Построение графиков")
            
            if not self.plot_manager:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("PlotManager не инициализирован")
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
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Не удалось получить временной диапазон")
                return

            self._start_processing("Построение графиков...")
            
            try:
                # Строим графики
                success = self.plot_manager.build_plots(
                    parameters=selected_params,
                    start_time=start_time,
                    end_time=end_time
                )
                
                if success:
                    self.logger.info(f"Графики построены для {len(selected_params)} параметров")
                    if hasattr(self.view, 'show_info'):
                        self.view.show_info("Графики", f"Построено графиков: {len(selected_params)}")
                else:
                    if hasattr(self.view, 'show_error'):
                        self.view.show_error("Ошибка построения графиков")

            finally:
                self._stop_processing()

        except Exception as e:
            self.logger.error(f"Ошибка построения графиков: {e}")
            self._stop_processing()
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка построения графиков: {e}")

    # === МЕТОДЫ ГЕНЕРАЦИИ ОТЧЕТОВ ===

    def generate_report(self):
        """Генерация отчета"""
        try:
            if not self.report_generator:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Генератор отчетов не инициализирован")
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
                            self.view.show_info("Отчет", f"Отчет сохранен: {file_path}")
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
            directory = filedialog.askdirectory(title="Выберите папку для экспорта графиков")
            
            if directory:
                success = self.plot_manager.export_all_plots(directory)
                if success:
                    self.logger.info(f"Графики экспортированы в: {directory}")
                    if hasattr(self.view, 'show_info'):
                        self.view.show_info("Экспорт", f"Графики сохранены в: {directory}")
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
                    self.logger.info("Все параметры выбраны через select_all_parameters")
                else:
                    self.logger.warning("Метод выбора всех параметров не найден")
            else:
                self.logger.warning("parameter_panel не найден для выбора всех параметров")
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
                    self.logger.warning("Метод отмены выбора параметров не найден")
            else:
                self.logger.warning("parameter_panel не найден для отмены выбора")
        except Exception as e:
            self.logger.error(f"Ошибка отмены выбора параметров: {e}")

    def get_selected_count(self) -> int:
        """Получение количества выбранных параметров"""
        try:
            selected_params = self._get_selected_parameters_unified()
            return len(selected_params)
        except Exception as e:
            self.logger.error(f"Ошибка получения количества выбранных параметров: {e}")
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
            
            self.logger.info(f"Фильтры очищены, показано {len(all_params)} параметров")

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
                    self.logger.warning("Метод очистки графиков не найден в plot_panel")
            
            # Также очищаем через plot_manager если есть
            if self.plot_manager and hasattr(self.plot_manager, 'clear_all_plots'):
                self.plot_manager.clear_all_plots()
                self.logger.info("Графики очищены через plot_manager")
                
        except Exception as e:
            self.logger.error(f"Ошибка очистки графиков: {e}")

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def _update_ui_with_filtered_params(self, parameters: List[Dict[str, Any]]):
        """Обновление UI с отфильтрованными параметрами"""
        try:
            # Проверяем кэш UI обновлений
            cache_key = f"params_{len(parameters)}_{hash(str(parameters[:5]))}"
            current_time = time.time()
            
            if (cache_key in self._ui_update_cache and 
                (current_time - self._last_ui_update) < 0.5):
                self.logger.debug("Использован кэш UI обновления")
                return
            
            # Обновляем parameter_panel
            parameter_panel = self.get_ui_component('parameter_panel')
            if parameter_panel:
                if hasattr(parameter_panel, 'update_parameters'):
                    parameter_panel.update_parameters(parameters)
                elif hasattr(parameter_panel, 'set_parameters'):
                    parameter_panel.set_parameters(parameters)
                else:
                    self.logger.warning("Метод обновления параметров не найден в parameter_panel")
            
            # Обновляем статистику
            if hasattr(self.view, 'update_parameter_count'):
                self.view.update_parameter_count(len(parameters))
            
            # Кэшируем обновление
            self._ui_update_cache[cache_key] = current_time
            self._last_ui_update = current_time
                
            self.logger.debug(f"UI обновлен с {len(parameters)} параметрами")
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления UI с параметрами: {e}")

    def _emit_event(self, event_name: str, data: Dict[str, Any]):
        """Отправка события подписчикам"""
        try:
            callbacks = self._ui_callbacks.get(event_name, [])
            for callback in callbacks:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Ошибка в callback для события {event_name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Ошибка отправки события {event_name}: {e}")

    def _show_no_data_message(self):
        """Показ сообщения об отсутствии данных"""
        if hasattr(self.view, 'show_warning'):
            self.view.show_warning("Нет загруженных данных. Загрузите CSV файл.")

    def _show_time_error(self):
        """Показ ошибки времени"""
        if hasattr(self.view, 'show_error'):
            self.view.show_error("Ошибка получения временного диапазона")

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
                stats['signal_types'][signal_type] = stats['signal_types'].get(signal_type, 0) + 1
                
                # Статистика по типам данных
                data_type = param.get('data_type', 'Unknown')
                stats['data_types'][data_type] = stats['data_types'].get(data_type, 0) + 1

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

    def _update_parameter_display(self, parameters: List[Dict[str, Any]]):
        """Обновление отображения параметров в UI"""
        try:
            self.logger.debug(f"Обновление отображения {len(parameters)} параметров")
            
            # Обновляем UI компоненты с новыми параметрами
            if self.ui_components and hasattr(self.ui_components, 'update_parameters'):
                self.ui_components.update_parameters(parameters)
                self.logger.debug("✅ UI компоненты обновлены")
            else:
                self.logger.warning("UIComponents не инициализированы или не имеют метод update_parameters")
                
            # Альтернативный способ через view
            if hasattr(self.view, 'update_tree_all_params'):
                self.view.update_tree_all_params(parameters)
                self.logger.debug("✅ View обновлен через update_tree_all_params")
                
            # Обновляем счетчик параметров
            if hasattr(self.view, 'update_parameter_count'):
                self.view.update_parameter_count(len(parameters))
                
            # Генерируем событие обновления
            self._emit_event('parameters_updated', {
                'count': len(parameters),
                'timestamp': datetime.now()
            })
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления отображения параметров: {e}")

    def _matches_system_filter(self, parameter: Dict[str, Any], system_filter: Dict[str, Any]) -> bool:
        """Проверка, соответствует ли параметр системному фильтру"""
        try:
            if not system_filter:
                return True  # Пустой фильтр пропускает все
                
            # Проверяем каждое условие фильтра
            for filter_key, filter_value in system_filter.items():
                if filter_key not in parameter:
                    return False
                    
                param_value = parameter[filter_key]
                
                # Обработка разных типов фильтров
                if isinstance(filter_value, str):
                    # Строковое совпадение (регистронезависимое)
                    if str(param_value).lower() != filter_value.lower():
                        return False
                        
                elif isinstance(filter_value, list):
                    # Проверка вхождения в список
                    if param_value not in filter_value:
                        return False
                        
                elif isinstance(filter_value, dict):
                    # Сложный фильтр с операторами
                    if not self._apply_complex_filter(param_value, filter_value):
                        return False
                        
                else:
                    # Прямое сравнение
                    if param_value != filter_value:
                        return False
                        
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки системного фильтра: {e}")
            return False

    def _apply_complex_filter(self, param_value: Any, filter_config: Dict[str, Any]) -> bool:
        """Применение сложного фильтра с операторами"""
        try:
            operator = filter_config.get('operator', 'eq')
            value = filter_config.get('value')
            
            if operator == 'eq':
                return param_value == value
            elif operator == 'ne':
                return param_value != value
            elif operator == 'gt':
                return float(param_value) > float(value)
            elif operator == 'lt':
                return float(param_value) < float(value)
            elif operator == 'gte':
                return float(param_value) >= float(value)
            elif operator == 'lte':
                return float(param_value) <= float(value)
            elif operator == 'contains':
                return str(value).lower() in str(param_value).lower()
            elif operator == 'startswith':
                return str(param_value).lower().startswith(str(value).lower())
            elif operator == 'endswith':
                return str(param_value).lower().endswith(str(value).lower())
            elif operator == 'in':
                return param_value in value if isinstance(value, (list, tuple)) else False
            elif operator == 'regex':
                import re
                return bool(re.search(str(value), str(param_value), re.IGNORECASE))
            else:
                self.logger.warning(f"Неизвестный оператор фильтра: {operator}")
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка применения сложного фильтра: {e}")
            return False

