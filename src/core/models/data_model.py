"""
Модель данных приложения (вынесена из main.py)
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..domain.entities.telemetry_data import TelemetryData
from ...infrastructure.data.csv_loader import CSVDataLoader

class DataModel:
    """Модель данных для новой архитектуры"""
    
    def __init__(self):
        self.data_loader = CSVDataLoader()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Кэшированные данные для производительности
        self._cached_parameters: Optional[List[Dict[str, Any]]] = None
        self._cached_lines: Optional[set] = None
        self._last_file_path: Optional[str] = None
        
        self.logger.info("DataModel (новая архитектура) инициализирована")
    
    def load_csv_file(self, file_path: str) -> bool:
        """Загрузка CSV через новую архитектуру с кэшированием"""
        try:
            # Проверяем кэш
            if self._last_file_path == file_path and self._cached_parameters:
                self.logger.info(f"Использование кэшированных данных для {file_path}")
                return True
            
            # Загружаем новые данные
            telemetry_data = self.data_loader.load_csv(file_path)
            
            # Обрабатываем данные
            self._process_telemetry_data(telemetry_data)
            
            # Обновляем кэш
            self._last_file_path = file_path
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки {file_path}: {e}")
            return False
    
    def _process_telemetry_data(self, telemetry_data: TelemetryData):
        """Обработка данных телеметрии с оптимизацией"""
        try:
            data = telemetry_data.data
            
            # Параллельная обработка столбцов
            parameters = []
            lines = set()
            
            exclude_columns = {'timestamp', 'TIMESTAMP', 'index'}
            
            for column in data.columns:
                if column not in exclude_columns:
                    param_info = self._parse_parameter_info_optimized(column)
                    if param_info:
                        parameters.append(param_info)
                        lines.add(param_info['line'])
            
            # Кэшируем результаты
            self._cached_parameters = parameters
            self._cached_lines = lines
            
            # Устанавливаем для совместимости
            self.data_loader.parameters = parameters
            self.data_loader.lines = lines
            self.data_loader.start_time = telemetry_data.timestamp_range[0]
            self.data_loader.end_time = telemetry_data.timestamp_range[1]
            
            self.logger.info(f"Обработано {len(parameters)} параметров, {len(lines)} линий")
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки данных телеметрии: {e}")
            raise
    
    def _parse_parameter_info_optimized(self, column_name: str) -> Optional[Dict[str, Any]]:
        """ОПТИМИЗИРОВАННЫЙ парсинг информации о параметре"""
        try:
            # Быстрая проверка формата
            if '::' in column_name:
                return self._parse_extended_format(column_name)
            else:
                return self._parse_simple_format(column_name)
                
        except Exception as e:
            self.logger.error(f"Ошибка парсинга параметра {column_name}: {e}")
            return None
    
    def _parse_extended_format(self, column_name: str) -> Dict[str, Any]:
        """Парсинг расширенного формата: 'B_SIGNAL_1::Line|Description'"""
        signal_code, metadata = column_name.split('::', 1)
        
        if '|' in metadata:
            line, description = metadata.split('|', 1)
        else:
            line, description = metadata, ''
        
        return self._create_parameter_dict(signal_code, column_name, description.strip(), line.strip())
    
    def _parse_simple_format(self, column_name: str) -> Dict[str, Any]:
        """Парсинг простого формата: 'B_SIGNAL_1'"""
        parts = column_name.split('_')
        signal_type = parts[0] if parts else 'Unknown'
        
        line = self._determine_line_fast(signal_type)
        description = '_'.join(parts[1:]).replace('_', ' ').title() if len(parts) > 1 else ''
        
        return self._create_parameter_dict(column_name, column_name, description, line)
    
    def _create_parameter_dict(self, signal_code: str, full_column: str, 
                             description: str, line: str) -> Dict[str, Any]:
        """Создание словаря параметра"""
        parts = signal_code.split('_')
        
        return {
            'signal_code': signal_code,
            'full_column': full_column,
            'description': description,
            'line': line,
            'wagon': self._extract_wagon_number_fast(signal_code),
            'signal_type': parts[0] if parts else 'Unknown'
        }
    
    def _determine_line_fast(self, signal_type: str) -> str:
        """БЫСТРОЕ определение линии по типу сигнала"""
        # Используем словарь для O(1) поиска
        line_mapping = {
            'B': 'L_CAN_BLOK_CH',
            'BY': 'L_CAN_ICU_CH_A', 
            'W': 'L_TV_MAIN_CH_A',
            'DW': 'L_TV_MAIN_CH_B',
            'F': 'L_LCUP_CH_A',
            'WF': 'L_LCUP_CH_B'
        }
        return line_mapping.get(signal_type, 'UNKNOWN_LINE')
    
    def _extract_wagon_number_fast(self, signal_code: str) -> str:
        """БЫСТРОЕ извлечение номера вагона"""
        # Ищем последнее число в строке
        parts = signal_code.split('_')
        for part in reversed(parts):
            if part.isdigit():
                num = int(part)
                if 1 <= num <= 15:
                    return str(num)
        return '1'
    
    # Методы для доступа к кэшированным данным
    def get_parameters(self) -> List[Dict[str, Any]]:
        """Получение параметров из кэша"""
        return self._cached_parameters or []
    
    def get_lines(self) -> List[str]:
        """Получение линий из кэша"""
        return list(self._cached_lines) if self._cached_lines else []
    
    def clear_cache(self):
        """Очистка кэша"""
        self._cached_parameters = None
        self._cached_lines = None
        self._last_file_path = None
        self.logger.info("Кэш данных очищен")