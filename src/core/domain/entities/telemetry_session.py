"""
Основная доменная сущность сессии телеметрии
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

@dataclass
class TelemetrySession:
    """Доменная сущность сессии анализа телеметрии"""
    
    id: str
    file_path: str
    loaded_at: datetime
    metadata: Dict[str, str]
    parameters: List['Parameter']
    time_range: tuple[datetime, datetime]
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not self.parameters:
            self.parameters = []
    
    @classmethod
    def create_new(cls, file_path: str, metadata: Dict[str, str], 
                   parameters: List['Parameter'], time_range: tuple[datetime, datetime]) -> 'TelemetrySession':
        """Фабричный метод для создания новой сессии"""
        return cls(
            id=str(uuid.uuid4()),
            file_path=file_path,
            loaded_at=datetime.now(),
            metadata=metadata,
            parameters=parameters,
            time_range=time_range
        )
    
    def get_parameters_by_line(self, line: str) -> List['Parameter']:
        """Получение параметров по линии связи"""
        return [p for p in self.parameters if p.line == line]
    
    def get_parameters_by_type(self, data_type: str) -> List['Parameter']:
        """Получение параметров по типу данных"""
        return [p for p in self.parameters if p.data_type.value == data_type]
    
    def get_unique_lines(self) -> List[str]:
        """Получение уникальных линий связи"""
        return list(set(p.line for p in self.parameters))
    
    def get_parameter_count(self) -> int:
        """Количество параметров в сессии"""
        return len(self.parameters)
    
    def is_valid(self) -> bool:
        """Проверка валидности сессии"""
        return (
            bool(self.file_path) and
            bool(self.parameters) and
            self.time_range[0] < self.time_range[1]
        )
