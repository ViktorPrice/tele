"""
Доменная сущность параметра телеметрии (исправленная версия для проблемных CSV)
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)

class DataType(Enum):
    """Типы данных параметров телеметрии"""
    BOOLEAN = "B"
    BYTE = "BY" 
    WORD = "W"
    DOUBLE_WORD = "DW"
    FLOAT = "F"
    WORD_FLOAT = "WF"
    
    @classmethod
    def from_string(cls, value: str) -> 'DataType':
        """Безопасное создание DataType из строки"""
        try:
            return cls(value.upper())
        except ValueError:
            # НЕ логируем warning для известных проблемных случаев
            return cls.BOOLEAN

@dataclass
class Parameter:
    """Доменная сущность параметра телеметрии (исправленная версия)"""
    
    signal_code: str
    full_column: str
    line: str
    description: str
    data_type: DataType
    signal_parts: List[str]
    wagon: Optional[str] = None
    plot: Optional[int] = None
    
    # Дополнительные поля для расширенной функциональности
    is_timestamp_related: bool = False
    component_type: Optional[str] = None
    hardware_type: Optional[str] = None
    is_problematic: bool = False  # НОВОЕ: флаг проблемных параметров
    
    def __post_init__(self):
        """Расширенная валидация после создания"""
        self._validate_required_fields()
        self._detect_problematic_parameters()
        
        # Валидируем только если не проблемный параметр
        if not self.is_problematic:
            self._validate_signal_code_format()
            self._validate_wagon_number()
            self._validate_line_format()
        
        self._detect_special_parameters()
        
        logger.debug(f"Создан параметр: {self.signal_code}")
    
    def _validate_required_fields(self):
        """Валидация обязательных полей"""
        if not self.signal_code or not isinstance(self.signal_code, str):
            raise ValueError("Код сигнала не может быть пустым")
        
        if not self.full_column or not isinstance(self.full_column, str):
            raise ValueError("Полное имя столбца не может быть пустым")
        
        if not self.line or not isinstance(self.line, str):
            raise ValueError("Линия связи не может быть пустой")
    
    def _detect_problematic_parameters(self):
        """Определение проблемных параметров"""
        problematic_patterns = [
            r'^Date:',           # Date: 2025-05-21
            r'^Unnamed:\s*\d+',  # Unnamed: 1, Unnamed: 2, etc.
            r'^\s*$',           # Пустые строки
            r'^[0-9]+$',        # Только цифры
            r'^index$',         # Индексные столбцы
            r'^timestamp$'      # Timestamp столбцы
        ]
        
        for pattern in problematic_patterns:
            if re.match(pattern, self.signal_code, re.IGNORECASE):
                self.is_problematic = True
                break
    
    def _validate_signal_code_format(self):
        """Улучшенная валидация формата кода сигнала (только для нормальных параметров)"""
        # Стандартная валидация только для нормальных кодов
        pattern = r'^[A-Z]+(_[A-Z0-9]+)*$'
        if not re.match(pattern, self.signal_code):
            logger.warning(f"Нестандартный формат кода сигнала: {self.signal_code}")
    
    def _validate_wagon_number(self):
        """Валидация номера вагона"""
        if self.wagon is not None:
            try:
                wagon_num = int(self.wagon)
                if not (1 <= wagon_num <= 15):
                    raise ValueError(f"Номер вагона должен быть от 1 до 15: {self.wagon}")
            except ValueError as e:
                if "invalid literal" not in str(e):
                    raise
                raise ValueError(f"Номер вагона должен быть числом: {self.wagon}")
    
    def _validate_line_format(self):
        """Валидация формата линии связи"""
        valid_line_prefixes = ['L_CAN_', 'L_TV_', 'L_LCUP_', 'L_', 'METADATA', 'UNKNOWN_LINE', 'NUMERIC_DATA']
        if not any(self.line.startswith(prefix) for prefix in valid_line_prefixes):
            logger.warning(f"Нестандартный формат линии: {self.line}")
    
    def _detect_special_parameters(self):
        """Определение специальных типов параметров"""
        # Определение timestamp параметров
        if 'TIMESTAMP' in self.signal_code.upper():
            self.is_timestamp_related = True
            logger.debug(f"Обнаружен timestamp параметр: {self.signal_code}")
        
        # Определение типа компонента
        self.component_type = self._extract_component_type()
        
        # Определение типа оборудования  
        self.hardware_type = self._extract_hardware_type()
    
    def _extract_component_type(self) -> Optional[str]:
        """Извлечение типа компонента из кода сигнала"""
        component_mapping = {
            'DOOR': 'DOOR_SYSTEM',
            'BRAKE': 'BRAKE_SYSTEM', 
            'HVAC': 'CLIMATE_SYSTEM',
            'TRACTION': 'TRACTION_SYSTEM',
            'AUX': 'AUXILIARY_SYSTEM',
            'SAFETY': 'SAFETY_SYSTEM',
            'TIMESTAMP': 'TIME_SYSTEM',
            'SPEED': 'TRACTION_SYSTEM',
            'TEMP': 'CLIMATE_SYSTEM',
            'PRESS': 'BRAKE_SYSTEM',
            'DATE': 'TIME_SYSTEM',
            'UNNAMED': 'UNKNOWN_SYSTEM',
            'NUMERIC': 'DATA_SYSTEM'
        }
        
        signal_upper = self.signal_code.upper()
        for keyword, component in component_mapping.items():
            if keyword in signal_upper:
                return component
        
        return 'UNKNOWN_SYSTEM'
    
    def _extract_hardware_type(self) -> Optional[str]:
        """Извлечение типа оборудования"""
        hardware_mapping = {
            'SENSOR': 'SENSOR',
            'RELAY': 'RELAY', 
            'CONTROLLER': 'CONTROLLER',
            'MOTOR': 'MOTOR',
            'VALVE': 'VALVE',
            'SWITCH': 'SWITCH',
            'INDICATOR': 'INDICATOR',
            'DATE': 'METADATA',
            'UNNAMED': 'UNKNOWN_DEVICE',
            'NUMERIC': 'NUMERIC_SENSOR'
        }
        
        signal_upper = self.signal_code.upper()
        for keyword, hardware in hardware_mapping.items():
            if keyword in signal_upper:
                return hardware
        
        # Определение по типу данных
        if self.data_type == DataType.BOOLEAN:
            return 'DIGITAL_DEVICE'
        elif self.data_type in [DataType.FLOAT, DataType.WORD_FLOAT]:
            return 'ANALOG_SENSOR'
        else:
            return 'DIGITAL_SENSOR'
    
    @classmethod
    def from_header(cls, header: str) -> 'Parameter':
        """Создание параметра из заголовка CSV с улучшенной обработкой ошибок"""
        try:
            if '::' not in header:
                return cls._create_from_simple_header(header)
            
            return cls._create_from_extended_header(header)
            
        except Exception as e:
            logger.error(f"Ошибка парсинга заголовка '{header}': {e}")
            # Возвращаем базовый параметр для продолжения работы
            return cls._create_fallback_parameter(header)
    
    @classmethod
    def _create_from_extended_header(cls, header: str) -> 'Parameter':
        """Создание из расширенного заголовка: 'CODE::LINE|DESCRIPTION'"""
        parts = header.split('::', 1)
        signal_code = parts[0].strip()
        
        if len(parts) < 2:
            raise ValueError("Отсутствуют метаданные после '::'")
        
        metadata = parts[1]
        if '|' in metadata:
            line, description = metadata.split('|', 1)
            line = line.strip()
            description = description.strip()
        else:
            line = metadata.strip()
            description = ''
        
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
    
    @classmethod
    def _create_from_simple_header(cls, header: str) -> 'Parameter':
        """Улучшенное создание из простого заголовка с обработкой проблемных случаев"""
        signal_code = header.strip()
        
        # Специальная обработка для проблемных заголовков
        if signal_code.startswith('Date:'):
            return cls._create_date_parameter(signal_code)
        elif signal_code.startswith('Unnamed:'):
            return cls._create_unnamed_parameter(signal_code)
        elif signal_code.isdigit():
            return cls._create_numeric_parameter(signal_code)
        elif signal_code.lower() in ['index', 'timestamp']:
            return cls._create_system_parameter(signal_code)
        
        # Стандартная обработка
        data_type, signal_parts, wagon = cls._parse_signal_code(signal_code)
        description = ' '.join(signal_parts).replace('_', ' ').title()
        line = cls._determine_line_by_data_type(data_type)
        
        return cls(
            signal_code=signal_code,
            full_column=header,
            line=line,
            description=description,
            data_type=data_type,
            signal_parts=signal_parts,
            wagon=wagon
        )
    
    @classmethod
    def _create_date_parameter(cls, signal_code: str) -> 'Parameter':
        """Создание параметра для Date столбца"""
        return cls(
            signal_code=signal_code,
            full_column=signal_code,
            line='METADATA',
            description='Дата записи данных',
            data_type=DataType.BOOLEAN,
            signal_parts=['DATE'],
            wagon=None,
            component_type='TIME_SYSTEM',
            hardware_type='METADATA',
            is_problematic=True
        )
    
    @classmethod
    def _create_unnamed_parameter(cls, signal_code: str) -> 'Parameter':
        """Создание параметра для Unnamed столбцов"""
        # Извлекаем номер из Unnamed: N
        import re
        match = re.search(r'(\d+)', signal_code)
        number = match.group(1) if match else '0'
        
        return cls(
            signal_code=signal_code,
            full_column=signal_code,
            line='DATA_CHANNEL',
            description=f'Канал данных {number}',
            data_type=DataType.WORD,  # Предполагаем числовые данные
            signal_parts=['CHANNEL', number],
            wagon='1',
            component_type='DATA_SYSTEM',
            hardware_type='DATA_CHANNEL',
            is_problematic=True
        )
    
    @classmethod
    def _create_numeric_parameter(cls, signal_code: str) -> 'Parameter':
        """Создание параметра для числовых столбцов"""
        return cls(
            signal_code=signal_code,
            full_column=signal_code,
            line='NUMERIC_DATA',
            description=f'Числовой параметр {signal_code}',
            data_type=DataType.WORD,
            signal_parts=['NUMERIC', signal_code],
            wagon='1',
            component_type='DATA_SYSTEM',
            hardware_type='NUMERIC_SENSOR',
            is_problematic=True
        )
    
    @classmethod
    def _create_system_parameter(cls, signal_code: str) -> 'Parameter':
        """Создание системного параметра"""
        return cls(
            signal_code=signal_code,
            full_column=signal_code,
            line='SYSTEM',
            description=f'Системный параметр {signal_code}',
            data_type=DataType.BOOLEAN,
            signal_parts=['SYSTEM', signal_code.upper()],
            wagon=None,
            component_type='SYSTEM',
            hardware_type='SYSTEM',
            is_problematic=True
        )
    
    @classmethod
    def _create_fallback_parameter(cls, header: str) -> 'Parameter':
        """Создание fallback параметра при ошибках парсинга"""
        return cls(
            signal_code=header,
            full_column=header,
            line='UNKNOWN_LINE',
            description='Ошибка парсинга заголовка',
            data_type=DataType.BOOLEAN,
            signal_parts=[header],
            wagon='1',
            is_problematic=True
        )
    
    @staticmethod
    def _parse_signal_code(signal_code: str) -> tuple[DataType, List[str], Optional[str]]:
        """Улучшенный парсинг кода сигнала с логированием"""
        try:
            parts = signal_code.split('_')
            if not parts:
                return DataType.BOOLEAN, [], None
            
            # Определение типа данных (БЕЗ логирования warning для проблемных)
            data_type = DataType.from_string(parts[0])
            
            remaining = parts[1:] if len(parts) > 1 else []
            
            # Поиск номера вагона (последняя цифра от 1 до 15)
            wagon = None
            if remaining and remaining[-1].isdigit():
                num = int(remaining[-1])
                if 1 <= num <= 15:
                    wagon = str(num)
                    remaining = remaining[:-1]
            
            return data_type, remaining, wagon
            
        except Exception as e:
            logger.error(f"Ошибка парсинга кода сигнала '{signal_code}': {e}")
            return DataType.BOOLEAN, [signal_code], None
    
    @staticmethod
    def _determine_line_by_data_type(data_type: DataType) -> str:
        """Определение линии связи по типу данных"""
        line_mapping = {
            DataType.BOOLEAN: 'L_CAN_BLOK_CH',
            DataType.BYTE: 'L_CAN_ICU_CH_A',
            DataType.WORD: 'L_TV_MAIN_CH_A', 
            DataType.DOUBLE_WORD: 'L_TV_MAIN_CH_B',
            DataType.FLOAT: 'L_LCUP_CH_A',
            DataType.WORD_FLOAT: 'L_LCUP_CH_B'
        }
        return line_mapping.get(data_type, 'UNKNOWN_LINE')
    
    def matches_filter(self, filter_criteria: 'FilterCriteria') -> bool:
        """Улучшенная проверка соответствия критериям фильтрации"""
        try:
            # Фильтр по типам данных
            if (filter_criteria.data_types and 
                self.data_type.value not in filter_criteria.data_types):
                return False
            
            # Фильтр по линиям связи
            if (filter_criteria.lines and 
                self.line not in filter_criteria.lines):
                return False
            
            # Фильтр по номерам вагонов
            if (filter_criteria.wagons and 
                self.wagon not in filter_criteria.wagons):
                return False
            
            # Фильтр по частям сигнала (точное пересечение)
            if filter_criteria.signal_parts:
                if not any(part.upper() in [sp.upper() for sp in self.signal_parts] 
                          for part in filter_criteria.signal_parts):
                    return False
            
            # Фильтр по тексту поиска
            if filter_criteria.search_text:
                search_text = filter_criteria.search_text.upper()
                searchable_text = f"{self.signal_code} {self.description} {self.line}".upper()
                if search_text not in searchable_text:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка фильтрации параметра {self.signal_code}: {e}")
            return False
    
    def is_timestamp_parameter(self) -> bool:
        """Проверка, является ли параметр временной меткой"""
        return self.is_timestamp_related
    
    def get_timestamp_component(self) -> Optional[str]:
        """Получение компонента временной метки (year, month, day, etc.)"""
        if not self.is_timestamp_parameter():
            return None
        
        timestamp_components = {
            'YEAR': 'year',
            'MONTH': 'month', 
            'DAY': 'day',
            'HOUR': 'hour',
            'MINUTE': 'minute',
            'SECOND': 'second',
            'SMALLSECOND': 'smallsecond'
        }
        
        signal_upper = self.signal_code.upper()
        for keyword, component in timestamp_components.items():
            if keyword in signal_upper:
                return component
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сериализации"""
        return {
            'signal_code': self.signal_code,
            'full_column': self.full_column,
            'line': self.line,
            'description': self.description,
            'data_type': self.data_type.value,
            'signal_parts': self.signal_parts,
            'wagon': self.wagon,
            'plot': self.plot,
            'is_timestamp_related': self.is_timestamp_related,
            'component_type': self.component_type,
            'hardware_type': self.hardware_type,
            'is_problematic': self.is_problematic
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Parameter':
        """Создание из словаря"""
        return cls(
            signal_code=data['signal_code'],
            full_column=data['full_column'],
            line=data['line'],
            description=data['description'],
            data_type=DataType(data['data_type']),
            signal_parts=data['signal_parts'],
            wagon=data.get('wagon'),
            plot=data.get('plot'),
            is_timestamp_related=data.get('is_timestamp_related', False),
            component_type=data.get('component_type'),
            hardware_type=data.get('hardware_type'),
            is_problematic=data.get('is_problematic', False)
        )
    
    def __str__(self) -> str:
        """Строковое представление"""
        return f"Parameter({self.signal_code}, {self.data_type.value}, wagon={self.wagon})"
    
    def __repr__(self) -> str:
        """Детальное представление для отладки"""
        return (f"Parameter(signal_code='{self.signal_code}', "
                f"data_type={self.data_type.value}, "
                f"line='{self.line}', "
                f"wagon={self.wagon}, "
                f"parts={self.signal_parts})")
