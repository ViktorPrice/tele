"""
Сущность данных телеметрии с расширенной поддержкой timestamp (исправленная версия)
"""
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

@dataclass
class TelemetryData:
    """Сущность данных телеметрии с поддержкой timestamp парсинга (исправленная версия)"""
    
    data: pd.DataFrame
    metadata: Dict[str, Any]
    timestamp_range: Tuple[datetime, datetime]
    source_file: Optional[str] = None
    
    # Новые поля для timestamp функциональности
    timestamp_columns: Optional[Dict[str, str]] = None
    timestamp_wagon: Optional[str] = None
    raw_timestamp_data: Optional[pd.DataFrame] = None
    analysis_time_range: Optional[Tuple[datetime, datetime]] = None
    
    def __post_init__(self):
        """Валидация и инициализация timestamp функциональности"""
        if self.data is None or self.data.empty:
            raise ValueError("Данные телеметрии не могут быть пустыми")
        
        # Проверяем наличие timestamp столбца
        if 'timestamp' not in self.data.columns:
            logger.info("Отсутствует столбец timestamp, создание...")
            self._create_timestamp_column()
        else:
            logger.info("Столбец timestamp уже существует")
            self._update_timestamp_range()
        
        logger.info(f"TelemetryData инициализирована: {self.records_count} записей, {self.parameters_count} параметров")
    
    def _create_timestamp_column(self):
        """Создание столбца timestamp из компонентов времени или синтетически"""
        try:
            # Сначала пытаемся найти timestamp столбцы
            timestamp_cols, wagon = self.find_timestamp_columns()
            
            if timestamp_cols:
                self.timestamp_columns = timestamp_cols
                self.timestamp_wagon = wagon
                self._parse_timestamp_from_components(timestamp_cols)
                self._update_timestamp_range()
                logger.info(f"Создан timestamp из компонентов вагона {wagon}")
            else:
                # FALLBACK: Создаем синтетический timestamp
                logger.warning("Timestamp компоненты не найдены, создание синтетического...")
                self._create_synthetic_timestamp()
                
        except Exception as e:
            logger.error(f"Ошибка создания timestamp столбца: {e}")
            # Последний fallback - текущее время
            self._create_fallback_timestamp()
    
    def _create_synthetic_timestamp(self):
        """Создание синтетического timestamp на основе индекса строк"""
        try:
            # Базовое время - час назад от текущего момента
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=len(self.data))
            
            # Создаем timestamp с интервалом 1 секунда между записями
            timestamps = [start_time + timedelta(seconds=i) for i in range(len(self.data))]
            
            self.data['timestamp'] = pd.to_datetime(timestamps)
            
            # Обновляем временной диапазон
            self.timestamp_range = (timestamps[0], timestamps[-1])
            
            logger.info(f"Создан синтетический timestamp: {len(timestamps)} записей, диапазон {timestamps[0]} - {timestamps[-1]}")
            
        except Exception as e:
            logger.error(f"Ошибка создания синтетического timestamp: {e}")
            self._create_fallback_timestamp()
    
    def _create_fallback_timestamp(self):
        """Создание fallback timestamp (все записи с текущим временем + смещение)"""
        try:
            # Создаем уникальные временные метки с микросекундными интервалами
            base_time = datetime.now()
            timestamps = [base_time + timedelta(microseconds=i*1000) for i in range(len(self.data))]
            
            self.data['timestamp'] = pd.to_datetime(timestamps)
            self.timestamp_range = (timestamps[0], timestamps[-1])
            
            logger.warning(f"Создан fallback timestamp: {len(timestamps)} записей")
            
        except Exception as e:
            logger.error(f"Критическая ошибка создания timestamp: {e}")
            # Абсолютный fallback - одно время для всех
            current_time = datetime.now()
            self.data['timestamp'] = pd.to_datetime([current_time] * len(self.data))
            self.timestamp_range = (current_time, current_time)
    
    def find_timestamp_columns(self) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
        """Поиск столбцов временных компонентов"""
        prefix_map = {
            'year': 'W_TIMESTAMP_YEAR_',
            'month': 'BY_TIMESTAMP_MONTH_',
            'day': 'BY_TIMESTAMP_DAY_',
            'hour': 'BY_TIMESTAMP_HOUR_',
            'minute': 'BY_TIMESTAMP_MINUTE_',
            'second': 'BY_TIMESTAMP_SECOND_',
            'smallsecond': 'BY_TIMESTAMP_SMALLSECOND_'
        }
        
        # Проверяем вагоны от 1 до 15
        for wagon_number in range(1, 16):
            timestamp_cols = {}
            
            for component, prefix in prefix_map.items():
                target_prefix = f"{prefix}{wagon_number}"
                
                # Ищем столбец с этим префиксом
                for col in self.data.columns:
                    if col.startswith(target_prefix):
                        timestamp_cols[component] = col
                        break
            
            # Если найдены все 7 компонентов
            if len(timestamp_cols) == 7:
                logger.info(f"Найдены timestamp столбцы для вагона {wagon_number}: {list(timestamp_cols.keys())}")
                return timestamp_cols, str(wagon_number)
        
        logger.warning("Timestamp столбцы не найдены ни для одного вагона")
        return None, None
    
    def _parse_timestamp_from_components(self, timestamp_cols: Dict[str, str]):
        """Парсинг timestamp из компонентов"""
        def parse_row_timestamp(row):
            try:
                return datetime(
                    int(row[timestamp_cols['year']]),
                    int(row[timestamp_cols['month']]),
                    int(row[timestamp_cols['day']]),
                    int(row[timestamp_cols['hour']]),
                    int(row[timestamp_cols['minute']]),
                    int(row[timestamp_cols['second']]),
                    int(row[timestamp_cols['smallsecond']]) * 10000  # Конвертация в микросекунды
                )
            except (ValueError, KeyError, TypeError) as e:
                logger.debug(f"Ошибка парсинга timestamp в строке: {e}")
                return pd.NaT
        
        logger.info("Создание столбца timestamp из компонентов...")
        
        # Сохраняем исходные данные timestamp
        timestamp_columns_list = list(timestamp_cols.values())
        self.raw_timestamp_data = self.data[timestamp_columns_list].copy()
        
        # Создаем timestamp столбец
        self.data['timestamp'] = self.data.apply(parse_row_timestamp, axis=1)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'], errors='coerce')
        
        # Статистика
        valid_count = self.data['timestamp'].count()
        total_count = len(self.data)
        
        logger.info(f"Создан столбец timestamp: {valid_count}/{total_count} валидных записей")
        
        if valid_count == 0:
            logger.warning("Не удалось создать валидные временные метки, переход к синтетическому timestamp")
            self._create_synthetic_timestamp()
    
    def _update_timestamp_range(self):
        """Обновление временного диапазона на основе данных"""
        try:
            valid_timestamps = self.data['timestamp'].dropna()
            if not valid_timestamps.empty:
                start_time = valid_timestamps.min()
                end_time = valid_timestamps.max()
                
                # Проверяем, что диапазон корректный
                if start_time == end_time:
                    logger.warning("Все timestamp одинаковые, создание минимального диапазона")
                    end_time = start_time + timedelta(seconds=1)
                
                self.timestamp_range = (start_time, end_time)
                logger.debug(f"Обновлен временной диапазон: {start_time} - {end_time}")
            else:
                logger.warning("Нет валидных timestamp для обновления диапазона")
                
        except Exception as e:
            logger.error(f"Ошибка обновления временного диапазона: {e}")
    
    def get_time_range_for_analysis(self) -> Tuple[datetime, datetime]:
        """Получение временного диапазона для анализа (от/до)"""
        return self.timestamp_range
    
    def get_formatted_time_range(self, format_str: str = "%Y-%m-%d %H:%M:%S") -> Dict[str, str]:
        """Получение отформатированного временного диапазона"""
        start_time, end_time = self.timestamp_range
        duration = end_time - start_time
        
        return {
            'from_time': start_time.strftime(format_str),
            'to_time': end_time.strftime(format_str),
            'duration': str(duration)
        }
    
    def set_analysis_time_range(self, start_time: datetime, end_time: datetime) -> bool:
        """Установка пользовательского временного диапазона для анализа"""
        try:
            if start_time >= end_time:
                raise ValueError("Время начала должно быть раньше времени окончания")
            
            # Проверяем, что диапазон в пределах данных
            data_start, data_end = self.timestamp_range
            if start_time < data_start or end_time > data_end:
                logger.warning(f"Пользовательский диапазон выходит за пределы данных")
            
            # Сохраняем пользовательский диапазон
            self.analysis_time_range = (start_time, end_time)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка установки временного диапазона: {e}")
            return False
    
    def get_analysis_time_range(self) -> Tuple[datetime, datetime]:
        """Получение диапазона для анализа (пользовательский или полный)"""
        return getattr(self, 'analysis_time_range', self.timestamp_range)
    
    def get_timestamp_parameters(self) -> List[str]:
        """Получение списка timestamp параметров"""
        if not self.timestamp_columns:
            return []
        
        return list(self.timestamp_columns.values())
    
    def get_timestamp_statistics(self) -> Dict[str, Any]:
        """Статистика по timestamp данным"""
        if 'timestamp' not in self.data.columns:
            return {}
        
        timestamps = self.data['timestamp'].dropna()
        
        if timestamps.empty:
            return {'status': 'no_valid_timestamps'}
        
        return {
            'total_records': len(self.data),
            'valid_timestamps': len(timestamps),
            'invalid_timestamps': len(self.data) - len(timestamps),
            'start_time': timestamps.min(),
            'end_time': timestamps.max(),
            'duration_seconds': (timestamps.max() - timestamps.min()).total_seconds(),
            'timestamp_wagon': self.timestamp_wagon,
            'timestamp_columns': self.timestamp_columns,
            'is_synthetic': self.timestamp_wagon is None
        }
    
    def validate_timestamp_integrity(self) -> Dict[str, Any]:
        """Валидация целостности timestamp данных"""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'warnings': []
        }
        
        try:
            if 'timestamp' not in self.data.columns:
                validation_result['is_valid'] = False
                validation_result['issues'].append("Отсутствует столбец timestamp")
                return validation_result
            
            timestamps = self.data['timestamp']
            
            # Проверка на пустые значения
            null_count = timestamps.isnull().sum()
            if null_count > 0:
                validation_result['warnings'].append(f"Найдено {null_count} пустых timestamp значений")
            
            # Проверка на дубликаты
            duplicate_count = timestamps.duplicated().sum()
            if duplicate_count > 0:
                validation_result['warnings'].append(f"Найдено {duplicate_count} дублированных timestamp значений")
            
            # Проверка на монотонность
            valid_timestamps = timestamps.dropna()
            if not valid_timestamps.empty:
                if not valid_timestamps.is_monotonic_increasing:
                    validation_result['warnings'].append("Timestamp значения не монотонно возрастают")
                
                # Проверка на разумные значения
                min_time = valid_timestamps.min()
                max_time = valid_timestamps.max()
                
                if min_time.year < 2000 or max_time.year > 2030:
                    validation_result['warnings'].append(f"Подозрительный диапазон дат: {min_time.year} - {max_time.year}")
                
                # Проверка на одинаковые времена
                if min_time == max_time:
                    validation_result['warnings'].append("Все timestamp значения одинаковые")
            
            logger.info(f"Валидация timestamp: {'успешна' if validation_result['is_valid'] else 'неуспешна'}")
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['issues'].append(f"Ошибка валидации: {e}")
            logger.error(f"Ошибка валидации timestamp: {e}")
        
        return validation_result
    
    def repair_timestamp_gaps(self, method: str = 'interpolate') -> bool:
        """Восстановление пропусков в timestamp данных"""
        try:
            if 'timestamp' not in self.data.columns:
                return False
            
            original_null_count = self.data['timestamp'].isnull().sum()
            if original_null_count == 0:
                logger.info("Пропуски в timestamp не найдены")
                return True
            
            if method == 'interpolate':
                # Интерполяция временных значений
                self.data['timestamp'] = self.data['timestamp'].interpolate(method='time')
            elif method == 'forward_fill':
                # Заполнение вперед
                self.data['timestamp'] = self.data['timestamp'].fillna(method='ffill')
            elif method == 'backward_fill':
                # Заполнение назад
                self.data['timestamp'] = self.data['timestamp'].fillna(method='bfill')
            elif method == 'synthetic':
                # Создание синтетических значений
                self._fill_synthetic_timestamps()
            
            new_null_count = self.data['timestamp'].isnull().sum()
            repaired_count = original_null_count - new_null_count
            
            logger.info(f"Восстановлено {repaired_count} timestamp значений методом {method}")
            
            # Обновляем временной диапазон
            self._update_timestamp_range()
            
            return repaired_count > 0
            
        except Exception as e:
            logger.error(f"Ошибка восстановления timestamp: {e}")
            return False
    
    def _fill_synthetic_timestamps(self):
        """Заполнение синтетическими timestamp значениями"""
        try:
            # Находим первое и последнее валидные значения
            valid_mask = self.data['timestamp'].notna()
            
            if valid_mask.sum() == 0:
                # Нет валидных значений - создаем полностью синтетические
                self._create_synthetic_timestamp()
                return
            
            first_valid_idx = valid_mask.idxmax()
            last_valid_idx = valid_mask[::-1].idxmax()
            
            first_time = self.data.loc[first_valid_idx, 'timestamp']
            last_time = self.data.loc[last_valid_idx, 'timestamp']
            
            # Создаем равномерно распределенные значения
            total_records = len(self.data)
            time_diff = (last_time - first_time).total_seconds()
            
            if time_diff <= 0:
                time_diff = total_records  # 1 секунда на запись
            
            interval = time_diff / (total_records - 1)
            
            for i, idx in enumerate(self.data.index):
                if pd.isna(self.data.loc[idx, 'timestamp']):
                    synthetic_time = first_time + timedelta(seconds=i * interval)
                    self.data.loc[idx, 'timestamp'] = synthetic_time
            
            logger.info("Заполнены синтетические timestamp значения")
            
        except Exception as e:
            logger.error(f"Ошибка заполнения синтетических timestamp: {e}")
    
    # Существующие методы остаются без изменений
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
            source_file=self.source_file,
            timestamp_columns=self.timestamp_columns,
            timestamp_wagon=self.timestamp_wagon
        )
