# src/ui/controllers/main_controller.py - ИСЧЕРПЫВАЮЩЕ ПОЛНАЯ ВЕРСИЯ
"""
Главный контроллер приложения с полной интеграцией Use Cases и UI компонентов
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
        FilterParametersUseCase, FilterParametersRequest
    )
    from ...core.application.use_cases.find_changed_parameters_use_case import (
        FindChangedParametersUseCase, FindChangedParametersRequest
    )
    from ...core.application.use_cases.time_range_init_use_case import (
        TimeRangeInitUseCase, TimeRangeInitRequest
    )
    from ...core.application.dto.filter_dto import FilterDTO
    USE_CASES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Use Cases не доступны: {e}")
    USE_CASES_AVAILABLE = False

class MainController:
    """Главный контроллер приложения (ПОЛНАЯ ИНТЕГРАЦИЯ)"""

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
            'time_changed': []
        }

        # Инициализация
        self._setup_use_cases()
        self._setup_ui_integration()

        self.logger.info("MainController инициализирован")

    # ДОБАВЛЯЕМ: Унифицированные методы доступа
    def _get_time_panel(self):
        """ЕДИНЫЙ метод получения time_panel (улучшенная версия)"""
        # Способ 1: Через ui_components (если установлен)
        if (hasattr(self, 'ui_components') and 
            self.ui_components and 
            hasattr(self.ui_components, '_get_time_panel')):
            return self.ui_components._get_time_panel()
        
        # Способ 2: Через view.ui_components
        if (hasattr(self.view, 'ui_components') and 
            self.view.ui_components and 
            hasattr(self.view.ui_components, 'time_panel')):
            return self.view.ui_components.time_panel
        
        # Способ 3: Прямой доступ
        if hasattr(self.view, 'time_panel'):
            return self.view.time_panel
            
        return None

    def _get_parameter_panel(self):
        """ЕДИНЫЙ метод получения parameter_panel (улучшенная версия)"""
        # Способ 1: Через ui_components (если установлен)
        if (hasattr(self, 'ui_components') and 
            self.ui_components and 
            hasattr(self.ui_components, '_get_parameter_panel')):
            return self.ui_components._get_parameter_panel()
        
        # Способ 2: Через view.ui_components
        if (hasattr(self.view, 'ui_components') and 
            self.view.ui_components and 
            hasattr(self.view.ui_components, 'parameter_panel')):
            return self.view.ui_components.parameter_panel
            
        return None

    def _get_filter_panel(self):
        """ЕДИНЫЙ метод получения filter_panel"""
        # Способ 1: Через ui_components
        if (hasattr(self, 'ui_components') and 
            self.ui_components and 
            hasattr(self.ui_components, '_get_filter_panel')):
            return self.ui_components._get_filter_panel()
        
        # Способ 2: Через view.ui_components
        if (hasattr(self.view, 'ui_components') and 
            self.view.ui_components and 
            hasattr(self.view.ui_components, 'filter_panel')):
            return self.view.ui_components.filter_panel
            
        return None

    def _get_action_panel(self):
        """ЕДИНЫЙ метод получения action_panel"""
        # Способ 1: Через ui_components
        if (hasattr(self, 'ui_components') and 
            self.ui_components and 
            hasattr(self.ui_components, '_get_action_panel')):
            return self.ui_components._get_action_panel()
        
        # Способ 2: Через view.ui_components
        if (hasattr(self.view, 'ui_components') and 
            self.view.ui_components and 
            hasattr(self.view.ui_components, 'action_panel')):
            return self.view.ui_components.action_panel
            
        return None

    # УЛУЧШАЕМ: Метод обновления времени с использованием унифицированного доступа
    def _update_time_panel_fields_unified(self, time_fields: Dict[str, Any]) -> bool:
        """УНИФИЦИРОВАННОЕ обновление времени с новыми методами доступа"""
        try:
            self.logger.info(f"Унифицированное обновление полей времени: {time_fields}")

            # Используем унифицированный метод доступа
            time_panel = self._get_time_panel()
            
            if time_panel and hasattr(time_panel, 'update_time_fields'):
                time_panel.update_time_fields(
                    from_time=time_fields['from_time'],
                    to_time=time_fields['to_time'], 
                    duration=time_fields.get('duration', ''),
                    total_records=time_fields.get('total_records', 0)
                )
                self.logger.info("✅ Время обновлено через унифицированный доступ")
                return True
            else:
                self.logger.error("❌ time_panel не найден или не имеет нужного метода")
                # Fallback к старому методу
                return self._update_time_panel_fields(time_fields)
                
        except Exception as e:
            self.logger.error(f"Ошибка унифицированного обновления времени: {e}")
            return False

    # УЛУЧШАЕМ: Получение выбранных параметров через унифицированный доступ
    def _get_selected_parameters_unified(self) -> List[Dict[str, Any]]:
        """УНИФИЦИРОВАННОЕ получение выбранных параметров"""
        try:
            parameter_panel = self._get_parameter_panel()
            
            if parameter_panel and hasattr(parameter_panel, 'get_selected_parameters'):
                selected = parameter_panel.get_selected_parameters()
                self.logger.debug(f"Получено выбранных параметров через унифицированный доступ: {len(selected)}")
                return selected
            else:
                # Fallback к старому методу
                return self._get_selected_parameters()
                
        except Exception as e:
            self.logger.error(f"Ошибка унифицированного получения параметров: {e}")
            return []

    # ДОБАВЛЯЕМ: Метод переключения режима UI
    def switch_ui_layout(self, mode: str):
        """Переключение режима UI (compact/standard)"""
        try:
            if (hasattr(self.view, 'ui_components') and 
                self.view.ui_components and 
                hasattr(self.view.ui_components, 'switch_layout_safe')):
                
                self.view.ui_components.switch_layout_safe(mode)
                self.logger.info(f"UI переключен на {mode} режим")
                
                # Переустанавливаем ссылки на панели
                if hasattr(self, 'ui_components'):
                    self.ui_components = self.view.ui_components
                
            else:
                self.logger.warning("Переключение режима UI недоступно")
                
        except Exception as e:
            self.logger.error(f"Ошибка переключения режима UI: {e}")

    # ДОБАВЛЯЕМ: Отложенное обновление времени (уже есть в коде, но улучшаем)
    def _delayed_time_update(self, time_fields: Dict[str, Any]):
        """УЛУЧШЕННОЕ отложенное обновление времени"""
        try:
            # Пытаемся унифицированный метод
            success = self._update_time_panel_fields_unified(time_fields)
            
            if not success:
                # Fallback к старому методу
                success = self._update_time_panel_fields(time_fields)
            
            if success:
                self.logger.info("✅ Отложенное обновление времени выполнено")
            else:
                self.logger.error("❌ Отложенное обновление времени не удалось")

        except Exception as e:
            self.logger.error(f"Ошибка отложенного обновления времени: {e}")

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

    def _setup_ui_integration(self):
        """Настройка интеграции с UI"""
        try:
            # Устанавливаем обратные связи с view
            if hasattr(self.view, 'set_controller'):
                # view уже знает о контроллере, но убеждаемся в двусторонней связи
                pass

            self.logger.debug("UI интеграция настроена")

        except Exception as e:
            self.logger.error(f"Ошибка настройки UI интеграции: {e}")

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

    def set_ui_components(self, ui_components):
        """Установка UI компонентов"""
        self.ui_components = ui_components
        self.logger.info("UIComponents установлен в контроллере")

    def set_view(self, view):
        """Установка view (для обратной совместимости)"""
        self.view = view
        self.logger.info("View установлен в контроллере")

    def save_filters(self):
        """Сохранение текущих фильтров"""
        try:
            # Получаем текущие критерии фильтрации
            criteria = self._get_filter_criteria()
            
            # Сохраняем в файл настроек (простая реализация)
            import json
            from pathlib import Path
            
            settings_file = Path.home() / '.tramm_filters.json'
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(criteria, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Фильтры сохранены в {settings_file}")
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения фильтров: {e}")

    def _get_selected_parameters(self) -> List[Dict[str, Any]]:
        """Получение выбранных параметров (расширенная версия)"""
        try:
            # Способ 1: Через ui_components (если установлен через set_ui_components)
            if (hasattr(self, 'ui_components') and 
                self.ui_components and 
                hasattr(self.ui_components, 'parameter_panel')):
                
                parameter_panel = self.ui_components.parameter_panel
                if hasattr(parameter_panel, 'get_selected_parameters'):
                    selected = parameter_panel.get_selected_parameters()
                    self.logger.debug(f"Получено выбранных параметров через ui_components: {len(selected)}")
                    return selected

            # Способ 2: Через view.ui_components
            if (hasattr(self.view, 'ui_components') and 
                self.view.ui_components and 
                hasattr(self.view.ui_components, 'parameter_panel')):
                
                parameter_panel = self.view.ui_components.parameter_panel
                if hasattr(parameter_panel, 'get_selected_parameters'):
                    selected = parameter_panel.get_selected_parameters()
                    self.logger.debug(f"Получено выбранных параметров через view: {len(selected)}")
                    return selected

            # Способ 3: Прямой доступ через view.parameter_panel
            if hasattr(self.view, 'parameter_panel') and self.view.parameter_panel:
                parameter_panel = self.view.parameter_panel
                if hasattr(parameter_panel, 'get_selected_parameters'):
                    selected = parameter_panel.get_selected_parameters()
                    self.logger.debug(f"Получено выбранных параметров напрямую: {len(selected)}")
                    return selected

            self.logger.warning("Не найден способ получения выбранных параметров")
            return []

        except Exception as e:
            self.logger.error(f"Ошибка получения выбранных параметров: {e}")
            return []

    def set_sop_manager(self, service):
        """Установка менеджера SOP"""
        self.sop_manager = service
        self.logger.info("SOPManager установлен")

    # === МЕТОДЫ ЗАГРУЗКИ ДАННЫХ ===

    def upload_csv(self):
        """ИСПРАВЛЕННАЯ загрузка CSV файла"""
        try:
            from tkinter import filedialog
            
            file_path = filedialog.askopenfilename(
                title="Выберите CSV файл",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if file_path:
                self.logger.info(f"Выбран файл: {file_path}")
                
                # Показываем процесс загрузки
                self._start_loading("Загрузка файла...")

                # Загружаем файл в отдельном потоке для UI отзывчивости
                def load_file():
                    try:
                        success = self._load_csv_file(file_path)
                        
                        # Выполняем UI обновления в главном потоке
                        if hasattr(self.view, 'root'):
                            self.view.root.after(0, lambda: self._handle_file_load_result(success, file_path))
                    except Exception as e:
                        self.logger.error(f"Ошибка в потоке загрузки: {e}")
                        if hasattr(self.view, 'root'):
                            self.view.root.after(0, lambda: self._handle_file_load_error(e))

                # Запускаем загрузку в отдельном потоке
                thread = threading.Thread(target=load_file, daemon=True)
                thread.start()

        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV: {e}")
            self._stop_loading()
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка загрузки: {e}")

    def _load_csv_file(self, file_path: str) -> bool:
        """Загрузка CSV файла через модель"""
        try:
            if hasattr(self.model, 'load_csv_file'):
                return self.model.load_csv_file(file_path)
            elif hasattr(self.model, 'data_loader') and hasattr(self.model.data_loader, 'load_csv'):
                return self.model.data_loader.load_csv(file_path)
            else:
                self.logger.error("Метод загрузки CSV не найден в модели")
                return False

        except Exception as e:
            self.logger.error(f"Ошибка в _load_csv_file: {e}")
            return False

    def _handle_file_load_result(self, success: bool, file_path: str):
        """Обработка результата загрузки файла"""
        try:
            if success:
                self.current_file_path = file_path
                self.logger.info("Файл успешно загружен")
                
                # Обработка успешной загрузки
                self._on_file_loaded(file_path)
                
                # Уведомляем UI об успехе
                if hasattr(self.view, 'update_status'):
                    file_name = Path(file_path).name
                    self.view.update_status(f"Файл загружен: {file_name}")
                
            else:
                self.logger.error("Ошибка загрузки файла")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Ошибка загрузки файла")

        except Exception as e:
            self.logger.error(f"Ошибка обработки результата загрузки: {e}")
        finally:
            self._stop_loading()

    def _handle_file_load_error(self, error: Exception):
        """Обработка ошибки загрузки файла"""
        try:
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка загрузки файла: {error}")
        except Exception as e:
            self.logger.error(f"Ошибка обработки ошибки загрузки: {e}")
        finally:
            self._stop_loading()

    def _on_file_loaded(self, file_path: str):
        """КРИТИЧНО ИСПРАВЛЕННАЯ обработка загрузки файла"""
        try:
            self.logger.info("=== НАЧАЛО ОБРАБОТКИ ЗАГРУЖЕННОГО ФАЙЛА ===")

            # ШАГ 1: Инициализация временного диапазона
            self._initialize_time_range_from_data()

            # ШАГ 2: Обработка параметров
            self._handle_successful_load()

            # ШАГ 3: Уведомление callbacks
            self._emit_event('data_loaded', {'file_path': file_path})

            self.logger.info("=== ОБРАБОТКА ФАЙЛА ЗАВЕРШЕНА УСПЕШНО ===")

        except Exception as e:
            self.logger.error(f"Ошибка обработки загруженного файла: {e}")
            import traceback
            traceback.print_exc()

    def _initialize_time_range_from_data(self):
        """Инициализация временного диапазона из загруженных данных"""
        try:
            time_fields = None

            # Способ 1: Через Use Case (если доступен)
            if self.time_range_init_use_case:
                try:
                    time_request = TimeRangeInitRequest(session_id="current_session")
                    time_response = self.time_range_init_use_case.execute(time_request)
                    
                    if time_response.success:
                        time_fields = {
                            'from_time': time_response.from_time,
                            'to_time': time_response.to_time,
                            'duration': time_response.duration,
                            'total_records': time_response.total_records
                        }
                        self.logger.info("Временной диапазон получен через Use Case")
                except Exception as e:
                    self.logger.warning(f"Ошибка Use Case для времени: {e}")

            # Способ 2: Через модель (fallback)
            if not time_fields:
                time_fields = self._get_time_fields_from_model()
                if time_fields:
                    self.logger.info(f"✅ Время получено через модель: {time_fields.get('from_time')} - {time_fields.get('to_time')}")

            # Способ 3: Через data_loader (fallback)
            if not time_fields:
                time_fields = self._get_time_fields_from_data_loader()
                if time_fields:
                    self.logger.info(f"✅ Время получено через data_loader: {time_fields.get('from_time')} - {time_fields.get('to_time')}")

            # Обновляем UI
            if time_fields and time_fields.get('from_time') and time_fields.get('to_time'):
                success = self._update_time_panel_fields(time_fields)
                if success:
                    self.logger.info(f"✅ Временной диапазон обновлен: {time_fields['from_time']} - {time_fields['to_time']}")
                else:
                    self.logger.error("❌ Не удалось обновить временной диапазон в UI")

                # Добавляем отложенное обновление времени через after
                if hasattr(self.view, 'root'):
                    self.view.root.after(100, lambda: self._delayed_time_update(time_fields))
                    self.logger.info("✅ Запланировано отложенное обновление времени")

            else:
                self.logger.warning("⚠️ Временной диапазон не получен")

        except Exception as e:
            self.logger.error(f"Ошибка инициализации временного диапазона: {e}")

    def _get_time_fields_from_model(self) -> Optional[Dict[str, Any]]:
        """Получение временных полей из модели"""
        try:
            if hasattr(self.model, 'get_time_range_fields'):
                return self.model.get_time_range_fields()
            elif hasattr(self.model, '_time_range_fields'):
                return self.model._time_range_fields
            return None
        except Exception as e:
            self.logger.error(f"Ошибка получения времени из модели: {e}")
            return None

    def _get_time_fields_from_data_loader(self) -> Optional[Dict[str, Any]]:
        """Получение временных полей из data_loader"""
        try:
            if (hasattr(self.model, 'data_loader') and 
                self.model.data_loader and 
                hasattr(self.model.data_loader, 'min_timestamp') and 
                hasattr(self.model.data_loader, 'max_timestamp')):
                
                return {
                    'from_time': self.model.data_loader.min_timestamp,
                    'to_time': self.model.data_loader.max_timestamp,
                    'duration': self._calculate_duration(
                        self.model.data_loader.min_timestamp,
                        self.model.data_loader.max_timestamp
                    ),
                    'total_records': getattr(self.model.data_loader, 'records_count', 0)
                }
            return None
        except Exception as e:
            self.logger.error(f"Ошибка получения времени из data_loader: {e}")
            return None

    def _calculate_duration(self, from_time_str: str, to_time_str: str) -> str:
        """Вычисление длительности"""
        try:
            from_time = datetime.strptime(from_time_str, '%Y-%m-%d %H:%M:%S')
            to_time = datetime.strptime(to_time_str, '%Y-%m-%d %H:%M:%S')
            duration = to_time - from_time
            
            days = duration.days
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                return f"{days} дн. {hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except Exception:
            return "Неизвестно"

    def _update_time_panel_fields(self, time_fields: Dict[str, Any]) -> bool:
        """КРИТИЧНО ИСПРАВЛЕННОЕ обновление полей времени в UI"""
        try:
            self.logger.info(f"Попытка обновления полей времени: {time_fields}")

            # МНОЖЕСТВЕННЫЕ СПОСОБЫ ПОИСКА time_panel
            time_panel = None
            search_paths = []

            # Способ 1: Через ui_components
            if (hasattr(self.view, 'ui_components') and 
                self.view.ui_components and 
                hasattr(self.view.ui_components, 'time_panel')):
                time_panel = self.view.ui_components.time_panel
                search_paths.append("ui_components.time_panel ✅")
            else:
                search_paths.append("ui_components.time_panel ❌")

            # Способ 2: Прямой доступ через view
            if not time_panel and hasattr(self.view, 'time_panel'):
                time_panel = self.view.time_panel
                search_paths.append("view.time_panel ✅")
            else:
                search_paths.append("view.time_panel ❌")

            # Способ 3: Через get_component
            if not time_panel and hasattr(self.view, 'get_component'):
                time_panel = self.view.get_component('time_panel')
                if time_panel:
                    search_paths.append("get_component('time_panel') ✅")
                else:
                    search_paths.append("get_component('time_panel') ❌")

            # Способ 4: Поиск в атрибутах view
            if not time_panel:
                time_panel = self._find_time_panel_in_view()
                if time_panel:
                    search_paths.append("_find_time_panel_in_view() ✅")
                else:
                    search_paths.append("_find_time_panel_in_view() ❌")

            self.logger.info(f"Поиск time_panel: {' | '.join(search_paths)}")

            # ПОПЫТКА ОБНОВЛЕНИЯ
            if time_panel:
                self.logger.info(f"time_panel найден: {type(time_panel)}")

                # Проверяем наличие метода update_time_fields
                if hasattr(time_panel, 'update_time_fields'):
                    self.logger.info("Вызов time_panel.update_time_fields...")
                    time_panel.update_time_fields(
                        from_time=time_fields['from_time'],
                        to_time=time_fields['to_time'],
                        duration=time_fields.get('duration', ''),
                        total_records=time_fields.get('total_records', 0)
                    )
                    self.logger.info("✅ time_panel.update_time_fields выполнен успешно")
                    return True
                else:
                    available_methods = [m for m in dir(time_panel) if not m.startswith('_')]
                    self.logger.error(f"❌ time_panel не имеет метода update_time_fields. Доступные методы: {available_methods}")
                    
                    # Попробуем альтернативные методы
                    if hasattr(time_panel, 'set_time_range'):
                        time_panel.set_time_range(time_fields['from_time'], time_fields['to_time'])
                        self.logger.info("✅ Использован альтернативный метод set_time_range")
                        return True
                    
                    return False
            else:
                self.logger.error("❌ time_panel НЕ НАЙДЕН во всех попытках поиска")
                self._diagnose_view_structure()
                return False

        except Exception as e:
            self.logger.error(f"Ошибка обновления полей времени: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _find_time_panel_in_view(self):
        """Поиск time_panel в атрибутах view"""
        try:
            if hasattr(self.view, '__dict__'):
                for attr_name, attr_value in self.view.__dict__.items():
                    if ('time' in attr_name.lower() and 
                        hasattr(attr_value, 'update_time_fields')):
                        self.logger.info(f"Найден time_panel через атрибут: {attr_name}")
                        return attr_value
            return None
        except Exception as e:
            self.logger.error(f"Ошибка поиска time_panel: {e}")
            return None

    def _diagnose_view_structure(self):
        """ДИАГНОСТИКА структуры view"""
        try:
            self.logger.info("=== ДИАГНОСТИКА СТРУКТУРЫ VIEW ===")
            
            if hasattr(self.view, '__dict__'):
                view_attrs = list(self.view.__dict__.keys())
                self.logger.info(f"Атрибуты view: {view_attrs}")

                # Ищем атрибуты связанные со временем
                time_related = [attr for attr in view_attrs if 'time' in attr.lower()]
                if time_related:
                    self.logger.info(f"Атрибуты связанные со временем: {time_related}")

                # Ищем UI компоненты
                ui_related = [attr for attr in view_attrs if any(keyword in attr.lower() 
                             for keyword in ['ui', 'component', 'panel'])]
                if ui_related:
                    self.logger.info(f"UI атрибуты: {ui_related}")

            # Проверяем ui_components детально
            if hasattr(self.view, 'ui_components'):
                self.logger.info("ui_components найден")
                if hasattr(self.view.ui_components, '__dict__'):
                    ui_attrs = list(self.view.ui_components.__dict__.keys())
                    self.logger.info(f"Атрибуты ui_components: {ui_attrs}")

        except Exception as e:
            self.logger.error(f"Ошибка диагностики: {e}")

    def _handle_successful_load(self):
        """ИСПРАВЛЕННАЯ обработка успешной загрузки"""
        try:
            if self._has_data():
                params = self.model.data_loader.parameters
                self.logger.info(f"Загружено параметров: {len(params)}")

                # Очищаем кэш фильтров
                self._filter_criteria_cache = None

                # КРИТИЧНО: Обновляем параметры в UI
                cleaned_params = self._clean_parameter_descriptions(params)
                self._update_parameters_in_ui(cleaned_params)

                # Обновляем фильтры
                self._update_filters_in_ui()

                # Применяем начальные фильтры
                self.apply_filters()

                # ПРИНУДИТЕЛЬНОЕ обновление UI
                if hasattr(self.view, 'root'):
                    self.view.root.update_idletasks()
                    self.view.root.update()

                # Уведомляем о загрузке параметров
                self._emit_event('parameters_updated', {'count': len(params)})

                self.logger.info("✅ Обработка успешной загрузки завершена")

        except Exception as e:
            self.logger.error(f"Ошибка обработки успешной загрузки: {e}")
            import traceback
            traceback.print_exc()

    def _update_parameters_in_ui(self, parameters: List[Dict[str, Any]]):
        """УНИВЕРСАЛЬНОЕ обновление параметров в UI"""
        try:
            self.logger.info(f"Обновление {len(parameters)} параметров в UI")

            # Способ 1: Через ui_components (предпочтительный)
            if (hasattr(self.view, 'ui_components') and 
                self.view.ui_components and 
                hasattr(self.view.ui_components, 'parameter_panel')):
                
                parameter_panel = self.view.ui_components.parameter_panel
                if hasattr(parameter_panel, 'update_parameters'):
                    parameter_panel.update_parameters(parameters)
                    self.logger.info("✅ Параметры обновлены через ui_components.parameter_panel.update_parameters")
                    return
                elif hasattr(parameter_panel, 'update_tree_all_params'):
                    parameter_panel.update_tree_all_params(parameters)
                    self.logger.info("✅ Параметры обновлены через ui_components.parameter_panel.update_tree_all_params")
                    return

            # Способ 2: Через прямой доступ к view
            if hasattr(self.view, 'update_tree_all_params'):
                self.view.update_tree_all_params(parameters)
                self.logger.info("✅ Параметры обновлены через view.update_tree_all_params")
                return

            # Способ 3: Через parameter_panel напрямую
            if hasattr(self.view, 'parameter_panel') and self.view.parameter_panel:
                parameter_panel = self.view.parameter_panel
                if hasattr(parameter_panel, 'update_parameters'):
                    parameter_panel.update_parameters(parameters)
                    self.logger.info("✅ Параметры обновлены через view.parameter_panel.update_parameters")
                    return

            self.logger.error("❌ Не найден способ обновления параметров в UI")

        except Exception as e:
            self.logger.error(f"Ошибка обновления параметров в UI: {e}")

    def _update_filters_in_ui(self):
        """Обновление фильтров в UI"""
        try:
            if not hasattr(self.model, 'data_loader') or not self.model.data_loader:
                return

            # Обновляем линии связи
            if hasattr(self.model.data_loader, 'lines'):
                lines = list(self.model.data_loader.lines)
                
                # Способ 1: Через ui_components
                if (hasattr(self.view, 'ui_components') and 
                    self.view.ui_components and 
                    hasattr(self.view.ui_components, 'filter_panel')):
                    
                    filter_panel = self.view.ui_components.filter_panel
                    if hasattr(filter_panel, 'update_line_checkboxes'):
                        filter_panel.update_line_checkboxes(lines)
                        self.logger.info(f"✅ Обновлены линии в фильтрах: {len(lines)} элементов")
                        return

                # Способ 2: Через прямой доступ
                if hasattr(self.view, 'update_line_checkboxes'):
                    self.view.update_line_checkboxes(lines)
                    self.logger.info(f"✅ Обновлены линии через view: {len(lines)} элементов")

        except Exception as e:
            self.logger.error(f"Ошибка обновления фильтров: {e}")

    def _clean_parameter_descriptions(self, params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Очистка описаний параметров от артефактов"""
        try:
            cleaned_params = []

            for param in params:
                if isinstance(param, dict):
                    # Создаем копию параметра
                    clean_param = param.copy()

                    # Очищаем описание
                    description = clean_param.get('description', '')
                    if description:
                        # Удаляем артефакты "|0", "|", пустые строки
                        description = description.replace('|0', '').replace('|', '').strip()

                        # Удаляем множественные пробелы
                        import re
                        description = re.sub(r'\s+', ' ', description).strip()

                        # Если описание стало пустым, генерируем из signal_code
                        if not description and clean_param.get('signal_code'):
                            signal_code = clean_param['signal_code']
                            description = signal_code.replace('_', ' ').title()

                        clean_param['description'] = description

                    cleaned_params.append(clean_param)
                else:
                    cleaned_params.append(param)

            self.logger.debug(f"Очищены описания {len(cleaned_params)} параметров")
            return cleaned_params

        except Exception as e:
            self.logger.error(f"Ошибка очистки описаний параметров: {e}")
            return params

    # === МЕТОДЫ ФИЛЬТРАЦИИ ===

    def apply_filters(self, changed_only: bool = False):
        """ОБНОВЛЕННОЕ применение фильтров с поддержкой Use Cases"""
        try:
            self.logger.info(f"Начало применения фильтров (changed_only={changed_only})")

            if self.is_processing:
                self.logger.warning("Фильтрация уже выполняется, пропускаем")
                return

            self.is_processing = True

            try:
                # Проверяем наличие данных
                if not self._has_data():
                    self.logger.warning("Нет параметров для фильтрации. Загрузите CSV файл.")
                    self._show_no_data_message()
                    return

                # Специальная обработка для "только изменяемые параметры"
                if changed_only:
                    self._apply_changed_params_filter()
                else:
                    self._apply_standard_filters()

            finally:
                self.is_processing = False

        except Exception as e:
            self.logger.error(f"Ошибка применения фильтров: {e}")
            self.is_processing = False

    def _apply_changed_params_filter(self):
        """Применение фильтра изменяемых параметров"""
        try:
            # Получаем временной диапазон
            start_time_str, end_time_str = self._get_time_range()

            if not start_time_str or not end_time_str:
                self.logger.error("Не удалось получить временной диапазон")
                self._show_time_error()
                return

            # Используем Use Case если доступен
            if self.find_changed_params_use_case:
                self._apply_changed_params_with_use_case(start_time_str, end_time_str)
            else:
                self._apply_changed_params_fallback(start_time_str, end_time_str)

        except Exception as e:
            self.logger.error(f"Ошибка фильтрации изменяемых параметров: {e}")

    def _apply_changed_params_with_use_case(self, start_time_str: str, end_time_str: str):
        """Применение фильтра изменяемых параметров через Use Case"""
        try:
            request = FindChangedParametersRequest(
                session_id="current_session",
                from_time=start_time_str,
                to_time=end_time_str,
                threshold=0.1,
                include_timestamp_params=False,
                include_problematic_params=True
            )

            response = self.find_changed_params_use_case.execute(request)

            # Преобразуем DTO обратно в словари для UI
            changed_params = [self._dto_to_dict(dto) for dto in response.changed_parameters]

            self.logger.info(f"Найдено {len(changed_params)} изменяемых параметров через Use Case ({response.execution_time_ms:.1f}ms)")
            self._update_ui_with_filtered_params(changed_params)

        except Exception as e:
            self.logger.error(f"Ошибка Use Case для изменяемых параметров: {e}")
            self._apply_changed_params_fallback(start_time_str, end_time_str)

    def _apply_changed_params_fallback(self, start_time_str: str, end_time_str: str):
        """Fallback для фильтрации изменяемых параметров"""
        try:
            # Пытаемся через сервис фильтрации
            if self.filtering_service and hasattr(self.filtering_service, 'filter_changed_params'):
                changed_params = self.filtering_service.filter_changed_params(start_time_str, end_time_str)
                self.logger.info(f"Найдено {len(changed_params)} изменяемых параметров через сервис")
                self._update_ui_with_filtered_params(changed_params)
                return

            # Пытаемся через data_loader
            if (hasattr(self.model, 'data_loader') and 
                hasattr(self.model.data_loader, 'filter_changed_params')):
                changed_params = self.model.data_loader.filter_changed_params(start_time_str, end_time_str)
                self.logger.info(f"Найдено {len(changed_params)} изменяемых параметров через data_loader")
                self._update_ui_with_filtered_params(changed_params)
                return

            # Последний fallback - эвристика (первые 50% параметров)
            all_params = self._get_all_parameters()
            changed_params = all_params[:len(all_params)//2]
            self.logger.warning(f"Использована эвристика: {len(changed_params)} параметров")
            self._update_ui_with_filtered_params(changed_params)

        except Exception as e:
            self.logger.error(f"Ошибка fallback фильтрации изменяемых параметров: {e}")

    def _apply_standard_filters(self):
        """Применение стандартных фильтров"""
        try:
            # Используем Use Case если доступен
            if self.filter_parameters_use_case:
                self._apply_standard_filters_with_use_case()
            else:
                self._apply_standard_filters_fallback()

        except Exception as e:
            self.logger.error(f"Ошибка применения стандартных фильтров: {e}")

    def _apply_standard_filters_with_use_case(self):
        """Применение стандартных фильтров через Use Case"""
        try:
            # Получаем критерии фильтрации
            criteria = self._get_filter_criteria()

            # Создаем DTO для фильтрации
            filter_dto = FilterDTO(
                data_types=criteria.get('signal_types', []),
                lines=criteria.get('lines', []),
                wagons=criteria.get('wagons', []),
                signal_parts=criteria.get('components', []),
                changed_only=criteria.get('changed_only', False),
                search_text=criteria.get('search_text', ''),
                time_range=None
            )

            # Выполняем фильтрацию через Use Case
            request = FilterParametersRequest(
                session_id="current_session",
                filter_criteria=filter_dto
            )

            response = self.filter_parameters_use_case.execute(request)

            # Преобразуем DTO обратно в словари для UI
            filtered_params = [self._dto_to_dict(dto) for dto in response.parameters]

            self.logger.info(f"Применены фильтры через Use Case: {response.total_count} -> {response.filtered_count} параметров")
            self._update_ui_with_filtered_params(filtered_params)

        except Exception as e:
            self.logger.error(f"Ошибка Use Case для стандартных фильтров: {e}")
            self._apply_standard_filters_fallback()

    def _apply_standard_filters_fallback(self):
        """Fallback для стандартных фильтров"""
        try:
            # Получаем все параметры
            all_params = self._get_all_parameters()

            # Применяем фильтрацию через сервис если доступен
            if self.filtering_service:
                criteria = self._get_filter_criteria()
                filtered_params = self.filtering_service.filter_parameters(all_params, criteria)
                self.logger.info(f"Применены фильтры через сервис: {len(all_params)} -> {len(filtered_params)} параметров")
            else:
                # Простейший fallback - возвращаем все параметры
                filtered_params = all_params
                self.logger.warning(f"Fallback фильтрация: {len(filtered_params)} параметров")

            self._update_ui_with_filtered_params(filtered_params)

        except Exception as e:
            self.logger.error(f"Ошибка fallback фильтрации: {e}")

    def _dto_to_dict(self, param_dto) -> Dict[str, Any]:
        """Преобразование ParameterDTO в словарь для UI"""
        try:
            return {
                'signal_code': param_dto.signal_code,
                'full_column': param_dto.full_column,
                'description': param_dto.description,
                'line': param_dto.line,
                'data_type': param_dto.data_type,
                'signal_parts': param_dto.signal_parts,
                'wagon': param_dto.wagon,
                'plot': param_dto.plot
            }
        except Exception as e:
            self.logger.error(f"Ошибка преобразования DTO: {e}")
            return {}

    def _get_filter_criteria(self) -> Dict[str, Any]:
        """Получение критериев фильтрации с кэшированием"""
        try:
            current_time = time.time()

            # Проверяем кэш (обновляем каждые 100мс)
            if (self._filter_criteria_cache and 
                current_time - self._last_filter_update < 0.1):
                return self._filter_criteria_cache

            criteria = {
                'signal_types': [],
                'lines': [],
                'wagons': [],
                'components': [],
                'hardware': [],
                'changed_only': False,
                'search_text': ''
            }

            # Получаем критерии из UI
            filter_panel = self._get_filter_panel()
            if filter_panel and hasattr(filter_panel, 'get_selected_filters'):
                filter_result = filter_panel.get_selected_filters()
                criteria.update(filter_result)

            # Кэшируем результат
            self._filter_criteria_cache = criteria
            self._last_filter_update = current_time

            return criteria

        except Exception as e:
            self.logger.error(f"Ошибка получения критериев фильтрации: {e}")
            return self._get_default_criteria()

    def _get_filter_panel(self):
        """Получение filter_panel"""
        try:
            # Способ 1: Через ui_components
            if (hasattr(self.view, 'ui_components') and 
                self.view.ui_components and 
                hasattr(self.view.ui_components, 'filter_panel')):
                return self.view.ui_components.filter_panel

            # Способ 2: Прямой доступ
            if hasattr(self.view, 'filter_panel'):
                return self.view.filter_panel

            # Способ 3: Через get_component
            if hasattr(self.view, 'get_component'):
                return self.view.get_component('filter_panel')

            return None
        except Exception as e:
            self.logger.error(f"Ошибка получения filter_panel: {e}")
            return None

    def _get_default_criteria(self) -> Dict[str, Any]:
        """Критерии по умолчанию (все включено)"""
        return {
            'signal_types': ['B', 'BY', 'W', 'DW', 'F', 'WF'],
            'lines': [],
            'wagons': [str(i) for i in range(1, 16)],
            'components': [],
            'hardware': [],
            'changed_only': False,
            'search_text': ''
        }

    def _update_ui_with_filtered_params(self, filtered_params: List[Any]):
        """Обновление UI с отфильтрованными параметрами"""
        try:
            # Очищаем описания перед обновлением UI
            cleaned_params = self._clean_parameter_descriptions(filtered_params)

            # Обновляем счетчик
            if hasattr(self.view, 'update_filtered_count'):
                self.view.update_filtered_count(len(cleaned_params))

            # Обновляем параметры в UI
            self._update_parameters_in_ui(cleaned_params)

            # Принудительное обновление экрана
            if hasattr(self.view, 'root'):
                self.view.root.update_idletasks()

            # Уведомляем о применении фильтров
            self._emit_event('filters_applied', {'count': len(cleaned_params)})

            self.logger.info(f"UI обновлен с отфильтрованными параметрами: {len(cleaned_params)}")

        except Exception as e:
            self.logger.error(f"Ошибка обновления UI с отфильтрованными параметрами: {e}")

    # === МЕТОДЫ ПОСТРОЕНИЯ ГРАФИКОВ ===

    def build_plot(self):
        """ОБНОВЛЕННОЕ построение графика с интеграцией PlotVisualizationPanel"""
        try:
            # Получаем выбранные параметры
            selected_params = self._get_selected_parameters()

            if not selected_params:
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning("Выберите параметры для построения графика")
                return

            # Получаем временной диапазон
            start_time_str, end_time_str = self._get_time_range()

            # Валидация времени
            if not self._validate_time_range(start_time_str, end_time_str):
                return

            # Преобразуем строки времени в datetime
            try:
                start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
            except ValueError as e:
                self.logger.error(f"Ошибка парсинга времени: {e}")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(f"Неверный формат времени: {e}")
                return

            # Используем PlotVisualizationPanel если доступен
            plot_panel = self._get_plot_panel()
            if plot_panel and hasattr(plot_panel, 'build_plots_for_parameters'):
                plot_panel.build_plots_for_parameters(selected_params, start_time, end_time)
                self.logger.info("График построен через PlotVisualizationPanel")
                
                if hasattr(self.view, 'update_status'):
                    self.view.update_status("График построен")
            else:
                # Fallback к legacy методу
                self.logger.warning("PlotVisualizationPanel не найден, используется fallback")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Компонент построения графиков недоступен")

        except Exception as e:
            self.logger.error(f"Ошибка построения графика: {e}")
            import traceback
            traceback.print_exc()
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка построения графика: {e}")

    def _get_selected_parameters(self) -> List[Dict[str, Any]]:
        """Получение выбранных параметров"""
        try:
            # Способ 1: Через ui_components
            if (hasattr(self.view, 'ui_components') and 
                self.view.ui_components and 
                hasattr(self.view.ui_components, 'parameter_panel')):
                
                parameter_panel = self.view.ui_components.parameter_panel
                if hasattr(parameter_panel, 'get_selected_parameters'):
                    return parameter_panel.get_selected_parameters()

            # Способ 2: Через прямой доступ
            if hasattr(self.view, 'parameter_panel') and self.view.parameter_panel:
                parameter_panel = self.view.parameter_panel
                if hasattr(parameter_panel, 'get_selected_parameters'):
                    return parameter_panel.get_selected_parameters()

            # Способ 3: Через get_component
            if hasattr(self.view, 'get_component'):
                parameter_panel = self.view.get_component('parameter_panel')
                if parameter_panel and hasattr(parameter_panel, 'get_selected_parameters'):
                    return parameter_panel.get_selected_parameters()

            self.logger.warning("Не найден способ получения выбранных параметров")
            return []

        except Exception as e:
            self.logger.error(f"Ошибка получения выбранных параметров: {e}")
            return []

    def _get_plot_panel(self):
        """Получение PlotVisualizationPanel"""
        try:
            # Способ 1: Через ui_components
            if (hasattr(self.view, 'ui_components') and 
                self.view.ui_components and 
                hasattr(self.view.ui_components, 'plot_panel')):
                return self.view.ui_components.plot_panel

            # Способ 2: Прямой доступ
            if hasattr(self.view, 'plot_panel'):
                return self.view.plot_panel

            # Способ 3: Через get_component
            if hasattr(self.view, 'get_component'):
                return self.view.get_component('plot_panel')

            return None
        except Exception as e:
            self.logger.error(f"Ошибка получения plot_panel: {e}")
            return None

    def _get_time_range(self) -> Tuple[str, str]:
        """ИСПРАВЛЕННОЕ получение временного диапазона"""
        try:
            # Способ 1: Через time_panel
            time_panel = None
            
            # Поиск time_panel
            if (hasattr(self.view, 'ui_components') and 
                self.view.ui_components and 
                hasattr(self.view.ui_components, 'time_panel')):
                time_panel = self.view.ui_components.time_panel
            elif hasattr(self.view, 'time_panel'):
                time_panel = self.view.time_panel
            elif hasattr(self.view, 'get_component'):
                time_panel = self.view.get_component('time_panel')

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

    def _validate_time_range(self, start_str: str, end_str: str) -> bool:
        """Валидация временного диапазона"""
        try:
            if not start_str or not end_str:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Укажите временной диапазон")
                return False

            # Валидация формата
            try:
                start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S')

                if start_dt >= end_dt:
                    if hasattr(self.view, 'show_error'):
                        self.view.show_error("Время начала должно быть раньше времени окончания")
                    return False

                return True

            except ValueError as e:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(f"Неверный формат времени: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Ошибка валидации времени: {e}")
            return False

    # === МЕТОДЫ ГЕНЕРАЦИИ ОТЧЕТОВ И SOP ===

    def generate_report(self):
        """Генерация отчета"""
        try:
            if not self.report_generator:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Генератор отчетов не инициализирован")
                return

            # Получаем выбранные параметры
            selected_params = self._get_selected_parameters()

            if not selected_params:
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning("Выберите параметры для отчета")
                return

            # Получаем временной диапазон
            start_time_str, end_time_str = self._get_time_range()

            if not self._validate_time_range(start_time_str, end_time_str):
                return

            # Генерируем отчет
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[
                    ("PDF files", "*.pdf"),
                    ("Text files", "*.txt"),
                    ("Excel files", "*.xlsx")
                ]
            )

            if file_path:
                success = self.report_generator.generate_full_report(
                    {'selected_params': selected_params},
                    datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S'),
                    datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S'),
                    file_path
                )

                if success:
                    self.logger.info(f"Отчет создан: {file_path}")
                    if hasattr(self.view, 'show_info'):
                        self.view.show_info("Отчет", f"Отчет сохранен: {file_path}")
                else:
                    if hasattr(self.view, 'show_error'):
                        self.view.show_error("Ошибка создания отчета")

        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка генерации отчета: {e}")

    def generate_sop(self):
        """Генерация SOP"""
        try:
            if not self.sop_manager:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("SOP менеджер не инициализирован")
                return

            # Получаем выбранные параметры
            selected_params = self._get_selected_parameters()

            if not selected_params:
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning("Выберите параметры для SOP")
                return

            # Получаем временной диапазон
            start_time_str, end_time_str = self._get_time_range()

            if not self._validate_time_range(start_time_str, end_time_str):
                return

            # Генерируем SOP
            sop_xml = self.sop_manager.generate_sop_for_params(
                selected_params,
                datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S'),
                datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
            )

            if sop_xml:
                # Сохраняем SOP
                from tkinter import filedialog
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".sop",
                    filetypes=[("SOP files", "*.sop"), ("XML files", "*.xml")]
                )

                if file_path:
                    success = self.sop_manager.save_sop_to_file(sop_xml, file_path)

                    if success:
                        self.logger.info(f"SOP создан: {file_path}")
                        if hasattr(self.view, 'show_info'):
                            self.view.show_info("SOP", f"SOP сохранен: {file_path}")
                    else:
                        if hasattr(self.view, 'show_error'):
                            self.view.show_error("Ошибка сохранения SOP")
            else:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Ошибка создания SOP")

        except Exception as e:
            self.logger.error(f"Ошибка генерации SOP: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка генерации SOP: {e}")

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def _has_data(self) -> bool:
        """Проверка наличия данных для работы"""
        return (hasattr(self.model, 'data_loader') and
                self.model.data_loader and
                hasattr(self.model.data_loader, 'parameters') and
                self.model.data_loader.parameters)

    def _get_all_parameters(self) -> List[Any]:
        """Получение всех параметров"""
        if self._has_data():
            return self.model.data_loader.parameters
        return []

    def _show_no_data_message(self):
        """Показ сообщения об отсутствии данных"""
        if hasattr(self.view, 'show_warning'):
            self.view.show_warning("Загрузите CSV файл для отображения параметров")
        self._update_ui_with_filtered_params([])

    def _show_time_error(self):
        """Показ ошибки времени"""
        if hasattr(self.view, 'show_error'):
            self.view.show_error("Не удалось получить временной диапазон")

    def _start_loading(self, message: str = "Загрузка..."):
        """Начало процесса загрузки"""
        self.is_loading = True
        if hasattr(self.view, 'start_processing'):
            self.view.start_processing(message)

    def _stop_loading(self):
        """Завершение процесса загрузки"""
        self.is_loading = False
        if hasattr(self.view, 'stop_processing'):
            self.view.stop_processing()

    # === СИСТЕМА СОБЫТИЙ ===

    def register_callback(self, event_type: str, callback: Callable):
        """Регистрация callback для события"""
        if event_type in self._ui_callbacks:
            self._ui_callbacks[event_type].append(callback)

    def _emit_event(self, event_type: str, data: Any = None):
        """Генерация события"""
        try:
            if event_type in self._ui_callbacks:
                for callback in self._ui_callbacks[event_type]:
                    try:
                        callback(data)
                    except Exception as e:
                        self.logger.error(f"Ошибка в callback {callback}: {e}")
        except Exception as e:
            self.logger.error(f"Ошибка генерации события {event_type}: {e}")

    # === МЕТОДЫ ОЧИСТКИ ===

    def cleanup(self):
        """Очистка ресурсов контроллера"""
        try:
            # Очищаем кэш
            self._filter_criteria_cache = None
            self._ui_update_cache.clear()
            self._ui_callbacks.clear()

            # Очищаем сервисы
            if self.filtering_service and hasattr(self.filtering_service, 'cleanup'):
                self.filtering_service.cleanup()

            if self.plot_manager and hasattr(self.plot_manager, 'cleanup'):
                self.plot_manager.cleanup()

            if self.report_generator and hasattr(self.report_generator, 'cleanup'):
                self.report_generator.cleanup()

            if self.sop_manager and hasattr(self.sop_manager, 'cleanup'):
                self.sop_manager.cleanup()

            # Обнуляем ссылки
            self.filtering_service = None
            self.plot_manager = None
            self.report_generator = None
            self.sop_manager = None

            self.logger.info("MainController очищен")

        except Exception as e:
            self.logger.error(f"Ошибка очистки MainController: {e}")

    def get_state(self) -> Dict[str, Any]:
        """Получение состояния контроллера"""
        return {
            'is_processing': self.is_processing,
            'is_loading': self.is_loading,
            'current_file': self.current_file_path,
            'has_data': self._has_data(),
            'cache_size': len(self._ui_update_cache),
            'callbacks_count': sum(len(callbacks) for callbacks in self._ui_callbacks.values())
        }

    def __str__(self):
        return f"MainController(processing={self.is_processing}, has_data={self._has_data()})"

    def __repr__(self):
        return self.__str__()

    def set_time_panel(self, time_panel):
        """Установка TimePanel"""
        self.time_panel = time_panel
        self.logger.info("TimePanel установлен в контроллере")

    def set_filter_panel(self, filter_panel):
        """Установка FilterPanel"""
        self.filter_panel = filter_panel
        self.logger.info("FilterPanel установлен в контроллере")

    def set_parameter_panel(self, parameter_panel):
        """Установка ParameterPanel"""
        self.parameter_panel = parameter_panel
        self.logger.info("ParameterPanel установлен в контроллере")

    def set_action_panel(self, action_panel):
        """Установка ActionPanel"""
        self.action_panel = action_panel
        self.logger.info("ActionPanel установлен в контроллере")

    # === ДОБАВЛЕННЫЕ ДИАГНОСТИЧЕСКИЕ МЕТОДЫ ===

    def apply_diagnostic_filters(self, diagnostic_filters: Dict[str, List[str]]):
        """Применение диагностических фильтров"""
        try:
            if not self._has_data():
                self.logger.warning("Нет данных для применения диагностических фильтров")
                return
            
            # Получаем все параметры
            all_parameters = self.model.data_loader.parameters
            if not all_parameters:
                return
            
            # Применяем диагностические фильтры
            if self.filtering_service and hasattr(self.filtering_service, 'filter_by_diagnostic_criteria'):
                filtered_parameters = self.filtering_service.filter_by_diagnostic_criteria(
                    all_parameters, diagnostic_filters
                )
            else:
                # Fallback - используем базовую фильтрацию
                filtered_parameters = self._apply_diagnostic_filters_fallback(
                    all_parameters, diagnostic_filters
                )
            
            # Обновляем параметры в UI
            self._update_parameters_in_ui(filtered_parameters)
            
            # Обновляем статистику
            self._update_diagnostic_statistics(filtered_parameters, diagnostic_filters)
            
            self.logger.info(f"Применены диагностические фильтры: {len(all_parameters)} -> {len(filtered_parameters)}")
            
        except Exception as e:
            self.logger.error(f"Ошибка применения диагностических фильтров: {e}")

    def perform_diagnostic_analysis(self):
        """Выполнение диагностического анализа"""
        try:
            if not self._has_data():
                self.logger.warning("Нет данных для диагностического анализа")
                return
            
            # Получаем все параметры
            all_parameters = self.model.data_loader.parameters
            if not all_parameters:
                return
            
            # Выполняем анализ паттернов неисправностей
            if (self.filtering_service and 
                hasattr(self.filtering_service, 'analyze_fault_patterns')):
                
                analysis_results = self.filtering_service.analyze_fault_patterns(all_parameters)
                
                # Отображаем результаты в UI
                self._display_diagnostic_results(analysis_results)
                
            else:
                self.logger.warning("Диагностический анализ недоступен")
                
        except Exception as e:
            self.logger.error(f"Ошибка выполнения диагностического анализа: {e}")

    def _apply_diagnostic_filters_fallback(self, parameters: List[Dict[str, Any]], 
                                         diagnostic_filters: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Fallback применение диагностических фильтров"""
        try:
            # Простая реализация без классификатора
            filtered = []
            
            for param in parameters:
                signal_code = param.get('signal_code', '').upper()
                description = param.get('description', '').upper()
                combined_text = f"{signal_code} {description}"
                
                include_param = False
                
                # Проверка критичности
                if diagnostic_filters.get('criticality'):
                    for crit_filter in diagnostic_filters['criticality']:
                        if crit_filter == 'emergency' and any(word in combined_text for word in ['EMERGENCY', 'ALARM', 'FAULT']):
                            include_param = True
                        elif crit_filter == 'safety' and any(word in combined_text for word in ['SAFETY', 'SECURITY', 'FIRE']):
                            include_param = True
                        # ... другие проверки
                
                # Проверка систем
                if diagnostic_filters.get('systems'):
                    for sys_filter in diagnostic_filters['systems']:
                        if sys_filter == 'brakes' and any(word in combined_text for word in ['BCU', 'BRAKE', 'PRESSURE']):
                            include_param = True
                        elif sys_filter == 'power' and any(word in combined_text for word in ['PSN', 'QF', '3000V']):
                            include_param = True
                        # ... другие проверки
                
                # Если нет активных фильтров, включаем все
                if not any(diagnostic_filters.values()):
                    include_param = True
                
                if include_param:
                    filtered.append(param)
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"Ошибка fallback диагностической фильтрации: {e}")
            return parameters

    def _display_diagnostic_results(self, results: Dict[str, Any]):
        """Отображение результатов диагностического анализа"""
        try:
            # Получаем панель диагностических фильтров
            diagnostic_panel = self._get_diagnostic_filter_panel()
            
            if diagnostic_panel and hasattr(diagnostic_panel, 'show_diagnostic_results'):
                diagnostic_panel.show_diagnostic_results(results)
            else:
                # Fallback - логируем результаты
                self.logger.info("Результаты диагностического анализа:")
                self.logger.info(f"Найдено неисправностей: {results.get('fault_count', 0)}")
                self.logger.info(f"Общий статус: {results.get('system_health', {}).get('overall_status', 'unknown')}")
                
        except Exception as e:
            self.logger.error(f"Ошибка отображения результатов диагностики: {e}")

    def _get_diagnostic_filter_panel(self):
        """Получение панели диагностических фильтров"""
        try:
            if (hasattr(self.view, 'ui_components') and 
                self.view.ui_components and 
                hasattr(self.view.ui_components, 'diagnostic_filter_panel')):
                return self.view.ui_components.diagnostic_filter_panel
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения диагностической панели: {e}")
            return None

    def load_test_data(self):
        """Загрузка тестовых данных для проверки UI"""
        try:
            test_params = [
                {
                    'signal_code': 'TEST_PARAM_1',
                    'description': 'Тестовый параметр телеметрии 1',
                    'line': 'L_CAN_BLOK_CH',
                    'wagon': '1',
                    'signal_type': 'B',
                    'data_type': 'BOOL'
                },
                {
                    'signal_code': 'TEST_PARAM_2', 
                    'description': 'Тестовый параметр телеметрии 2',
                    'line': 'L_CAN_ICU_CH_A',
                    'wagon': '2',
                    'signal_type': 'BY',
                    'data_type': 'BYTE'
                },
                {
                    'signal_code': 'TEST_PARAM_3',
                    'description': 'Тестовый параметр телеметрии 3', 
                    'line': 'L_CAN_POS_CH',
                    'wagon': '1',
                    'signal_type': 'W',
                    'data_type': 'WORD'
                },
                {
                    'signal_code': 'TEST_PARAM_4',
                    'description': 'Тестовый параметр телеметрии 4',
                    'line': 'L_CAN_BLOK_CH',
                    'wagon': '3',
                    'signal_type': 'DW',
                    'data_type': 'DWORD'
                },
                {
                    'signal_code': 'TEST_PARAM_5',
                    'description': 'Тестовый параметр телеметрии 5',
                    'line': 'L_CAN_ICU_CH_B',
                    'wagon': '2',
                    'signal_type': 'F',
                    'data_type': 'FLOAT'
                }
            ]

            self.logger.info(f"Загрузка тестовых данных: {len(test_params)} параметров")
            
            # Обновляем UI через правильные пути
            if hasattr(self.view, 'ui_components') and self.view.ui_components:
                if hasattr(self.view.ui_components, 'parameter_panel'):
                    self.view.ui_components.parameter_panel.update_parameters(test_params)
                    self.logger.info("✅ Тестовые данные переданы в ParameterPanel")
                else:
                    self.logger.error("❌ parameter_panel не найден в ui_components")
            else:
                self.logger.error("❌ ui_components не найден в view")
            
            # Обновляем время
            from datetime import datetime
            now = datetime.now()
            time_fields = {
                'from_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                'to_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': '00:00:00',
                'total_records': len(test_params)
            }
            
            if hasattr(self, '_update_time_panel_fields'):
                self._update_time_panel_fields(time_fields)

            self.logger.info("✅ Тестовые данные загружены успешно")

        except Exception as e:
            self.logger.error(f"Ошибка загрузки тестовых данных: {e}")
            import traceback
            traceback.print_exc()
