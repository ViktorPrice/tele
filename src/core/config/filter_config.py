"""
Конфигурация фильтров
"""
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class FilterConfig:
    """Конфигурация фильтров"""
    
    signal_types: List[str]
    wagon_numbers: List[str]
    component_types: List[str]
    hardware_types: List[str]
    
    @classmethod
    def get_default(cls) -> 'FilterConfig':
        """Конфигурация по умолчанию"""
        return cls(
            signal_types=['B', 'BY', 'W', 'DW', 'F', 'WF'],
            wagon_numbers=[str(i) for i in range(1, 16)],
            component_types=['DOOR', 'BRAKE', 'HVAC', 'TRACTION', 'AUX', 'SAFETY'],
            hardware_types=['SENSOR', 'RELAY', 'CONTROLLER', 'MOTOR', 'VALVE']
        )
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'FilterConfig':
        """Загрузка конфигурации из файла"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)
        except Exception:
            return cls.get_default()
    
    def save_to_file(self, file_path: str):
        """Сохранение конфигурации в файл"""
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)
