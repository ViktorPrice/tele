# src/core/models/data_model.py - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Модель данных приложения с поддержкой приоритетной логики изменяемых параметров
"""
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import time

# Импорты доменных сущностей
try:
    from ..domain.entities.telemetry_data import TelemetryData
    from ..domain.entities.parameter import Parameter
    from ..domain.services.time_range_service import TimeRangeService
except ImportError as e:
    logging.warning(f"Доменные сущности недоступны: {e}")
    TelemetryData = None
    Parameter = None
    TimeRangeService = None

# Импорты инфраструктуры
try:
    from ...infrastructure.data.csv_loader import CSVDataLoader
except ImportError as e:
    logging.warning(f"CSV Loader недоступен: {e}")
    CSVDataLoader = None

# Импорты Use Cases для интеграции
try:
    from ..application.use_cases.filter_parameters_use_case import (
        FindChangedParametersRequest, FindChangedParametersResponse,
        TimeRangeInitRequest, TimeRangeInitResponse
    )
    USE_CASES_AVAILABLE = True
except ImportError:
    USE_CASES_AVAILABLE = False


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

        self.logger.info(f"Найдены timestamp параметры для {len(timestamp_params)} вагонов")
        return timestamp_params

    def _sort_timestamp_components(self, params: List[Parameter]) -> List[Parameter]:
        """Сортировка timestamp компонентов в правильном порядке"""
        component_order = ['year', 'month', 'day', 'hour', 'minute', 'second', 'smallsecond']

        sorted_params = []
        for component in component_order:
            for param in params:
                if param.get_timestamp_component() == component:
                    sorted_params.append(param)
                    break

        return sorted_params

    def validate_timestamp_completeness(self, timestamp_params: Dict[str, List[Parameter]]) -> Dict[str, Any]:
        """Валидация полноты timestamp параметров"""
        required_components = {'year', 'month', 'day', 'hour', 'minute', 'second', 'smallsecond'}
        validation_result = {}

        for wagon, params in timestamp_params.items():
            found_components = {param.get_timestamp_component() for param in params}
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
                self.logger.info(f"Выбран вагон {wagon} для timestamp (полный набор компонентов)")
                return wagon

        # Если полного набора нет, выбираем с максимальным количеством компонентов
        best_wagon = max(validation.keys(),
                         key=lambda w: validation[w]['parameter_count'],
                         default=None)

        if best_wagon:
            self.logger.warning(f"Выбран вагон {best_wagon} для timestamp (неполный набор)")

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
            column_mapping = self.create_timestamp_column_mapping(parameters, best_wagon)

            if not column_mapping:
                self.logger.error("Не удалось создать маппинг timestamp столбцов")
                return False

            # Устанавливаем данные в TelemetryData
            telemetry_data.timestamp_columns = column_mapping
            telemetry_data.timestamp_wagon = best_wagon

            # Создаем timestamp столбец если его нет
            if 'timestamp' not in telemetry_data.data.columns:
                telemetry_data._parse_timestamp_from_components(column_mapping)

            self.logger.info(f"Успешная интеграция timestamp для вагона {best_wagon}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка интеграции timestamp: {e}")
            return False

class DataModel:
    """ИСПРАВЛЕННАЯ модель данных с приоритетной логикой изменяемых параметров"""

    def __init__(self):
        # Основные сервисы
        self.data_loader = CSVDataLoader() if CSVDataLoader else None
        self.timestamp_service = TimestampParameterService()
        self.time_range_service = TimeRangeService() if TimeRangeService else None
        self.logger = logging.getLogger(self.__class__.__name__)

        # Кэшированные данные для производительности
        self._cached_parameters: Optional[List[Parameter]] = None
        self._cached_parameter_dicts: Optional[List[Dict[str, Any]]] = None
        self._cached_lines: Optional[set] = None
        self._last_file_path: Optional[str] = None
        self._telemetry_data: Optional[TelemetryData] = None

        # ПРИОРИТЕТНЫЕ поля для изменяемых параметров
        self._time_range_fields: Optional[Dict[str, str]] = None
        self._changed_params_cache: Dict[str, List[Parameter]] = {}
        self._analysis_cache: Dict[str, Any] = {}
        self._priority_mode_active = False

        # Статистика и метрики
        self._load_statistics: Dict[str, Any] = {}
        self._performance_metrics: Dict[str, float] = {}

        # Интеграция с Use Cases
        self._use_case_integration = USE_CASES_AVAILABLE

        self.logger.info("DataModel инициализирована с приоритетной логикой изменяемых параметров")

    def load_csv_file(self, file_path: str) -> bool:
        """ПРИОРИТЕТНАЯ загрузка CSV с поддержкой изменяемых параметров"""
        start_time = time.time()
        
        try:
            self.logger.info(f"🔥 ПРИОРИТЕТНАЯ загрузка файла: {file_path}")

            # Проверяем кэш
            if self._last_file_path == file_path and self._cached_parameters:
                self.logger.info(f"Использование кэшированных данных для {file_path}")
                return True

            # Очищаем предыдущие данные
            self.clear_cache()

            # Загружаем новые данные
            if not self.data_loader:
                self.logger.error("CSVDataLoader недоступен")
                return False

            telemetry_data = self.data_loader.load_csv(file_path)
            if not telemetry_data:
                self.logger.error("Не удалось загрузить данные телеметрии")
                return False

            self._telemetry_data = telemetry_data

            # Обрабатываем данные с приоритетом
            success = self._process_telemetry_data_priority(telemetry_data)

            # Логируем временные диапазоны для отладки
            if self._time_range_fields:
                self.logger.info(f"Временные поля после инициализации: {self._time_range_fields}")
            else:
                self.logger.warning("Временные поля после инициализации отсутствуют")

            if telemetry_data and hasattr(telemetry_data, 'timestamp_range'):
                self.logger.info(f"TelemetryData.timestamp_range: {telemetry_data.timestamp_range}")
            else:
                self.logger.warning("TelemetryData.timestamp_range отсутствует")

            if success:
                # Обновляем кэш
                self._last_file_path = file_path
                
                # Собираем статистику загрузки
                load_time = time.time() - start_time
                self._collect_load_statistics(file_path, load_time)
                
                self.logger.info(f"✅ ПРИОРИТЕТНАЯ загрузка завершена за {load_time:.2f}с")
                return True
            else:
                self.logger.error("Ошибка обработки данных телеметрии")
                return False

        except Exception as e:
            load_time = time.time() - start_time
            self.logger.error(f"Ошибка приоритетной загрузки {file_path}: {e} (время: {load_time:.2f}с)")
            return False

    def _process_telemetry_data_priority(self, telemetry_data: TelemetryData) -> bool:
        """ПРИОРИТЕТНАЯ обработка данных телеметрии"""
        try:
            self.logger.info("🔥 Начало приоритетной обработки данных")
            
            data = telemetry_data.data
            parameters = []
            lines = set()
            exclude_columns = {'timestamp', 'TIMESTAMP', 'index'}

            self.logger.info(f"Обработка {len(data.columns)} столбцов...")

            # Параллельная обработка столбцов
            for column in data.columns:
                if column not in exclude_columns:
                    try:
                        # Создаем Parameter объект
                        if '::' in column:
                            parameter = Parameter.from_header(column)
                        else:
                            parameter = Parameter._create_from_simple_header(column)

                        parameters.append(parameter)
                        lines.add(parameter.line)

                    except Exception as e:
                        self.logger.error(f"Ошибка обработки столбца {column}: {e}")
                        continue

            # ПРИОРИТЕТНАЯ интеграция timestamp функциональности
            timestamp_integrated = self.timestamp_service.integrate_with_telemetry_data(
                telemetry_data, parameters
            )

            if timestamp_integrated:
                self.logger.info("✅ Timestamp функциональность интегрирована")
                
                # Валидация timestamp данных
                validation_result = telemetry_data.validate_timestamp_integrity()
                if not validation_result['is_valid']:
                    self.logger.warning(f"Проблемы с timestamp: {validation_result['issues']}")
                    
                    # Попытка восстановления
                    if validation_result.get('warnings'):
                        self.logger.info("Попытка восстановления timestamp данных...")
                        telemetry_data.repair_timestamp_gaps(method='interpolate')

            # ПРИОРИТЕТНАЯ инициализация полей времени
            if self.time_range_service:
                self._time_range_fields = self.time_range_service.initialize_from_telemetry_data(
                    telemetry_data)
                
                if self._time_range_fields:
                    self.logger.info(f"✅ Поля времени инициализированы: {self._time_range_fields['from_time']} - {self._time_range_fields['to_time']}")
                else:
                    self.logger.warning("⚠️ Не удалось инициализировать поля времени")

            # Кэшируем результаты
            self._cached_parameters = parameters
            self._cached_parameter_dicts = [p.to_dict() for p in parameters]
            self._cached_lines = lines

            # ИСПРАВЛЕНИЕ: Устанавливаем для совместимости с legacy кодом
            if self.data_loader:
                self.data_loader.parameters = self._cached_parameter_dicts
                self.data_loader.lines = list(lines)
                
                # Устанавливаем временные метки
                if hasattr(telemetry_data, 'timestamp_range') and telemetry_data.timestamp_range:
                    self.data_loader.min_timestamp = telemetry_data.timestamp_range[0].strftime('%Y-%m-%d %H:%M:%S')
                    self.data_loader.max_timestamp = telemetry_data.timestamp_range[1].strftime('%Y-%m-%d %H:%M:%S')
                    self.data_loader.start_time = telemetry_data.timestamp_range[0]
                    self.data_loader.end_time = telemetry_data.timestamp_range[1]

            # Подсчитываем статистику
            problematic_count = sum(1 for p in parameters if p.is_problematic)
            normal_count = len(parameters) - problematic_count

            self.logger.info(f"✅ Обработано {len(parameters)} параметров ({normal_count} нормальных, {problematic_count} проблемных), {len(lines)} линий")

            return True

        except Exception as e:
            self.logger.error(f"Ошибка приоритетной обработки данных телеметрии: {e}")
            return False

    def _collect_load_statistics(self, file_path: str, load_time: float):
        """Сбор статистики загрузки"""
        try:
            self._load_statistics = {
                'file_path': file_path,
                'load_time_seconds': load_time,
                'timestamp': datetime.now().isoformat(),
                'parameters_count': len(self._cached_parameters) if self._cached_parameters else 0,
                'lines_count': len(self._cached_lines) if self._cached_lines else 0,
                'telemetry_records': self._telemetry_data.records_count if self._telemetry_data else 0,
                'timestamp_integrated': bool(self._telemetry_data and hasattr(self._telemetry_data, 'timestamp_columns')),
                'time_range_initialized': bool(self._time_range_fields)
            }
            
            # Производительность
            self._performance_metrics['last_load_time'] = load_time
            self._performance_metrics['parameters_per_second'] = (
                len(self._cached_parameters) / load_time if load_time > 0 and self._cached_parameters else 0
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка сбора статистики загрузки: {e}")

    # === ПРИОРИТЕТНЫЕ МЕТОДЫ ДЛЯ ИЗМЕНЯЕМЫХ ПАРАМЕТРОВ ===

    def find_changed_parameters_in_range(self, threshold: float = 0.1) -> List[Parameter]:
        """🔥 ПРИОРИТЕТНЫЙ поиск изменяемых параметров в текущем диапазоне"""
        try:
            self.logger.info(f"🔥 ПРИОРИТЕТНЫЙ поиск изменяемых параметров (threshold={threshold})")
            
            if not self._telemetry_data or not self._cached_parameters:
                self.logger.warning("Данные не загружены для поиска изменяемых параметров")
                return []

            # Проверяем кэш
            cache_key = f"changed_params_{threshold}_{self._get_current_range_key()}"
            if cache_key in self._changed_params_cache:
                self.logger.debug("Использование кэшированных изменяемых параметров")
                return self._changed_params_cache[cache_key]

            # Выполняем приоритетный анализ
            start_time = time.time()
            
            if self.time_range_service:
                changed_params = self.time_range_service.find_changed_parameters_in_range(
                    self._telemetry_data,
                    self._cached_parameters,
                    threshold
                )
            else:
                # Fallback анализ
                changed_params = self._fallback_changed_analysis(threshold)

            analysis_time = time.time() - start_time

            # Кэшируем результат
            self._changed_params_cache[cache_key] = changed_params
            
            # Обновляем метрики производительности
            self._performance_metrics['last_changed_analysis_time'] = analysis_time
            self._performance_metrics['changed_params_found'] = len(changed_params)

            self.logger.info(f"✅ ПРИОРИТЕТНЫЙ анализ завершен: {len(changed_params)} изменяемых параметров за {analysis_time:.2f}с")
            
            return changed_params

        except Exception as e:
            self.logger.error(f"Ошибка приоритетного поиска изменяемых параметров: {e}")
            return []

    def _fallback_changed_analysis(self, threshold: float) -> List[Parameter]:
        """Fallback анализ изменяемых параметров"""
        try:
            if not self._telemetry_data or not self._cached_parameters:
                return []

            changed_params = []
            data = self._telemetry_data.data

            for param in self._cached_parameters:
                if param.full_column in data.columns:
                    series = data[param.full_column]
                    
                    # Простой анализ изменяемости
                    if self._is_parameter_changed_simple(series, threshold):
                        changed_params.append(param)

            return changed_params

        except Exception as e:
            self.logger.error(f"Ошибка fallback анализа: {e}")
            return []

    def _is_parameter_changed_simple(self, series, threshold: float) -> bool:
        """Простая проверка изменяемости параметра"""
        try:
            clean_series = series.dropna()
            
            if len(clean_series) < 2:
                return False
            
            # Для числовых данных
            if clean_series.dtype.kind in 'biufc':
                unique_ratio = len(clean_series.unique()) / len(clean_series)
                return unique_ratio > threshold
            
            # Для категориальных данных
            unique_count = len(clean_series.unique())
            return unique_count > 1 and unique_count < len(clean_series) * 0.9

        except Exception:
            return False

    def set_priority_mode(self, enabled: bool):
        """Установка приоритетного режима для изменяемых параметров"""
        self._priority_mode_active = enabled
        
        if enabled:
            self.logger.info("🔥 ПРИОРИТЕТНЫЙ режим изменяемых параметров ВКЛЮЧЕН")
            # Очищаем кэш для пересчета
            self._changed_params_cache.clear()
        else:
            self.logger.info("Приоритетный режим изменяемых параметров отключен")

    def is_priority_mode_active(self) -> bool:
        """Проверка активности приоритетного режима"""
        return self._priority_mode_active

    def get_changed_parameters_statistics(self) -> Dict[str, Any]:
        """Получение статистики по изменяемым параметрам"""
        try:
            if not self._cached_parameters:
                return {'error': 'Параметры не загружены'}

            # Анализируем с разными порогами
            thresholds = [0.05, 0.1, 0.2, 0.5]
            statistics = {
                'total_parameters': len(self._cached_parameters),
                'analysis_by_threshold': {},
                'performance_metrics': self._performance_metrics.copy()
            }

            for threshold in thresholds:
                changed_params = self.find_changed_parameters_in_range(threshold)
                statistics['analysis_by_threshold'][threshold] = {
                    'changed_count': len(changed_params),
                    'change_percentage': (len(changed_params) / len(self._cached_parameters) * 100) if self._cached_parameters else 0
                }

            return statistics

        except Exception as e:
            self.logger.error(f"Ошибка получения статистики изменяемых параметров: {e}")
            return {'error': str(e)}

    def _get_current_range_key(self) -> str:
        """Получение ключа текущего временного диапазона для кэширования"""
        try:
            if self.time_range_service:
                current_range = self.time_range_service.get_current_range()
                if current_range and len(current_range) >= 2:
                    return f"{current_range[0]}_{current_range[1]}"
            
            return "full_range"
        except Exception:
            return "unknown_range"

    # === МЕТОДЫ РАБОТЫ С ВРЕМЕННЫМИ ДИАПАЗОНАМИ ===

    def get_time_range_fields(self) -> Optional[Dict[str, Any]]:
        """ИСПРАВЛЕННОЕ получение полей времени с приоритетной логикой"""
        try:
            # Приоритет 1: Через time_range_service.get_current_range()
            if self.time_range_service and hasattr(self.time_range_service, 'get_current_range'):
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
                        'total_records': getattr(self.time_range_service, 'total_records', 0),
                        'source': 'time_range_service'
                    }

            # Приоритет 2: Через _telemetry_data.timestamp_range
            if self._telemetry_data and hasattr(self._telemetry_data, 'timestamp_range'):
                timestamp_range = self._telemetry_data.timestamp_range
                if timestamp_range and len(timestamp_range) >= 2:
                    from_time = timestamp_range[0].strftime('%Y-%m-%d %H:%M:%S')
                    to_time = timestamp_range[1].strftime('%Y-%m-%d %H:%M:%S')
                    
                    return {
                        'from_time': from_time,
                        'to_time': to_time,
                        'duration': self._calculate_duration(from_time, to_time),
                        'total_records': getattr(self._telemetry_data, 'records_count', 0),
                        'source': 'telemetry_data'
                    }

            # Приоритет 3: Через data_loader
            if (self.data_loader and 
                hasattr(self.data_loader, 'min_timestamp') and 
                hasattr(self.data_loader, 'max_timestamp')):
                
                min_time = self.data_loader.min_timestamp
                max_time = self.data_loader.max_timestamp
                
                if min_time and max_time:
                    return {
                        'from_time': str(min_time),
                        'to_time': str(max_time),
                        'duration': self._calculate_duration(str(min_time), str(max_time)),
                        'total_records': getattr(self.data_loader, 'records_count', 0),
                        'source': 'data_loader'
                    }

            # Приоритет 4: Из кэшированных полей
            if self._time_range_fields:
                result = self._time_range_fields.copy()
                result['source'] = 'cached_fields'
                return result

            self.logger.warning("Не удалось получить поля времени из всех источников")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения полей времени: {e}")
            return None

    def set_user_time_range(self, from_time: str, to_time: str) -> bool:
        """ПРИОРИТЕТНАЯ установка пользовательского временного диапазона"""
        try:
            self.logger.info(f"🔥 ПРИОРИТЕТНАЯ установка временного диапазона: {from_time} - {to_time}")

            if not self.time_range_service:
                self.logger.error("TimeRangeService недоступен")
                return False

            # Валидация временного диапазона
            if not self._validate_time_range(from_time, to_time):
                return False

            # Устанавливаем через сервис
            success = self.time_range_service.set_user_time_range(from_time, to_time)

            if success:
                # Обновляем кэшированные поля
                if self._time_range_fields:
                    self._time_range_fields.update({
                        'from_time': from_time,
                        'to_time': to_time,
                        'duration': self._calculate_duration(from_time, to_time),
                        'source': 'user_set'
                    })

                # ПРИОРИТЕТНАЯ очистка кэша изменяемых параметров
                self._changed_params_cache.clear()
                self._analysis_cache.clear()

                self.logger.info(f"✅ ПРИОРИТЕТНЫЙ диапазон установлен: {from_time} - {to_time}")

            return success

        except Exception as e:
            self.logger.error(f"Ошибка установки приоритетного диапазона: {e}")
            return False

    def _validate_time_range(self, from_time: str, to_time: str) -> bool:
        """Валидация временного диапазона"""
        try:
            from_dt = datetime.strptime(from_time, '%Y-%m-%d %H:%M:%S')
            to_dt = datetime.strptime(to_time, '%Y-%m-%d %H:%M:%S')

            if from_dt >= to_dt:
                self.logger.error("Время начала должно быть раньше времени окончания")
                return False

            # Проверяем что диапазон в пределах данных
            if self._telemetry_data and hasattr(self._telemetry_data, 'timestamp_range'):
                data_range = self._telemetry_data.timestamp_range
                if data_range and len(data_range) >= 2:
                    if from_dt < data_range[0] or to_dt > data_range[1]:
                        self.logger.warning("Запрошенный диапазон выходит за пределы данных")
                        # Не блокируем, но предупреждаем

            return True

        except ValueError as e:
            self.logger.error(f"Неверный формат времени: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка валидации времени: {e}")
            return False

    def reset_time_range_to_full(self):
        """ПРИОРИТЕТНЫЙ сброс временного диапазона к полному"""
        try:
            self.logger.info("🔥 ПРИОРИТЕТНЫЙ сброс временного диапазона к полному")

            if self.time_range_service:
                self.time_range_service.reset_to_data_range()

                if self._telemetry_data:
                    self._time_range_fields = self.time_range_service.initialize_from_telemetry_data(
                        self._telemetry_data)
                    self.logger.info("✅ Временной диапазон сброшен к полному")

            # ПРИОРИТЕТНАЯ очистка кэша
            self._changed_params_cache.clear()
            self._analysis_cache.clear()

        except Exception as e:
            self.logger.error(f"Ошибка приоритетного сброса временного диапазона: {e}")

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

    def get_time_range_statistics(self) -> Dict[str, Any]:
        """Получение статистики временного диапазона"""
        try:
            if not self.time_range_service:
                return {'error': 'TimeRangeService недоступен'}

            stats = self.time_range_service.get_range_statistics()

            # Добавляем дополнительную информацию
            if self._telemetry_data:
                current_range = self.time_range_service.get_current_range()
                if current_range:
                    filtered_data = self._telemetry_data.filter_by_time(*current_range)
                    stats.update({
                        'filtered_records': filtered_data.records_count if filtered_data else 0,
                        'total_records': self._telemetry_data.records_count,
                        'records_ratio': (
                            (filtered_data.records_count / self._telemetry_data.records_count * 100) 
                            if self._telemetry_data.records_count > 0 and filtered_data else 0
                        )
                    })

            return stats

        except Exception as e:
            self.logger.error(f"Ошибка получения статистики временного диапазона: {e}")
            return {'error': str(e)}

    # === МЕТОДЫ ПОЛУЧЕНИЯ ПАРАМЕТРОВ И СОВМЕСТИМОСТИ ===

    def get_filterable_parameters(self) -> List[Parameter]:
        """ПРИОРИТЕТНЫЙ метод получения параметров для фильтрации"""
        try:
            if not self._cached_parameters:
                self.logger.warning("Параметры не загружены для фильтрации")
                return []

            # В приоритетном режиме возвращаем ВСЕ параметры
            # Фильтрация сама решит что показывать
            if self._priority_mode_active:
                self.logger.debug("🔥 ПРИОРИТЕТНЫЙ режим: возвращаем все параметры для фильтрации")
                return self._cached_parameters

            # В обычном режиме можем исключить проблемные
            return self._cached_parameters

        except Exception as e:
            self.logger.error(f"Ошибка получения параметров для фильтрации: {e}")
            return []

    def get_parameter_objects(self) -> List[Parameter]:
        """Получение Parameter объектов"""
        return self._cached_parameters or []

    def get_parameters(self) -> List[Dict[str, Any]]:
        """Получение параметров в формате словарей (legacy совместимость)"""
        return self._cached_parameter_dicts or []

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

    def get_lines(self) -> List[str]:
        """Получение линий из кэша"""
        return list(self._cached_lines) if self._cached_lines else []

    def get_telemetry_data(self) -> Optional[TelemetryData]:
        """Получение объекта TelemetryData"""
        return self._telemetry_data

    def get_parameters_by_type(self, parameter_type: str) -> List[Parameter]:
        """НОВЫЙ МЕТОД: Получение параметров по типу"""
        try:
            if not self._cached_parameters:
                return []

            if parameter_type == 'normal':
                return self.get_normal_parameters()
            elif parameter_type == 'problematic':
                return self.get_problematic_parameters()
            elif parameter_type == 'timestamp':
                return [p for p in self._cached_parameters if p.is_timestamp_parameter()]
            elif parameter_type == 'changed':
                # Возвращаем последние найденные изменяемые параметры
                if self._changed_params_cache:
                    latest_key = max(self._changed_params_cache.keys())
                    return self._changed_params_cache[latest_key]
                return []
            else:  # 'all'
                return self._cached_parameters

        except Exception as e:
            self.logger.error(f"Ошибка получения параметров по типу {parameter_type}: {e}")
            return []

    def get_parameters_by_line(self, line: str) -> List[Parameter]:
        """НОВЫЙ МЕТОД: Получение параметров по линии"""
        try:
            if not self._cached_parameters:
                return []

            return [p for p in self._cached_parameters if p.line == line]

        except Exception as e:
            self.logger.error(f"Ошибка получения параметров по линии {line}: {e}")
            return []

    def get_parameters_by_wagon(self, wagon: str) -> List[Parameter]:
        """НОВЫЙ МЕТОД: Получение параметров по вагону"""
        try:
            if not self._cached_parameters:
                return []

            return [p for p in self._cached_parameters if p.wagon == wagon]

        except Exception as e:
            self.logger.error(f"Ошибка получения параметров по вагону {wagon}: {e}")
            return []

    def search_parameters(self, search_text: str) -> List[Parameter]:
        """НОВЫЙ МЕТОД: Поиск параметров по тексту"""
        try:
            if not self._cached_parameters or not search_text:
                return []

            search_text = search_text.lower()
            found_parameters = []

            for param in self._cached_parameters:
                # Поиск в signal_code
                if search_text in param.signal_code.lower():
                    found_parameters.append(param)
                    continue

                # Поиск в description
                if param.description and search_text in param.description.lower():
                    found_parameters.append(param)
                    continue

                # Поиск в line
                if search_text in param.line.lower():
                    found_parameters.append(param)
                    continue

            self.logger.info(f"Найдено {len(found_parameters)} параметров по запросу '{search_text}'")
            return found_parameters

        except Exception as e:
            self.logger.error(f"Ошибка поиска параметров: {e}")
            return []

    # === МЕТОДЫ АНАЛИЗА И СТАТИСТИКИ ===

    def analyze_parameter_changes_detailed(self, threshold: float = 0.1) -> Dict[str, Any]:
        """ПРИОРИТЕТНЫЙ детальный анализ изменений параметров"""
        try:
            self.logger.info(f"🔥 ПРИОРИТЕТНЫЙ детальный анализ изменений (threshold={threshold})")

            if not self._telemetry_data or not self._cached_parameters:
                return {'error': 'Данные не загружены'}

            # Проверяем кэш
            cache_key = f"detailed_analysis_{threshold}_{self._get_current_range_key()}"
            if cache_key in self._analysis_cache:
                self.logger.debug("Использование кэшированного детального анализа")
                return self._analysis_cache[cache_key]

            start_time = time.time()

            # Получаем текущий диапазон
            if self.time_range_service:
                current_range = self.time_range_service.get_current_range()
            else:
                current_range = None

            if not current_range:
                return {'error': 'Временной диапазон не установлен'}

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
                'statistics': {},
                'performance': {}
            }

            # Анализируем каждый параметр
            for param in self._cached_parameters:
                if param.full_column in filtered_data.data.columns:
                    series = filtered_data.data[param.full_column]
                    
                    # Определяем изменяемость
                    is_changed = self._is_parameter_changed_advanced(series, threshold)
                    
                    # Собираем статистику
                    param_stats = self._calculate_parameter_statistics(series)
                    
                    param_info = {
                        'parameter': param.to_dict(),
                        'is_changed': is_changed,
                        'change_statistics': param_stats,
                        'change_score': param_stats.get('change_score', 0)
                    }

                    if is_changed:
                        analysis_result['changed_parameters'].append(param_info)
                    else:
                        analysis_result['unchanged_parameters'].append(param_info)

            # Сортируем изменяемые параметры по score
            analysis_result['changed_parameters'].sort(
                key=lambda x: x['change_score'], reverse=True
            )

            # Общая статистика
            analysis_result['statistics'] = {
                'changed_count': len(analysis_result['changed_parameters']),
                'unchanged_count': len(analysis_result['unchanged_parameters']),
                'change_ratio': (len(analysis_result['changed_parameters']) / len(self._cached_parameters) * 100) if self._cached_parameters else 0,
                'filtered_records': filtered_data.records_count if filtered_data else 0,
                'total_records': self._telemetry_data.records_count
            }

            # Метрики производительности
            analysis_time = time.time() - start_time
            analysis_result['performance'] = {
                'analysis_time_seconds': analysis_time,
                'parameters_per_second': len(self._cached_parameters) / analysis_time if analysis_time > 0 else 0,
                'cache_used': False
            }

            # Кэшируем результат
            self._analysis_cache[cache_key] = analysis_result

            self.logger.info(f"✅ ПРИОРИТЕТНЫЙ детальный анализ завершен за {analysis_time:.2f}с")
            return analysis_result

        except Exception as e:
            self.logger.error(f"Ошибка детального анализа: {e}")
            return {'error': str(e)}

    def _is_parameter_changed_advanced(self, series, threshold: float) -> bool:
        """Продвинутая проверка изменяемости параметра"""
        try:
            if self.time_range_service and hasattr(self.time_range_service, '_is_parameter_changed'):
                return self.time_range_service._is_parameter_changed(series, threshold)
            else:
                # Fallback метод
                return self._is_parameter_changed_simple(series, threshold)

        except Exception as e:
            self.logger.error(f"Ошибка проверки изменяемости: {e}")
            return False

    def _calculate_parameter_statistics(self, series) -> Dict[str, Any]:
        """РАСШИРЕННЫЙ расчет статистики для параметра"""
        try:
            clean_series = series.dropna()

            if len(clean_series) == 0:
                return {'error': 'no_data', 'change_score': 0}

            stats = {
                'total_values': len(series),
                'valid_values': len(clean_series),
                'null_values': len(series) - len(clean_series),
                'unique_values': len(clean_series.unique()),
                'unique_ratio': len(clean_series.unique()) / len(clean_series) if len(clean_series) > 0 else 0
            }

            # Для числовых данных добавляем расширенную статистику
            if clean_series.dtype.kind in 'biufc':  # числовые типы
                stats.update({
                    'min_value': float(clean_series.min()),
                    'max_value': float(clean_series.max()),
                    'mean_value': float(clean_series.mean()),
                    'std_value': float(clean_series.std()),
                    'variance': float(clean_series.var()),
                    'range': float(clean_series.max() - clean_series.min()),
                    'coefficient_of_variation': float(clean_series.std() / clean_series.mean()) if clean_series.mean() != 0 else 0
                })

                # Вычисляем change_score для числовых данных
                if stats['range'] > 0:
                    stats['change_score'] = min(stats['unique_ratio'] * stats['coefficient_of_variation'], 1.0)
                else:
                    stats['change_score'] = 0
            else:
                # Для категориальных данных
                stats['change_score'] = stats['unique_ratio']

            return stats

        except Exception as e:
            self.logger.error(f"Ошибка расчета статистики параметра: {e}")
            return {'error': str(e), 'change_score': 0}

    def get_model_statistics(self) -> Dict[str, Any]:
        """РАСШИРЕННАЯ статистика модели"""
        try:
            stats = {
                'loaded_file': self._last_file_path,
                'load_statistics': self._load_statistics,
                'performance_metrics': self._performance_metrics,
                'priority_mode_active': self._priority_mode_active,
                'cache_status': {
                    'parameters_cached': self._cached_parameters is not None,
                    'lines_cached': self._cached_lines is not None,
                    'analysis_cache_size': len(self._analysis_cache),
                    'changed_params_cache_size': len(self._changed_params_cache)
                },
                'time_range_fields': self._time_range_fields
            }

            # Добавляем статистику по параметрам
            if self._cached_parameters:
                normal_count = sum(1 for p in self._cached_parameters if not p.is_problematic)
                problematic_count = len(self._cached_parameters) - normal_count
                timestamp_count = sum(1 for p in self._cached_parameters if p.is_timestamp_parameter())

                stats['parameter_statistics'] = {
                    'total_parameters': len(self._cached_parameters),
                    'normal_parameters': normal_count,
                    'problematic_parameters': problematic_count,
                    'timestamp_parameters': timestamp_count,
                    'lines_count': len(self._cached_lines) if self._cached_lines else 0,
                    'normal_percentage': (normal_count / len(self._cached_parameters) * 100) if self._cached_parameters else 0,
                    'problematic_percentage': (problematic_count / len(self._cached_parameters) * 100) if self._cached_parameters else 0
                }

            # Добавляем timestamp статистику
            if self._telemetry_data:
                stats['telemetry_statistics'] = {
                    'records_count': self._telemetry_data.records_count,
                    'has_timestamp': hasattr(self._telemetry_data, 'timestamp_columns'),
                    'timestamp_stats': self.get_timestamp_statistics(),
                    'timestamp_validation': self.validate_timestamp_data()
                }

                # Статистика временного диапазона
                if self.time_range_service:
                    stats['time_range_statistics'] = self.get_time_range_statistics()

            return stats

        except Exception as e:
            self.logger.error(f"Ошибка получения статистики модели: {e}")
            return {'error': str(e)}

    def get_performance_report(self) -> Dict[str, Any]:
        """НОВЫЙ МЕТОД: Отчет о производительности"""
        try:
            return {
                'load_performance': self._load_statistics,
                'runtime_performance': self._performance_metrics,
                'cache_performance': {
                    'analysis_cache_hits': len(self._analysis_cache),
                    'changed_params_cache_hits': len(self._changed_params_cache),
                    'memory_usage_estimate': self._estimate_memory_usage()
                },
                'recommendations': self._get_performance_recommendations()
            }

        except Exception as e:
            self.logger.error(f"Ошибка создания отчета производительности: {e}")
            return {'error': str(e)}

    def _estimate_memory_usage(self) -> Dict[str, Any]:
        """Оценка использования памяти"""
        try:
            import sys
            
            memory_estimate = {
                'cached_parameters_mb': sys.getsizeof(self._cached_parameters) / 1024 / 1024 if self._cached_parameters else 0,
                'cached_dicts_mb': sys.getsizeof(self._cached_parameter_dicts) / 1024 / 1024 if self._cached_parameter_dicts else 0,
                'analysis_cache_mb': sys.getsizeof(self._analysis_cache) / 1024 / 1024,
                'changed_params_cache_mb': sys.getsizeof(self._changed_params_cache) / 1024 / 1024,
                'telemetry_data_mb': sys.getsizeof(self._telemetry_data) / 1024 / 1024 if self._telemetry_data else 0
            }
            
            memory_estimate['total_estimated_mb'] = sum(memory_estimate.values())
            return memory_estimate

        except Exception as e:
            return {'error': str(e)}

    def _get_performance_recommendations(self) -> List[str]:
        """Рекомендации по производительности"""
        recommendations = []

        try:
            # Проверяем размер кэша
            if len(self._analysis_cache) > 50:
                recommendations.append("Рассмотрите очистку кэша анализа для экономии памяти")

            # Проверяем время загрузки
            if self._performance_metrics.get('last_load_time', 0) > 10:
                recommendations.append("Время загрузки превышает 10 секунд, рассмотрите оптимизацию")

            # Проверяем количество параметров
            if self._cached_parameters and len(self._cached_parameters) > 10000:
                recommendations.append("Большое количество параметров может замедлить работу")

            # Проверяем приоритетный режим
            if self._priority_mode_active:
                recommendations.append("Приоритетный режим активен - используйте кэширование для оптимизации")

        except Exception as e:
            recommendations.append(f"Ошибка анализа производительности: {e}")

        return recommendations

    # === МЕТОДЫ TIMESTAMP И ВАЛИДАЦИИ ===

    def get_timestamp_statistics(self) -> Dict[str, Any]:
        """Получение статистики timestamp"""
        try:
            if self._telemetry_data and hasattr(self._telemetry_data, 'get_timestamp_statistics'):
                return self._telemetry_data.get_timestamp_statistics()
            return {'error': 'Timestamp данные недоступны'}

        except Exception as e:
            self.logger.error(f"Ошибка получения timestamp статистики: {e}")
            return {'error': str(e)}

    def get_timestamp_parameters(self) -> Dict[str, List[Parameter]]:
        """Получение timestamp параметров по вагонам"""
        try:
            if self._cached_parameters:
                return self.timestamp_service.extract_timestamp_parameters(self._cached_parameters)
            return {}

        except Exception as e:
            self.logger.error(f"Ошибка получения timestamp параметров: {e}")
            return {}

    def validate_timestamp_data(self) -> Dict[str, Any]:
        """Валидация timestamp данных"""
        try:
            if self._telemetry_data and hasattr(self._telemetry_data, 'validate_timestamp_integrity'):
                return self._telemetry_data.validate_timestamp_integrity()
            return {'is_valid': False, 'issues': ['Данные не загружены']}

        except Exception as e:
            self.logger.error(f"Ошибка валидации timestamp: {e}")
            return {'is_valid': False, 'issues': [str(e)]}

    def repair_timestamp_data(self, method: str = 'interpolate') -> bool:
        """Восстановление timestamp данных"""
        try:
            if self._telemetry_data and hasattr(self._telemetry_data, 'repair_timestamp_gaps'):
                success = self._telemetry_data.repair_timestamp_gaps(method)
                
                if success:
                    # Обновляем поля времени после восстановления
                    if self.time_range_service:
                        self._time_range_fields = self.time_range_service.initialize_from_telemetry_data(
                            self._telemetry_data)
                    
                    # Очищаем кэш для пересчета
                    self._analysis_cache.clear()
                    self._changed_params_cache.clear()
                    
                    self.logger.info(f"✅ Timestamp данные восстановлены методом '{method}'")
                
                return success
            
            return False

        except Exception as e:
            self.logger.error(f"Ошибка восстановления timestamp: {e}")
            return False

    def filter_data_by_time(self, start_time: datetime, end_time: datetime) -> Optional[TelemetryData]:
        """Фильтрация данных по времени"""
        try:
            if self._telemetry_data and hasattr(self._telemetry_data, 'filter_by_time'):
                return self._telemetry_data.filter_by_time(start_time, end_time)
            return None

        except Exception as e:
            self.logger.error(f"Ошибка фильтрации по времени: {e}")
            return None

    def validate_data_integrity(self) -> Dict[str, Any]:
        """НОВЫЙ МЕТОД: Комплексная валидация целостности данных"""
        try:
            validation_result = {
                'overall_status': 'unknown',
                'validations': {},
                'issues': [],
                'warnings': [],
                'recommendations': []
            }

            # Валидация основных данных
            if not self._cached_parameters:
                validation_result['issues'].append('Параметры не загружены')
            else:
                validation_result['validations']['parameters_loaded'] = True
                validation_result['validations']['parameters_count'] = len(self._cached_parameters)

            # Валидация телеметрии
            if not self._telemetry_data:
                validation_result['issues'].append('Данные телеметрии не загружены')
            else:
                validation_result['validations']['telemetry_loaded'] = True
                validation_result['validations']['telemetry_records'] = self._telemetry_data.records_count

            # Валидация timestamp
            if self._telemetry_data:
                timestamp_validation = self.validate_timestamp_data()
                validation_result['validations']['timestamp'] = timestamp_validation
                
                if not timestamp_validation['is_valid']:
                    validation_result['warnings'].extend(timestamp_validation.get('issues', []))

            # Валидация временного диапазона
            if self.time_range_service:
                time_range_validation = self.time_range_service.validate_current_range()
                validation_result['validations']['time_range'] = time_range_validation
            else:
                validation_result['warnings'].append('TimeRangeService недоступен')

            # Определяем общий статус
            if validation_result['issues']:
                validation_result['overall_status'] = 'error'
            elif validation_result['warnings']:
                validation_result['overall_status'] = 'warning'
            else:
                validation_result['overall_status'] = 'ok'

            # Рекомендации
            if validation_result['warnings']:
                validation_result['recommendations'].append('Рассмотрите восстановление timestamp данных')
            
            if len(self._analysis_cache) == 0 and self._cached_parameters:
                validation_result['recommendations'].append('Выполните анализ изменяемых параметров для лучшей производительности')

            return validation_result

        except Exception as e:
            self.logger.error(f"Ошибка валидации целостности данных: {e}")
            return {
                'overall_status': 'error',
                'validations': {},
                'issues': [str(e)],
                'warnings': [],
                'recommendations': []
            }

    # === МЕТОДЫ ОЧИСТКИ И УПРАВЛЕНИЯ РЕСУРСАМИ ===

    def clear_cache(self):
        """РАСШИРЕННАЯ очистка кэша"""
        try:
            self.logger.info("Начало очистки кэша DataModel")

            # Основные кэшированные данные
            self._cached_parameters = None
            self._cached_parameter_dicts = None
            self._cached_lines = None
            self._last_file_path = None
            self._telemetry_data = None
            self._time_range_fields = None

            # ПРИОРИТЕТНАЯ очистка кэша изменяемых параметров
            self._changed_params_cache.clear()
            self._analysis_cache.clear()

            # Сброс режимов
            self._priority_mode_active = False

            # Очистка статистики
            self._load_statistics.clear()
            self._performance_metrics.clear()

            # Очистка сервисов
            if self.time_range_service and hasattr(self.time_range_service, 'clear_cache'):
                self.time_range_service.clear_cache()

            self.logger.info("✅ Кэш DataModel полностью очищен")

        except Exception as e:
            self.logger.error(f"Ошибка очистки кэша: {e}")

    def clear_analysis_cache(self):
        """НОВЫЙ МЕТОД: Очистка только кэша анализа"""
        try:
            cache_size_before = len(self._analysis_cache) + len(self._changed_params_cache)
            
            self._analysis_cache.clear()
            self._changed_params_cache.clear()
            
            self.logger.info(f"✅ Очищен кэш анализа: {cache_size_before} записей")

        except Exception as e:
            self.logger.error(f"Ошибка очистки кэша анализа: {e}")

    def optimize_memory_usage(self):
        """НОВЫЙ МЕТОД: Оптимизация использования памяти"""
        try:
            self.logger.info("Начало оптимизации памяти")

            # Очищаем старые записи кэша (оставляем только последние 10)
            if len(self._analysis_cache) > 10:
                # Сортируем по времени и оставляем последние
                sorted_keys = sorted(self._analysis_cache.keys())
                for key in sorted_keys[:-10]:
                    del self._analysis_cache[key]

            if len(self._changed_params_cache) > 5:
                sorted_keys = sorted(self._changed_params_cache.keys())
                for key in sorted_keys[:-5]:
                    del self._changed_params_cache[key]

            # Принудительная сборка мусора
            import gc
            gc.collect()

            self.logger.info("✅ Оптимизация памяти завершена")

        except Exception as e:
            self.logger.error(f"Ошибка оптимизации памяти: {e}")

    def export_model_state(self) -> Dict[str, Any]:
        """НОВЫЙ МЕТОД: Экспорт состояния модели"""
        try:
            state = {
                'metadata': {
                    'export_timestamp': datetime.now().isoformat(),
                    'loaded_file': self._last_file_path,
                    'priority_mode': self._priority_mode_active
                },
                'statistics': self.get_model_statistics(),
                'performance': self.get_performance_report(),
                'validation': self.validate_data_integrity(),
                'cache_info': {
                    'analysis_cache_keys': list(self._analysis_cache.keys()),
                    'changed_params_cache_keys': list(self._changed_params_cache.keys())
                }
            }

            # Добавляем конфигурацию временного диапазона
            if self.time_range_service:
                state['time_range_config'] = {
                    'current_range': self.time_range_service.get_current_range(),
                    'statistics': self.get_time_range_statistics()
                }

            return state

        except Exception as e:
            self.logger.error(f"Ошибка экспорта состояния модели: {e}")
            return {'error': str(e)}

    def import_model_state(self, state: Dict[str, Any]) -> bool:
        """НОВЫЙ МЕТОД: Импорт состояния модели"""
        try:
            self.logger.info("Начало импорта состояния модели")

            # Восстанавливаем приоритетный режим
            if 'metadata' in state and 'priority_mode' in state['metadata']:
                self.set_priority_mode(state['metadata']['priority_mode'])

            # Восстанавливаем временной диапазон
            if 'time_range_config' in state and self.time_range_service:
                time_config = state['time_range_config']
                if 'current_range' in time_config and time_config['current_range']:
                    current_range = time_config['current_range']
                    if len(current_range) >= 2:
                        self.time_range_service.set_user_time_range(
                            current_range[0].strftime('%Y-%m-%d %H:%M:%S') if isinstance(current_range[0], datetime) else str(current_range[0]),
                            current_range[1].strftime('%Y-%m-%d %H:%M:%S') if isinstance(current_range[1], datetime) else str(current_range[1])
                        )

            self.logger.info("✅ Состояние модели импортировано")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка импорта состояния модели: {e}")
            return False

    def cleanup(self):
        """Финальная очистка ресурсов"""
        try:
            self.logger.info("Начало финальной очистки DataModel")

            # Очищаем все кэши
            self.clear_cache()

            # Очищаем сервисы
            if self.time_range_service and hasattr(self.time_range_service, 'cleanup'):
                self.time_range_service.cleanup()

            if self.timestamp_service:
                self.timestamp_service = None

            if self.data_loader and hasattr(self.data_loader, 'cleanup'):
                self.data_loader.cleanup()

            self.logger.info("✅ DataModel полностью очищена")

        except Exception as e:
            self.logger.error(f"Ошибка финальной очистки: {e}")

    def __str__(self):
        return f"DataModel(loaded={bool(self._cached_parameters)}, priority={self._priority_mode_active}, params={len(self._cached_parameters) if self._cached_parameters else 0})"

    def __repr__(self):
        return self.__str__()

    def __del__(self):
        """Деструктор"""
        try:
            if hasattr(self, 'logger'):
                self.logger.info("DataModel удаляется из памяти")
        except:
            pass  # Игнорируем ошибки в деструкторе
