"""
Доменная сущность параметра телеметрии
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class DataType(Enum):
    """Типы данных параметров"""
    BOOLEAN = "B"
    BYTE = "BY"
    WORD = "W"
    DOUBLE_WORD = "DW"
    FLOAT = "F"
    WORD_FLOAT = "WF"

@dataclass
class Parameter:
    """Доменная сущность параметра"""
    
    signal_code: str
    full_column: str
    line: str
    description: str
    data_type: DataType
    signal_parts: List[str]
    wagon: Optional[str] = None
    plot: Optional[int] = None
    
    def __post_init__(self):
        """Валидация после создания"""
        if not self.signal_code:
            raise ValueError("Код сигнала не может быть пустым")
        
        if not self.full_column:
            raise ValueError("Полное имя столбца не может быть пустым")
    
    @classmethod
    def from_header(cls, header: str) -> 'Parameter':
        """Создание параметра из заголовка CSV"""
        if '::' not in header:
            raise ValueError(f"Неверный формат заголовка: {header}")
        
        parts = header.split('::')
        signal_code = parts[0]
        line_desc = parts[1].split('|')
        line = line_desc[0].strip()
        description = line_desc[1].strip() if len(line_desc) > 1 else ''
        
        # Парсинг кода сигнала
        data_type, signal_parts, wagon = cls._parse_signal_code(signal_code)
        
        return cls(
            signal_code=signal_code,
            full_column=header,
            line=line,
            description=description,
            data_type=data_type,
            signal_parts=signal_parts,
            wagon=wagon
        )
    
    @staticmethod
    def _parse_signal_code(signal_code: str) -> tuple[DataType, List[str], Optional[str]]:
        """Парсинг кода сигнала"""
        parts = signal_code.split('_')
        if not parts:
            return DataType.BOOLEAN, [], None
        
        # Определение типа данных
        try:
            data_type = DataType(parts[0])
        except ValueError:
            data_type = DataType.BOOLEAN
        
        remaining = parts[1:]
        
        # Поиск номера вагона
        wagon = None
        if remaining and remaining[-1].isdigit():
            num = int(remaining[-1])
            if 1 <= num <= 15:
                wagon = str(num)
                remaining = remaining[:-1]
        
        return data_type, remaining, wagon
    
    def matches_filter(self, filter_criteria: 'FilterCriteria') -> bool:
        """Проверка соответствия критериям фильтрации"""
        if filter_criteria.data_types and self.data_type not in filter_criteria.data_types:
            return False
        
        if filter_criteria.lines and self.line not in filter_criteria.lines:
            return False
        
        if filter_criteria.wagons and self.wagon not in filter_criteria.wagons:
            return False
        
        if filter_criteria.signal_parts:
            if not any(part in self.signal_parts for part in filter_criteria.signal_parts):
                return False
        
        return True
