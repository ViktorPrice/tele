# data_model.py
"""
Модель данных приложения с поддержкой timestamp функциональности и временных диапазонов (ИСПРАВЛЕННАЯ)
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..domain.entities.telemetry_data import TelemetryData
from ..domain.entities.parameter import Parameter
from ..domain.services.time_range_service import TimeRangeService
from ...infrastructure.data.csv_loader import CSVDataLoader


class TimestampParameterService:
    """Сервис для работы с timestamp параметрами"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_timestamp_parameters(self, parameters: List[Parameter]) -> Dict[str, List[Parameter]]:
        """Извлечение timestamp параметров по вагонам"""
        timestamp_params = {}

        for param in parameters:
            if param.is_timestamp_parameter():
                wagon = param.wagon or '1'

                if wagon not in timestamp_params:
                    timestamp_params[wagon] = []

                timestamp_params[wagon].append(param)

        # Сортируем по компонентам времени
        for wagon in timestamp_params:
            timestamp_params[wagon] = self._sort_timestamp_components(
                timestamp_params[wagon])

        self.logger.info(
            f"Найдены timestamp параметры для {len(timestamp_params)} вагонов")
        return timestamp_params

    def _sort_timestamp_components(self, params: List[Parameter]) -> List[Parameter]:
        """Сортировка timestamp компонентов в правильном порядке"""
        component_order = ['year', 'month', 'day',
                           'hour', 'minute', 'second', 'smallsecond']

        sorted_params = []
        for component in component_order:
            for param in params:
                if param.get_timestamp_component() == component:
                    sorted_params.append(param)
                    break

        return sorted_params

    def validate_timestamp_completeness(self, timestamp_params: Dict[str, List[Parameter]]) -> Dict[str, Any]:
        """Валидация полноты timestamp параметров"""
        required_components = {'year', 'month', 'day',
                               'hour', 'minute', 'second', 'smallsecond'}
        validation_result = {}

        for wagon, params in timestamp_params.items():
            found_components = {param.get_timestamp_component()
                                for param in params}
            missing_components = required_components - found_components

            validation_result[wagon] = {
                'is_complete': len(missing_components) == 0,
                'found_components': list(found_components),
                'missing_components': list(missing_components),
                'parameter_count': len(params)
            }

        return validation_result

    def get_best_timestamp_wagon(self, timestamp_params: Dict[str, List[Parameter]]) -> Optional[str]:
        """Определение лучшего вагона для timestamp"""
        validation = self.validate_timestamp_completeness(timestamp_params)

        # Ищем полный набор компонентов
        for wagon, info in validation.items():
            if info['is_complete']:
                self.logger.info(
                    f"Выбран вагон {wagon} для timestamp (полный набор компонентов)")
                return wagon

        # Если полного набора нет, выбираем с максимальным количеством компонентов
        best_wagon = max(validation.keys(),
                         key=lambda w: validation[w]['parameter_count'],
                         default=None)

        if best_wagon:
            self.logger.warning(
                f"Выбран вагон {best_wagon} для timestamp (неполный набор)")

        return best_wagon

    def create_timestamp_column_mapping(self, parameters: List[Parameter], wagon: str) -> Optional[Dict[str, str]]:
        """Создание маппинга timestamp столбцов"""
        timestamp_params = [p for p in parameters
                            if p.is_timestamp_parameter() and p.wagon == wagon]

        if not timestamp_params:
            return None

        column_mapping = {}
        for param in timestamp_params:
            component = param.get_timestamp_component()
            if component:
                column_mapping[component] = param.full_column

        return column_mapping

    def integrate_with_telemetry_data(self, telemetry_data: TelemetryData,
                                      parameters: List[Parameter]) -> bool:
        """Интеграция timestamp параметров с TelemetryData"""
        try:
            # Извлекаем timestamp параметры
            timestamp_params = self.extract_timestamp_parameters(parameters)

            if not timestamp_params:
                self.logger.warning("Timestamp параметры не найдены")
                return False

            # Выбираем лучший вагон
            best_wagon = self.get_best_timestamp_wagon(timestamp_params)

            if not best_wagon:
                self.logger.error("Не удалось выбрать вагон для timestamp")
                return False

            # Создаем маппинг столбцов
            column_mapping = self.create_timestamp_column_mapping(
                parameters, best_wagon)

            if not column_mapping:
                self.logger.error(
                    "Не удалось создать маппинг timestamp столбцов")
                return False

            # Устанавливаем данные в TelemetryData
            telemetry_data.timestamp_columns = column_mapping
            telemetry_data.timestamp_wagon = best_wagon

            # Создаем timestamp столбец если его нет
            if 'timestamp' not in telemetry_data.data.columns:
                telemetry_data._parse_timestamp_from_components(column_mapping)

            self.logger.info(
                f"Успешная интеграция timestamp для вагона {best_wagon}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка интеграции timestamp: {e}")
            return False


