"""
Use Case для фильтрации параметров
"""
from typing import List
from dataclasses import dataclass
from ..dto.parameter_dto import ParameterDTO
from ..dto.filter_dto import FilterDTO
from ...domain.services.filtering_service import ParameterFilteringService
from ...domain.entities.filter_criteria import FilterCriteria
from ...domain.repositories.parameter_repository import ParameterRepository

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

class FilterParametersUseCase:
    """Use Case для фильтрации параметров"""
    
    def __init__(self, parameter_repository: ParameterRepository,
                 filtering_service: ParameterFilteringService):
        self.parameter_repository = parameter_repository
        self.filtering_service = filtering_service
    
    def execute(self, request: FilterParametersRequest) -> FilterParametersResponse:
        """Выполнение фильтрации параметров"""
        # Получаем все параметры сессии
        all_parameters = self.parameter_repository.get_by_session(request.session_id)
        
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
        
        return FilterParametersResponse(
            parameters=parameter_dtos,
            total_count=len(all_parameters),
            filtered_count=len(filtered_parameters)
        )
