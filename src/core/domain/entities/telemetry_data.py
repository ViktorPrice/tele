# src/core/domain/entities/telemetry_data.py - НОВЫЙ ФАЙЛ
"""
Сущность данных телеметрии
"""
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import pandas as pd

@dataclass
class TelemetryData:
    """Сущность данных телеметрии"""
    
    data: pd.DataFrame
    metadata: Dict[str, Any]
    timestamp_range: Tuple[datetime, datetime]
    source_file: Optional[str] = None
    
    def __post_init__(self):
        """Валидация после инициализации"""
        if self.data is None or self.data.empty:
            raise ValueError("Данные телеметрии не могут быть пустыми")
        
        if 'timestamp' not in self.data.columns:
            raise ValueError("Отсутствует столбец timestamp")
    
    @property
    def parameters_count(self) -> int:
        """Количество параметров (столбцов кроме timestamp)"""
        return len(self.data.columns) - 1
    
    @property
    def records_count(self) -> int:
        """Количество записей"""
        return len(self.data)
    
    @property
    def duration_seconds(self) -> float:
        """Длительность в секундах"""
        return (self.timestamp_range[1] - self.timestamp_range[0]).total_seconds()
    
    def get_parameter_columns(self) -> list:
        """Получение списка столбцов параметров"""
        return [col for col in self.data.columns if col != 'timestamp']
    
    def filter_by_time(self, start_time: datetime, end_time: datetime) -> 'TelemetryData':
        """Фильтрация по времени"""
        mask = (self.data['timestamp'] >= start_time) & (self.data['timestamp'] <= end_time)
        filtered_data = self.data[mask].copy()
        
        return TelemetryData(
            data=filtered_data,
            metadata=self.metadata.copy(),
            timestamp_range=(start_time, end_time),
            source_file=self.source_file
        )
