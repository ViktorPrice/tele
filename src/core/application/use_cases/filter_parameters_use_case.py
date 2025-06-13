# src/core/application/use_cases/filter_parameters_use_case.py - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Use Cases для фильтрации параметров и поиска изменяемых параметров с приоритетной логикой
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import time

# Импорты DTO и сущностей
try:
    from ..dto.parameter_dto import ParameterDTO
    from ..dto.filter_dto import FilterDTO
except ImportError:
    # Fallback для случая отсутствия DTO
    logging.warning("DTO классы не найдены, используется fallback")
    ParameterDTO = None
    FilterDTO = None

# Импорты доменных сервисов
try:
    from ...domain.services.filtering_service import ParameterFilteringService
    from ...domain.entities.filter_criteria import FilterCriteria
except ImportError:
    logging.warning("Доменные сервисы не найдены")
    ParameterFilteringService = None
    FilterCriteria = None

# Импорты репозиториев и моделей
try:
    from ...repositories.parameter_repository import ParameterRepository
    from ...models.data_model import DataModel
except ImportError:
    logging.warning("Репозитории и модели не найдены")
    ParameterRepository = None
    DataModel = None

logger = logging.getLogger(__name__)


# === ЗАПРОСЫ И ОТВЕТЫ ===

@dataclass
class FilterParametersRequest:
    """Запрос на фильтрацию параметров"""
    session_id: str
    filter_criteria: Optional[Dict[str, Any]] = None  # Изменено для гибкости
    changed_only: bool = False  # ПРИОРИТЕТНЫЙ флаг
    include_problematic: bool = True
    search_text: Optional[str] = None


@dataclass
class FilterParametersResponse:
    """Ответ с отфильтрованными параметрами"""
    parameters: List[Dict[str, Any]]  # Изменено на Dict для совместимости
    total_count: int
    filtered_count: int
    execution_time_ms: float
    filter_type: str  # 'standard', 'changed_only', 'diagnostic'
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class FindChangedParametersRequest:
    """ПРИОРИТЕТНЫЙ запрос на поиск изменяемых параметров"""
    session_id: str
    from_time: str
    to_time: str
    threshold: float = 0.1
    include_timestamp_params: bool = False
    include_problematic_params: bool = True
    auto_apply: bool = True  # Автоматическое применение при изменении времени


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


@dataclass
class TimeRangeInitRequest:
    """Запрос на инициализацию временного диапазона"""
    session_id: str
    force_refresh: bool = False


@dataclass
class TimeRangeInitResponse:
    """Ответ с инициализированным временным диапазоном"""
    from_time: str
    to_time: str
    duration: str
    total_records: int
    success: bool
    message: str
    data_source: str  # 'data_loader', 'model', 'fallback'


# === БАЗОВЫЙ КЛАСС ===

class BaseUseCase:
    """Базовый класс для всех Use Cases с общей логикой"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _validate_session(self, session_id: str) -> bool:
        """Валидация session_id"""
        return bool(session_id and session_id.strip())
    
    def _handle_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Единая обработка ошибок"""
        error_msg = f"Ошибка в {context}: {str(error)}"
        self.logger.error(error_msg)
        return {
            'success': False,
            'error_message': error_msg,
            'parameters': [],
            'total_count': 0,
            'filtered_count': 0
        }
    
    def _convert_to_dict(self, param) -> Dict[str, Any]:
        """Универсальное преобразование параметра в словарь"""
        try:
            if isinstance(param, dict):
                return param
            elif hasattr(param, 'to_dict'):
                return param.to_dict()
            elif hasattr(param, '__dict__'):
                return {
                    'signal_code': getattr(param, 'signal_code', ''),
                    'description': getattr(param, 'description', ''),
                    'line': getattr(param, 'line', ''),
                    'wagon': getattr(param, 'wagon', ''),
                    'data_type': getattr(param, 'data_type', ''),
                    'signal_type': getattr(param, 'signal_type', ''),
                    'is_problematic': getattr(param, 'is_problematic', False)
                }
            else:
                return {'signal_code': str(param), 'description': str(param)}
        except Exception as e:
            self.logger.error(f"Ошибка преобразования параметра: {e}")
            return {'signal_code': 'ERROR', 'description': 'Ошибка преобразования'}


