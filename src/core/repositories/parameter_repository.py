# src/core/repositories/parameter_repository.py - НОВЫЙ ФАЙЛ
"""
Репозиторий для работы с параметрами телеметрии
"""
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

class ParameterRepository(ABC):
    """Абстрактный репозиторий параметров"""
    
    @abstractmethod
    def get_all_parameters(self) -> List[Dict[str, Any]]:
        """Получение всех параметров"""
        pass
    
    @abstractmethod
    def get_parameters_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Получение параметров по критериям"""
        pass
    
    @abstractmethod
    def get_changed_parameters(self, start_time, end_time) -> List[Dict[str, Any]]:
        """Получение изменяемых параметров в диапазоне времени"""
        pass

class InMemoryParameterRepository(ParameterRepository):
    """Реализация репозитория в памяти"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_all_parameters(self) -> List[Dict[str, Any]]:
        """Получение всех параметров"""
        if hasattr(self.data_loader, 'parameters'):
            return self.data_loader.parameters or []
        return []
    
    def get_parameters_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Получение параметров по критериям"""
        all_params = self.get_all_parameters()
        
        # Простая фильтрация по критериям
        filtered = []
        for param in all_params:
            if self._matches_criteria(param, criteria):
                filtered.append(param)
        
        return filtered
    
    def get_changed_parameters(self, start_time, end_time) -> List[Dict[str, Any]]:
        """Получение изменяемых параметров"""
        if hasattr(self.data_loader, 'filter_changed_params'):
            return self.data_loader.filter_changed_params(start_time, end_time)
        
        # Fallback - возвращаем все параметры
        return self.get_all_parameters()
    
    def _matches_criteria(self, param: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Проверка соответствия параметра критериям"""
        for key, values in criteria.items():
            if not values:  # Пустой список означает "все"
                continue
            
            param_value = param.get(key, '')
            if param_value not in values:
                return False
        
        return True
