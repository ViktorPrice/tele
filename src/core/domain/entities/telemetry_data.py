# src/core/domain/entities/telemetry_data.py - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Доменная сущность для данных телеметрии с восстановленной логикой парсинга timestamp
"""
import pandas as pd
import logging
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, timedelta
import numpy as np


class TelemetryData:
    """ИСПРАВЛЕННАЯ доменная сущность для данных телеметрии с восстановленной логикой timestamp"""

    def __init__(self, data: pd.DataFrame, metadata: Dict[str, Any] = None, 
                 timestamp_range: Optional[Tuple[datetime, datetime]] = None,
                 source_file: str = ""):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Основные данные
        self._data = data
        self.metadata = metadata or {}
        self.timestamp_range = timestamp_range
        self.source_file = source_file
        
        # Дополнительные атрибуты
        self.columns_count = len(data.columns) if data is not None else 0
        self.timestamp_columns: Optional[Dict[str, str]] = None
        self.timestamp_wagon: Optional[str] = None
        self.raw_timestamp_data: Optional[pd.DataFrame] = None
        self.analysis_time_range: Optional[Tuple[datetime, datetime]] = None
        
        # Кэш для производительности
        self._statistics_cache: Dict[str, Any] = {}
        self._validation_cache: Dict[str, Any] = {}
        
        # ВОССТАНОВЛЕННАЯ логика: автоматическая инициализация timestamp
        self._initialize_timestamp()
        
        self.logger.info(f"TelemetryData создан: {self.records_count} записей, {self.columns_count} столбцов")

    def _initialize_timestamp(self):
        """ВОССТАНОВЛЕННАЯ инициализация timestamp функциональности"""
        try:
            if self._data is None or self._data.empty:
                self.logger.warning("Данные пусты, пропуск инициализации timestamp")
                return

            # Проверяем наличие timestamp столбца
            if 'timestamp' not in self._data.columns:
                self.logger.info("Отсутствует столбец timestamp, создание...")
                self._create_timestamp_column()
            else:
                self.logger.info("Столбец timestamp уже существует")
                self._update_timestamp_range()
                
        except Exception as e:
            self.logger.error(f"Ошибка инициализации timestamp: {e}")

    def _create_timestamp_column(self):
        """ВОССТАНОВЛЕННОЕ создание столбца timestamp из компонентов времени"""
        try:
            # Сначала пытаемся найти timestamp столбцы
            timestamp_cols, wagon = self.find_timestamp_columns()
            
            if timestamp_cols:
                self.timestamp_columns = timestamp_cols
                self.timestamp_wagon = wagon
                self._parse_timestamp_from_components(timestamp_cols)
                self._update_timestamp_range()
                self.logger.info(f"Создан timestamp из компонентов вагона {wagon}")
            else:
                # FALLBACK: Создаем синтетический timestamp
                self.logger.warning("Timestamp компоненты не найдены, создание синтетического...")
                self._create_synthetic_timestamp()
                
        except Exception as e:
            self.logger.error(f"Ошибка создания timestamp столбца: {e}")
            # Последний fallback - текущее время
            self._create_fallback_timestamp()

    def find_timestamp_columns(self) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
        """ВОССТАНОВЛЕННЫЙ поиск столбцов временных компонентов"""
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
                for col in self._data.columns:
                    if col.startswith(target_prefix):
                        timestamp_cols[component] = col
                        break
            
            # Если найдены все 7 компонентов
            if len(timestamp_cols) == 7:
                self.logger.info(f"Найдены timestamp столбцы для вагона {wagon_number}: {list(timestamp_cols.keys())}")
                return timestamp_cols, str(wagon_number)
        
        self.logger.warning("Timestamp столбцы не найдены ни для одного вагона")
        return None, None

    def _parse_timestamp_from_components(self, timestamp_cols: Dict[str, str]):
        """ВОССТАНОВЛЕННЫЙ парсинг timestamp из компонентов"""
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
                self.logger.debug(f"Ошибка парсинга timestamp в строке: {e}")
                return pd.NaT
        
        self.logger.info("Создание столбца timestamp из компонентов...")
        
        # Сохраняем исходные данные timestamp
        timestamp_columns_list = list(timestamp_cols.values())
        self.raw_timestamp_data = self._data[timestamp_columns_list].copy()
        
        # Создаем timestamp столбец
        self._data['timestamp'] = self._data.apply(parse_row_timestamp, axis=1)
        self._data['timestamp'] = pd.to_datetime(self._data['timestamp'], errors='coerce')
        
        # Статистика
        valid_count = self._data['timestamp'].count()
        total_count = len(self._data)
        
        self.logger.info(f"Создан столбец timestamp: {valid_count}/{total_count} валидных записей")
        
        if valid_count == 0:
            self.logger.warning("Не удалось создать валидные временные метки, переход к синтетическому timestamp")
            self._create_synthetic_timestamp()

    def _create_synthetic_timestamp(self):
        """ВОССТАНОВЛЕННОЕ создание синтетического timestamp на основе индекса строк"""
        try:
            # Базовое время - час назад от текущего момента
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=len(self._data))
            
            # Создаем timestamp с интервалом 1 секунда между записями
            timestamps = [start_time + timedelta(seconds=i) for i in range(len(self._data))]
            
            self._data['timestamp'] = pd.to_datetime(timestamps)
            
            # Обновляем временной диапазон
            self.timestamp_range = (timestamps[0], timestamps[-1])
            
            self.logger.info(f"Создан синтетический timestamp: {len(timestamps)} записей, диапазон {timestamps[0]} - {timestamps[-1]}")
            
        except Exception as e:
            self.logger.error(f"Ошибка создания синтетического timestamp: {e}")
            self._create_fallback_timestamp()

    def _create_fallback_timestamp(self):
        """ВОССТАНОВЛЕННОЕ создание fallback timestamp"""
        try:
            # Создаем уникальные временные метки с микросекундными интервалами
            base_time = datetime.now()
            timestamps = [base_time + timedelta(microseconds=i*1000) for i in range(len(self._data))]
            
            self._data['timestamp'] = pd.to_datetime(timestamps)
            self.timestamp_range = (timestamps[0], timestamps[-1])
            
            self.logger.warning(f"Создан fallback timestamp: {len(timestamps)} записей")
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка создания timestamp: {e}")
            # Абсолютный fallback - одно время для всех
            current_time = datetime.now()
            self._data['timestamp'] = pd.to_datetime([current_time] * len(self._data))
            self.timestamp_range = (current_time, current_time)

    def _update_timestamp_range(self):
        """ВОССТАНОВЛЕННОЕ обновление временного диапазона на основе данных"""
        try:
            if 'timestamp' not in self._data.columns:
                return
                
            valid_timestamps = self._data['timestamp'].dropna()
            if not valid_timestamps.empty:
                start_time = valid_timestamps.min()
                end_time = valid_timestamps.max()
                
                # Проверяем, что диапазон корректный
                if start_time == end_time:
                    self.logger.warning("Все timestamp одинаковые, создание минимального диапазона")
                    end_time = start_time + timedelta(seconds=1)
                
                self.timestamp_range = (start_time, end_time)
                self.logger.debug(f"Обновлен временной диапазон: {start_time} - {end_time}")
            else:
                self.logger.warning("Нет валидных timestamp для обновления диапазона")
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления временного диапазона: {e}")

    @property
    def data(self) -> pd.DataFrame:
        """Получение данных DataFrame"""
        return self._data

    @data.setter
    def data(self, value: pd.DataFrame):
        """Установка данных DataFrame с очисткой кэша"""
        self._data = value
        self.columns_count = len(value.columns) if value is not None else 0
        self._clear_cache()

    @property
    def records_count(self) -> int:
        """ИСПРАВЛЕНО: Только getter для records_count (вычисляемое свойство)"""
        return len(self._data) if self._data is not None else 0

    @property
    def parameters_count(self) -> int:
        """Количество параметров (столбцов кроме timestamp)"""
        return len(self._data.columns) - 1 if self._data is not None else 0

    @property
    def duration_seconds(self) -> float:
        """Длительность в секундах"""
        if self.timestamp_range:
            return (self.timestamp_range[1] - self.timestamp_range[0]).total_seconds()
        return 0.0

    def get_time_range_for_analysis(self) -> Tuple[datetime, datetime]:
        """ВОССТАНОВЛЕННОЕ получение временного диапазона для анализа"""
        return self.timestamp_range or (datetime.now(), datetime.now())

    def get_formatted_time_range(self, format_str: str = "%Y-%m-%d %H:%M:%S") -> Dict[str, str]:
        """ВОССТАНОВЛЕННОЕ получение отформатированного временного диапазона"""
        if not self.timestamp_range:
            return {
                'from_time': '',
                'to_time': '',
                'duration': ''
            }
            
        start_time, end_time = self.timestamp_range
        duration = end_time - start_time
        
        return {
            'from_time': start_time.strftime(format_str),
            'to_time': end_time.strftime(format_str),
            'duration': self._format_duration(duration)
        }

    def set_analysis_time_range(self, start_time: datetime, end_time: datetime) -> bool:
        """ВОССТАНОВЛЕННАЯ установка пользовательского временного диапазона для анализа"""
        try:
            if start_time >= end_time:
                raise ValueError("Время начала должно быть раньше времени окончания")
            
            # Проверяем, что диапазон в пределах данных
            if self.timestamp_range:
                data_start, data_end = self.timestamp_range
                if start_time < data_start or end_time > data_end:
                    self.logger.warning(f"Пользовательский диапазон выходит за пределы данных")
            
            # Сохраняем пользовательский диапазон
            self.analysis_time_range = (start_time, end_time)
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка установки временного диапазона: {e}")
            return False

    def get_analysis_time_range(self) -> Tuple[datetime, datetime]:
        """ВОССТАНОВЛЕННОЕ получение диапазона для анализа"""
        return getattr(self, 'analysis_time_range', None) or self.timestamp_range or (datetime.now(), datetime.now())

    def get_timestamp_parameters(self) -> List[str]:
        """ВОССТАНОВЛЕННОЕ получение списка timestamp параметров"""
        if not self.timestamp_columns:
            return []
        
        return list(self.timestamp_columns.values())

    def get_parameter_columns(self) -> list:
        """Получение списка столбцов параметров"""
        if self._data is None:
            return []
        return [col for col in self._data.columns if col != 'timestamp']

    def get_timestamp_statistics(self) -> Dict[str, Any]:
        """ВОССТАНОВЛЕННАЯ статистика по timestamp данным"""
        try:
            cache_key = 'timestamp_statistics'
            if cache_key in self._statistics_cache:
                return self._statistics_cache[cache_key]

            if 'timestamp' not in self._data.columns:
                return {'status': 'no_timestamp_column'}
            
            timestamps = self._data['timestamp'].dropna()
            
            if timestamps.empty:
                return {'status': 'no_valid_timestamps'}
            
            stats = {
                'total_records': len(self._data),
                'valid_timestamps': len(timestamps),
                'invalid_timestamps': len(self._data) - len(timestamps),
                'start_time': timestamps.min(),
                'end_time': timestamps.max(),
                'duration_seconds': (timestamps.max() - timestamps.min()).total_seconds(),
                'timestamp_wagon': self.timestamp_wagon,
                'timestamp_columns': self.timestamp_columns,
                'is_synthetic': self.timestamp_wagon is None,
                'has_timestamp_columns': bool(self.timestamp_columns),
                'timestamp_range': self.timestamp_range,
                'columns_count': len(self.timestamp_columns) if self.timestamp_columns else 0
            }

            if self.timestamp_range:
                duration = self.timestamp_range[1] - self.timestamp_range[0]
                stats.update({
                    'duration_formatted': self._format_duration(duration),
                    'start_time_iso': self.timestamp_range[0].isoformat(),
                    'end_time_iso': self.timestamp_range[1].isoformat()
                })

            # Кэшируем результат
            self._statistics_cache[cache_key] = stats
            return stats

        except Exception as e:
            self.logger.error(f"Ошибка получения timestamp статистики: {e}")
            return {'error': str(e)}

    def validate_timestamp_integrity(self) -> Dict[str, Any]:
        """ВОССТАНОВЛЕННАЯ валидация целостности timestamp данных"""
        try:
            cache_key = 'timestamp_validation'
            if cache_key in self._validation_cache:
                return self._validation_cache[cache_key]

            validation_result = {
                'is_valid': True,
                'issues': [],
                'warnings': [],
                'statistics': {}
            }

            if 'timestamp' not in self._data.columns:
                validation_result['is_valid'] = False
                validation_result['issues'].append("Отсутствует столбец timestamp")
                return validation_result
            
            timestamps = self._data['timestamp']
            
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

            # Проверяем наличие timestamp столбцов
            if not self.timestamp_columns:
                validation_result['warnings'].append('Отсутствуют исходные timestamp столбцы')
            else:
                # Проверяем полноту timestamp компонентов
                required_components = {'year', 'month', 'day', 'hour', 'minute', 'second'}
                available_components = set(self.timestamp_columns.keys())
                missing_components = required_components - available_components

                if missing_components:
                    validation_result['warnings'].append(f'Отсутствуют компоненты: {missing_components}')

                # Проверяем данные в timestamp столбцах
                if self._data is not None:
                    timestamp_validation = self._validate_timestamp_data()
                    validation_result['statistics'].update(timestamp_validation)

            # Кэшируем результат
            self._validation_cache[cache_key] = validation_result
            return validation_result

        except Exception as e:
            self.logger.error(f"Ошибка валидации timestamp: {e}")
            return {
                'is_valid': False,
                'issues': [str(e)],
                'warnings': [],
                'statistics': {}
            }

    def _validate_timestamp_data(self) -> Dict[str, Any]:
        """Внутренняя валидация timestamp данных"""
        try:
            stats = {
                'total_records': self.records_count,
                'valid_timestamps': 0,
                'invalid_timestamps': 0,
                'gaps_detected': 0
            }

            if not self.timestamp_columns or not self._data:
                return stats

            # Проверяем каждую строку timestamp
            for index, row in self._data.iterrows():
                try:
                    # Пытаемся создать datetime из компонентов
                    timestamp_components = {}
                    for component, column in self.timestamp_columns.items():
                        if column in self._data.columns:
                            timestamp_components[component] = int(row[column])

                    if len(timestamp_components) >= 6:  # year, month, day, hour, minute, second
                        datetime(
                            year=timestamp_components.get('year', 2000),
                            month=timestamp_components.get('month', 1),
                            day=timestamp_components.get('day', 1),
                            hour=timestamp_components.get('hour', 0),
                            minute=timestamp_components.get('minute', 0),
                            second=timestamp_components.get('second', 0)
                        )
                        stats['valid_timestamps'] += 1
                    else:
                        stats['invalid_timestamps'] += 1

                except (ValueError, TypeError):
                    stats['invalid_timestamps'] += 1

            return stats

        except Exception as e:
            self.logger.error(f"Ошибка валидации timestamp данных: {e}")
            return {'error': str(e)}

    def repair_timestamp_gaps(self, method: str = 'interpolate') -> bool:
        """Восстановление пропусков в timestamp данных"""
        try:
            if not self.timestamp_columns or not self._data:
                self.logger.warning("Нет timestamp данных для восстановления")
                return False

            self.logger.info(f"Начало восстановления timestamp методом: {method}")

            if method == 'interpolate':
                return self._interpolate_timestamp_gaps()
            elif method == 'forward_fill':
                return self._forward_fill_timestamp_gaps()
            elif method == 'sequence':
                return self._sequence_fill_timestamp_gaps()
            else:
                self.logger.error(f"Неизвестный метод восстановления: {method}")
                return False

        except Exception as e:
            self.logger.error(f"Ошибка восстановления timestamp: {e}")
            return False

    def _interpolate_timestamp_gaps(self) -> bool:
        """Интерполяция пропусков timestamp"""
        try:
            # Создаем timestamp столбец из компонентов
            if not self._create_timestamp_column_from_existing():
                return False

            # Интерполируем пропуски
            if 'timestamp' in self._data.columns:
                self._data['timestamp'] = pd.to_datetime(self._data['timestamp'], errors='coerce')
                self._data['timestamp'] = self._data['timestamp'].interpolate(method='time')
                
                # Обновляем компоненты из интерполированного timestamp
                self._update_timestamp_components()
                
                self.logger.info("Timestamp пропуски интерполированы")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Ошибка интерполяции timestamp: {e}")
            return False

    def _create_timestamp_column_from_existing(self) -> bool:
        """Создание timestamp столбца из существующих компонентов"""
        try:
            if not self.timestamp_columns:
                return False

            timestamps = []
            for index, row in self._data.iterrows():
                try:
                    timestamp_components = {}
                    for component, column in self.timestamp_columns.items():
                        if column in self._data.columns:
                            timestamp_components[component] = int(row[column])

                    timestamp = datetime(
                        year=timestamp_components.get('year', 2000),
                        month=timestamp_components.get('month', 1),
                        day=timestamp_components.get('day', 1),
                        hour=timestamp_components.get('hour', 0),
                        minute=timestamp_components.get('minute', 0),
                        second=timestamp_components.get('second', 0)
                    )
                    timestamps.append(timestamp)

                except (ValueError, TypeError):
                    timestamps.append(pd.NaT)

            self._data['timestamp'] = timestamps
            return True

        except Exception as e:
            self.logger.error(f"Ошибка создания timestamp столбца: {e}")
            return False

    def _forward_fill_timestamp_gaps(self) -> bool:
        """Заполнение пропусков методом forward fill"""
        try:
            for component, column in self.timestamp_columns.items():
                if column in self._data.columns:
                    self._data[column] = self._data[column].fillna(method='ffill')

            self.logger.info("Timestamp пропуски заполнены методом forward fill")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка forward fill timestamp: {e}")
            return False

    def _sequence_fill_timestamp_gaps(self) -> bool:
        """Заполнение пропусков последовательными значениями"""
        try:
            # Определяем период дискретизации
            sampling_period_ms = self.metadata.get('sampling_period_ms', 100)
            
            if self.timestamp_range:
                start_time = self.timestamp_range[0]
                
                # Создаем последовательность timestamp
                timestamps = []
                for i in range(self.records_count):
                    timestamp = start_time + timedelta(milliseconds=i * sampling_period_ms)
                    timestamps.append(timestamp)

                # Обновляем компоненты timestamp
                for i, timestamp in enumerate(timestamps):
                    if i < len(self._data):
                        for component, column in self.timestamp_columns.items():
                            if column in self._data.columns:
                                if component == 'year':
                                    self._data.at[i, column] = timestamp.year
                                elif component == 'month':
                                    self._data.at[i, column] = timestamp.month
                                elif component == 'day':
                                    self._data.at[i, column] = timestamp.day
                                elif component == 'hour':
                                    self._data.at[i, column] = timestamp.hour
                                elif component == 'minute':
                                    self._data.at[i, column] = timestamp.minute
                                elif component == 'second':
                                    self._data.at[i, column] = timestamp.second

                self.logger.info("Timestamp пропуски заполнены последовательными значениями")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Ошибка sequence fill timestamp: {e}")
            return False

    def _update_timestamp_components(self):
        """Обновление компонентов timestamp из timestamp столбца"""
        try:
            if 'timestamp' not in self._data.columns:
                return

            for index, row in self._data.iterrows():
                timestamp = row['timestamp']
                if pd.notna(timestamp):
                    for component, column in self.timestamp_columns.items():
                        if column in self._data.columns:
                            if component == 'year':
                                self._data.at[index, column] = timestamp.year
                            elif component == 'month':
                                self._data.at[index, column] = timestamp.month
                            elif component == 'day':
                                self._data.at[index, column] = timestamp.day
                            elif component == 'hour':
                                self._data.at[index, column] = timestamp.hour
                            elif component == 'minute':
                                self._data.at[index, column] = timestamp.minute
                            elif component == 'second':
                                self._data.at[index, column] = timestamp.second

        except Exception as e:
            self.logger.error(f"Ошибка обновления timestamp компонентов: {e}")

    def filter_by_time(self, start_time: datetime, end_time: datetime) -> Optional['TelemetryData']:
        """Фильтрация данных по временному диапазону"""
        try:
            if not self._data or 'timestamp' not in self._data.columns:
                # Пытаемся создать timestamp столбец
                if not self._create_timestamp_column_from_existing():
                    self.logger.warning("Невозможно фильтровать по времени - нет timestamp данных")
                    return None

            # Фильтруем данные
            mask = (self._data['timestamp'] >= start_time) & (self._data['timestamp'] <= end_time)
            filtered_data = self._data[mask].copy()

            if filtered_data.empty:
                self.logger.warning("Нет данных в указанном временном диапазоне")
                return None

            # Создаем новый объект TelemetryData
            filtered_telemetry = TelemetryData(
                data=filtered_data,
                metadata=self.metadata.copy(),
                timestamp_range=(start_time, end_time),
                source_file=self.source_file
            )

            # Копируем timestamp настройки
            filtered_telemetry.timestamp_columns = self.timestamp_columns
            filtered_telemetry.timestamp_wagon = self.timestamp_wagon

            self.logger.info(f"Данные отфильтрованы: {len(filtered_data)} записей из {self.records_count}")
            return filtered_telemetry

        except Exception as e:
            self.logger.error(f"Ошибка фильтрации по времени: {e}")
            return None

    def _parse_timestamp_from_components(self, column_mapping: Dict[str, str]):
        """Парсинг timestamp из компонентов"""
        try:
            self.timestamp_columns = column_mapping
            return self._create_timestamp_column_from_existing()
        except Exception as e:
            self.logger.error(f"Ошибка парсинга timestamp из компонентов: {e}")
            return False

    def _format_duration(self, duration: timedelta) -> str:
        """Форматирование длительности"""
        try:
            days = duration.days
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            if days > 0:
                return f"{days} дн. {hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except Exception:
            return "Неизвестно"

    def _clear_cache(self):
        """Очистка кэша"""
        self._statistics_cache.clear()
        self._validation_cache.clear()

    def get_data_summary(self) -> Dict[str, Any]:
        """Получение сводки данных"""
        try:
            return {
                'records_count': self.records_count,
                'columns_count': self.columns_count,
                'source_file': self.source_file,
                'has_timestamp': bool(self.timestamp_columns),
                'timestamp_range': self.timestamp_range,
                'metadata_keys': list(self.metadata.keys()) if self.metadata else [],
                'data_types': self._data.dtypes.to_dict() if self._data is not None else {},
                'memory_usage_mb': self._data.memory_usage(deep=True).sum() / 1024 / 1024 if self._data is not None else 0
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения сводки данных: {e}")
            return {'error': str(e)}

    def export_metadata(self) -> Dict[str, Any]:
        """Экспорт метаданных"""
        try:
            return {
                'metadata': self.metadata,
                'timestamp_columns': self.timestamp_columns,
                'timestamp_wagon': self.timestamp_wagon,
                'timestamp_range': {
                    'start': self.timestamp_range[0].isoformat() if self.timestamp_range else None,
                    'end': self.timestamp_range[1].isoformat() if self.timestamp_range else None
                },
                'source_file': self.source_file,
                'records_count': self.records_count,
                'columns_count': self.columns_count,
                'export_timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Ошибка экспорта метаданных: {e}")
            return {'error': str(e)}

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self._clear_cache()
            self._data = None
            self.metadata = None
            self.timestamp_columns = None
            self.logger.info("TelemetryData очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки TelemetryData: {e}")

    def __str__(self):
        return f"TelemetryData(records={self.records_count}, columns={self.columns_count}, source='{self.source_file}')"

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return self.records_count