class DataModel:
    """Модель данных для новой архитектуры (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""

    def __init__(self):
        self.data_loader = CSVDataLoader()
        self.timestamp_service = TimestampParameterService()
        self.time_range_service = TimeRangeService()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Кэшированные данные для производительности
        self._cached_parameters: Optional[List[Parameter]] = None
        self._cached_parameter_dicts: Optional[List[Dict[str, Any]]] = None
        self._cached_lines: Optional[set] = None
        self._last_file_path: Optional[str] = None
        self._telemetry_data: Optional[TelemetryData] = None

        # Новые поля для временных диапазонов
        self._time_range_fields: Optional[Dict[str, str]] = None
        self._analysis_cache: Dict[str, Any] = {}

        self.logger.info(
            "DataModel (новая архитектура с timestamp и временными диапазонами) инициализирована")

    def load_csv_file(self, file_path: str) -> bool:
        """Загрузка CSV через новую архитектуру с кэшированием"""
        try:
            # Проверяем кэш
            if self._last_file_path == file_path and self._cached_parameters:
                self.logger.info(
                    f"Использование кэшированных данных для {file_path}")
                return True

            # Очищаем предыдущие данные
            self.clear_cache()

            # Загружаем новые данные
            telemetry_data = self.data_loader.load_csv(file_path)
            self._telemetry_data = telemetry_data

            # Обрабатываем данные
            self._process_telemetry_data(telemetry_data)

            # Обновляем кэш
            self._last_file_path = file_path

            self.logger.info(f"Успешно загружен файл: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка загрузки {file_path}: {e}")
            return False

    def _process_telemetry_data(self, telemetry_data: TelemetryData):
        """ИСПРАВЛЕННАЯ обработка данных телеметрии"""
        try:
            data = telemetry_data.data

            # Параллельная обработка столбцов
            parameters = []
            lines = set()

            exclude_columns = {'timestamp', 'TIMESTAMP', 'index'}

            self.logger.info(f"Обработка {len(data.columns)} столбцов...")

            for column in data.columns:
                if column not in exclude_columns:
                    try:
                        # Создаем Parameter объект
                        if '::' in column:
                            parameter = Parameter.from_header(column)
                        else:
                            parameter = Parameter._create_from_simple_header(
                                column)

                        parameters.append(parameter)
                        lines.add(parameter.line)

                    except Exception as e:
                        self.logger.error(
                            f"Ошибка обработки столбца {column}: {e}")
                        continue

            # Интеграция timestamp функциональности
            timestamp_integrated = self.timestamp_service.integrate_with_telemetry_data(
                telemetry_data, parameters
            )

            if timestamp_integrated:
                self.logger.info(
                    "Timestamp функциональность успешно интегрирована")

                # Валидация timestamp данных
                validation_result = telemetry_data.validate_timestamp_integrity()
                if not validation_result['is_valid']:
                    self.logger.warning(
                        f"Проблемы с timestamp: {validation_result['issues']}")

                # Попытка восстановления пропусков
                if validation_result.get('warnings'):
                    self.logger.info(
                        "Попытка восстановления timestamp данных...")
                    telemetry_data.repair_timestamp_gaps(method='interpolate')

            # НОВОЕ: Инициализация полей "от/до"
            self._time_range_fields = self.time_range_service.initialize_from_telemetry_data(
                telemetry_data)

            # ДИАГНОСТИКА: Проверяем что получили
            if self._time_range_fields:
                self.logger.info(
                    f"Поля времени инициализированы: {self._time_range_fields['from_time']} - {self._time_range_fields['to_time']}")
            else:
                self.logger.error("Не удалось инициализировать поля времени")

            # Кэшируем результаты
            self._cached_parameters = parameters
            self._cached_parameter_dicts = [p.to_dict() for p in parameters]
            self._cached_lines = lines

            # ИСПРАВЛЕНИЕ: Устанавливаем для совместимости с legacy кодом
            # НЕ исключаем проблемные параметры из общего списка
            self.data_loader.parameters = self._cached_parameter_dicts
            self.data_loader.lines = list(lines)
            self.data_loader.start_time = telemetry_data.timestamp_range[0]
            self.data_loader.end_time = telemetry_data.timestamp_range[1]

            # Подсчитываем статистику
            problematic_count = sum(1 for p in parameters if p.is_problematic)
            normal_count = len(parameters) - problematic_count

            self.logger.info(
                f"Обработано {len(parameters)} параметров ({normal_count} нормальных, {problematic_count} проблемных), {len(lines)} линий")

        except Exception as e:
            self.logger.error(f"Ошибка обработки данных телеметрии: {e}")
            raise

    def get_time_range_fields(self) -> Optional[Dict[str, Any]]:
        """ИСПРАВЛЕННОЕ получение полей времени"""
        try:
            # Способ 1: Через time_range_service.get_current_range()
            if hasattr(self, 'time_range_service') and self.time_range_service:
                if hasattr(self.time_range_service, 'get_current_range'):
                    time_range = self.time_range_service.get_current_range()
                    if time_range and len(time_range) >= 2:
                        from_time = time_range[0]
                        to_time = time_range[1]
                        
                        # Форматируем в строки если нужно
                        if isinstance(from_time, datetime):
                            from_time_str = from_time.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            from_time_str = str(from_time)
                        
                        if isinstance(to_time, datetime):
                            to_time_str = to_time.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            to_time_str = str(to_time)
                        
                        return {
                            'from_time': from_time_str,
                            'to_time': to_time_str,
                            'duration': self._calculate_duration(from_time_str, to_time_str),
                            'total_records': getattr(self.time_range_service, 'total_records', 3001)
                        }

            # Fallback 1: Через _telemetry_data.timestamp_range
            if hasattr(self, '_telemetry_data') and self._telemetry_data:
                if hasattr(self._telemetry_data, 'timestamp_range'):
                    timestamp_range = self._telemetry_data.timestamp_range
                    if timestamp_range and len(timestamp_range) >= 2:
                        from_time = timestamp_range[0].strftime('%Y-%m-%d %H:%M:%S')
                        to_time = timestamp_range[1].strftime('%Y-%m-%d %H:%M:%S')
                        
                        return {
                            'from_time': from_time,
                            'to_time': to_time,
                            'duration': self._calculate_duration(from_time, to_time),
                            'total_records': getattr(self._telemetry_data, 'records_count', 3001)
                        }

            # Fallback 2: Через data_loader
            if hasattr(self, 'data_loader') and self.data_loader:
                if (hasattr(self.data_loader, 'min_timestamp') and 
                    hasattr(self.data_loader, 'max_timestamp')):
                    
                    min_time = self.data_loader.min_timestamp
                    max_time = self.data_loader.max_timestamp
                    
                    if min_time and max_time:
                        return {
                            'from_time': str(min_time),
                            'to_time': str(max_time),
                            'duration': self._calculate_duration(str(min_time), str(max_time)),
                            'total_records': getattr(self.data_loader, 'records_count', 3001)
                        }

            self.logger.warning("Не удалось получить поля времени из всех источников")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения полей времени: {e}")
            return None

    def _calculate_duration(self, from_time_str: str, to_time_str: str) -> str:
        """Вычисление длительности"""
        try:
            from datetime import datetime
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

    def set_user_time_range(self, from_time: str, to_time: str) -> bool:
        """Установка пользовательского временного диапазона"""
        try:
            success = self.time_range_service.set_user_time_range(
                from_time, to_time)

            if success:
                # Обновляем поля для UI
                self._time_range_fields.update({
                    'from_time': from_time,
                    'to_time': to_time
                })

                # Очищаем кэш анализа
                self._analysis_cache.clear()

                self.logger.info(
                    f"Установлен пользовательский диапазон: {from_time} - {to_time}")

            return success

        except Exception as e:
            self.logger.error(
                f"Ошибка установки пользовательского диапазона: {e}")
            return False

    def find_changed_parameters_in_range(self, threshold: float = 0.1) -> List[Parameter]:
        """ИСПРАВЛЕННЫЙ поиск изменяемых параметров в текущем диапазоне"""
        try:
            if not self._telemetry_data or not self._cached_parameters:
                self.logger.warning("Данные не загружены")
                return []

            # Проверяем кэш
            cache_key = f"changed_params_{threshold}_{self.time_range_service.get_current_range()}"
            if cache_key in self._analysis_cache:
                self.logger.debug(
                    "Использование кэшированных результатов анализа")
                return self._analysis_cache[cache_key]

            # Выполняем анализ
            changed_params = self.time_range_service.find_changed_parameters_in_range(
                self._telemetry_data,
                self._cached_parameters,
                threshold
            )

            # Кэшируем результат
            self._analysis_cache[cache_key] = changed_params

            return changed_params

        except Exception as e:
            self.logger.error(f"Ошибка поиска изменяемых параметров: {e}")
            return []

    def get_filterable_parameters(self) -> List[Parameter]:
        """НОВЫЙ МЕТОД: Получение параметров для фильтрации (включая проблемные)"""
        if not self._cached_parameters:
            return []

        # Возвращаем ВСЕ параметры для фильтрации
        # Фильтрация сама решит что показывать
        return self._cached_parameters

    def get_normal_parameters(self) -> List[Parameter]:
        """Получение только нормальных параметров"""
        if not self._cached_parameters:
            return []

        return [p for p in self._cached_parameters if not p.is_problematic]

    def get_problematic_parameters(self) -> List[Parameter]:
        """Получение только проблемных параметров"""
        if not self._cached_parameters:
            return []

        return [p for p in self._cached_parameters if p.is_problematic]

    def reset_time_range_to_full(self):
        """Сброс временного диапазона к полному"""
        try:
            self.time_range_service.reset_to_data_range()

            if self._telemetry_data:
                self._time_range_fields = self.time_range_service.initialize_from_telemetry_data(
                    self._telemetry_data)
                self.logger.info("Временной диапазон сброшен к полному")

            # Очищаем кэш анализа
            self._analysis_cache.clear()

        except Exception as e:
            self.logger.error(f"Ошибка сброса временного диапазона: {e}")

    def get_time_range_statistics(self) -> Dict[str, Any]:
        """Получение статистики временного диапазона"""
        try:
            stats = self.time_range_service.get_range_statistics()

            # Добавляем дополнительную информацию
            if self._telemetry_data:
                current_range = self.time_range_service.get_current_range()
                if current_range:
                    filtered_data = self._telemetry_data.filter_by_time(
                        *current_range)
                    stats['filtered_records'] = filtered_data.records_count
                    stats['total_records'] = self._telemetry_data.records_count
                    stats['records_ratio'] = (
                        filtered_data.records_count / self._telemetry_data.records_count * 100) if self._telemetry_data.records_count > 0 else 0

            return stats

        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {}

    def analyze_parameter_changes_detailed(self, threshold: float = 0.1) -> Dict[str, Any]:
        """Детальный анализ изменений параметров"""
        try:
            if not self._telemetry_data or not self._cached_parameters:
                return {}

            current_range = self.time_range_service.get_current_range()
            if not current_range:
                return {}

            # Фильтруем данные по времени
            filtered_data = self._telemetry_data.filter_by_time(*current_range)

            analysis_result = {
                'total_parameters': len(self._cached_parameters),
                'changed_parameters': [],
                'unchanged_parameters': [],
                'analysis_threshold': threshold,
                'time_range': {
                    'start': current_range[0].strftime('%Y-%m-%d %H:%M:%S'),
                    'end': current_range[1].strftime('%Y-%m-%d %H:%M:%S')
                },
                'statistics': {}
            }

            for param in self._cached_parameters:
                if param.full_column in filtered_data.data.columns:
                    series = filtered_data.data[param.full_column]
                    is_changed = self.time_range_service._is_parameter_changed(
                        series, threshold)

                    param_info = {
                        'parameter': param.to_dict(),
                        'change_statistics': self._calculate_parameter_statistics(series)
                    }

                    if is_changed:
                        analysis_result['changed_parameters'].append(
                            param_info)
                    else:
                        analysis_result['unchanged_parameters'].append(
                            param_info)

            # Общая статистика
            analysis_result['statistics'] = {
                'changed_count': len(analysis_result['changed_parameters']),
                'unchanged_count': len(analysis_result['unchanged_parameters']),
                'change_ratio': len(analysis_result['changed_parameters']) / len(self._cached_parameters) * 100 if self._cached_parameters else 0
            }

            return analysis_result

        except Exception as e:
            self.logger.error(f"Ошибка детального анализа: {e}")
            return {}

    def _calculate_parameter_statistics(self, series) -> Dict[str, Any]:
        """Расчет статистики для параметра"""
        try:
            clean_series = series.dropna()

            if len(clean_series) == 0:
                return {'error': 'no_data'}

            stats = {
                'total_values': len(series),
                'valid_values': len(clean_series),
                'null_values': len(series) - len(clean_series),
                'unique_values': len(clean_series.unique()),
                'unique_ratio': len(clean_series.unique()) / len(clean_series) if len(clean_series) > 0 else 0
            }

            # Для числовых данных добавляем статистику
            if clean_series.dtype.kind in 'biufc':  # числовые типы
                stats.update({
                    'min_value': float(clean_series.min()),
                    'max_value': float(clean_series.max()),
                    'mean_value': float(clean_series.mean()),
                    'std_value': float(clean_series.std()),
                    'variance': float(clean_series.var())
                })

            return stats

        except Exception as e:
            return {'error': str(e)}

    # Существующие методы для совместимости
    def get_parameters(self) -> List[Dict[str, Any]]:
        """Получение параметров из кэша (legacy формат)"""
        return self._cached_parameter_dicts or []

    def get_parameter_objects(self) -> List[Parameter]:
        """Получение Parameter объектов"""
        return self._cached_parameters or []

    def get_lines(self) -> List[str]:
        """Получение линий из кэша"""
        return list(self._cached_lines) if self._cached_lines else []

    def get_telemetry_data(self) -> Optional[TelemetryData]:
        """Получение объекта TelemetryData"""
        return self._telemetry_data

    def get_timestamp_statistics(self) -> Dict[str, Any]:
        """Получение статистики timestamp"""
        if self._telemetry_data:
            return self._telemetry_data.get_timestamp_statistics()
        return {}

    def get_timestamp_parameters(self) -> Dict[str, List[Parameter]]:
        """Получение timestamp параметров по вагонам"""
        if self._cached_parameters:
            return self.timestamp_service.extract_timestamp_parameters(self._cached_parameters)
        return {}

    def validate_timestamp_data(self) -> Dict[str, Any]:
        """Валидация timestamp данных"""
        if self._telemetry_data:
            return self._telemetry_data.validate_timestamp_integrity()
        return {'is_valid': False, 'issues': ['Данные не загружены']}

    def repair_timestamp_data(self, method: str = 'interpolate') -> bool:
        """Восстановление timestamp данных"""
        if self._telemetry_data:
            success = self._telemetry_data.repair_timestamp_gaps(method)
            if success:
                # Обновляем поля времени после восстановления
                self._time_range_fields = self.time_range_service.initialize_from_telemetry_data(
                    self._telemetry_data)
            return success
        return False

    def filter_data_by_time(self, start_time: datetime, end_time: datetime) -> Optional[TelemetryData]:
        """Фильтрация данных по времени"""
        if self._telemetry_data:
            return self._telemetry_data.filter_by_time(start_time, end_time)
        return None

    def clear_cache(self):
        """Очистка кэша"""
        self._cached_parameters = None
        self._cached_parameter_dicts = None
        self._cached_lines = None
        self._last_file_path = None
        self._telemetry_data = None
        self._time_range_fields = None
        self._analysis_cache.clear()
        self.logger.info("Кэш данных очищен")

    def get_model_statistics(self) -> Dict[str, Any]:
        """Получение общей статистики модели"""
        stats = {
            'loaded_file': self._last_file_path,
            'parameters_count': len(self._cached_parameters) if self._cached_parameters else 0,
            'lines_count': len(self._cached_lines) if self._cached_lines else 0,
            'has_telemetry_data': self._telemetry_data is not None,
            'cache_status': {
                'parameters_cached': self._cached_parameters is not None,
                'lines_cached': self._cached_lines is not None,
                'analysis_cache_size': len(self._analysis_cache)
            },
            'time_range_fields': self._time_range_fields
        }

        # Добавляем статистику по типам параметров
        if self._cached_parameters:
            normal_count = sum(
                1 for p in self._cached_parameters if not p.is_problematic)
            problematic_count = len(self._cached_parameters) - normal_count

            stats['parameter_types'] = {
                'normal_parameters': normal_count,
                'problematic_parameters': problematic_count,
                'total_parameters': len(self._cached_parameters)
            }

        # Добавляем timestamp статистику
        if self._telemetry_data:
            stats['timestamp_stats'] = self.get_timestamp_statistics()
            stats['timestamp_validation'] = self.validate_timestamp_data()
            stats['time_range_stats'] = self.get_time_range_statistics()

        return stats