# === ОСНОВНЫЕ USE CASES ===

class FilterParametersUseCase(BaseUseCase):
    """Use Case для стандартной фильтрации параметров"""

    def __init__(self, parameter_repository=None, filtering_service=None, data_model=None):
        super().__init__()
        self.parameter_repository = parameter_repository
        self.filtering_service = filtering_service
        self.data_model = data_model

    def execute(self, request: FilterParametersRequest) -> FilterParametersResponse:
        """Выполнение стандартной фильтрации параметров"""
        start_time = time.time()
        
        try:
            if not self._validate_session(request.session_id):
                return FilterParametersResponse(
                    parameters=[],
                    total_count=0,
                    filtered_count=0,
                    execution_time_ms=0,
                    filter_type='standard',
                    success=False,
                    error_message="Неверный session_id"
                )

            # ПРИОРИТЕТНАЯ проверка: если changed_only=True, перенаправляем
            if request.changed_only:
                self.logger.info("🔥 Обнаружен приоритетный флаг changed_only, перенаправление")
                return self._redirect_to_changed_params(request, start_time)

            # Получаем все параметры
            all_parameters = self._get_all_parameters(request.session_id)
            
            if not all_parameters:
                return FilterParametersResponse(
                    parameters=[],
                    total_count=0,
                    filtered_count=0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    filter_type='standard',
                    success=True,
                    error_message="Нет данных для фильтрации"
                )

            # Применяем фильтрацию
            filtered_parameters = self._apply_standard_filters(all_parameters, request)
            
            # Преобразуем в словари
            parameter_dicts = [self._convert_to_dict(param) for param in filtered_parameters]
            
            execution_time = (time.time() - start_time) * 1000
            
            self.logger.info(f"✅ Стандартная фильтрация: {len(all_parameters)} -> {len(filtered_parameters)} параметров ({execution_time:.1f}ms)")

            return FilterParametersResponse(
                parameters=parameter_dicts,
                total_count=len(all_parameters),
                filtered_count=len(filtered_parameters),
                execution_time_ms=execution_time,
                filter_type='standard',
                success=True
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_response = self._handle_error(e, "стандартной фильтрации")
            error_response.update({
                'execution_time_ms': execution_time,
                'filter_type': 'standard'
            })
            return FilterParametersResponse(**error_response)

    def _redirect_to_changed_params(self, request: FilterParametersRequest, start_time: float) -> FilterParametersResponse:
        """Перенаправление на приоритетную фильтрацию изменяемых параметров"""
        try:
            # Создаем запрос для изменяемых параметров
            changed_request = FindChangedParametersRequest(
                session_id=request.session_id,
                from_time="",  # Будет получено из модели
                to_time="",    # Будет получено из модели
                include_problematic_params=request.include_problematic
            )
            
            # Используем FindChangedParametersUseCase
            changed_use_case = FindChangedParametersUseCase(self.data_model)
            changed_response = changed_use_case.execute(changed_request)
            
            # Преобразуем ответ
            execution_time = (time.time() - start_time) * 1000
            
            return FilterParametersResponse(
                parameters=changed_response.changed_parameters,
                total_count=changed_response.total_parameters,
                filtered_count=changed_response.changed_count,
                execution_time_ms=execution_time,
                filter_type='changed_only',
                success=changed_response.success,
                error_message=changed_response.error_message
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"Ошибка перенаправления на изменяемые параметры: {e}")
            
            return FilterParametersResponse(
                parameters=[],
                total_count=0,
                filtered_count=0,
                execution_time_ms=execution_time,
                filter_type='changed_only',
                success=False,
                error_message=f"Ошибка приоритетной фильтрации: {e}"
            )

    def _get_all_parameters(self, session_id: str) -> List[Any]:
        """Получение всех параметров из доступных источников"""
        try:
            # Приоритет 1: Репозиторий
            if self.parameter_repository and hasattr(self.parameter_repository, 'get_all_parameters'):
                params = self.parameter_repository.get_all_parameters()
                if params:
                    return params

            # Приоритет 2: Модель данных
            if self.data_model and hasattr(self.data_model, 'get_parameter_objects'):
                params = self.data_model.get_parameter_objects()
                if params:
                    return params

            # Приоритет 3: data_loader через модель
            if (self.data_model and 
                hasattr(self.data_model, 'data_loader') and 
                hasattr(self.data_model.data_loader, 'parameters')):
                return self.data_model.data_loader.parameters or []

            return []

        except Exception as e:
            self.logger.error(f"Ошибка получения параметров: {e}")
            return []

    def _apply_standard_filters(self, parameters: List[Any], request: FilterParametersRequest) -> List[Any]:
        """Применение стандартных фильтров"""
        try:
            # Если нет критериев фильтрации, возвращаем все
            if not request.filter_criteria:
                return parameters

            # Используем сервис фильтрации если доступен
            if self.filtering_service:
                return self.filtering_service.filter_parameters(parameters, request.filter_criteria)

            # Fallback - простая фильтрация
            return self._apply_simple_filters(parameters, request.filter_criteria)

        except Exception as e:
            self.logger.error(f"Ошибка применения фильтров: {e}")
            return parameters

    def _apply_simple_filters(self, parameters: List[Any], criteria: Dict[str, Any]) -> List[Any]:
        """Простая фильтрация без сервиса"""
        try:
            filtered = []
            
            for param in parameters:
                param_dict = self._convert_to_dict(param)
                
                # Фильтр по типам сигналов
                if criteria.get('signal_types'):
                    signal_type = param_dict.get('signal_type', '')
                    if signal_type not in criteria['signal_types']:
                        continue
                
                # Фильтр по линиям
                if criteria.get('lines'):
                    line = param_dict.get('line', '')
                    if line not in criteria['lines']:
                        continue
                
                # Фильтр по вагонам
                if criteria.get('wagons'):
                    wagon = param_dict.get('wagon', '')
                    if wagon not in criteria['wagons']:
                        continue
                
                # Фильтр по поиску
                if criteria.get('search_text'):
                    search_text = criteria['search_text'].lower()
                    signal_code = param_dict.get('signal_code', '').lower()
                    description = param_dict.get('description', '').lower()
                    if search_text not in signal_code and search_text not in description:
                        continue
                
                filtered.append(param)
            
            return filtered

        except Exception as e:
            self.logger.error(f"Ошибка простой фильтрации: {e}")
            return parameters


class FindChangedParametersUseCase(BaseUseCase):
    """ПРИОРИТЕТНЫЙ Use Case для поиска изменяемых параметров"""

    def __init__(self, data_model=None):
        super().__init__()
        self.data_model = data_model

    def execute(self, request: FindChangedParametersRequest) -> FindChangedParametersResponse:
        """ПРИОРИТЕТНОЕ выполнение поиска изменяемых параметров"""
        start_time = time.time()

        try:
            self.logger.info(f"🔥 ПРИОРИТЕТНЫЙ поиск изменяемых параметров: {request.from_time} - {request.to_time}")

            if not self._validate_session(request.session_id):
                return FindChangedParametersResponse(
                    changed_parameters=[],
                    total_parameters=0,
                    changed_count=0,
                    time_range={},
                    analysis_statistics={},
                    execution_time_ms=0,
                    success=False,
                    error_message="Неверный session_id"
                )

            # Получаем или устанавливаем временной диапазон
            time_range = self._setup_time_range(request)
            
            if not time_range['success']:
                return FindChangedParametersResponse(
                    changed_parameters=[],
                    total_parameters=0,
                    changed_count=0,
                    time_range=time_range,
                    analysis_statistics={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    success=False,
                    error_message=time_range.get('error', 'Ошибка установки временного диапазона')
                )

            # Ищем изменяемые параметры
            changed_params, all_params = self._find_changed_parameters(request)
            
            # Фильтруем по настройкам
            filtered_changed = self._filter_by_settings(changed_params, request)
            filtered_all = self._filter_by_settings(all_params, request)
            
            # Преобразуем в словари
            changed_dicts = [self._convert_to_dict(param) for param in filtered_changed]
            
            # Собираем статистику
            statistics = self._collect_statistics(filtered_changed, filtered_all, request)
            
            execution_time = (time.time() - start_time) * 1000
            
            self.logger.info(f"✅ ПРИОРИТЕТНЫЙ поиск завершен: {len(filtered_changed)} изменяемых из {len(filtered_all)} ({execution_time:.1f}ms)")

            return FindChangedParametersResponse(
                changed_parameters=changed_dicts,
                total_parameters=len(filtered_all),
                changed_count=len(filtered_changed),
                time_range=time_range,
                analysis_statistics=statistics,
                execution_time_ms=execution_time,
                success=True,
                priority_applied=True
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_response = self._handle_error(e, "приоритетного поиска изменяемых параметров")
            error_response.update({
                'time_range': {},
                'analysis_statistics': {},
                'execution_time_ms': execution_time,
                'priority_applied': False
            })
            return FindChangedParametersResponse(**error_response)

    def _setup_time_range(self, request: FindChangedParametersRequest) -> Dict[str, Any]:
        """Настройка временного диапазона"""
        try:
            if not self.data_model:
                return {'success': False, 'error': 'DataModel недоступна'}

            # Если время не указано, получаем из модели
            from_time = request.from_time
            to_time = request.to_time
            
            if not from_time or not to_time:
                if hasattr(self.data_model, 'get_time_range_fields'):
                    time_fields = self.data_model.get_time_range_fields()
                    if time_fields:
                        from_time = time_fields.get('from_time', '')
                        to_time = time_fields.get('to_time', '')

            if not from_time or not to_time:
                return {'success': False, 'error': 'Временной диапазон не определен'}

            # Устанавливаем пользовательский диапазон
            if hasattr(self.data_model, 'set_user_time_range'):
                range_set = self.data_model.set_user_time_range(from_time, to_time)
                if not range_set:
                    return {'success': False, 'error': 'Неверный временной диапазон'}

            return {
                'success': True,
                'from_time': from_time,
                'to_time': to_time,
                'threshold': request.threshold
            }

        except Exception as e:
            return {'success': False, 'error': f'Ошибка настройки времени: {e}'}

    def _find_changed_parameters(self, request: FindChangedParametersRequest) -> tuple:
        """Поиск изменяемых параметров"""
        try:
            if not self.data_model:
                return [], []

            # Получаем изменяемые параметры
            if hasattr(self.data_model, 'find_changed_parameters_in_range'):
                changed_params = self.data_model.find_changed_parameters_in_range(request.threshold)
            else:
                changed_params = []

            # Получаем все параметры
            if hasattr(self.data_model, 'get_parameter_objects'):
                all_params = self.data_model.get_parameter_objects()
            else:
                all_params = []

            return changed_params, all_params

        except Exception as e:
            self.logger.error(f"Ошибка поиска изменяемых параметров: {e}")
            return [], []

    def _filter_by_settings(self, parameters: List[Any], request: FindChangedParametersRequest) -> List[Any]:
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

    def _collect_statistics(self, changed_params: List[Any], all_params: List[Any], 
                          request: FindChangedParametersRequest) -> Dict[str, Any]:
        """Сбор статистики анализа"""
        try:
            statistics = {
                'filter_settings': {
                    'threshold': request.threshold,
                    'include_timestamp_params': request.include_timestamp_params,
                    'include_problematic_params': request.include_problematic_params
                },
                'counts': {
                    'total_parameters': len(all_params),
                    'changed_parameters': len(changed_params),
                    'change_percentage': (len(changed_params) / len(all_params) * 100) if all_params else 0
                }
            }

            # Дополнительная статистика из модели
            if self.data_model and hasattr(self.data_model, 'get_time_range_statistics'):
                time_stats = self.data_model.get_time_range_statistics()
                statistics['time_range_stats'] = time_stats

            # Детальный анализ
            if self.data_model and hasattr(self.data_model, 'analyze_parameter_changes_detailed'):
                detailed_analysis = self.data_model.analyze_parameter_changes_detailed(request.threshold)
                statistics['detailed_analysis'] = detailed_analysis

            return statistics

        except Exception as e:
            self.logger.error(f"Ошибка сбора статистики: {e}")
            return {'error': str(e)}


class TimeRangeInitUseCase(BaseUseCase):
    """Use Case для инициализации временного диапазона"""

    def __init__(self, data_model=None):
        super().__init__()
        self.data_model = data_model

    def execute(self, request: TimeRangeInitRequest) -> TimeRangeInitResponse:
        """Инициализация временного диапазона для UI"""
        try:
            if not self._validate_session(request.session_id):
                return TimeRangeInitResponse(
                    from_time='',
                    to_time='',
                    duration='',
                    total_records=0,
                    success=False,
                    message='Неверный session_id',
                    data_source='error'
                )

            # Получаем временные поля из модели
            time_fields, data_source = self._get_time_fields_with_source(request.force_refresh)

            if not time_fields or not time_fields.get('from_time') or not time_fields.get('to_time'):
                return TimeRangeInitResponse(
                    from_time='',
                    to_time='',
                    duration='',
                    total_records=0,
                    success=False,
                    message='Временной диапазон не инициализирован. Загрузите данные.',
                    data_source=data_source
                )

            self.logger.info(f"✅ Временной диапазон инициализирован из {data_source}: {time_fields['from_time']} - {time_fields['to_time']}")

            return TimeRangeInitResponse(
                from_time=time_fields['from_time'],
                to_time=time_fields['to_time'],
                duration=time_fields.get('duration', ''),
                total_records=int(time_fields.get('total_records', 0)),
                success=True,
                message=f'Временной диапазон успешно инициализирован из {data_source}',
                data_source=data_source
            )

        except Exception as e:
            self.logger.error(f"Ошибка инициализации временного диапазона: {e}")

            return TimeRangeInitResponse(
                from_time='',
                to_time='',
                duration='',
                total_records=0,
                success=False,
                message=f'Ошибка инициализации: {str(e)}',
                data_source='error'
            )

    def _get_time_fields_with_source(self, force_refresh: bool = False) -> tuple:
        """Получение временных полей с указанием источника"""
        try:
            if not self.data_model:
                return None, 'no_model'

            # Приоритет 1: Метод модели
            if hasattr(self.data_model, 'get_time_range_fields'):
                time_fields = self.data_model.get_time_range_fields()
                if time_fields and time_fields.get('from_time'):
                    return time_fields, 'model'

            # Приоритет 2: data_loader
            if (hasattr(self.data_model, 'data_loader') and 
                self.data_model.data_loader):
                
                data_loader = self.data_model.data_loader
                
                if (hasattr(data_loader, 'min_timestamp') and 
                    hasattr(data_loader, 'max_timestamp') and
                    data_loader.min_timestamp and data_loader.max_timestamp):
                    
                    time_fields = {
                        'from_time': data_loader.min_timestamp,
                        'to_time': data_loader.max_timestamp,
                        'duration': self._calculate_duration(
                            data_loader.min_timestamp, 
                            data_loader.max_timestamp
                        ),
                        'total_records': getattr(data_loader, 'records_count', 0)
                    }
                    return time_fields, 'data_loader'

            # Приоритет 3: Fallback
            return self._create_fallback_time_fields(), 'fallback'

        except Exception as e:
            self.logger.error(f"Ошибка получения временных полей: {e}")
            return None, 'error'

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

    def _create_fallback_time_fields(self) -> Dict[str, Any]:
        """Создание fallback временных полей"""
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return {
            'from_time': start.strftime('%Y-%m-%d %H:%M:%S'),
            'to_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': self._calculate_duration(
                start.strftime('%Y-%m-%d %H:%M:%S'),
                now.strftime('%Y-%m-%d %H:%M:%S')
            ),
            'total_records': 0
        }


# === ДОПОЛНИТЕЛЬНЫЕ USE CASES ===

class ResetTimeRangeUseCase(BaseUseCase):
    """Use Case для сброса временного диапазона к полному"""

    def __init__(self, data_model=None):
        super().__init__()
        self.data_model = data_model

    def execute(self, session_id: str) -> TimeRangeInitResponse:
        """Сброс временного диапазона к полному диапазону данных"""
        try:
            if not self._validate_session(session_id):
                return TimeRangeInitResponse(
                    from_time='',
                    to_time='',
                    duration='',
                    total_records=0,
                    success=False,
                    message='Неверный session_id',
                    data_source='error'
                )

            if not self.data_model:
                return TimeRangeInitResponse(
                    from_time='',
                    to_time='',
                    duration='',
                    total_records=0,
                    success=False,
                    message='DataModel недоступна',
                    data_source='no_model'
                )

            # Сбрасываем к полному диапазону
            if hasattr(self.data_model, 'reset_time_range_to_full'):
                self.data_model.reset_time_range_to_full()

            # Получаем обновленные поля
            if hasattr(self.data_model, 'get_time_range_fields'):
                time_fields = self.data_model.get_time_range_fields()
            else:
                time_fields = {}

            self.logger.info("✅ Временной диапазон сброшен к полному")

            return TimeRangeInitResponse(
                from_time=time_fields.get('from_time', ''),
                to_time=time_fields.get('to_time', ''),
                duration=time_fields.get('duration', ''),
                total_records=int(time_fields.get('total_records', 0)),
                success=True,
                message='Временной диапазон сброшен к полному диапазону данных',
                data_source='model'
            )

        except Exception as e:
            self.logger.error(f"Ошибка сброса временного диапазона: {e}")

            return TimeRangeInitResponse(
                from_time='',
                to_time='',
                duration='',
                total_records=0,
                success=False,
                message=f'Ошибка сброса: {str(e)}',
                data_source='error'
            )


class ValidateTimeRangeUseCase(BaseUseCase):
    """Use Case для валидации пользовательского временного диапазона"""

    def __init__(self, data_model=None):
        super().__init__()
        self.data_model = data_model

    def execute(self, from_time: str, to_time: str) -> Dict[str, Any]:
        """Валидация временного диапазона"""
        try:
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'statistics': {}
            }

            # Базовая валидация формата
            try:
                from_dt = datetime.strptime(from_time, '%Y-%m-%d %H:%M:%S')
                to_dt = datetime.strptime(to_time, '%Y-%m-%d %H:%M:%S')
                
                if from_dt >= to_dt:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append('Время начала должно быть раньше времени окончания')
                    
            except ValueError as e:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f'Неверный формат времени: {e}')
                return validation_result

            # Валидация через модель если доступна
            if self.data_model and hasattr(self.data_model, 'time_range_service'):
                try:
                    temp_success = self.data_model.time_range_service.set_user_time_range(from_time, to_time)
                    
                    if not temp_success:
                        validation_result['is_valid'] = False
                        validation_result['errors'].append('Диапазон не поддерживается моделью данных')
                        return validation_result

                    # Получаем статистику
                    if hasattr(self.data_model, 'get_time_range_statistics'):
                        stats = self.data_model.get_time_range_statistics()
                        validation_result['statistics'] = stats

                        # Предупреждения на основе статистики
                        if stats.get('coverage_percent', 0) < 1:
                            validation_result['warnings'].append('Выбранный диапазон покрывает менее 1% данных')

                        if stats.get('filtered_records', 0) == 0:
                            validation_result['warnings'].append('В выбранном диапазоне нет данных')

                except Exception as e:
                    validation_result['warnings'].append(f'Не удалось проверить через модель: {e}')

            self.logger.debug(f"Валидация диапазона {from_time} - {to_time}: {'успешна' if validation_result['is_valid'] else 'неуспешна'}")

            return validation_result

        except Exception as e:
            self.logger.error(f"Ошибка валидации временного диапазона: {e}")

            return {
                'is_valid': False,
                'errors': [f'Ошибка валидации: {str(e)}'],
                'warnings': [],
                'statistics': {}
            }


class GetParametersByTypeUseCase(BaseUseCase):
    """Use Case для получения параметров по типу (нормальные/проблемные)"""

    def __init__(self, data_model=None):
        super().__init__()
        self.data_model = data_model

    def execute(self, parameter_type: str = 'all', session_id: str = 'default') -> Dict[str, Any]:
        """Получение параметров по типу"""
        try:
            if not self._validate_session(session_id):
                return {
                    'parameters': [],
                    'total_count': 0,
                    'filtered_count': 0,
                    'parameter_type': parameter_type,
                    'statistics': {},
                    'success': False,
                    'error': 'Неверный session_id'
                }

            if not self.data_model:
                return {
                    'parameters': [],
                    'total_count': 0,
                    'filtered_count': 0,
                    'parameter_type': parameter_type,
                    'statistics': {},
                    'success': False,
                    'error': 'DataModel недоступна'
                }

            # Получаем все параметры
            if hasattr(self.data_model, 'get_parameter_objects'):
                all_params = self.data_model.get_parameter_objects()
            else:
                all_params = []

            # Фильтруем по типу
            if parameter_type == 'normal':
                filtered_params = [p for p in all_params if not getattr(p, 'is_problematic', False)]
            elif parameter_type == 'problematic':
                filtered_params = [p for p in all_params if getattr(p, 'is_problematic', False)]
            else:  # 'all'
                filtered_params = all_params

            # Преобразуем в словари
            parameter_dicts = [self._convert_to_dict(param) for param in filtered_params]

            # Статистика
            normal_count = sum(1 for p in all_params if not getattr(p, 'is_problematic', False))
            problematic_count = sum(1 for p in all_params if getattr(p, 'is_problematic', False))

            result = {
                'parameters': parameter_dicts,
                'total_count': len(all_params),
                'filtered_count': len(filtered_params),
                'parameter_type': parameter_type,
                'statistics': {
                    'normal_count': normal_count,
                    'problematic_count': problematic_count,
                    'total_count': len(all_params),
                    'normal_percentage': (normal_count / len(all_params) * 100) if all_params else 0,
                    'problematic_percentage': (problematic_count / len(all_params) * 100) if all_params else 0
                },
                'success': True
            }

            self.logger.info(f"✅ Получены параметры типа '{parameter_type}': {len(filtered_params)} из {len(all_params)}")

            return result

        except Exception as e:
            self.logger.error(f"Ошибка получения параметров по типу: {e}")
            return {
                'parameters': [],
                'total_count': 0,
                'filtered_count': 0,
                'parameter_type': parameter_type,
                'statistics': {},
                'success': False,
                'error': str(e)
            }
