# src/infrastructure/data/csv_loader.py - ИСПРАВЛЕННЫЕ ИМПОРТЫ
"""
Загрузчик CSV файлов с исправленными зависимостями
"""
import pandas as pd
import chardet
import logging
from pathlib import Path
from typing import Tuple, Dict, Optional, List, Any
from datetime import datetime
import hashlib
import json

from ...core.domain.entities.telemetry_data import TelemetryData
from ...core.repositories.data_repository import DataRepository

# ИСПРАВЛЕНО: Правильные импорты
try:
    from .parsers.csv_parser import CSVParser
    from .validators.data_validator import DataValidator
    from .processors.timestamp_processor import TimestampProcessor
except ImportError as e:
    # Fallback если модули отсутствуют
    logging.getLogger(__name__).warning(f"Импорт модулей: {e}")
    
    class CSVParser:
        def parse_csv(self, file_path: str, **kwargs):
            return pd.read_csv(file_path, **kwargs)
    
    class DataValidator:
        def validate_dataframe(self, df):
            from dataclasses import dataclass
            @dataclass
            class ValidationResult:
                is_valid: bool = True
                warnings: List = None
                errors: List = None
            return ValidationResult()
    
    class TimestampProcessor:
        def process_timestamps(self, df):
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        
        def get_time_range(self, df):
            if 'timestamp' in df.columns:
                return df['timestamp'].min(), df['timestamp'].max()
            return datetime.now(), datetime.now()

