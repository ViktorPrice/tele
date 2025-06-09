"""
Сервис фильтрации параметров с КРИТИЧЕСКИМИ исправлениями для проблемных CSV
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from functools import lru_cache
import hashlib
import json

from ..entities.parameter import Parameter
from ..entities.filter_criteria import FilterCriteria

class ParameterFilteringService:
    """Сервис фильтрации параметров (КРИТИЧЕСКИ ИСПРАВЛЕННАЯ ВЕРСИЯ)"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Кэш для результатов фильтрации
        self._filter_cache: Dict[str, List[Any]] = {}
        self._cache_enabled = True
        self._max_cache_size = 100
        
        # Метрики производительности
        self._filter_stats = {
            'total_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'filter_time_ms': []
        }
        
        self.logger.info("ParameterFilteringService инициализирован")
    
    def filter_parameters(self, parameters: List[Any], 
                         criteria: Dict[str, List[str]]) -> List[Any]:
        """КРИТИЧЕСКИ ИСПРАВЛЕННАЯ фильтрация параметров"""
        import time
        start_time = time.time()
        
        try:
            self._filter_stats['total_calls'] += 1
            
            # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Если критерии пустые или None, возвращаем ВСЕ параметры
            if not criteria or self._is_empty_criteria(criteria):
                self.logger.info("Пустые критерии фильтрации, возвращаем все параметры")
                filter_time = (time.time() - start_time) * 1000
                self.logger.info(f"Фильтрация: {len(parameters)} -> {len(parameters)} параметров ({filter_time:.1f}ms)")
                return parameters
            
            # Проверка кэша
            cache_key = self._generate_cache_key(parameters, criteria)
            if self._cache_enabled and cache_key in self._filter_cache:
                self._filter_stats['cache_hits'] += 1
                self.logger.debug(f"Использование кэша фильтрации: {cache_key[:8]}...")
                return self._filter_cache[cache_key]
            
            self._filter_stats['cache_misses'] += 1
            
            # Валидация входных данных
            if not self._validate_filter_input(parameters, criteria):
                return parameters  # Возвращаем все при ошибке валидации
            
            # Применение фильтров
            filtered_params = self._apply_sequential_filters(parameters, criteria)
            
            # Сохранение в кэш
            if self._cache_enabled:
                self._update_cache(cache_key, filtered_params)
            
            # Обновление метрик
            filter_time = (time.time() - start_time) * 1000
            self._filter_stats['filter_time_ms'].append(filter_time)
            
            self.logger.info(f"Фильтрация: {len(parameters)} -> {len(filtered_params)} параметров ({filter_time:.1f}ms)")
            return filtered_params
            
        except Exception as e:
            self.logger.error(f"Ошибка фильтрации параметров: {e}")
            return parameters  # Возвращаем исходные данные при ошибке
    
    def _is_empty_criteria(self, criteria: Dict[str, List[str]]) -> bool:
        """НОВЫЙ МЕТОД: Проверка на пустые критерии"""
        try:
            if not criteria:
                return True
            
            # Проверяем все возможные ключи критериев
            for key, value in criteria.items():
                if value:  # Если есть непустое значение
                    if isinstance(value, list) and len(value) > 0:
                        return False
                    elif not isinstance(value, list) and value:
                        return False
            
            return True  # Все критерии пустые
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки пустых критериев: {e}")
            return True  # При ошибке считаем критерии пустыми
    
    def filter_changed_params(self, start_time, end_time) -> List[Any]:
        """Фильтрация изменяемых параметров"""
        try:
            self.logger.info(f"Фильтрация изменяемых параметров: {start_time} - {end_time}")
            
            # Делегируем к data_loader если метод есть
            if hasattr(self.data_loader, 'filter_changed_params'):
                return self.data_loader.filter_changed_params(start_time, end_time)
            
            # Fallback - возвращаем ВСЕ не проблемные параметры как изменяемые
            return self._filter_changed_parameters_fallback(start_time, end_time)
            
        except Exception as e:
            self.logger.error(f"Ошибка фильтрации изменяемых параметров: {e}")
            return []
    
    def _validate_filter_input(self, parameters: List[Any], 
                              criteria: Dict[str, List[str]]) -> bool:
        """Валидация входных данных для фильтрации"""
        try:
            if not isinstance(parameters, list):
                self.logger.error("Параметры должны быть списком")
                return False
            
            if not isinstance(criteria, dict):
                self.logger.error("Критерии должны быть словарем")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации входных данных: {e}")
            return False
    
    def _apply_sequential_filters(self, parameters: List[Any], 
                                 criteria: Dict[str, List[str]]) -> List[Any]:
        """ИСПРАВЛЕННОЕ последовательное применение фильтров"""
        filtered = parameters.copy()
        
        # Применяем фильтры в порядке селективности
        filter_order = [
            ('signal_types', self._filter_by_signal_types),
            ('wagons', self._filter_by_wagons),
            ('lines', self._filter_by_lines),
            ('components', self._filter_by_components),
            ('hardware', self._filter_by_hardware),
            ('problematic', self._filter_by_problematic_status)  # НОВЫЙ фильтр
        ]
        
        for filter_name, filter_func in filter_order:
            if filter_name in criteria and criteria[filter_name]:
                try:
                    before_count = len(filtered)
                    filtered = filter_func(filtered, criteria[filter_name])
                    after_count = len(filtered)
                    
                    self.logger.debug(f"Фильтр {filter_name}: {before_count} -> {after_count} параметров")
                    
                    # НЕ делаем ранний выход если результатов нет - это может быть нормально
                        
                except Exception as e:
                    self.logger.error(f"Ошибка применения фильтра {filter_name}: {e}")
                    continue
        
        return filtered
    
    def _filter_by_problematic_status(self, parameters: List[Any], 
                                    statuses: List[str]) -> List[Any]:
        """НОВЫЙ МЕТОД: Фильтрация по статусу проблемности"""
        if not statuses:
            return parameters
        
        filtered = []
        
        for param in parameters:
            try:
                is_problematic = self._extract_problematic_status(param)
                
                # Проверяем соответствие критериям
                if ('problematic' in statuses and is_problematic) or \
                   ('normal' in statuses and not is_problematic) or \
                   ('all' in statuses):
                    filtered.append(param)
                    
            except Exception as e:
                self.logger.debug(f"Ошибка обработки параметра в фильтре статуса: {e}")
                # При ошибке включаем параметр
                filtered.append(param)
                continue
        
        return filtered
    
    def _extract_problematic_status(self, param: Any) -> bool:
        """Извлечение статуса проблемности параметра"""
        try:
            if hasattr(param, 'is_problematic'):
                return param.is_problematic
            elif isinstance(param, dict):
                return param.get('is_problematic', False)
            return False
        except Exception:
            return False
    
    def _filter_by_signal_types(self, parameters: List[Any], 
                               signal_types: List[str]) -> List[Any]:
        """ИСПРАВЛЕННАЯ фильтрация по типам сигналов"""
        if not signal_types:
            return parameters
        
        signal_types_set = set(signal_types)
        filtered = []
        
        for param in parameters:
            try:
                param_type = self._extract_signal_type(param)
                if param_type in signal_types_set:
                    filtered.append(param)
            except Exception as e:
                self.logger.debug(f"Ошибка обработки параметра в фильтре типов: {e}")
                # При ошибке включаем параметр
                filtered.append(param)
                continue
        
        return filtered
    
    def _filter_by_lines(self, parameters: List[Any], 
                        lines: List[str]) -> List[Any]:
        """Фильтрация по линиям связи"""
        if not lines:
            return parameters
        
        lines_set = set(lines)
        filtered = []
        
        for param in parameters:
            try:
                param_line = self._extract_line(param)
                if param_line in lines_set:
                    filtered.append(param)
            except Exception as e:
                self.logger.debug(f"Ошибка обработки параметра в фильтре линий: {e}")
                filtered.append(param)
                continue
        
        return filtered
    
    def _filter_by_wagons(self, parameters: List[Any], 
                         wagons: List[str]) -> List[Any]:
        """Фильтрация по номерам вагонов"""
        if not wagons:
            return parameters
        
        wagons_set = set(wagons)
        filtered = []
        
        for param in parameters:
            try:
                param_wagon = self._extract_wagon(param)
                if param_wagon in wagons_set:
                    filtered.append(param)
            except Exception as e:
                self.logger.debug(f"Ошибка обработки параметра в фильтре вагонов: {e}")
                filtered.append(param)
                continue
        
        return filtered
    
    def _filter_by_components(self, parameters: List[Any], 
                            components: List[str]) -> List[Any]:
        """Фильтрация по компонентам"""
        if not components:
            return parameters
        
        components_set = set(components)
        filtered = []
        
        for param in parameters:
            try:
                param_component = self._extract_component(param)
                if param_component in components_set:
                    filtered.append(param)
            except Exception as e:
                self.logger.debug(f"Ошибка обработки параметра в фильтре компонентов: {e}")
                filtered.append(param)
                continue
        
        return filtered
    
    def _filter_by_hardware(self, parameters: List[Any], 
                           hardware: List[str]) -> List[Any]:
        """Фильтрация по типам оборудования"""
        if not hardware:
            return parameters
        
        hardware_set = set(hardware)
        filtered = []
        
        for param in parameters:
            try:
                param_hardware = self._extract_hardware(param)
                if param_hardware in hardware_set:
                    filtered.append(param)
            except Exception as e:
                self.logger.debug(f"Ошибка обработки параметра в фильтре оборудования: {e}")
                filtered.append(param)
                continue
        
        return filtered
    
    def _extract_signal_type(self, param: Any) -> str:
        """УЛУЧШЕННОЕ извлечение типа сигнала из параметра"""
        try:
            # Обработка Parameter объектов
            if hasattr(param, 'data_type'):
                return param.data_type.value if hasattr(param.data_type, 'value') else str(param.data_type)
            
            # Обработка словарей
            if isinstance(param, dict):
                signal_code = param.get('signal_code', '')
                data_type = param.get('data_type', '')
                
                if data_type:
                    return data_type
                
                if signal_code:
                    return signal_code.split('_')[0] if '_' in signal_code else signal_code[:2]
            
            # Обработка списков/кортежей
            elif isinstance(param, (list, tuple)) and len(param) > 0:
                signal_code = str(param[0])
                return signal_code.split('_')[0] if '_' in signal_code else signal_code[:2]
            
            return 'Unknown'
            
        except Exception as e:
            self.logger.debug(f"Ошибка извлечения типа сигнала: {e}")
            return 'Unknown'
    
    def _extract_line(self, param: Any) -> str:
        """Извлечение линии из параметра"""
        try:
            if hasattr(param, 'line'):
                return param.line
            elif isinstance(param, dict):
                return param.get('line', 'Unknown')
            elif isinstance(param, (list, tuple)) and len(param) > 2:
                return str(param[2])
            return 'Unknown'
        except Exception:
            return 'Unknown'
    
    def _extract_wagon(self, param: Any) -> str:
        """Извлечение номера вагона из параметра"""
        try:
            if hasattr(param, 'wagon'):
                return str(param.wagon) if param.wagon else '1'
            elif isinstance(param, dict):
                return str(param.get('wagon', '1'))
            elif isinstance(param, (list, tuple)) and len(param) > 3:
                return str(param[3])
            return '1'
        except Exception:
            return '1'
    
    def _extract_component(self, param: Any) -> str:
        """Извлечение компонента из параметра"""
        try:
            if hasattr(param, 'component_type'):
                return param.component_type or 'Unknown'
            elif isinstance(param, dict):
                return param.get('component_type', 'Unknown')
            return 'Unknown'
        except Exception:
            return 'Unknown'
    
    def _extract_hardware(self, param: Any) -> str:
        """Извлечение типа оборудования из параметра"""
        try:
            if hasattr(param, 'hardware_type'):
                return param.hardware_type or 'Unknown'
            elif isinstance(param, dict):
                return param.get('hardware_type', 'Unknown')
            return 'Unknown'
        except Exception:
            return 'Unknown'
    
    def _filter_changed_parameters_fallback(self, start_time, end_time) -> List[Any]:
        """ИСПРАВЛЕННЫЙ Fallback фильтрация изменяемых параметров"""
        try:
            # Получаем все параметры
            if hasattr(self.data_loader, 'parameters'):
                all_params = self.data_loader.parameters
            else:
                self.logger.warning("Нет доступа к параметрам в data_loader")
                return []
            
            # Возвращаем ВСЕ параметры как потенциально изменяемые
            # Исключаем только явно системные
            changed_params = []
            for param in all_params:
                try:
                    # Исключаем только timestamp и системные параметры
                    if isinstance(param, dict):
                        signal_code = param.get('signal_code', '').upper()
                        if 'TIMESTAMP' in signal_code or signal_code.startswith('DATE:'):
                            continue
                    elif hasattr(param, 'signal_code'):
                        signal_code = param.signal_code.upper()
                        if 'TIMESTAMP' in signal_code or signal_code.startswith('DATE:'):
                            continue
                    
                    changed_params.append(param)
                except Exception:
                    # При ошибке включаем параметр
                    changed_params.append(param)
                    continue
            
            self.logger.info(f"Fallback: возвращено {len(changed_params)} потенциально изменяемых параметров")
            return changed_params
            
        except Exception as e:
            self.logger.error(f"Ошибка fallback фильтрации: {e}")
            return []
    
    # Остальные методы остаются без изменений...
    def _generate_cache_key(self, parameters: List[Any], 
                           criteria: Dict[str, List[str]]) -> str:
        """Генерация ключа кэша"""
        try:
            params_hash = hashlib.md5(str(len(parameters)).encode()).hexdigest()[:8]
            criteria_str = json.dumps(criteria, sort_keys=True)
            criteria_hash = hashlib.md5(criteria_str.encode()).hexdigest()[:8]
            return f"{params_hash}_{criteria_hash}"
        except Exception as e:
            self.logger.error(f"Ошибка генерации ключа кэша: {e}")
            return f"fallback_{len(parameters)}_{len(criteria)}"
    
    def _update_cache(self, cache_key: str, filtered_params: List[Any]):
        """Обновление кэша с контролем размера"""
        try:
            if len(self._filter_cache) >= self._max_cache_size:
                oldest_key = next(iter(self._filter_cache))
                del self._filter_cache[oldest_key]
            
            self._filter_cache[cache_key] = filtered_params.copy()
        except Exception as e:
            self.logger.error(f"Ошибка обновления кэша: {e}")
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """Получение статистики фильтрации"""
        try:
            cache_hit_rate = 0
            if self._filter_stats['total_calls'] > 0:
                cache_hit_rate = (self._filter_stats['cache_hits'] / 
                                self._filter_stats['total_calls']) * 100
            
            avg_filter_time = 0
            if self._filter_stats['filter_time_ms']:
                avg_filter_time = sum(self._filter_stats['filter_time_ms']) / len(self._filter_stats['filter_time_ms'])
            
            return {
                'total_calls': self._filter_stats['total_calls'],
                'cache_hits': self._filter_stats['cache_hits'],
                'cache_misses': self._filter_stats['cache_misses'],
                'cache_hit_rate_percent': round(cache_hit_rate, 2),
                'cache_size': len(self._filter_cache),
                'avg_filter_time_ms': round(avg_filter_time, 2),
                'cache_enabled': self._cache_enabled
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def clear_cache(self):
        """Очистка кэша фильтрации"""
        try:
            cache_size = len(self._filter_cache)
            self._filter_cache.clear()
            self.logger.info(f"Кэш фильтрации очищен ({cache_size} элементов)")
        except Exception as e:
            self.logger.error(f"Ошибка очистки кэша: {e}")
