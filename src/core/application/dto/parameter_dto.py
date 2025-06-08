"""
DTO для передачи данных параметров между слоями
"""
from dataclasses import dataclass
from typing import List, Optional
from ...domain.entities.parameter import Parameter

@dataclass
class ParameterDTO:
    """DTO для параметра телеметрии"""
    
    signal_code: str
    full_column: str
    line: str
    description: str
    data_type: str
    signal_parts: List[str]
    wagon: Optional[str] = None
    plot: Optional[int] = None
    
    @classmethod
    def from_entity(cls, parameter: Parameter) -> 'ParameterDTO':
        """Создание DTO из доменной сущности"""
        return cls(
            signal_code=parameter.signal_code,
            full_column=parameter.full_column,
            line=parameter.line,
            description=parameter.description,
            data_type=parameter.data_type.value,
            signal_parts=parameter.signal_parts,
            wagon=parameter.wagon,
            plot=parameter.plot
        )
    
    def to_entity(self) -> Parameter:
        """Преобразование DTO в доменную сущность"""
        from ...domain.entities.parameter import Parameter, DataType
        
        return Parameter(
            signal_code=self.signal_code,
            full_column=self.full_column,
            line=self.line,
            description=self.description,
            data_type=DataType(self.data_type),
            signal_parts=self.signal_parts,
            wagon=self.wagon,
            plot=self.plot
        )
