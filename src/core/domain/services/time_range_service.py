"""
Сервис для работы с временными диапазонами анализа (исправленная версия)
"""
from typing import Tuple, Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import pandas as pd

from ..entities.telemetry_data import TelemetryData
from ..entities.parameter import Parameter

class TimeRangeService:
    """Сервис управления временными диапазонами для анализа (исправленная версия)"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._current_range: Optional[Tuple[datetime, datetime]] = None
        self._data_range: Optional[Tuple[datetime, datetime]] = None
    
    def initialize_from_telemetry_data(self, telemetry_data: TelemetryData) -> Dict[str, str]:
        """Улучшенная инициализация временного диапазона из данных телеметрии"""
        try:
            # Получаем полный диапазон данных
            self._data_range = telemetry_data.get_time_range_for_analysis()
            
            # Проверяем качество временного диапазона
            start_time, end_time = self._data_range
            duration = (end_time - start_time).total_seconds()
            
            if duration <= 0:
                # Если диапазон некорректный, создаем синтетический
                self.logger.warning("Некорректный временной диапазон, создание синтетического...")
                self._create_synthetic_time_range(telemetry_data)
                start_time, end_time = self._data_range
                duration = (end_time - start_time).total_seconds()
            
            self._current_range = self._data_range
            
            # Возвращаем отформатированные значения
            formatted_range = telemetry_data.get_formatted_time_range()
            
            result = {
                'from_time': formatted_range['from_time'],
                'to_time': formatted_range['to_time'],
                'duration': formatted_range['duration'],
                'total_records': telemetry_data.records_count,
                'synthetic': duration <= 1  # Помечаем как синтетический если очень короткий
            }
            
            self.logger.info(f"Инициализирован временной диапазон: {result['from_time']} - {result['to_time']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации временного диапазона: {e}")
            return self._create_fallback_range()
    
    def _create_synthetic_time_range(self, telemetry_data: TelemetryData):
        """Создание синтетического временного диапазона"""
        try:
            # Создаем диапазон на основе количества записей
            records_count = telemetry_data.records_count
            
            # Базовое время - час назад от текущего момента
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=max(records_count, 3600))  # Минимум час
            
            # Обновляем диапазон в TelemetryData
            telemetry_data.timestamp_range = (start_time, end_time)
            self._data_range = (start_time, end_time)
            
            self.logger.info(f"Создан синтетический диапазон: {start_time} - {end_time}")
            
        except Exception as e:
            self.logger.error(f"Ошибка создания синтетического диапазона: {e}")
    
    def _create_fallback_range(self) -> Dict[str, str]:
        """Создание fallback диапазона"""
        current_time = datetime.now()
        hour_ago = current_time - timedelta(hours=1)
        
        return {
            'from_time': hour_ago.strftime('%Y-%m-%d %H:%M:%S'),
            'to_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': '1:00:00',
            'total_records': 0,
            'error': True
        }
    
    def set_user_time_range(self, from_time_str: str, to_time_str: str) -> bool:
        """Установка пользовательского временного диапазона"""
        try:
            # Парсинг времени
            from_time = self._parse_time_string(from_time_str)
            to_time = self._parse_time_string(to_time_str)
            
            if not from_time or not to_time:
                self.logger.error("Неверный формат времени")
                return False
            
            if from_time >= to_time:
                self.logger.error("Время начала должно быть раньше времени окончания")
                return False
            
            # Проверяем границы данных
            if self._data_range:
                data_start, data_end = self._data_range
                if from_time < data_start or to_time > data_end:
                    self.logger.warning("Выбранный диапазон выходит за пределы данных")
            
            self._current_range = (from_time, to_time)
            self.logger.info(f"Установлен пользовательский диапазон: {from_time} - {to_time}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка установки пользовательского диапазона: {e}")
            return False
    
    def get_current_range(self) -> Optional[Tuple[datetime, datetime]]:
        """Получение текущего временного диапазона"""
        return self._current_range
    
    def get_data_range(self) -> Optional[Tuple[datetime, datetime]]:
        """Получение полного диапазона данных"""
        return self._data_range
    
    def reset_to_data_range(self):
        """Сброс к полному диапазону данных"""
        self._current_range = self._data_range
        self.logger.info("Сброшен к полному диапазону данных")
    
    def find_changed_parameters_in_range(self, telemetry_data: TelemetryData, 
                                       parameters: List[Parameter],
                                       threshold: float = 0.1) -> List[Parameter]:
        """Поиск изменяемых параметров в заданном диапазоне"""
        try:
            if not self._current_range:
                self.logger.error("Временной диапазон не установлен")
                return []
            
            start_time, end_time = self._current_range
            
            # Фильтруем данные по времени
            filtered_data = telemetry_data.filter_by_time(start_time, end_time)
            
            if filtered_data.records_count == 0:
                self.logger.warning("Нет данных в выбранном диапазоне")
                return []
            
            # Анализируем изменчивость параметров
            changed_params = []
            
            for param in parameters:
                # Пропускаем проблемные параметры для анализа изменчивости
                if param.is_problematic:
                    continue
                    
                if param.full_column in filtered_data.data.columns:
                    if self._is_parameter_changed(filtered_data.data[param.full_column], threshold):
                        changed_params.append(param)
            
            self.logger.info(f"Найдено {len(changed_params)} изменяемых параметров в диапазоне (исключены проблемные)")
            return changed_params
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска изменяемых параметров: {e}")
            return []
    
    def _is_parameter_changed(self, series: pd.Series, threshold: float) -> bool:
        """Проверка изменчивости параметра"""
        try:
            # Удаляем NaN значения
            clean_series = series.dropna()
            
            if len(clean_series) < 2:
                return False
            
            # Для числовых данных - проверяем стандартное отклонение
            if pd.api.types.is_numeric_dtype(clean_series):
                # Нормализуем стандартное отклонение относительно среднего
                mean_val = clean_series.mean()
                std_val = clean_series.std()
                
                if mean_val != 0:
                    normalized_std = std_val / abs(mean_val)
                    if normalized_std > threshold:
                        return True
                elif std_val > threshold:
                    return True
            
            # Для всех типов - проверяем количество уникальных значений
            unique_ratio = len(clean_series.unique()) / len(clean_series)
            return unique_ratio > threshold
            
        except Exception:
            return False
    
    def _parse_time_string(self, time_str: str) -> Optional[datetime]:
        """Парсинг строки времени"""
        if not time_str or not isinstance(time_str, str):
            return None
        
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%d.%m.%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%d',
            '%d.%m.%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def get_range_statistics(self) -> Dict[str, Any]:
        """Получение статистики временного диапазона"""
        if not self._current_range or not self._data_range:
            return {}
        
        current_start, current_end = self._current_range
        data_start, data_end = self._data_range
        
        current_duration = (current_end - current_start).total_seconds()
        total_duration = (data_end - data_start).total_seconds()
        
        coverage_percent = (current_duration / total_duration * 100) if total_duration > 0 else 100
        
        return {
            'current_range': {
                'start': current_start.strftime('%Y-%m-%d %H:%M:%S'),
                'end': current_end.strftime('%Y-%m-%d %H:%M:%S'),
                'duration_seconds': current_duration
            },
            'data_range': {
                'start': data_start.strftime('%Y-%m-%d %H:%M:%S'),
                'end': data_end.strftime('%Y-%m-%d %H:%M:%S'),
                'duration_seconds': total_duration
            },
            'coverage_percent': round(coverage_percent, 2),
            'is_full_range': current_start == data_start and current_end == data_end
        }
