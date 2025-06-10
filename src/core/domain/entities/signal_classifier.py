# src/core/domain/entities/signal_classifier.py
"""
Классификатор сигналов телеметрии для диагностической фильтрации
"""
import re
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from ....config.diagnostic_filters_config import (
    CRITICAL_FILTERS, SYSTEM_FILTERS, FUNCTIONAL_FILTERS, 
    COMPONENT_MAPPING, SEVERITY_LEVELS
)

class SignalCriticality(Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"

class SignalSystem(Enum):
    TRACTION = "traction"
    BRAKES = "brakes"
    DOORS = "doors"
    POWER = "power"
    CLIMATE = "climate"
    INFO_SYSTEMS = "info_systems"
    COMMUNICATION = "communication"
    UNKNOWN = "unknown"

@dataclass
class SignalClassification:
    signal_code: str
    criticality: SignalCriticality
    system: SignalSystem
    component: str
    function_type: str
    wagon_number: Optional[int]
    is_train_level: bool
    severity_score: int
    related_signals: List[str]

class SignalClassifier:
    """Классификатор сигналов телеметрии"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._pattern_cache: Dict[str, SignalClassification] = {}
        self._compiled_patterns = self._compile_patterns()
        
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Компиляция регулярных выражений для оптимизации"""
        compiled = {}
        
        # Критичность
        for crit_type, config in CRITICAL_FILTERS.items():
            compiled[f"critical_{crit_type}"] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in config['patterns']
            ]
        
        # Системы
        for system_type, config in SYSTEM_FILTERS.items():
            compiled[f"system_{system_type}"] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in config['patterns']
            ]
        
        # Функции
        for func_type, config in FUNCTIONAL_FILTERS.items():
            compiled[f"function_{func_type}"] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in config['patterns']
            ]
        
        return compiled
    
    def classify_signal(self, signal_code: str, 
                       description: str = "", 
                       additional_info: Dict[str, Any] = None) -> SignalClassification:
        """Классификация сигнала"""
        try:
            # Проверяем кэш
            cache_key = f"{signal_code}_{hash(description)}"
            if cache_key in self._pattern_cache:
                return self._pattern_cache[cache_key]
            
            # Выполняем классификацию
            classification = self._perform_classification(
                signal_code, description, additional_info or {}
            )
            
            # Сохраняем в кэш
            self._pattern_cache[cache_key] = classification
            
            return classification
            
        except Exception as e:
            self.logger.error(f"Ошибка классификации сигнала {signal_code}: {e}")
            return self._create_fallback_classification(signal_code)
    
    def _perform_classification(self, signal_code: str, 
                               description: str,
                               additional_info: Dict[str, Any]) -> SignalClassification:
        """Выполнение классификации сигнала"""
        
        # Определяем критичность
        criticality = self._classify_criticality(signal_code, description)
        
        # Определяем систему
        system = self._classify_system(signal_code, description)
        
        # Извлекаем компонент
        component = self._extract_component(signal_code)
        
        # Определяем функциональный тип
        function_type = self._classify_function(signal_code, description)
        
        # Извлекаем номер вагона
        wagon_number = self._extract_wagon_number(signal_code)
        
        # Определяем уровень (вагон/состав)
        is_train_level = self._is_train_level_signal(signal_code, wagon_number)
        
        # Вычисляем оценку серьезности
        severity_score = self._calculate_severity_score(
            criticality, system, function_type
        )
        
        # Находим связанные сигналы
        related_signals = self._find_related_signals(signal_code, component, system)
        
        return SignalClassification(
            signal_code=signal_code,
            criticality=criticality,
            system=system,
            component=component,
            function_type=function_type,
            wagon_number=wagon_number,
            is_train_level=is_train_level,
            severity_score=severity_score,
            related_signals=related_signals
        )
    
    def _classify_criticality(self, signal_code: str, description: str) -> SignalCriticality:
        """Классификация по критичности"""
        combined_text = f"{signal_code} {description}".upper()
        
        for crit_type, config in CRITICAL_FILTERS.items():
            for pattern in config['patterns']:
                if pattern.upper() in combined_text:
                    if crit_type == 'emergency':
                        return SignalCriticality.CRITICAL
                    elif crit_type in ['safety', 'power_critical', 'brake_critical']:
                        return SignalCriticality.HIGH
        
        # Проверяем по функциональному типу
        if any(pattern in combined_text for pattern in ['FAULT', 'FAIL', 'ERROR', 'ALARM']):
            return SignalCriticality.HIGH
        elif any(pattern in combined_text for pattern in ['WARNING', 'TEMP', 'PRESSURE']):
            return SignalCriticality.MEDIUM
        
        return SignalCriticality.LOW
    
    def _classify_system(self, signal_code: str, description: str) -> SignalSystem:
        """Классификация по системе"""
        combined_text = f"{signal_code} {description}".upper()
        
        for system_type, config in SYSTEM_FILTERS.items():
            for pattern in config['patterns']:
                if pattern.upper() in combined_text:
                    try:
                        return SignalSystem(system_type)
                    except ValueError:
                        continue
        
        return SignalSystem.UNKNOWN
    
    def _extract_component(self, signal_code: str) -> str:
        """Извлечение компонента из кода сигнала"""
        try:
            # Паттерны извлечения компонента
            patterns = [
                r'^[A-Z]+_([A-Z]+[0-9]*)',  # B_PST_READY -> PST
                r'^[A-Z]+_([A-Z]{2,})',     # F_BCU_STATUS -> BCU
                r'([A-Z]{3,})',             # Любая аббревиатура 3+ символа
            ]
            
            for pattern in patterns:
                match = re.search(pattern, signal_code)
                if match:
                    component = match.group(1)
                    # Проверяем в маппинге компонентов
                    for comp_abbr in COMPONENT_MAPPING.keys():
                        if comp_abbr in component:
                            return comp_abbr
                    return component
            
            # Fallback - первые 3-4 символа после префикса
            parts = signal_code.split('_')
            if len(parts) > 1:
                return parts[1][:4]
            
            return "UNKNOWN"
            
        except Exception as e:
            self.logger.debug(f"Ошибка извлечения компонента: {e}")
            return "UNKNOWN"
    
    def _classify_function(self, signal_code: str, description: str) -> str:
        """Классификация функционального типа"""
        combined_text = f"{signal_code} {description}".upper()
        
        for func_type, config in FUNCTIONAL_FILTERS.items():
            for pattern in config['patterns']:
                if pattern.upper() in combined_text:
                    return func_type
        
        # Дополнительная классификация по префиксу
        if signal_code.startswith('B_'):
            return 'states'
        elif signal_code.startswith(('F_', 'S_', 'W_', 'DW_')):
            return 'measurements'
        elif signal_code.startswith('BY_'):
            return 'diagnostics'
        
        return 'unknown'
    
    def _extract_wagon_number(self, signal_code: str) -> Optional[int]:
        """Извлечение номера вагона"""
        try:
            # Ищем номер вагона в конце сигнала _N
            match = re.search(r'_(\d+)$', signal_code)
            if match:
                wagon_num = int(match.group(1))
                # Проверяем диапазон вагонов (1-11)
                if 1 <= wagon_num <= 11:
                    return wagon_num
            return None
        except Exception:
            return None
    
    def _is_train_level_signal(self, signal_code: str, wagon_number: Optional[int]) -> bool:
        """Определение сигнала уровня состава"""
        try:
            # Если нет номера вагона - составной сигнал
            if wagon_number is None:
                return True
            
            # Проверяем наличие других цифр в коде
            parts = signal_code.split('_')
            for part in parts[:-1]:  # Исключаем последнюю часть (номер вагона)
                if re.search(r'\d+', part):
                    return True
            
            # Специальные паттерны составных сигналов
            train_patterns = [
                'CONSIST_', 'TRAIN_', 'GLOBAL_', 'TOTAL_',
                'ALL_', 'MASTER_', 'GENERAL_'
            ]
            
            for pattern in train_patterns:
                if pattern in signal_code.upper():
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _calculate_severity_score(self, criticality: SignalCriticality,
                                 system: SignalSystem, 
                                 function_type: str) -> int:
        """Вычисление оценки серьезности (0-100)"""
        try:
            base_score = 0
            
            # Базовая оценка по критичности
            criticality_scores = {
                SignalCriticality.CRITICAL: 80,
                SignalCriticality.HIGH: 60,
                SignalCriticality.MEDIUM: 40,
                SignalCriticality.LOW: 20
            }
            base_score += criticality_scores.get(criticality, 20)
            
            # Модификатор по системе
            system_modifiers = {
                SignalSystem.BRAKES: 15,
                SignalSystem.POWER: 10,
                SignalSystem.TRACTION: 8,
                SignalSystem.DOORS: 5,
                SignalSystem.CLIMATE: 2,
                SignalSystem.INFO_SYSTEMS: 1
            }
            base_score += system_modifiers.get(system, 0)
            
            # Модификатор по функции
            function_modifiers = {
                'faults': 10,
                'controls': 5,
                'measurements': 3,
                'states': 2,
                'diagnostics': 1
            }
            base_score += function_modifiers.get(function_type, 0)
            
            return min(100, max(0, base_score))
            
        except Exception:
            return 50  # Средняя оценка при ошибке
    
    def _find_related_signals(self, signal_code: str, 
                             component: str, 
                             system: SignalSystem) -> List[str]:
        """Поиск связанных сигналов"""
        try:
            related = []
            
            # Связанные по компоненту
            if component and component != "UNKNOWN":
                base_pattern = signal_code.split('_')[0] + '_' + component
                related.append(f"{base_pattern}_*")
            
            # Связанные по системе
            if system != SignalSystem.UNKNOWN:
                system_patterns = SYSTEM_FILTERS.get(system.value, {}).get('patterns', [])
                related.extend(system_patterns[:3])  # Первые 3 паттерна
            
            return related[:5]  # Максимум 5 связанных сигналов
            
        except Exception:
            return []
    
    def _create_fallback_classification(self, signal_code: str) -> SignalClassification:
        """Создание fallback классификации при ошибке"""
        return SignalClassification(
            signal_code=signal_code,
            criticality=SignalCriticality.LOW,
            system=SignalSystem.UNKNOWN,
            component="UNKNOWN",
            function_type="unknown",
            wagon_number=self._extract_wagon_number(signal_code),
            is_train_level=False,
            severity_score=30,
            related_signals=[]
        )
    
    # === ПУБЛИЧНЫЕ МЕТОДЫ ДЛЯ МАССОВОЙ ОБРАБОТКИ ===
    
    def classify_signals_batch(self, signals: List[Dict[str, Any]]) -> Dict[str, SignalClassification]:
        """Массовая классификация сигналов"""
        try:
            results = {}
            
            for signal in signals:
                signal_code = signal.get('signal_code', '')
                description = signal.get('description', '')
                
                if signal_code:
                    classification = self.classify_signal(signal_code, description, signal)
                    results[signal_code] = classification
            
            self.logger.info(f"Классифицировано {len(results)} сигналов")
            return results
            
        except Exception as e:
            self.logger.error(f"Ошибка массовой классификации: {e}")
            return {}
    
    def get_signals_by_criticality(self, signals: List[Dict[str, Any]], 
                                  criticality: SignalCriticality) -> List[Dict[str, Any]]:
        """Получение сигналов по уровню критичности"""
        try:
            filtered = []
            
            for signal in signals:
                signal_code = signal.get('signal_code', '')
                if signal_code:
                    classification = self.classify_signal(signal_code, signal.get('description', ''))
                    if classification.criticality == criticality:
                        signal['classification'] = classification
                        filtered.append(signal)
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"Ошибка фильтрации по критичности: {e}")
            return []
    
    def get_signals_by_system(self, signals: List[Dict[str, Any]], 
                             system: SignalSystem) -> List[Dict[str, Any]]:
        """Получение сигналов по системе"""
        try:
            filtered = []
            
            for signal in signals:
                signal_code = signal.get('signal_code', '')
                if signal_code:
                    classification = self.classify_signal(signal_code, signal.get('description', ''))
                    if classification.system == system:
                        signal['classification'] = classification
                        filtered.append(signal)
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"Ошибка фильтрации по системе: {e}")
            return []
    
    def clear_cache(self):
        """Очистка кэша классификации"""
        cache_size = len(self._pattern_cache)
        self._pattern_cache.clear()
        self.logger.info(f"Очищен кэш классификации ({cache_size} элементов)")
    
    def get_classification_statistics(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Получение статистики классификации"""
        try:
            stats = {
                'total_signals': len(signals),
                'by_criticality': {},
                'by_system': {},
                'by_function': {},
                'train_level_count': 0,
                'wagon_level_count': 0
            }
            
            for signal in signals:
                signal_code = signal.get('signal_code', '')
                if signal_code:
                    classification = self.classify_signal(signal_code, signal.get('description', ''))
                    
                    # По критичности
                    crit = classification.criticality.value
                    stats['by_criticality'][crit] = stats['by_criticality'].get(crit, 0) + 1
                    
                    # По системе
                    sys = classification.system.value
                    stats['by_system'][sys] = stats['by_system'].get(sys, 0) + 1
                    
                    # По функции
                    func = classification.function_type
                    stats['by_function'][func] = stats['by_function'].get(func, 0) + 1
                    
                    # По уровню
                    if classification.is_train_level:
                        stats['train_level_count'] += 1
                    else:
                        stats['wagon_level_count'] += 1
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {}
