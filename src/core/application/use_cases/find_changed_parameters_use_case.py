# src/core/application/use_cases/find_changed_parameters_use_case.py - НОВЫЙ ФАЙЛ
"""
ПРИОРИТЕТНЫЙ Use Case для поиска изменяемых параметров с интеграцией в main.py
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import time

# Импорты DTO и сущностей
try:
    from ..dto.parameter_dto import ParameterDTO
    from ..dto.filter_dto import FilterDTO
except ImportError:
    logging.warning("DTO классы не найдены, используется fallback")
    ParameterDTO = None
    FilterDTO = None

# Импорты доменных сервисов
try:
    from ...domain.services.filtering_service import ParameterFilteringService
    from ...domain.entities.filter_criteria import FilterCriteria
    from ...domain.entities.parameter import Parameter
except ImportError:
    logging.warning("Доменные сервисы не найдены")
    ParameterFilteringService = None
    FilterCriteria = None
    Parameter = None

# Импорты моделей
try:
    from ...models.data_model import DataModel
except ImportError:
    logging.warning("DataModel не найдена")
    DataModel = None

logger = logging.getLogger(__name__)


# === ЗАПРОСЫ И ОТВЕТЫ ===

@dataclass
class FindChangedParametersRequest:
    """ПРИОРИТЕТНЫЙ запрос на поиск изменяемых параметров"""
    session_id: str
    from_time: Optional[str] = None
    to_time: Optional[str] = None
    threshold: float = 0.1
    include_timestamp_params: bool = False
    include_problematic_params: bool = True
    auto_apply: bool = True  # Автоматическое применение при изменении времени
    force_refresh: bool = False  # Принудительное обновление кэша


@dataclass
class FindChangedParametersResponse:
    """Ответ с изменяемыми параметрами"""
    changed_parameters: List[Dict[str, Any]]
    total_parameters: int
    changed_count: int
    time_range: Dict[str, Any]
    analysis_statistics: Dict[str, Any]
    execution_time_ms: float
    success: bool = True
    priority_applied: bool = False  # Был ли применен приоритетный фильтр
    error_message: Optional[str] = None
    cache_used: bool = False


# === ПРИОРИТЕТНЫЙ USE CASE ===

class FindChangedParametersUseCase:
    """🔥 ПРИОРИТЕТНЫЙ Use Case для поиска изменяемых параметров"""

    def __init__(self, data_model: Optional[DataModel] = None):
        self.data_model = data_model
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Кэш для производительности
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_ttl = 300  # 5 минут

    def execute(self, request: FindChangedParametersRequest) -> FindChangedParametersResponse:
        """🔥 ПРИОРИТЕТНОЕ выполнение поиска изменяемых параметров"""
        start_time = time.time()

        try:
            self.logger.info(f"🔥 ПРИОРИТЕТНЫЙ поиск изменяемых параметров: {request.from_time} - {request.to_time}")

            # Валидация запроса
            if not self._validate_request(request):
                return self._create_error_response(
                    "Неверный запрос", start_time
                )

            # Проверяем кэш
            cache_key = self._generate_cache_key(request)
            if not request.force_refresh and self._is_cache_valid(cache_key):
                cached_response = self._get_cached_response(cache_key, start_time)
                if cached_response:
                    self.logger.info("✅ Использован кэшированный результат")
                    return cached_response

            # Получаем или устанавливаем временной диапазон
            time_range = self._setup_time_range(request)
            
            if not time_range['success']:
                return self._create_error_response(
                    time_range.get('error', 'Ошибка установки временного диапазона'),
                    start_time
                )

            # ПРИОРИТЕТНЫЙ поиск изменяемых параметров
            changed_params, all_params = self._find_changed_parameters_priority(request)
            
            # Фильтруем по настройкам запроса
            filtered_changed = self._filter_by_request_settings(changed_params, request)
            filtered_all = self._filter_by_request_settings(all_params, request)
            
            # Преобразуем в словари для совместимости с main.py
            changed_dicts = [self._convert_to_dict(param) for param in filtered_changed]
            
            # Собираем детальную статистику
            statistics = self._collect_comprehensive_statistics(
                filtered_changed, filtered_all, request, time_range
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Создаем ответ
            response = FindChangedParametersResponse(
                changed_parameters=changed_dicts,
                total_parameters=len(filtered_all),
                changed_count=len(filtered_changed),
                time_range=time_range,
                analysis_statistics=statistics,
                execution_time_ms=execution_time,
                success=True,
                priority_applied=True,
                cache_used=False
            )

            # Кэшируем результат
            self._cache_response(cache_key, response)

            self.logger.info(f"✅ ПРИОРИТЕТНЫЙ поиск завершен: {len(filtered_changed)} изменяемых из {len(filtered_all)} ({execution_time:.1f}ms)")

            return response

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"Ошибка приоритетного поиска изменяемых параметров: {e}")
            
            return FindChangedParametersResponse(
                changed_parameters=[],
                total_parameters=0,
                changed_count=0,
                time_range={},
                analysis_statistics={'error': str(e)},
                execution_time_ms=execution_time,
                success=False,
                priority_applied=False,
                error_message=str(e)
            )

    def _validate_request(self, request: FindChangedParametersRequest) -> bool:
        """Валидация запроса"""
        try:
            if not request.session_id or not request.session_id.strip():
                self.logger.error("Отсутствует session_id")
                return False

            if request.threshold < 0 or request.threshold > 1:
                self.logger.error(f"Неверный threshold: {request.threshold}")
                return False

            # Валидация временного диапазона если указан
            if request.from_time and request.to_time:
                try:
                    from_dt = datetime.strptime(request.from_time, '%Y-%m-%d %H:%M:%S')
                    to_dt = datetime.strptime(request.to_time, '%Y-%m-%d %H:%M:%S')
                    
                    if from_dt >= to_dt:
                        self.logger.error("Время начала должно быть раньше времени окончания")
                        return False
                        
                except ValueError as e:
                    self.logger.error(f"Неверный формат времени: {e}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Ошибка валидации запроса: {e}")
            return False

    def _setup_time_range(self, request: FindChangedParametersRequest) -> Dict[str, Any]:
        """ПРИОРИТЕТНАЯ настройка временного диапазона"""
        try:
            if not self.data_model:
                return {'success': False, 'error': 'DataModel недоступна'}

            # Если время указано в запросе, используем его
            from_time = request.from_time
            to_time = request.to_time
            
            # Если время не указано, получаем из модели
            if not from_time or not to_time:
                time_fields = self.data_model.get_time_range_fields()
                if time_fields:
                    from_time = time_fields.get('from_time', '')
                    to_time = time_fields.get('to_time', '')

            if not from_time or not to_time:
                return {'success': False, 'error': 'Временной диапазон не определен'}

            # ПРИОРИТЕТНАЯ установка пользовательского диапазона
            if hasattr(self.data_model, 'set_user_time_range'):
                range_set = self.data_model.set_user_time_range(from_time, to_time)
                if not range_set:
                    return {'success': False, 'error': 'Неверный временной диапазон'}

            return {
                'success': True,
                'from_time': from_time,
                'to_time': to_time,
                'threshold': request.threshold,
                'source': 'priority_setup'
            }

        except Exception as e:
            self.logger.error(f"Ошибка настройки временного диапазона: {e}")
            return {'success': False, 'error': f'Ошибка настройки времени: {e}'}

    def _find_changed_parameters_priority(self, request: FindChangedParametersRequest) -> Tuple[List[Any], List[Any]]:
        """🔥 ПРИОРИТЕТНЫЙ поиск изменяемых параметров"""
        try:
            if not self.data_model:
                self.logger.error("DataModel недоступна для приоритетного поиска")
                return [], []

            # Приоритет 1: Через специализированный метод модели
            if hasattr(self.data_model, 'find_changed_parameters_in_range'):
                changed_params = self.data_model.find_changed_parameters_in_range(request.threshold)
                self.logger.info(f"🔥 Найдено {len(changed_params)} изменяемых параметров через DataModel")
            else:
                changed_params = []
                self.logger.warning("Метод find_changed_parameters_in_range недоступен в DataModel")

            # Получаем все параметры
            if hasattr(self.data_model, 'get_filterable_parameters'):
                all_params = self.data_model.get_filterable_parameters()
            elif hasattr(self.data_model, 'get_parameter_objects'):
                all_params = self.data_model.get_parameter_objects()
            else:
                all_params = []
                self.logger.warning("Методы получения параметров недоступны в DataModel")

            # Fallback анализ если основной метод не сработал
            if not changed_params and all_params:
                self.logger.info("Выполняется fallback анализ изменяемых параметров")
                changed_params = self._fallback_changed_analysis(all_params, request.threshold)

            return changed_params, all_params

        except Exception as e:
            self.logger.error(f"Ошибка приоритетного поиска изменяемых параметров: {e}")
            return [], []

    def _fallback_changed_analysis(self, parameters: List[Any], threshold: float) -> List[Any]:
        """Fallback анализ изменяемых параметров"""
        try:
            if not self.data_model or not hasattr(self.data_model, '_telemetry_data'):
                return []

            telemetry_data = self.data_model._telemetry_data
            if not telemetry_data or not hasattr(telemetry_data, 'data'):
                return []

            changed_params = []
            data = telemetry_data.data

            for param in parameters:
                # Получаем имя столбца
                if hasattr(param, 'full_column'):
                    column_name = param.full_column
                elif hasattr(param, 'signal_code'):
                    column_name = param.signal_code
                else:
                    continue

                if column_name in data.columns:
                    series = data[column_name]
                    
                    # Простой анализ изменяемости
                    if self._is_parameter_changed_simple(series, threshold):
                        changed_params.append(param)

            self.logger.info(f"Fallback анализ: найдено {len(changed_params)} изменяемых параметров")
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

    def _filter_by_request_settings(self, parameters: List[Any], request: FindChangedParametersRequest) -> List[Any]:
        """Фильтрация параметров по настройкам запроса"""
        try:
            filtered = []
            
            for param in parameters:
                # Фильтр временных параметров
                if not request.include_timestamp_params:
                    if hasattr(param, 'is_timestamp_parameter') and param.is_timestamp_parameter():
                        continue
                
                # Фильтр проблемных параметров
                if not request.include_problematic_params:
                    if hasattr(param, 'is_problematic') and param.is_problematic:
                        continue
                
                filtered.append(param)
            
            return filtered

        except Exception as e:
            self.logger.error(f"Ошибка фильтрации по настройкам: {e}")
            return parameters

    def _convert_to_dict(self, param) -> Dict[str, Any]:
        """Универсальное преобразование параметра в словарь для совместимости с main.py"""
        try:
            if isinstance(param, dict):
                return param
            elif hasattr(param, 'to_dict'):
                return param.to_dict()
            elif hasattr(param, '__dict__'):
                # Создаем словарь с основными полями для совместимости
                return {
                    'signal_code': getattr(param, 'signal_code', ''),
                    'full_column': getattr(param, 'full_column', getattr(param, 'signal_code', '')),
                    'description': getattr(param, 'description', ''),
                    'line': getattr(param, 'line', ''),
                    'wagon': getattr(param, 'wagon', ''),
                    'data_type': getattr(param, 'data_type', ''),
                    'signal_type': getattr(param, 'signal_type', ''),
                    'is_problematic': getattr(param, 'is_problematic', False),
                    'is_changed': True,  # Помечаем как изменяемый
                    'plot': getattr(param, 'plot', False)
                }
            else:
                return {
                    'signal_code': str(param),
                    'full_column': str(param),
                    'description': str(param),
                    'line': 'Unknown',
                    'wagon': '1',
                    'data_type': 'Unknown',
                    'signal_type': 'Unknown',
                    'is_problematic': False,
                    'is_changed': True,
                    'plot': False
                }
        except Exception as e:
            self.logger.error(f"Ошибка преобразования параметра: {e}")
            return {
                'signal_code': 'ERROR',
                'full_column': 'ERROR',
                'description': 'Ошибка преобразования',
                'line': 'ERROR',
                'wagon': '1',
                'data_type': 'ERROR',
                'signal_type': 'ERROR',
                'is_problematic': True,
                'is_changed': False,
                'plot': False
            }

    def _collect_comprehensive_statistics(self, changed_params: List[Any], all_params: List[Any], 
                                        request: FindChangedParametersRequest, 
                                        time_range: Dict[str, Any]) -> Dict[str, Any]:
        """Сбор комплексной статистики анализа"""
        try:
            statistics = {
                'filter_settings': {
                    'threshold': request.threshold,
                    'include_timestamp_params': request.include_timestamp_params,
                    'include_problematic_params': request.include_problematic_params,
                    'auto_apply': request.auto_apply
                },
                'counts': {
                    'total_parameters': len(all_params),
                    'changed_parameters': len(changed_params),
                    'change_percentage': (len(changed_params) / len(all_params) * 100) if all_params else 0,
                    'unchanged_parameters': len(all_params) - len(changed_params)
                },
                'time_range': time_range,
                'analysis_method': 'priority_use_case'
            }

            # Дополнительная статистика из модели
            if self.data_model:
                try:
                    if hasattr(self.data_model, 'get_time_range_statistics'):
                        time_stats = self.data_model.get_time_range_statistics()
                        statistics['time_range_stats'] = time_stats

                    if hasattr(self.data_model, 'get_changed_parameters_statistics'):
                        changed_stats = self.data_model.get_changed_parameters_statistics()
                        statistics['model_stats'] = changed_stats

                    # Детальный анализ если доступен
                    if hasattr(self.data_model, 'analyze_parameter_changes_detailed'):
                        detailed_analysis = self.data_model.analyze_parameter_changes_detailed(request.threshold)
                        statistics['detailed_analysis'] = detailed_analysis

                except Exception as e:
                    statistics['model_stats_error'] = str(e)

            # Статистика по типам параметров
            if changed_params:
                try:
                    problematic_count = sum(1 for p in changed_params 
                                          if hasattr(p, 'is_problematic') and p.is_problematic)
                    timestamp_count = sum(1 for p in changed_params 
                                        if hasattr(p, 'is_timestamp_parameter') and p.is_timestamp_parameter())
                    
                    statistics['parameter_types'] = {
                        'normal_changed': len(changed_params) - problematic_count,
                        'problematic_changed': problematic_count,
                        'timestamp_changed': timestamp_count
                    }
                except Exception as e:
                    statistics['parameter_types_error'] = str(e)

            return statistics

        except Exception as e:
            self.logger.error(f"Ошибка сбора статистики: {e}")
            return {
                'error': str(e),
                'filter_settings': {
                    'threshold': request.threshold
                },
                'counts': {
                    'total_parameters': len(all_params),
                    'changed_parameters': len(changed_params)
                }
            }

    # === МЕТОДЫ КЭШИРОВАНИЯ ===

    def _generate_cache_key(self, request: FindChangedParametersRequest) -> str:
        """Генерация ключа кэша"""
        try:
            key_parts = [
                request.session_id,
                request.from_time or 'auto',
                request.to_time or 'auto',
                str(request.threshold),
                str(request.include_timestamp_params),
                str(request.include_problematic_params)
            ]
            return "_".join(key_parts)
        except Exception:
            return f"fallback_{time.time()}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Проверка валидности кэша"""
        try:
            if cache_key not in self._cache_timestamps:
                return False
            
            cache_time = self._cache_timestamps[cache_key]
            current_time = time.time()
            
            return (current_time - cache_time) < self._cache_ttl
        except Exception:
            return False

    def _get_cached_response(self, cache_key: str, start_time: float) -> Optional[FindChangedParametersResponse]:
        """Получение кэшированного ответа"""
        try:
            if cache_key not in self._cache:
                return None
            
            cached_data = self._cache[cache_key]
            execution_time = (time.time() - start_time) * 1000
            
            # Создаем новый ответ на основе кэшированных данных
            response = FindChangedParametersResponse(
                changed_parameters=cached_data['changed_parameters'],
                total_parameters=cached_data['total_parameters'],
                changed_count=cached_data['changed_count'],
                time_range=cached_data['time_range'],
                analysis_statistics=cached_data['analysis_statistics'],
                execution_time_ms=execution_time,
                success=True,
                priority_applied=True,
                cache_used=True
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Ошибка получения кэшированного ответа: {e}")
            return None

    def _cache_response(self, cache_key: str, response: FindChangedParametersResponse):
        """Кэширование ответа"""
        try:
            self._cache[cache_key] = {
                'changed_parameters': response.changed_parameters,
                'total_parameters': response.total_parameters,
                'changed_count': response.changed_count,
                'time_range': response.time_range,
                'analysis_statistics': response.analysis_statistics
            }
            
            self._cache_timestamps[cache_key] = time.time()
            
            # Очистка старого кэша (оставляем только последние 10 записей)
            if len(self._cache) > 10:
                oldest_keys = sorted(self._cache_timestamps.keys(), 
                                   key=lambda k: self._cache_timestamps[k])[:-10]
                for old_key in oldest_keys:
                    self._cache.pop(old_key, None)
                    self._cache_timestamps.pop(old_key, None)
                    
        except Exception as e:
            self.logger.error(f"Ошибка кэширования ответа: {e}")

    def _create_error_response(self, error_message: str, start_time: float) -> FindChangedParametersResponse:
        """Создание ответа с ошибкой"""
        execution_time = (time.time() - start_time) * 1000
        
        return FindChangedParametersResponse(
            changed_parameters=[],
            total_parameters=0,
            changed_count=0,
            time_range={},
            analysis_statistics={'error': error_message},
            execution_time_ms=execution_time,
            success=False,
            priority_applied=False,
            error_message=error_message
        )

    # === ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ===

    def clear_cache(self):
        """Очистка кэша"""
        try:
            self._cache.clear()
            self._cache_timestamps.clear()
            self.logger.info("Кэш FindChangedParametersUseCase очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки кэша: {e}")

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        try:
            current_time = time.time()
            valid_entries = sum(1 for timestamp in self._cache_timestamps.values() 
                              if (current_time - timestamp) < self._cache_ttl)
            
            return {
                'total_entries': len(self._cache),
                'valid_entries': valid_entries,
                'expired_entries': len(self._cache) - valid_entries,
                'cache_ttl_seconds': self._cache_ttl,
                'memory_usage_estimate': len(str(self._cache))
            }
        except Exception as e:
            return {'error': str(e)}

    def set_cache_ttl(self, ttl_seconds: int):
        """Установка времени жизни кэша"""
        try:
            if ttl_seconds > 0:
                self._cache_ttl = ttl_seconds
                self.logger.info(f"Cache TTL установлен: {ttl_seconds} секунд")
            else:
                self.logger.warning("Неверное значение TTL, используется значение по умолчанию")
        except Exception as e:
            self.logger.error(f"Ошибка установки Cache TTL: {e}")

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.clear_cache()
            self.data_model = None
            self.logger.info("FindChangedParametersUseCase очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки ресурсов: {e}")

    def __str__(self):
        return f"FindChangedParametersUseCase(cache_entries={len(self._cache)}, model={'available' if self.data_model else 'unavailable'})"

    def __repr__(self):
        return self.__str__()


# === ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ===

def create_find_changed_parameters_use_case(data_model: Optional[DataModel] = None) -> FindChangedParametersUseCase:
    """Фабричная функция для создания Use Case"""
    try:
        use_case = FindChangedParametersUseCase(data_model)
        logger.info("FindChangedParametersUseCase создан успешно")
        return use_case
    except Exception as e:
        logger.error(f"Ошибка создания FindChangedParametersUseCase: {e}")
        raise


def create_quick_changed_params_request(session_id: str, threshold: float = 0.1) -> FindChangedParametersRequest:
    """Быстрое создание запроса с настройками по умолчанию"""
    return FindChangedParametersRequest(
        session_id=session_id,
        threshold=threshold,
        include_timestamp_params=False,
        include_problematic_params=True,
        auto_apply=True
    )
