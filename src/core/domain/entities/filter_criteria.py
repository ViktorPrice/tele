"""
Value Object для критериев фильтрации
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass(frozen=True)
class FilterCriteria:
    """Неизменяемый объект критериев фильтрации"""
    
    data_types: Optional[List[str]] = None
    lines: Optional[List[str]] = None
    wagons: Optional[List[str]] = None
    signal_parts: Optional[List[str]] = None
    changed_only: bool = False
    time_range: Optional[tuple[datetime, datetime]] = None
    search_text: Optional[str] = None
    
    def __post_init__(self):
        # Валидация временного диапазона
        if self.time_range and self.time_range[0] >= self.time_range[1]:
            raise ValueError("Время начала должно быть раньше времени окончания")
    
    def is_empty(self) -> bool:
        """Проверка на пустые критерии"""
        return not any([
            self.data_types,
            self.lines, 
            self.wagons,
            self.signal_parts,
            self.changed_only,
            self.search_text
        ])
    
    def has_time_filter(self) -> bool:
        """Есть ли фильтр по времени"""
        return self.time_range is not None
    
    @classmethod
    def create_empty(cls) -> 'FilterCriteria':
        """Создание пустых критериев"""
        return cls()
    
    @classmethod
    def create_for_changed_params(cls, start_time: datetime, end_time: datetime) -> 'FilterCriteria':
        """Создание критериев для изменяемых параметров"""
        return cls(
            changed_only=True,
            time_range=(start_time, end_time)
        )
