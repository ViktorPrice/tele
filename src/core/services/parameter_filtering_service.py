# src/core/services/parameter_filtering_service.py
"""
Сервис фильтрации параметров с диагностической логикой
"""
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache
import hashlib
import json
import re
from datetime import datetime

from ..domain.entities.signal_classifier import SignalClassifier, SignalCriticality
from ...config.diagnostic_filters_config import (
    CRITICAL_FILTERS, SYSTEM_FILTERS, FUNCTIONAL_FILTERS
)

class ParameterFilteringService:
    """Полная реализация сервиса фильтрации с диагностикой"""

    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Инициализирован DiagnosticAnalyzer")
        
        self.signal_classifier = SignalClassifier()
        self._filter_cache = {}
        self._cache_enabled = True
        self._max_cache_size = 100
        
        # Метрики
        self.metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'diagnostic_filters_applied': 0
        }

    def filter_parameters(self, parameters: List[Any], 
                        criteria: Dict[str, List[str]]) -> List[Any]:
        """Основной метод фильтрации с диагностикой"""
        self.metrics['total_requests'] += 1
        
        if not self._validate_input(parameters, criteria):
            return []
            
        cache_key = self._generate_cache_key(parameters, criteria)
        if self._cache_enabled and cache_key in self._filter_cache:
            self.metrics['cache_hits'] += 1
            return self._filter_cache[cache_key]
            
        filtered = self._apply_filters(parameters, criteria)
        
        if 'diagnostic' in criteria:
            filtered = self._apply_diagnostic_filters(filtered, criteria['diagnostic'])
            self.metrics['diagnostic_filters_applied'] += 1
            
        if self._cache_enabled:
            self._update_cache(cache_key, filtered)
            
        return filtered

    def _apply_filters(self, params: List[Any], 
                      criteria: Dict[str, List[str]]) -> List[Any]:
        """Применение комплексных фильтров"""
        try:
            # Базовые фильтры
            filtered = self._filter_by_types(params, criteria.get('types', []))
            filtered = self._filter_by_lines(filtered, criteria.get('lines', []))
            filtered = self._filter_by_wagons(filtered, criteria.get('wagons', []))
            
            # Текстовая фильтрация
            if 'search_text' in criteria:
                filtered = self._filter_by_text(filtered, criteria['search_text'])
                
            return filtered
            
        except Exception as e:
            self.logger.error(f"Filter error: {e}")
            return []

    def _apply_diagnostic_filters(self, params: List[Any],
                             diagnostic_criteria: Dict[str, List[str]]) -> List[Any]:
        """ИНТЕГРАЦИЯ реальных диагностических фильтров"""
        try:
            from ...config.diagnostic_filters_config import (
                CRITICAL_FILTERS, SYSTEM_FILTERS, FUNCTIONAL_FILTERS
            )
            
            filtered = []
            
            for param in params:
                signal_code = param.get('signal_code', '').upper()
                description = param.get('description', '').upper()
                
                matches = False
                
                # ИНТЕГРАЦИЯ: Проверяем критичность
                if diagnostic_criteria.get('criticality'):
                    for crit_key in diagnostic_criteria['criticality']:
                        if crit_key in CRITICAL_FILTERS:
                            patterns = CRITICAL_FILTERS[crit_key]['patterns']
                            if any(pattern in signal_code or pattern in description for pattern in patterns):
                                matches = True
                                break
                
                # ИНТЕГРАЦИЯ: Проверяем системы
                if diagnostic_criteria.get('systems'):
                    for sys_key in diagnostic_criteria['systems']:
                        if sys_key in SYSTEM_FILTERS:
                            patterns = SYSTEM_FILTERS[sys_key]['patterns']
                            if any(pattern in signal_code or pattern in description for pattern in patterns):
                                matches = True
                                break
                
                # ИНТЕГРАЦИЯ: Реальные паттерны из анализа
                if not matches and diagnostic_criteria.get('real_patterns'):
                    real_patterns = diagnostic_criteria['real_patterns']
                    if any(pattern in signal_code for pattern in real_patterns):
                        matches = True
                
                if matches:
                    filtered.append(param)
            
            self.logger.info(f"🚨 Диагностическая фильтрация: {len(params)} → {len(filtered)} параметров")
            return filtered
            
        except Exception as e:
            self.logger.error(f"Ошибка диагностической фильтрации: {e}")
            return params

    def _matches_diagnostic_criteria(self, classification,
                                    criteria: Dict[str, List[str]]) -> bool:
        """Проверка соответствия диагностическим критериям"""
        match = False
        
        # Критичность
        if 'criticality' in criteria:
            crit_levels = [SignalCriticality(c) for c in criteria['criticality']]
            match |= classification.criticality in crit_levels
            
        # Системы
        if 'systems' in criteria:
            match |= classification.system.value in criteria['systems']
            
        # Функции
        if 'functions' in criteria:
            match |= classification.function_type in criteria['functions']
            
        return match

    def get_filter_stats(self) -> Dict[str, Any]:
        """Статистика работы сервиса"""
        return {
            'total_requests': self.metrics['total_requests'],
            'cache_hits': self.metrics['cache_hits'],
            'cache_hit_rate': self.metrics['cache_hits'] / self.metrics['total_requests'] if self.metrics['total_requests'] > 0 else 0,
            'diagnostic_filters': self.metrics['diagnostic_filters_applied'],
            'cache_size': len(self._filter_cache)
        }

    def clear_cache(self):
        """Очистка кэша"""
        self._filter_cache.clear()
        self.metrics['cache_hits'] = 0

    # Базовые методы фильтрации
    def _filter_by_types(self, params: List[Any], types: List[str]) -> List[Any]:
        if not types:
            return params
        return [p for p in params if self._get_signal_type(p) in types]

    def _filter_by_lines(self, params: List[Any], lines: List[str]) -> List[Any]:
        if not lines:
            return params
        return [p for p in params if self._get_line(p) in lines]

    def _filter_by_wagons(self, params: List[Any], wagons: List[str]) -> List[Any]:
        if not wagons:
            return params
        return [p for p in params if str(self._get_wagon(p)) in wagons]

    def _filter_by_text(self, params: List[Any], search_text: str) -> List[Any]:
        if not search_text:
            return params
            
        search_text = search_text.lower()
        return [
            p for p in params
            if (search_text in p.get('signal_code', '').lower() or
                search_text in p.get('description', '').lower())
        ]

    # Вспомогательные методы
    def _generate_cache_key(self, params: List[Any], criteria: Dict[str, Any]) -> str:
        params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]
        crit_hash = hashlib.md5(json.dumps(criteria, sort_keys=True).encode()).hexdigest()[:8]
        return f"{params_hash}_{crit_hash}"

    def _update_cache(self, key: str, data: List[Any]):
        if len(self._filter_cache) >= self._max_cache_size:
            self._filter_cache.popitem(last=False)
        self._filter_cache[key] = data

    def _validate_input(self, params: List[Any], criteria: Dict[str, Any]) -> bool:
        if not isinstance(params, list):
            self.logger.error("Parameters must be a list")
            return False
        if not isinstance(criteria, dict):
            self.logger.error("Criteria must be a dict")
            return False
        return True

    def _get_signal_type(self, param: Any) -> str:
        code = param.get('signal_code', '')
        return code.split('_')[0] if '_' in code else code[:2]

    def _get_line(self, param: Any) -> str:
        return param.get('line', 'unknown')

    def _get_wagon(self, param: Any) -> int:
        try:
            return int(param.get('wagon', 0))
        except:
            return 0

    # Диагностические методы
    def get_criticality_distribution(self, params: List[Any]) -> Dict[str, int]:
        """Распределение параметров по критичности"""
        dist = {c.value: 0 for c in SignalCriticality}
        classified = self.signal_classifier.classify_signals_batch(params)
        
        for param in params:
            classification = classified.get(param.get('signal_code', ''))
            if classification:
                dist[classification.criticality.value] += 1
                
        return dist

    def find_related_parameters(self, param: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Поиск связанных параметров"""
        classification = self.signal_classifier.classify_signal(
            param.get('signal_code', ''),
            param.get('description', '')
        )
        
        related = []
        for p in self.data_loader.parameters:
            p_code = p.get('signal_code', '')
            if any(r in p_code for r in classification.related_signals):
                related.append(p)
                
        return related[:10]

    # Оптимизированные методы для больших данных
    @lru_cache(maxsize=100)
    def get_parameter_metadata(self, signal_code: str) -> Optional[Dict[str, Any]]:
        """Получение метаданных параметра с кэшированием"""
        for param in self.data_loader.parameters:
            if param.get('signal_code') == signal_code:
                return {
                    'type': self._get_signal_type(param),
                    'line': self._get_line(param),
                    'wagon': self._get_wagon(param),
                    'description': param.get('description', '')
                }
        return None