class CSVDataLoader:
    """Загрузчик CSV файлов с автоопределением параметров"""
    
    def __init__(self, cache_enabled: bool = True):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Компоненты обработки
        self.csv_parser = CSVParser()
        self.data_validator = DataValidator()
        self.timestamp_processor = TimestampProcessor()
        
        # Кэширование
        self.cache_enabled = cache_enabled
        self._detection_cache: Dict[str, Dict] = {}
        
        # Состояние для совместимости с legacy
        self.parameters: List[Dict[str, Any]] = []
        self.lines: set = set()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.data: Optional[pd.DataFrame] = None
        
        self.logger.info("CSVDataLoader инициализирован")
    
    def load_csv(self, file_path: str) -> TelemetryData:
        """ИСПРАВЛЕННАЯ загрузка CSV с полной обработкой"""
        try:
            self.logger.info(f"Загрузка CSV: {file_path}")
            
            # Проверка существования файла
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            
            # Получение параметров файла (с кэшированием)
            file_params = self._get_file_parameters(file_path)
            
            # Парсинг метаданных
            metadata = self._parse_metadata(file_path, file_params['encoding'])
            
            # Загрузка данных
            raw_data = self._load_raw_data(file_path, file_params)
            
            # Валидация данных
            validation_result = self.data_validator.validate_dataframe(raw_data)
            if not validation_result.is_valid:
                self.logger.warning(f"Данные содержат проблемы: {validation_result.warnings}")
            
            # Обработка временных меток
            processed_data = self.timestamp_processor.process_timestamps(raw_data)
            
            # Создание TelemetryData
            telemetry_data = self._create_telemetry_data(
                processed_data, metadata, file_path
            )
            
            # Сохранение для совместимости с legacy
            self._update_legacy_attributes(telemetry_data)
            
            self.logger.info(f"CSV успешно загружен: {len(processed_data)} строк")
            return telemetry_data
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV {file_path}: {e}")
            raise
    
    # ДОБАВЛЕН метод для совместимости
    def filter_by_time_range(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Фильтрация данных по временному диапазону"""
        if self.data is not None:
            mask = (self.data['timestamp'] >= start_time) & (self.data['timestamp'] <= end_time)
            return self.data[mask]
        return pd.DataFrame()
    
    # ДОБАВЛЕН метод для совместимости с legacy
    def filter_changed_params(self, start_time, end_time) -> List[Dict[str, Any]]:
        """Фильтрация изменяемых параметров для совместимости"""
        try:
            from datetime import datetime
            
            # Преобразование строк в datetime если необходимо
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            
            self.logger.info(f"Фильтрация изменяемых параметров в диапазоне {start_time} - {end_time}")
            
            if not hasattr(self, 'data') or self.data is None:
                self.logger.warning("Нет данных для фильтрации")
                return []
            
            # Фильтрация данных по временному диапазону
            time_mask = (self.data['timestamp'] >= start_time) & (self.data['timestamp'] <= end_time)
            filtered_data = self.data[time_mask]
            
            self.logger.info(f"Найдено {len(filtered_data)} строк данных в временном диапазоне")
            
            # Поиск изменяемых параметров
            changed_params = []
            exclude_columns = ['timestamp', 'TIMESTAMP', 'index']
            
            for column in self.data.columns:
                if column not in exclude_columns:
                    # Проверяем изменяемость параметра в диапазоне
                    column_data = filtered_data[column].dropna()
                    if len(column_data) > 1:
                        # Параметр считается изменяемым если есть различия в значениях
                        unique_values = column_data.nunique()
                        if unique_values > 1:
                            # Создаем информацию о параметре
                            param_info = self._parse_parameter_info(column)
                            if param_info:
                                changed_params.append(param_info)
            
            self.logger.info(f"Найдено {len(changed_params)} изменяемых параметров")
            return changed_params
            
        except Exception as e:
            self.logger.error(f"Ошибка фильтрации изменяемых параметров: {e}")
            return []
    
    def _get_file_parameters(self, file_path: str) -> Dict[str, Any]:
        """Получение параметров файла с кэшированием"""
        try:
            # Генерация ключа кэша
            cache_key = self._generate_cache_key(file_path)
            
            # Проверка кэша
            if self.cache_enabled and cache_key in self._detection_cache:
                self.logger.debug(f"Использование кэшированных параметров для {file_path}")
                return self._detection_cache[cache_key]
            
            # Определение параметров
            file_params = {
                'encoding': self._detect_encoding(file_path),
                'delimiter': ',',
                'skiprows': 0
            }
            
            # Определение разделителя и пропускаемых строк
            file_params['delimiter'] = self._detect_delimiter(
                file_path, file_params['encoding']
            )
            file_params['skiprows'] = self._detect_skiprows(
                file_path, file_params['encoding'], file_params['delimiter']
            )
            
            # Сохранение в кэш
            if self.cache_enabled:
                self._detection_cache[cache_key] = file_params
            
            return file_params
            
        except Exception as e:
            self.logger.error(f"Ошибка определения параметров файла: {e}")
            # Возвращаем параметры по умолчанию
            return {
                'encoding': 'utf-8',
                'delimiter': ',',
                'skiprows': 0
            }
    
    def _generate_cache_key(self, file_path: str) -> str:
        """Генерация ключа кэша на основе файла"""
        try:
            file_stat = Path(file_path).stat()
            key_data = f"{file_path}_{file_stat.st_size}_{file_stat.st_mtime}"
            return hashlib.md5(key_data.encode()).hexdigest()
        except Exception:
            return hashlib.md5(file_path.encode()).hexdigest()
    
    def _detect_encoding(self, file_path: str) -> str:
        """ОПТИМИЗИРОВАННОЕ определение кодировки"""
        try:
            # Читаем только первые 10KB для определения кодировки
            with open(file_path, 'rb') as file:
                raw_data = file.read(10240)
            
            if not raw_data:
                return 'utf-8'
            
            # Определение кодировки
            detection = chardet.detect(raw_data)
            encoding = detection.get('encoding', 'utf-8')
            confidence = detection.get('confidence', 0)
            
            # Проверка надежности определения
            if confidence < 0.7:
                self.logger.warning(f"Низкая уверенность в кодировке: {confidence}")
                # Пробуем стандартные кодировки
                for fallback_encoding in ['utf-8', 'windows-1251', 'cp1251']:
                    try:
                        with open(file_path, 'r', encoding=fallback_encoding) as f:
                            f.read(1024)  # Пробуем прочитать
                        encoding = fallback_encoding
                        break
                    except UnicodeDecodeError:
                        continue
            
            self.logger.debug(f"Определена кодировка: {encoding} (уверенность: {confidence})")
            return encoding
            
        except Exception as e:
            self.logger.error(f"Ошибка определения кодировки: {e}")
            return 'utf-8'
    
    def _detect_delimiter(self, file_path: str, encoding: str) -> str:
        """УЛУЧШЕННОЕ определение разделителя"""
        try:
            # Читаем первые несколько строк
            with open(file_path, 'r', encoding=encoding) as file:
                sample_lines = [file.readline() for _ in range(5)]
            
            # Кандидаты разделителей
            delimiters = [',', ';', '\t', '|']
            delimiter_scores = {}
            
            for delimiter in delimiters:
                scores = []
                for line in sample_lines:
                    if line.strip():
                        count = line.count(delimiter)
                        scores.append(count)
                
                if scores:
                    # Оценка: среднее количество + консистентность
                    avg_count = sum(scores) / len(scores)
                    consistency = 1.0 - (max(scores) - min(scores)) / (max(scores) + 1)
                    delimiter_scores[delimiter] = avg_count * consistency
            
            # Выбираем лучший разделитель
            if delimiter_scores:
                best_delimiter = max(delimiter_scores.items(), key=lambda x: x[1])[0]
                self.logger.debug(f"Определен разделитель: '{best_delimiter}'")
                return best_delimiter
            
            return ','
            
        except Exception as e:
            self.logger.error(f"Ошибка определения разделителя: {e}")
            return ','
    
    def _detect_skiprows(self, file_path: str, encoding: str, delimiter: str) -> int:
        """Определение количества пропускаемых строк"""
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                lines = [file.readline() for _ in range(10)]
            
            for i, line in enumerate(lines):
                if line.strip():
                    # Проверяем, похожа ли строка на заголовок данных
                    parts = line.split(delimiter)
                    if len(parts) > 1:
                        # Если большинство частей не числа, это заголовок
                        non_numeric = sum(1 for part in parts 
                                        if not self._is_numeric(part.strip()))
                        if non_numeric / len(parts) > 0.5:
                            return i  # Пропускаем строки до заголовка
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Ошибка определения skiprows: {e}")
            return 0
    
    def _is_numeric(self, value: str) -> bool:
        """Проверка является ли значение числовым"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _parse_metadata(self, file_path: str, encoding: str) -> Dict[str, Any]:
        """Парсинг метаданных из файла"""
        try:
            metadata = {
                'file_path': file_path,
                'file_size': Path(file_path).stat().st_size,
                'encoding': encoding,
                'creation_time': datetime.now(),
                'source': 'csv_loader'
            }
            
            # Попытка извлечь дополнительные метаданные из комментариев
            with open(file_path, 'r', encoding=encoding) as file:
                first_lines = [file.readline() for _ in range(5)]
            
            for line in first_lines:
                if line.startswith('#') or line.startswith('//'):
                    # Парсинг комментариев
                    comment = line.lstrip('#/').strip()
                    if ':' in comment:
                        key, value = comment.split(':', 1)
                        metadata[key.strip().lower()] = value.strip()
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга метаданных: {e}")
            return {'file_path': file_path, 'encoding': encoding}
    
    def _load_raw_data(self, file_path: str, file_params: Dict[str, Any]) -> pd.DataFrame:
        """Загрузка сырых данных"""
        try:
            # Загрузка с обработкой ошибок
            data = pd.read_csv(
                file_path,
                delimiter=file_params['delimiter'],
                encoding=file_params['encoding'],
                skiprows=file_params['skiprows'],
                low_memory=False,
                na_values=['', 'N/A', 'NULL', 'null', 'NaN'],
                keep_default_na=True
            )
            
            self.logger.info(f"Загружено {len(data)} строк, {len(data.columns)} столбцов")
            return data
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки данных: {e}")
            raise
    
    def _create_telemetry_data(self, data: pd.DataFrame, 
                             metadata: Dict[str, Any], 
                             file_path: str) -> TelemetryData:
        """Создание объекта TelemetryData"""
        try:
            # Определение временного диапазона
            timestamp_range = self.timestamp_processor.get_time_range(data)
            
            # Создание TelemetryData
            telemetry_data = TelemetryData(
                data=data,
                metadata=metadata,
                timestamp_range=timestamp_range,
                source_file=file_path
            )
            
            return telemetry_data
            
        except Exception as e:
            self.logger.error(f"Ошибка создания TelemetryData: {e}")
            raise
    
    def _update_legacy_attributes(self, telemetry_data: TelemetryData):
        """Обновление атрибутов для совместимости с legacy кодом"""
        try:
            self.data = telemetry_data.data
            self.start_time = telemetry_data.timestamp_range[0]
            self.end_time = telemetry_data.timestamp_range[1]
            
            # Извлечение параметров
            self.parameters = self._extract_parameters(telemetry_data.data)
            self.lines = self._extract_lines(self.parameters)
            
            self.logger.debug(f"Legacy атрибуты обновлены: {len(self.parameters)} параметров")
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления legacy атрибутов: {e}")
    
    def _extract_parameters(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Извлечение параметров из данных"""
        parameters = []
        exclude_columns = {'timestamp', 'TIMESTAMP', 'index', 'time'}
        
        for column in data.columns:
            if column.lower() not in exclude_columns:
                param_info = self._parse_parameter_info(column)
                if param_info:
                    parameters.append(param_info)
        
        return parameters
    
    def _parse_parameter_info(self, column_name: str) -> Optional[Dict[str, Any]]:
        """Парсинг информации о параметре"""
        try:
            if '::' in column_name:
                # Расширенный формат
                signal_code, metadata = column_name.split('::', 1)
                if '|' in metadata:
                    line, description = metadata.split('|', 1)
                else:
                    line, description = metadata, ''
            else:
                # Простой формат
                signal_code = column_name
                parts = column_name.split('_')
                signal_type = parts[0] if parts else 'Unknown'
                line = self._determine_line(signal_type)
                description = '_'.join(parts[1:]).replace('_', ' ').title() if len(parts) > 1 else ''
            
            return {
                'signal_code': signal_code,
                'full_column': column_name,
                'description': description.strip(),
                'line': line.strip(),
                'wagon': self._extract_wagon_number(signal_code),
                'signal_type': signal_code.split('_')[0] if '_' in signal_code else 'Unknown'
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга параметра {column_name}: {e}")
            return None
    
    def _determine_line(self, signal_type: str) -> str:
        """Определение линии по типу сигнала"""
        line_mapping = {
            'B': 'L_CAN_BLOK_CH',
            'BY': 'L_CAN_ICU_CH_A', 
            'W': 'L_TV_MAIN_CH_A',
            'DW': 'L_TV_MAIN_CH_B',
            'F': 'L_LCUP_CH_A',
            'WF': 'L_LCUP_CH_B'
        }
        return line_mapping.get(signal_type, 'UNKNOWN_LINE')
    
    def _extract_wagon_number(self, signal_code: str) -> str:
        """Извлечение номера вагона"""
        parts = signal_code.split('_')
        for part in reversed(parts):
            if part.isdigit():
                num = int(part)
                if 1 <= num <= 15:
                    return str(num)
        return '1'
    
    def _extract_lines(self, parameters: List[Dict[str, Any]]) -> set:
        """Извлечение уникальных линий"""
        return {param['line'] for param in parameters if param.get('line')}
    
    def clear_cache(self):
        """Очистка кэша определения параметров"""
        self._detection_cache.clear()
        self.logger.info("Кэш определения параметров очищен")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Статистика кэша"""
        return {
            'cache_size': len(self._detection_cache),
            'cache_enabled': self.cache_enabled
        }
