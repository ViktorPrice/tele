# src/core/application/dto/filter_dto.py - НОВЫЙ ФАЙЛ
"""
DTO для критериев фильтрации
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime


@dataclass
class FilterDTO:
    """DTO для критериев фильтрации параметров"""

    data_types: Optional[List[str]] = None
    lines: Optional[List[str]] = None
    wagons: Optional[List[str]] = None
    signal_parts: Optional[List[str]] = None
    changed_only: bool = False
    search_text: Optional[str] = None
    time_range: Optional[Tuple[datetime, datetime]] = None

    def __post_init__(self):
        """Инициализация пустых списков"""
        if self.data_types is None:
            self.data_types = []
        if self.lines is None:
            self.lines = []
        if self.wagons is None:
            self.wagons = []
        if self.signal_parts is None:
            self.signal_parts = []

    def is_empty(self) -> bool:
        """Проверка на пустые критерии"""
        return not any([
            self.data_types,
            self.lines,
            self.wagons,
            self.signal_parts,
            self.changed_only,
            self.search_text,
            self.time_range
        ])

    @classmethod
    def create_empty(cls) -> 'FilterDTO':
        """Создание пустого DTO"""
        return cls()

    @classmethod
    def create_for_changed_params(cls, start_time: datetime, end_time: datetime) -> 'FilterDTO':
        """Создание DTO для изменяемых параметров"""
        return cls(
            changed_only=True,
            time_range=(start_time, end_time)
        )
