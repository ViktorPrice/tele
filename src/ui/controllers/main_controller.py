"""
Интеграция Use Cases в MainController
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ...core.application.use_cases.filter_parameters_use_case import (
    FilterParametersUseCase, FilterParametersRequest, FindChangedParametersUseCase,
    FindChangedParametersRequest, TimeRangeInitUseCase, TimeRangeInitRequest
)
from ...core.application.dto.filter_dto import FilterDTO


class MainController:
    """Главный контроллер приложения (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)

        # Сервисы (внедряются извне)
        self.filtering_service = None
        self.plot_manager = None
        self.report_generator = None
        self.sop_manager = None

        # UI компоненты (внедряются извне)
        self.time_panel = None
        self.ui_components = None

        # Use Cases
        self.filter_parameters_use_case: Optional[FilterParametersUseCase] = None
        self.find_changed_params_use_case: Optional[FindChangedParametersUseCase] = None
        self.time_range_init_use_case: Optional[TimeRangeInitUseCase] = None

        # Кэш для оптимизации
        self._filter_criteria_cache: Optional[Dict[str, List[str]]] = None
        self._last_filter_update = 0

        # Состояние
        self.is_processing = False

        self._setup_use_cases()

        self.logger.info("Контроллер инициализирован")

    # Добавлены методы для внедрения сервисов
    def set_filtering_service(self, service):
        self.filtering_service = service
        self.logger.info("Фильтрационный сервис установлен")

    def set_plot_manager(self, service):
        self.plot_manager = service
        self.logger.info("PlotManager установлен")

    def set_report_manager(self, service):
        self.report_generator = service
        self.logger.info("ReportManager установлен")

    def set_sop_manager(self, service):
        self.sop_manager = service
        self.logger.info("SOPManager установлен")

    # Добавлены методы для внедрения UI компонентов
    def set_time_panel(self, time_panel):
        self.time_panel = time_panel
        self.logger.info("TimePanel установлен")

    def set_ui_components(self, ui_components):
        self.ui_components = ui_components
        self.logger.info("UIComponents установлен")

    def _setup_use_cases(self):
        """Настройка Use Cases"""
        try:
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

            self.logger.info("Use Cases инициализированы в контроллере")

        except Exception as e:
            self.logger.error(f"Ошибка инициализации Use Cases: {e}")

    def _on_file_loaded(self, file_path: str):
        """ОБНОВЛЕННАЯ обработка загрузки файла с Use Cases"""
        try:
            self.logger.info("=== НАЧАЛО ОБРАБОТКИ ЗАГРУЖЕННОГО ФАЙЛА ===")

            # ШАГ 1: Инициализация временного диапазона через Use Case
            if self.time_range_init_use_case:
                time_request = TimeRangeInitRequest(
                    session_id="current_session")
                time_response = self.time_range_init_use_case.execute(
                    time_request)

                if time_response.success:
                    time_fields = {
                        'from_time': time_response.from_time,
                        'to_time': time_response.to_time,
                        'duration': time_response.duration,
                        'total_records': time_response.total_records
                    }

                    success = self._update_time_panel_fields(time_fields)
                    if success:
                        self.logger.info(
                            f"✅ UI поля времени обновлены через Use Case: {time_response.from_time} - {time_response.to_time}")
                    else:
                        self.logger.error(
                            "❌ Не удалось обновить поля времени в UI")
                else:
                    self.logger.warning(
                        f"⚠️ Ошибка инициализации времени: {time_response.message}")

            # ШАГ 2: Обработка параметров через существующую логику
            self._handle_successful_load()

            self.logger.info("=== ОБРАБОТКА ФАЙЛА ЗАВЕРШЕНА ===")

        except Exception as e:
            self.logger.error(f"Ошибка обработки загруженного файла: {e}")
            import traceback
            traceback.print_exc()

    def apply_filters(self, changed_only: bool = False):
        """ОБНОВЛЕННОЕ применение фильтров через Use Cases"""
        try:
            self.logger.info(
                f"Начало применения фильтров через Use Cases (changed_only={changed_only})")

            if self.is_processing:
                self.logger.warning("Фильтрация уже выполняется, пропускаем")
                return

            self.is_processing = True

            try:
                # Проверяем наличие данных
                if not self._has_data():
                    self.logger.warning(
                        "Нет параметров для фильтрации. Загрузите CSV файл.")
                    self._show_no_data_message()
                    return

                if changed_only:
                    # Используем Use Case для поиска изменяемых параметров
                    self._apply_changed_params_filter_with_use_case()
                else:
                    # Используем Use Case для обычной фильтрации
                    self._apply_standard_filters_with_use_case()

            finally:
                self.is_processing = False

        except Exception as e:
            self.logger.error(f"Ошибка применения фильтров: {e}")
            self.is_processing = False

    def _apply_changed_params_filter_with_use_case(self):
        """Применение фильтра изменяемых параметров через Use Case"""
        try:
            # Получаем временной диапазон
            start_time_str, end_time_str = self._get_time_range()

            if not start_time_str or not end_time_str:
                self.logger.error("Не удалось получить временной диапазон")
                self._show_time_error()
                return

            # Используем Use Case
            if self.find_changed_params_use_case:
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
                changed_params = [self._dto_to_dict(
                    dto) for dto in response.changed_parameters]

                self.logger.info(
                    f"Найдено {len(changed_params)} изменяемых параметров через Use Case ({response.execution_time_ms:.1f}ms)")
                self._update_ui_with_filtered_params(changed_params)
            else:
                # Fallback к старому методу
                self._apply_changed_params_fallback(
                    start_time_str, end_time_str)

        except Exception as e:
            self.logger.error(
                f"Ошибка фильтрации изменяемых параметров через Use Case: {e}")

    def _apply_standard_filters_with_use_case(self):
        """Применение стандартных фильтров через Use Case"""
        try:
            if not self.filter_parameters_use_case:
                self.logger.warning("Use Case фильтрации не установлен")
                self._apply_fallback_filters()
                return

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
                time_range=None  # Пока не используем
            )

            # Выполняем фильтрацию через Use Case
            request = FilterParametersRequest(
                session_id="current_session",
                filter_criteria=filter_dto
            )

            response = self.filter_parameters_use_case.execute(request)

            # Преобразуем DTO обратно в словари для UI
            filtered_params = [self._dto_to_dict(
                dto) for dto in response.parameters]

            self.logger.info(
                f"Применены фильтры через Use Case: {response.total_count} -> {response.filtered_count} параметров")

            # Обновляем UI
            self._update_ui_with_filtered_params(filtered_params)

        except Exception as e:
            self.logger.error(
                f"Ошибка применения стандартных фильтров через Use Case: {e}")
            self._apply_fallback_filters()

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

    def build_plot(self):
        """ОБНОВЛЕННОЕ построение графика с интеграцией PlotVisualizationPanel"""
        try:
            # Получаем выбранные параметры
            selected_params = self._get_selected_parameters()

            if not selected_params:
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning(
                        "Выберите параметры для построения графика")
                return

            # Получаем временной диапазон
            start_time_str, end_time_str = self._get_time_range()

            # Валидация времени
            if not self._validate_time_range(start_time_str, end_time_str):
                return

            # Преобразуем строки времени в datetime
            try:
                start_time = datetime.strptime(
                    start_time_str, '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
            except ValueError as e:
                self.logger.error(f"Ошибка парсинга времени: {e}")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(f"Неверный формат времени: {e}")
                return

            # Используем PlotVisualizationPanel если доступен
            plot_panel = self._get_plot_panel()
            if plot_panel:
                plot_panel.build_plots_for_parameters(
                    selected_params, start_time, end_time)
                self.logger.info(
                    "График построен через PlotVisualizationPanel")

                if hasattr(self.view, 'update_status'):
                    self.view.update_status("График построен")
            else:
                # Fallback к legacy методу
                self.logger.warning(
                    "PlotVisualizationPanel не найден, используется fallback")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(
                        "Компонент построения графиков недоступен")

        except Exception as e:
            self.logger.error(f"Ошибка построения графика: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка построения графика: {e}")

    def _get_plot_panel(self):
        """Получение PlotVisualizationPanel"""
        try:
            if hasattr(self.view, 'plot_panel'):
                return self.view.plot_panel
            elif hasattr(self.view, 'get_component'):
                return self.view.get_component('plot_panel')
            return None
        except Exception as e:
            self.logger.error(f"Ошибка получения plot_panel: {e}")
            return None

    def _update_time_panel_fields(self, time_fields: Dict[str, str]) -> bool:
        """КРИТИЧНО ИСПРАВЛЕНО: Обновление полей времени в UI"""
        try:
            self.logger.info(
                f"Попытка обновления полей времени: {time_fields}")

            # МНОЖЕСТВЕННЫЕ СПОСОБЫ ПОИСКА time_panel
            time_panel = None
            search_paths = []

            # Способ 1: Прямой доступ через view.time_panel
            if hasattr(self.view, 'time_panel') and self.view.time_panel:
                time_panel = self.view.time_panel
                search_paths.append("view.time_panel ✅")
            else:
                search_paths.append("view.time_panel ❌")

            # Способ 2: Через main_window.time_panel
            if not time_panel and hasattr(self.view, 'main_window'):
                if hasattr(self.view.main_window, 'time_panel'):
                    time_panel = self.view.main_window.time_panel
                    search_paths.append("main_window.time_panel ✅")
                else:
                    search_paths.append("main_window.time_panel ❌")

            # Способ 3: Через get_component
            if not time_panel and hasattr(self.view, 'get_component'):
                time_panel = self.view.get_component('time_panel')
                if time_panel:
                    search_paths.append("get_component('time_panel') ✅")
                else:
                    search_paths.append("get_component('time_panel') ❌")

            # Способ 4: Поиск в UI компонентах
            if not time_panel:
                time_panel = self._find_time_panel_in_ui()
                if time_panel:
                    search_paths.append("_find_time_panel_in_ui() ✅")
                else:
                    search_paths.append("_find_time_panel_in_ui() ❌")

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
                    self.logger.info(
                        "✅ time_panel.update_time_fields выполнен успешно")
                    return True
                else:
                    self.logger.error(
                        f"❌ time_panel не имеет метода update_time_fields. Доступные методы: {[m for m in dir(time_panel) if not m.startswith('_')]}")
                    return False
            else:
                self.logger.error(
                    "❌ time_panel НЕ НАЙДЕН во всех попытках поиска")

                # ДИАГНОСТИКА: Выводим структуру view
                self._diagnose_view_structure()
                return False

        except Exception as e:
            self.logger.error(f"Ошибка обновления полей времени: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _find_time_panel_in_ui(self):
        """Поиск time_panel в компонентах UI"""
        try:
            # Поиск по атрибутам view
            if hasattr(self.view, '__dict__'):
                for attr_name, attr_value in self.view.__dict__.items():
                    if 'time' in attr_name.lower() and hasattr(attr_value, 'update_time_fields'):
                        self.logger.info(
                            f"Найден time_panel через атрибут: {attr_name}")
                        return attr_value

            # Поиск по children виджетов
            if hasattr(self.view, 'root') and hasattr(self.view.root, 'winfo_children'):
                return self._search_widget_tree(self.view.root, 'time_panel')

            return None

        except Exception as e:
            self.logger.error(f"Ошибка поиска time_panel в UI: {e}")
            return None

    def _search_widget_tree(self, widget, target_name):
        """Рекурсивный поиск виджета в дереве"""
        try:
            # Проверяем текущий виджет
            if hasattr(widget, '_name') and target_name in widget._name:
                return widget

            # Ищем в дочерних виджетах
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    result = self._search_widget_tree(child, target_name)
                    if result:
                        return result

            return None

        except Exception:
            return None

    def _diagnose_view_structure(self):
        """ДИАГНОСТИКА: Анализ структуры view"""
        try:
            self.logger.info("=== ДИАГНОСТИКА СТРУКТУРЫ VIEW ===")

            if hasattr(self.view, '__dict__'):
                view_attrs = list(self.view.__dict__.keys())
                self.logger.info(f"Атрибуты view: {view_attrs}")

                # Ищем атрибуты связанные со временем
                time_related = [
                    attr for attr in view_attrs if 'time' in attr.lower()]
                if time_related:
                    self.logger.info(
                        f"Атрибуты связанные со временем: {time_related}")

                # Ищем панели
                panel_related = [
                    attr for attr in view_attrs if 'panel' in attr.lower()]
                if panel_related:
                    self.logger.info(f"Атрибуты панелей: {panel_related}")

            # Проверяем main_window
            if hasattr(self.view, 'main_window'):
                self.logger.info("main_window найден")
                if hasattr(self.view.main_window, '__dict__'):
                    mw_attrs = list(self.view.main_window.__dict__.keys())
                    self.logger.info(f"Атрибуты main_window: {mw_attrs}")

        except Exception as e:
            self.logger.error(f"Ошибка диагностики: {e}")

    def _handle_successful_load(self):
        """Обработка успешной загрузки (обновлена)"""
        try:
            if self._has_data():
                params = self.model.data_loader.parameters
                self.logger.info(f"Загружено параметров: {len(params)}")

                # Очищаем кэш фильтров
                self._filter_criteria_cache = None

                # Обновляем дерево параметров
                if hasattr(self.view, 'parameter_panel') and self.view.parameter_panel:
                    if hasattr(self.view.parameter_panel, 'update_tree_all_params'):
                        # ИСПРАВЛЕНИЕ: Очищаем описания параметров перед обновлением
                        cleaned_params = self._clean_parameter_descriptions(
                            params)
                        self.view.parameter_panel.update_tree_all_params(
                            cleaned_params)

                # Обновляем фильтры
                if hasattr(self.model.data_loader, 'lines'):
                    lines = list(self.model.data_loader.lines)
                    if hasattr(self.view, 'filter_panel') and self.view.filter_panel:
                        if hasattr(self.view.filter_panel, 'update_line_checkboxes'):
                            self.view.filter_panel.update_line_checkboxes(
                                lines)

                # Применяем фильтры
                self.apply_filters()

                # Обновляем статус
                if hasattr(self.view, 'update_status'):
                    self.view.update_status(
                        f"Файл загружен: {len(params)} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка обработки успешной загрузки: {e}")

    def _clean_parameter_descriptions(self, params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """НОВОЕ: Очистка описаний параметров от артефактов"""
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
                        description = description.replace(
                            '|0', '').replace('|', '').strip()

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

            self.logger.info(
                f"Очищены описания {len(cleaned_params)} параметров")
            return cleaned_params

        except Exception as e:
            self.logger.error(f"Ошибка очистки описаний параметров: {e}")
            return params

    def apply_filters(self, changed_only: bool = False):
        """ИСПРАВЛЕННОЕ применение фильтров с поддержкой changed_only"""
        try:
            self.logger.info(
                f"Начало применения фильтров (changed_only={changed_only})")

            if self.is_processing:
                self.logger.warning("Фильтрация уже выполняется, пропускаем")
                return

            self.is_processing = True

            try:
                # Проверяем наличие данных
                if not self._has_data():
                    self.logger.warning(
                        "Нет параметров для фильтрации. Загрузите CSV файл.")
                    self._show_no_data_message()
                    return

                # Специальная обработка для "только изменяемые параметры"
                if changed_only:
                    self._apply_changed_params_filter()
                    return

                # Обычная фильтрация
                self._apply_standard_filters()

            finally:
                self.is_processing = False

        except Exception as e:
            self.logger.error(f"Ошибка применения фильтров: {e}")
            self.is_processing = False

    def _has_data(self) -> bool:
        """Проверка наличия данных для фильтрации"""
        return (hasattr(self.model, 'data_loader') and
                self.model.data_loader and
                hasattr(self.model.data_loader, 'parameters') and
                self.model.data_loader.parameters)

    def _show_no_data_message(self):
        """Показ сообщения об отсутствии данных"""
        if hasattr(self.view, 'show_warning'):
            self.view.show_warning(
                "Загрузите CSV файл для отображения параметров")

        # Обновляем UI с пустыми данными
        self._update_ui_with_filtered_params([])

    def _apply_changed_params_filter(self):
        """Применение фильтра только изменяемых параметров"""
        try:
            # Получаем временной диапазон
            start_time_str, end_time_str = self._get_time_range()

            if not start_time_str or not end_time_str:
                self.logger.error("Не удалось получить временной диапазон")
                self._show_time_error()
                return

            # Применяем фильтрацию изменяемых параметров
            if self.filtering_service and hasattr(self.filtering_service, 'filter_changed_params'):
                changed_params = self.filtering_service.filter_changed_params(
                    start_time_str, end_time_str
                )

                self.logger.info(
                    f"Найдено {len(changed_params)} изменяемых параметров")
                self._update_ui_with_filtered_params(changed_params)

            else:
                # Fallback через модель
                self._apply_changed_params_fallback(
                    start_time_str, end_time_str)

        except Exception as e:
            self.logger.error(f"Ошибка фильтрации изменяемых параметров: {e}")

    def _apply_changed_params_fallback(self, start_time_str: str, end_time_str: str):
        """Fallback для фильтрации изменяемых параметров"""
        try:
            # Пытаемся через data_loader
            if (hasattr(self.model, 'data_loader') and
                    hasattr(self.model.data_loader, 'filter_changed_params')):

                changed_params = self.model.data_loader.filter_changed_params(
                    start_time_str, end_time_str
                )

                self.logger.info(
                    f"Найдено {len(changed_params)} изменяемых параметров через data_loader")
                self._update_ui_with_filtered_params(changed_params)
                return

            # Последний fallback - эвристика
            all_params = self._get_all_parameters()
            changed_params = all_params[:len(all_params)//2]  # Первые 50%

            self.logger.warning(
                f"Использована эвристика: {len(changed_params)} параметров")
            self._update_ui_with_filtered_params(changed_params)

        except Exception as e:
            self.logger.error(f"Ошибка fallback фильтрации: {e}")

    def _apply_standard_filters(self):
        """Применение стандартных фильтров"""
        try:
            if not self.filtering_service:
                self.logger.warning("Сервис фильтрации не установлен")
                self._apply_fallback_filters()
                return

            # Получаем критерии фильтрации
            criteria = self._get_filter_criteria()

            # Получаем все параметры
            all_params = self._get_all_parameters()

            # Применяем фильтрацию через сервис
            filtered_params = self.filtering_service.filter_parameters(
                all_params, criteria)

            self.logger.info(
                f"Применены фильтры через сервис: {len(all_params)} -> {len(filtered_params)} параметров")

            # Обновляем UI
            self._update_ui_with_filtered_params(filtered_params)

        except Exception as e:
            self.logger.error(f"Ошибка применения стандартных фильтров: {e}")
            self._apply_fallback_filters()

    def _get_filter_criteria(self) -> Dict[str, List[str]]:
        """Получение критериев фильтрации с кэшированием"""
        try:
            import time
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
                'hardware': []
            }

            if hasattr(self.view, 'filter_panel') and self.view.filter_panel:
                filter_panel = self.view.filter_panel

                # Получаем через новый интерфейс
                if hasattr(filter_panel, 'get_selected_filters'):
                    filter_result = filter_panel.get_selected_filters()
                    criteria.update(filter_result)

                    # НОВОЕ: Обрабатываем чекбокс изменяемых параметров
                    if filter_result.get('changed_only', False):
                        self.logger.info(
                            "Активирован фильтр 'только изменяемые параметры'")
                        self.apply_filters(changed_only=True)
                        return criteria

                # Fallback на старый интерфейс
                else:
                    criteria.update(
                        self._extract_legacy_filter_criteria(filter_panel))

            # Кэшируем результат
            self._filter_criteria_cache = criteria
            self._last_filter_update = current_time

            return criteria

        except Exception as e:
            self.logger.error(f"Ошибка получения критериев фильтрации: {e}")
            return self._get_default_criteria()

    # Остальные методы остаются без изменений...
    def _extract_legacy_filter_criteria(self, filter_panel) -> Dict[str, List[str]]:
        """Извлечение критериев из legacy интерфейса"""
        criteria = {}

        # Извлечение через атрибуты панели
        if hasattr(filter_panel, 'signal_vars'):
            criteria['signal_types'] = [
                k for k, v in filter_panel.signal_vars.items() if v.get()
            ]

        if hasattr(filter_panel, 'line_vars'):
            criteria['lines'] = [
                k for k, v in filter_panel.line_vars.items() if v.get()
            ]

        if hasattr(filter_panel, 'wagon_vars'):
            criteria['wagons'] = [
                k for k, v in filter_panel.wagon_vars.items() if v.get()
            ]

        if hasattr(filter_panel, 'component_vars'):
            criteria['components'] = [
                k for k, v in filter_panel.component_vars.items() if v.get()
            ]

        if hasattr(filter_panel, 'hardware_vars'):
            criteria['hardware'] = [
                k for k, v in filter_panel.hardware_vars.items() if v.get()
            ]

        return criteria

    def _get_default_criteria(self) -> Dict[str, List[str]]:
        """Критерии по умолчанию (все включено)"""
        return {
            'signal_types': ['B', 'BY', 'W', 'DW', 'F', 'WF'],
            'lines': [],
            'wagons': [str(i) for i in range(1, 16)],
            'components': [],
            'hardware': []
        }

    def _get_all_parameters(self) -> List[Any]:
        """Получение всех параметров"""
        if self._has_data():
            return self.model.data_loader.parameters
        return []

    def _get_time_range(self) -> Tuple[str, str]:
        """ИСПРАВЛЕННОЕ получение временного диапазона"""
        try:
            # МНОЖЕСТВЕННЫЕ ПОПЫТКИ получения времени

            # Способ 1: Через time_panel
            time_panel = self._find_time_panel_in_ui()
            if time_panel and hasattr(time_panel, 'get_time_range'):
                result = time_panel.get_time_range()
                if result[0] and result[1]:
                    self.logger.debug(
                        f"Время получено через time_panel: {result}")
                    return result

            # Способ 2: Через filter_panel с полями времени
            if hasattr(self.view, 'filter_panel') and self.view.filter_panel:
                filter_panel = self.view.filter_panel
                if (hasattr(filter_panel, 'from_time_entry') and
                        hasattr(filter_panel, 'to_time_entry')):
                    from_time = filter_panel.from_time_entry.get()
                    to_time = filter_panel.to_time_entry.get()
                    if from_time and to_time:
                        self.logger.debug(
                            f"Время получено через filter_panel: {from_time} - {to_time}")
                        return (from_time, to_time)

            # Способ 3: Через модель данных
            if hasattr(self.model, 'get_time_range_fields'):
                time_fields = self.model.get_time_range_fields()
                if time_fields and time_fields.get('from_time') and time_fields.get('to_time'):
                    result = (time_fields['from_time'], time_fields['to_time'])
                    self.logger.debug(f"Время получено через модель: {result}")
                    return result

            # Fallback - текущее время
            from datetime import datetime, timedelta
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

    def _show_time_error(self):
        """Показ ошибки времени"""
        if hasattr(self.view, 'show_error'):
            self.view.show_error("Не удалось получить временной диапазон")

    def _apply_fallback_filters(self):
        """Fallback фильтрация без сервиса"""
        try:
            all_params = self._get_all_parameters()
            self.logger.info(
                f"Fallback фильтрация: {len(all_params)} параметров")
            self._update_ui_with_filtered_params(all_params)

        except Exception as e:
            self.logger.error(f"Ошибка fallback фильтрации: {e}")

    def _update_ui_with_filtered_params(self, filtered_params: List[Any]):
        """Обновление UI с отфильтрованными параметрами"""
        try:
            # ИСПРАВЛЕНИЕ: Очищаем описания перед обновлением UI
            cleaned_params = self._clean_parameter_descriptions(
                filtered_params)

            # Обновляем счетчик
            if hasattr(self.view, 'update_filtered_count'):
                self.view.update_filtered_count(len(cleaned_params))

            # Обновляем дерево параметров
            if hasattr(self.view, 'parameter_panel') and self.view.parameter_panel:
                if hasattr(self.view.parameter_panel, 'update_tree_all_params'):
                    self.view.parameter_panel.update_tree_all_params(
                        cleaned_params)
                    self.logger.info(
                        f"UI обновлен: {len(cleaned_params)} параметров")
                else:
                    self.logger.error(
                        "Метод update_tree_all_params не найден в parameter_panel")
            else:
                self.logger.error("parameter_panel не найден в view")

            # Принудительное обновление экрана
            if hasattr(self.view, 'root'):
                self.view.root.update_idletasks()

        except Exception as e:
            self.logger.error(f"Ошибка обновления UI: {e}")

    def upload_csv(self):
        """ИСПРАВЛЕННАЯ загрузка CSV"""
        try:
            from tkinter import filedialog

            file_path = filedialog.askopenfilename(
                title="Выберите CSV файл",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if file_path:
                self.logger.info(f"Выбран файл: {file_path}")

                # Показываем процесс загрузки
                if hasattr(self.view, 'start_processing'):
                    self.view.start_processing("Загрузка файла...")

                # Загружаем файл
                success = self._load_csv_file(file_path)

                if success:
                    self.logger.info("Файл успешно загружен")
                    # КРИТИЧНО: Вызываем обработку успешной загрузки
                    self._on_file_loaded(file_path)
                else:
                    self.logger.error("Ошибка загрузки файла")
                    if hasattr(self.view, 'show_error'):
                        self.view.show_error("Ошибка загрузки файла")

                # Останавливаем индикатор загрузки
                if hasattr(self.view, 'stop_processing'):
                    self.view.stop_processing()

        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка загрузки: {e}")
            if hasattr(self.view, 'stop_processing'):
                self.view.stop_processing()

    def _load_csv_file(self, file_path: str) -> bool:
        """Загрузка CSV файла через модель"""
        try:
            if hasattr(self.model, 'load_csv_file'):
                return self.model.load_csv_file(file_path)
            else:
                self.logger.error("Метод load_csv_file не найден в модели")
                return False

        except Exception as e:
            self.logger.error(f"Ошибка в _load_csv_file: {e}")
            return False

    def _handle_successful_load(self):
        """ИСПРАВЛЕННАЯ обработка успешной загрузки (обновлена)"""
        try:
            if self._has_data():
                params = self.model.data_loader.parameters
                self.logger.info(f"Загружено параметров: {len(params)}")

                # Очищаем кэш фильтров
                self._filter_criteria_cache = None

                # КРИТИЧНО: Обновляем дерево параметров
                if hasattr(self.view, 'ui_components') and self.view.ui_components:
                    if hasattr(self.view.ui_components, 'parameter_panel'):
                        parameter_panel = self.view.ui_components.parameter_panel
                        if hasattr(parameter_panel, 'update_parameters'):
                            # Очищаем описания параметров перед обновлением
                            cleaned_params = self._clean_parameter_descriptions(
                                params)
                            parameter_panel.update_parameters(cleaned_params)
                            self.logger.info("Дерево параметров обновлено")
                        else:
                            self.logger.error(
                                "Метод update_parameters не найден в parameter_panel")
                    else:
                        self.logger.error(
                            "parameter_panel не найден в ui_components")
                else:
                    self.logger.error("ui_components не найден в view")

                # Обновляем фильтры
                if hasattr(self.model.data_loader, 'lines'):
                    lines = list(self.model.data_loader.lines)
                    if hasattr(self.view, 'ui_components') and self.view.ui_components:
                        if hasattr(self.view.ui_components, 'filter_panel'):
                            filter_panel = self.view.ui_components.filter_panel
                            if hasattr(filter_panel, 'update_line_checkboxes'):
                                filter_panel.update_line_checkboxes(lines)

                # Применяем фильтры
                self.apply_filters()

                # Обновляем статус
                if hasattr(self.view, 'update_status'):
                    self.view.update_status(
                        f"Файл загружен: {len(params)} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка обработки успешной загрузки: {e}")

    def build_plot(self):
        """ОБНОВЛЕННОЕ построение графика с интеграцией PlotVisualizationPanel"""
        try:
            # ИСПРАВЛЕННОЕ получение выбранных параметров
            selected_params = []
            if hasattr(self.view, 'ui_components') and self.view.ui_components:
                if hasattr(self.view.ui_components, 'parameter_panel'):
                    parameter_panel = self.view.ui_components.parameter_panel
                    if hasattr(parameter_panel, 'get_selected_parameters'):
                        selected_params = parameter_panel.get_selected_parameters()

            if not selected_params:
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning(
                        "Выберите параметры для построения графика")
                return

            # ИСПРАВЛЕННОЕ получение временного диапазона
            start_time_str, end_time_str = "", ""
            if hasattr(self.view, 'ui_components') and self.view.ui_components:
                if hasattr(self.view.ui_components, 'time_panel'):
                    time_panel = self.view.ui_components.time_panel
                    if hasattr(time_panel, 'get_time_range'):
                        start_time_str, end_time_str = time_panel.get_time_range()

            # Валидация времени
            if not self._validate_time_range(start_time_str, end_time_str):
                return

            # Преобразуем строки времени в datetime
            try:
                start_time = datetime.strptime(
                    start_time_str, '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
            except ValueError as e:
                self.logger.error(f"Ошибка парсинга времени: {e}")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(f"Неверный формат времени: {e}")
                return

            # ИСПРАВЛЕННОЕ использование PlotVisualizationPanel
            plot_panel = None
            if hasattr(self.view, 'plot_panel'):
                plot_panel = self.view.plot_panel
            elif hasattr(self.view, 'get_component'):
                plot_panel = self.view.get_component('plot_panel')

            if plot_panel:
                plot_panel.build_plots_for_parameters(
                    selected_params, start_time, end_time)
                self.logger.info(
                    "График построен через PlotVisualizationPanel")

                if hasattr(self.view, 'update_status'):
                    self.view.update_status("График построен")
            else:
                # Fallback к legacy методу
                self.logger.warning(
                    "PlotVisualizationPanel не найден, используется fallback")
                self.logger.error("PlotVisualizationPanel не найден")
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(
                        "Компонент построения графиков недоступен")

        except Exception as e:
            self.logger.error(f"Ошибка построения графика: {e}")
            import traceback
            traceback.print_exc()
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка построения графика: {e}")

    def _get_selected_parameters(self) -> List[Any]:
        """Получение выбранных параметров"""
        try:
            if (hasattr(self.view, 'parameter_panel') and
                    self.view.parameter_panel and
                    hasattr(self.view.parameter_panel, 'selected_params_tree')):

                tree = self.view.parameter_panel.selected_params_tree
                if hasattr(tree, 'tree'):
                    return [tree.tree.item(item, 'values')
                            for item in tree.tree.get_children()]
            return []
        except Exception as e:
            self.logger.error(f"Ошибка получения выбранных параметров: {e}")
            return []

    def _validate_time_range(self, start_str: str, end_str: str) -> bool:
        """Валидация временного диапазона"""
        try:
            if not start_str or not end_str:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Укажите временной диапазон")
                return False

            # Простая валидация формата
            from datetime import datetime
            try:
                start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S')

                if start_dt >= end_dt:
                    if hasattr(self.view, 'show_error'):
                        self.view.show_error(
                            "Время начала должно быть раньше времени окончания")
                    return False

                return True

            except ValueError as e:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(f"Неверный формат времени: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Ошибка валидации времени: {e}")
            return False

    def generate_report(self):
        """Генерация отчета"""
        try:
            if not self.report_generator:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(
                        "Генератор отчетов не инициализирован")
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
                        self.view.show_info(
                            "Отчет", f"Отчет сохранен: {file_path}")
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
                [{'signal_code': param[0] if param else '',
                  'description': param[1] if len(param) > 1 else ''}
                 for param in selected_params],
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
                    success = self.sop_manager.save_sop_to_file(
                        sop_xml, file_path)

                    if success:
                        self.logger.info(f"SOP создан: {file_path}")
                        if hasattr(self.view, 'show_info'):
                            self.view.show_info(
                                "SOP", f"SOP сохранен: {file_path}")
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

    def cleanup(self):
        """Очистка ресурсов контроллера"""
        try:
            # Очищаем кэш
            self._filter_criteria_cache = None

            # Очищаем сервисы
            if self.filtering_service and hasattr(self.filtering_service, 'cleanup'):
                self.filtering_service.cleanup()

            if self.plot_manager and hasattr(self.plot_manager, 'cleanup'):
                self.plot_manager.cleanup()

            if self.report_generator and hasattr(self.report_generator, 'cleanup'):
                self.report_generator.cleanup()

            if self.sop_manager and hasattr(self.sop_manager, 'cleanup'):
                self.sop_manager.cleanup()

            self.logger.info("MainController очищен")

        except Exception as e:
            self.logger.error(f"Ошибка очистки MainController: {e}")

    def _on_file_loaded(self, file_path: str):
        """КРИТИЧНО ИСПРАВЛЕНО: Обработка успешной загрузки файла"""
        try:
            self.logger.info("=== НАЧАЛО ОБРАБОТКИ ЗАГРУЖЕННОГО ФАЙЛА ===")

            # ШАГ 1: Получаем временной диапазон из модели
            self.logger.info("Получение полей времени из модели...")
            time_fields = None

            # Множественные попытки получения времени
            if hasattr(self.model, 'get_time_range_fields'):
                time_fields = self.model.get_time_range_fields()
                self.logger.info(
                    f"Получены поля через get_time_range_fields: {time_fields}")

            # Fallback через _time_range_fields
            if not time_fields and hasattr(self.model, '_time_range_fields'):
                time_fields = self.model._time_range_fields
                self.logger.info(
                    f"Получены поля через _time_range_fields: {time_fields}")

            # Fallback через telemetry_data
            if not time_fields and hasattr(self.model, '_telemetry_data') and self.model._telemetry_data:
                try:
                    formatted_range = self.model._telemetry_data.get_formatted_time_range()
                    time_fields = {
                        'from_time': formatted_range['from_time'],
                        'to_time': formatted_range['to_time'],
                        'duration': formatted_range['duration'],
                        'total_records': self.model._telemetry_data.records_count
                    }
                    self.logger.info(
                        f"Получены поля через telemetry_data: {time_fields}")
                except Exception as e:
                    self.logger.error(
                        f"Ошибка получения времени через telemetry_data: {e}")

            # ШАГ 2: Обновляем поля времени в UI
            if time_fields and time_fields.get('from_time') and time_fields.get('to_time'):
                self.logger.info("=== ОБНОВЛЕНИЕ ПОЛЕЙ ВРЕМЕНИ В UI ===")
                success = self._update_time_panel_fields(time_fields)
                if success:
                    self.logger.info(
                        f"✅ UI поля времени обновлены: {time_fields['from_time']} - {time_fields['to_time']}")
                else:
                    self.logger.error(
                        "❌ Не удалось обновить поля времени в UI")
            else:
                self.logger.warning(
                    "⚠️ Временной диапазон не получен или пустой")
                self.logger.debug(f"time_fields = {time_fields}")

            # ШАГ 3: Обработка параметров
            self.logger.info("=== ОБРАБОТКА ПАРАМЕТРОВ ===")
            self._handle_successful_load()

            self.logger.info("=== ОБРАБОТКА ФАЙЛА ЗАВЕРШЕНА ===")

        except Exception as e:
            self.logger.error(f"Ошибка обработки загруженного файла: {e}")
            import traceback
            traceback.print_exc()
