"""
Use Case для фильтрации параметров и поиска изменяемых параметров (ФИНАЛЬНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ)
"""
from typing import List
from dataclasses import dataclass
from datetime import datetime
import logging

from ..dto.parameter_dto import ParameterDTO
from ..dto.filter_dto import FilterDTO
from ...domain.services.filtering_service import ParameterFilteringService
from ...domain.entities.filter_criteria import FilterCriteria
from ...domain.repositories.parameter_repository import ParameterRepository
from ...models.data_model import DataModel

logger = logging.getLogger(__name__)

@dataclass
class FilterParametersRequest:
    """Запрос на фильтрацию параметров"""
    session_id: str
    filter_criteria: FilterDTO

@dataclass
class FilterParametersResponse:
    """Ответ с отфильтрованными параметрами"""
    parameters: List[ParameterDTO]
    total_count: int
    filtered_count: int

@dataclass
class FindChangedParametersRequest:
    """Запрос на поиск изменяемых параметров"""
    session_id: str
    from_time: str
    to_time: str
    threshold: float = 0.1
    include_timestamp_params: bool = False
    include_problematic_params: bool = True  # НОВОЕ: включать проблемные параметры

@dataclass
class FindChangedParametersResponse:
    """Ответ с изменяемыми параметрами"""
    changed_parameters: List[ParameterDTO]
    total_parameters: int
    changed_count: int
    time_range: dict
    analysis_statistics: dict
    execution_time_ms: float

@dataclass
class TimeRangeInitRequest:
    """Запрос на инициализацию временного диапазона"""
    session_id: str

@dataclass
class TimeRangeInitResponse:
    """Ответ с инициализированным временным диапазоном"""
    from_time: str
    to_time: str
    duration: str
    total_records: int
    success: bool
    message: str

class FilterParametersUseCase:
    """Use Case для фильтрации параметров (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""
    
    def __init__(self, parameter_repository: ParameterRepository,
                 filtering_service: ParameterFilteringService):
        self.parameter_repository = parameter_repository
        self.filtering_service = filtering_service
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def execute(self, request: FilterParametersRequest) -> FilterParametersResponse:
        """ИСПРАВЛЕННОЕ выполнение фильтрации параметров"""
        try:
            # Получаем все параметры сессии
            all_parameters = self.parameter_repository.get_by_session(request.session_id)
            
            # ИСПРАВЛЕНИЕ: Если критерии пустые, возвращаем все параметры
            if not request.filter_criteria or self._is_empty_criteria(request.filter_criteria):
                self.logger.info("Пустые критерии фильтрации, возвращаем все параметры")
                parameter_dtos = [ParameterDTO.from_entity(param) for param in all_parameters]
                
                return FilterParametersResponse(
                    parameters=parameter_dtos,
                    total_count=len(all_parameters),
                    filtered_count=len(all_parameters)
                )
            
            # Преобразуем DTO в доменный объект
            criteria = FilterCriteria(
                data_types=request.filter_criteria.data_types,
                lines=request.filter_criteria.lines,
                wagons=request.filter_criteria.wagons,
                signal_parts=request.filter_criteria.signal_parts,
                changed_only=request.filter_criteria.changed_only,
                time_range=request.filter_criteria.time_range,
                search_text=request.filter_criteria.search_text
            )
            
            # Применяем фильтрацию
            filtered_parameters = self.filtering_service.filter_parameters(all_parameters, criteria)
            
            # Преобразуем в DTO для ответа
            parameter_dtos = [
                ParameterDTO.from_entity(param) for param in filtered_parameters
            ]
            
            self.logger.info(f"Фильтрация завершена: {len(all_parameters)} -> {len(filtered_parameters)} параметров")
            
            return FilterParametersResponse(
                parameters=parameter_dtos,
                total_count=len(all_parameters),
                filtered_count=len(filtered_parameters)
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка фильтрации параметров: {e}")
            return FilterParametersResponse(
                parameters=[],
                total_count=0,
                filtered_count=0
            )
    
    def _is_empty_criteria(self, criteria: FilterDTO) -> bool:
        """Проверка на пустые критерии фильтрации"""
        try:
            return not any([
                criteria.data_types,
                criteria.lines,
                criteria.wagons,
                criteria.signal_parts,
                criteria.changed_only,
                criteria.search_text,
                criteria.time_range
            ])
        except Exception:
            return True

class FindChangedParametersUseCase:
    """Use Case для поиска изменяемых параметров в временном диапазоне (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""
    
    def __init__(self, data_model: DataModel):
        self.data_model = data_model
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def execute(self, request: FindChangedParametersRequest) -> FindChangedParametersResponse:
        """ИСПРАВЛЕННОЕ выполнение поиска изменяемых параметров"""
        import time
        start_time = time.time()
        
        try:
            self.logger.info(f"Начат поиск изменяемых параметров: {request.from_time} - {request.to_time}")
            
            # Устанавливаем пользовательский диапазон
            range_set = self.data_model.set_user_time_range(
                request.from_time, 
                request.to_time
            )
            
            if not range_set:
                raise ValueError("Неверный временной диапазон")
            
            # Ищем изменяемые параметры
            changed_params = self.data_model.find_changed_parameters_in_range(request.threshold)
            all_params = self.data_model.get_parameter_objects()
            
            # ИСПРАВЛЕНИЕ: Фильтруем параметры по настройкам
            filtered_changed_params = []
            filtered_all_params = []
            
            for param in changed_params:
                if not request.include_timestamp_params and param.is_timestamp_parameter():
                    continue
                if not request.include_problematic_params and param.is_problematic:
                    continue
                filtered_changed_params.append(param)
            
            for param in all_params:
                if not request.include_timestamp_params and param.is_timestamp_parameter():
                    continue
                if not request.include_problematic_params and param.is_problematic:
                    continue
                filtered_all_params.append(param)
            
            # Преобразуем в DTO
            changed_dtos = [ParameterDTO.from_entity(param) for param in filtered_changed_params]
            
            # Получаем статистику
            statistics = self.data_model.get_time_range_statistics()
            
            # Добавляем детальную статистику анализа
            detailed_analysis = self.data_model.analyze_parameter_changes_detailed(request.threshold)
            
            execution_time = (time.time() - start_time) * 1000
            
            self.logger.info(f"Поиск завершен: найдено {len(filtered_changed_params)} изменяемых параметров из {len(filtered_all_params)} ({execution_time:.1f}ms)")
            
            return FindChangedParametersResponse(
                changed_parameters=changed_dtos,
                total_parameters=len(filtered_all_params),
                changed_count=len(filtered_changed_params),
                time_range={
                    'from_time': request.from_time,
                    'to_time': request.to_time,
                    'threshold': request.threshold
                },
                analysis_statistics={
                    'time_range_stats': statistics,
                    'detailed_analysis': detailed_analysis,
                    'filter_settings': {
                        'threshold': request.threshold,
                        'include_timestamp_params': request.include_timestamp_params,
                        'include_problematic_params': request.include_problematic_params
                    }
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"Ошибка поиска изменяемых параметров: {e}")
            
            return FindChangedParametersResponse(
                changed_parameters=[],
                total_parameters=0,
                changed_count=0,
                time_range={
                    'from_time': request.from_time,
                    'to_time': request.to_time,
                    'error': str(e)
                },
                analysis_statistics={},
                execution_time_ms=execution_time
            )

class TimeRangeInitUseCase:
    """Use Case для инициализации временного диапазона из данных"""
    
    def __init__(self, data_model: DataModel):
        self.data_model = data_model
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def execute(self, request: TimeRangeInitRequest) -> TimeRangeInitResponse:
        """Инициализация временного диапазона для UI"""
        try:
            # Получаем поля времени из модели
            time_fields = self.data_model.get_time_range_fields()
            
            if not time_fields or not time_fields.get('from_time') or not time_fields.get('to_time'):
                return TimeRangeInitResponse(
                    from_time='',
                    to_time='',
                    duration='',
                    total_records=0,
                    success=False,
                    message='Временной диапазон не инициализирован. Загрузите данные.'
                )
            
            self.logger.info(f"Временной диапазон инициализирован: {time_fields['from_time']} - {time_fields['to_time']}")
            
            return TimeRangeInitResponse(
                from_time=time_fields['from_time'],
                to_time=time_fields['to_time'],
                duration=time_fields.get('duration', ''),
                total_records=int(time_fields.get('total_records', 0)),
                success=True,
                message='Временной диапазон успешно инициализирован'
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации временного диапазона: {e}")
            
            return TimeRangeInitResponse(
                from_time='',
                to_time='',
                duration='',
                total_records=0,
                success=False,
                message=f'Ошибка инициализации: {str(e)}'
            )

class ResetTimeRangeUseCase:
    """Use Case для сброса временного диапазона к полному"""
    
    def __init__(self, data_model: DataModel):
        self.data_model = data_model
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def execute(self, session_id: str) -> TimeRangeInitResponse:
        """Сброс временного диапазона к полному диапазону данных"""
        try:
            # Сбрасываем к полному диапазону
            self.data_model.reset_time_range_to_full()
            
            # Получаем обновленные поля
            time_fields = self.data_model.get_time_range_fields()
            
            self.logger.info("Временной диапазон сброшен к полному")
            
            return TimeRangeInitResponse(
                from_time=time_fields.get('from_time', ''),
                to_time=time_fields.get('to_time', ''),
                duration=time_fields.get('duration', ''),
                total_records=int(time_fields.get('total_records', 0)),
                success=True,
                message='Временной диапазон сброшен к полному диапазону данных'
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка сброса временного диапазона: {e}")
            
            return TimeRangeInitResponse(
                from_time='',
                to_time='',
                duration='',
                total_records=0,
                success=False,
                message=f'Ошибка сброса: {str(e)}'
            )

class ValidateTimeRangeUseCase:
    """Use Case для валидации пользовательского временного диапазона"""
    
    def __init__(self, data_model: DataModel):
        self.data_model = data_model
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def execute(self, from_time: str, to_time: str) -> dict:
        """Валидация временного диапазона"""
        try:
            # Проверяем формат времени
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'statistics': {}
            }
            
            # Пытаемся установить диапазон для проверки
            temp_success = self.data_model.time_range_service.set_user_time_range(from_time, to_time)
            
            if not temp_success:
                validation_result['is_valid'] = False
                validation_result['errors'].append('Неверный формат времени или диапазон')
                return validation_result
            
            # Получаем статистику для валидации
            stats = self.data_model.get_time_range_statistics()
            validation_result['statistics'] = stats
            
            # Проверяем покрытие данных
            if stats.get('coverage_percent', 0) < 1:
                validation_result['warnings'].append('Выбранный диапазон покрывает менее 1% данных')
            
            if stats.get('filtered_records', 0) == 0:
                validation_result['warnings'].append('В выбранном диапазоне нет данных')
            
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

# НОВЫЙ Use Case для работы с проблемными параметрами
class GetParametersByTypeUseCase:
    """Use Case для получения параметров по типу (нормальные/проблемные)"""
    
    def __init__(self, data_model: DataModel):
        self.data_model = data_model
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def execute(self, parameter_type: str = 'all') -> dict:
        """Получение параметров по типу"""
        try:
            all_params = self.data_model.get_parameter_objects()
            
            if parameter_type == 'normal':
                filtered_params = [p for p in all_params if not p.is_problematic]
            elif parameter_type == 'problematic':
                filtered_params = [p for p in all_params if p.is_problematic]
            else:  # 'all'
                filtered_params = all_params
            
            # Преобразуем в DTO
            parameter_dtos = [ParameterDTO.from_entity(param) for param in filtered_params]
            
            result = {
                'parameters': parameter_dtos,
                'total_count': len(all_params),
                'filtered_count': len(filtered_params),
                'parameter_type': parameter_type,
                'statistics': {
                    'normal_count': sum(1 for p in all_params if not p.is_problematic),
                    'problematic_count': sum(1 for p in all_params if p.is_problematic),
                    'total_count': len(all_params)
                }
            }
            
            self.logger.info(f"Получены параметры типа '{parameter_type}': {len(filtered_params)} из {len(all_params)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка получения параметров по типу: {e}")
            return {
                'parameters': [],
                'total_count': 0,
                'filtered_count': 0,
                'parameter_type': parameter_type,
                'statistics': {},
                'error': str(e)
            }
