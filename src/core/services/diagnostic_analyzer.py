# src/core/services/diagnostic_analyzer.py
"""
Анализатор причинно-следственных связей для диагностики неисправностей
"""
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..domain.entities.signal_classifier import SignalClassifier, SignalCriticality, SignalSystem
from ...config.diagnostic_filters_config import CAUSAL_RELATIONSHIPS, SEVERITY_LEVELS

@dataclass
class CausalChain:
    """Причинно-следственная цепочка"""
    chain_id: str
    root_cause_signals: List[str]
    effect_signals: List[str]
    description: str
    severity: str
    confidence: float
    timestamp: datetime
    affected_systems: List[SignalSystem]

@dataclass
class DiagnosticResult:
    """Результат диагностического анализа"""
    signal_code: str
    possible_root_causes: List[str]
    potential_effects: List[str]
    causal_chains: List[CausalChain]
    severity_assessment: str
    confidence_score: float
    recommendations: List[str]
    related_faults: List[str]

class DiagnosticAnalyzer:
    """Анализатор причинно-следственных связей"""
    
    def __init__(self, signal_classifier: SignalClassifier = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signal_classifier = signal_classifier or SignalClassifier()
        
        # Кэш анализа
        self._analysis_cache: Dict[str, DiagnosticResult] = {}
        self._causal_chains_cache: Dict[str, List[CausalChain]] = {}
        
        # Конфигурация
        self.confidence_threshold = 0.6
        self.max_chain_depth = 5
        
        self.logger.info("DiagnosticAnalyzer инициализирован")
    
    def analyze_fault_signals(self, fault_signals: List[Dict[str, Any]], 
                             all_signals: List[Dict[str, Any]] = None,
                             timestamp: datetime = None) -> List[DiagnosticResult]:
        """Анализ неисправных сигналов"""
        try:
            if not fault_signals:
                return []
            
            timestamp = timestamp or datetime.now()
            results = []
            
            for fault_signal in fault_signals:
                signal_code = fault_signal.get('signal_code', '')
                if not signal_code:
                    continue
                
                # Проверяем кэш
                cache_key = f"{signal_code}_{timestamp.strftime('%Y%m%d_%H')}"
                if cache_key in self._analysis_cache:
                    results.append(self._analysis_cache[cache_key])
                    continue
                
                # Выполняем анализ
                result = self._analyze_single_fault(
                    fault_signal, all_signals or [], timestamp
                )
                
                # Сохраняем в кэш
                self._analysis_cache[cache_key] = result
                results.append(result)
            
            self.logger.info(f"Проанализировано {len(results)} неисправных сигналов")
            return results
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа неисправных сигналов: {e}")
            return []
    
    def _analyze_single_fault(self, fault_signal: Dict[str, Any],
                             all_signals: List[Dict[str, Any]],
                             timestamp: datetime) -> DiagnosticResult:
        """Анализ одного неисправного сигнала"""
        try:
            signal_code = fault_signal.get('signal_code', '')
            
            # Классифицируем сигнал
            classification = self.signal_classifier.classify_signal(
                signal_code, fault_signal.get('description', '')
            )
            
            # Ищем возможные причины
            root_causes = self._find_root_causes(signal_code, classification, all_signals)
            
            # Ищем потенциальные эффекты
            effects = self._find_potential_effects(signal_code, classification, all_signals)
            
            # Строим причинно-следственные цепочки
            causal_chains = self._build_causal_chains(signal_code, all_signals, timestamp)
            
            # Оценка серьезности
            severity = self._assess_fault_severity(classification, causal_chains)
            
            # Расчет уверенности
            confidence = self._calculate_confidence(root_causes, effects, causal_chains)
            
            # Генерация рекомендаций
            recommendations = self._generate_recommendations(
                signal_code, classification, root_causes, effects
            )
            
            # Поиск связанных неисправностей
            related_faults = self._find_related_faults(signal_code, all_signals)
            
            return DiagnosticResult(
                signal_code=signal_code,
                possible_root_causes=root_causes,
                potential_effects=effects,
                causal_chains=causal_chains,
                severity_assessment=severity,
                confidence_score=confidence,
                recommendations=recommendations,
                related_faults=related_faults
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа сигнала {fault_signal.get('signal_code', 'Unknown')}: {e}")
            return self._create_fallback_result(fault_signal.get('signal_code', ''))
    
    def _find_root_causes(self, signal_code: str, 
                         classification, 
                         all_signals: List[Dict[str, Any]]) -> List[str]:
        """Поиск возможных первопричин"""
        try:
            root_causes = []
            
            # Поиск в предопределенных связях
            for chain_name, chain_data in CAUSAL_RELATIONSHIPS.items():
                if signal_code in chain_data.get('effects', []):
                    root_causes.extend(chain_data.get('root_causes', []))
            
            # Поиск по системе
            if classification.system != SignalSystem.UNKNOWN:
                system_causes = self._find_system_root_causes(
                    classification.system, signal_code, all_signals
                )
                root_causes.extend(system_causes)
            
            # Поиск по компоненту
            if classification.component != "UNKNOWN":
                component_causes = self._find_component_root_causes(
                    classification.component, signal_code, all_signals
                )
                root_causes.extend(component_causes)
            
            # Убираем дубликаты и сам сигнал
            return list(set(root_causes) - {signal_code})
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска первопричин: {e}")
            return []
    
    def _find_potential_effects(self, signal_code: str,
                               classification,
                               all_signals: List[Dict[str, Any]]) -> List[str]:
        """Поиск потенциальных эффектов"""
        try:
            effects = []
            
            # Поиск в предопределенных связях
            for chain_name, chain_data in CAUSAL_RELATIONSHIPS.items():
                if signal_code in chain_data.get('root_causes', []):
                    effects.extend(chain_data.get('effects', []))
            
            # Поиск каскадных эффектов по системе
            if classification.system != SignalSystem.UNKNOWN:
                system_effects = self._find_system_effects(
                    classification.system, signal_code, all_signals
                )
                effects.extend(system_effects)
            
            return list(set(effects) - {signal_code})
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска эффектов: {e}")
            return []
    
    def _build_causal_chains(self, signal_code: str,
                            all_signals: List[Dict[str, Any]],
                            timestamp: datetime) -> List[CausalChain]:
        """Построение причинно-следственных цепочек"""
        try:
            chains = []
            
            # Ищем предопределенные цепочки
            for chain_id, chain_data in CAUSAL_RELATIONSHIPS.items():
                if (signal_code in chain_data.get('root_causes', []) or 
                    signal_code in chain_data.get('effects', [])):
                    
                    # Проверяем наличие других сигналов цепочки в данных
                    chain_signals = (chain_data.get('root_causes', []) + 
                                   chain_data.get('effects', []))
                    present_signals = self._find_present_signals(chain_signals, all_signals)
                    
                    if len(present_signals) >= 2:  # Минимум 2 сигнала для цепочки
                        confidence = len(present_signals) / len(chain_signals)
                        
                        # Определяем затронутые системы
                        affected_systems = self._get_affected_systems(present_signals)
                        
                        chain = CausalChain(
                            chain_id=chain_id,
                            root_cause_signals=chain_data.get('root_causes', []),
                            effect_signals=chain_data.get('effects', []),
                            description=chain_data.get('description', ''),
                            severity=chain_data.get('severity', 'medium'),
                            confidence=confidence,
                            timestamp=timestamp,
                            affected_systems=affected_systems
                        )
                        chains.append(chain)
            
            return chains
            
        except Exception as e:
            self.logger.error(f"Ошибка построения цепочек: {e}")
            return []
    
    def _find_system_root_causes(self, system: SignalSystem, 
                                signal_code: str,
                                all_signals: List[Dict[str, Any]]) -> List[str]:
        """Поиск первопричин в рамках системы"""
        try:
            causes = []
            
            # Специфичные для системы причины
            system_specific_causes = {
                SignalSystem.POWER: [
                    'F_U3000', 'B_PANTO_UP', 'B_QF1_TRIP', 'B_WAGON_3000V_OK'
                ],
                SignalSystem.BRAKES: [
                    'F_R_PRESSURE_MPA', 'B_R_PRESSURE_LOW', 'F_T_PRESSURE_MPA'
                ],
                SignalSystem.TRACTION: [
                    'B_PST_CONNECTED', 'B_INVERTER1_READY', 'B_MOTOR_READY'
                ],
                SignalSystem.DOORS: [
                    'B_DOOR_HINDRANCE', 'B_BUD_POWER_OK', 'B_DOOR_LOCK_OK'
                ]
            }
            
            system_causes = system_specific_causes.get(system, [])
            
            # Фильтруем только существующие сигналы
            present_causes = self._find_present_signals(system_causes, all_signals)
            causes.extend(present_causes)
            
            return causes
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска причин в системе {system}: {e}")
            return []
    
    def _find_component_root_causes(self, component: str,
                                   signal_code: str,
                                   all_signals: List[Dict[str, Any]]) -> List[str]:
        """Поиск первопричин в рамках компонента"""
        try:
            causes = []
            
            # Общие паттерны для компонентов
            component_patterns = [
                f"B_{component}_POWER_OK",
                f"B_{component}_READY", 
                f"B_{component}_CONNECTED",
                f"B_{component}_FAULT",
                f"F_{component}_VOLTAGE"
            ]
            
            # Ищем существующие сигналы по паттернам
            for signal in all_signals:
                signal_code_check = signal.get('signal_code', '')
                for pattern in component_patterns:
                    if pattern in signal_code_check and signal_code_check != signal_code:
                        causes.append(signal_code_check)
            
            return list(set(causes))
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска причин компонента {component}: {e}")
            return []
    
    def _find_system_effects(self, system: SignalSystem,
                            signal_code: str,
                            all_signals: List[Dict[str, Any]]) -> List[str]:
        """Поиск эффектов в рамках системы"""
        try:
            effects = []
            
            # Специфичные для системы эффекты
            system_effects = {
                SignalSystem.POWER: [
                    'B_PST_CONNECTED', 'B_PSN_CONNECTED', 'B_TRACTION_AVAILABLE'
                ],
                SignalSystem.BRAKES: [
                    'B_EMERGENCY_BRAKING', 'B_BRAKE_APPLIED', 'B_MOTION_BLOCKED'
                ],
                SignalSystem.DOORS: [
                    'B_ALL_DOORS_CLOSED', 'B_TRAIN_IS_MOVING_PERMIT'
                ]
            }
            
            system_effect_list = system_effects.get(system, [])
            present_effects = self._find_present_signals(system_effect_list, all_signals)
            effects.extend(present_effects)
            
            return effects
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска эффектов системы {system}: {e}")
            return []
    
    def _find_present_signals(self, signal_list: List[str],
                             all_signals: List[Dict[str, Any]]) -> List[str]:
        """Поиск присутствующих сигналов из списка"""
        present = []
        all_signal_codes = {s.get('signal_code', '') for s in all_signals}
        
        for signal_pattern in signal_list:
            if signal_pattern in all_signal_codes:
                present.append(signal_pattern)
            else:
                # Поиск по паттерну (если содержит *)
                if '*' in signal_pattern:
                    pattern_base = signal_pattern.replace('*', '')
                    for signal_code in all_signal_codes:
                        if pattern_base in signal_code:
                            present.append(signal_code)
        
        return present
    
    def _get_affected_systems(self, signal_codes: List[str]) -> List[SignalSystem]:
        """Определение затронутых систем"""
        try:
            systems = set()
            
            for signal_code in signal_codes:
                classification = self.signal_classifier.classify_signal(signal_code)
                if classification.system != SignalSystem.UNKNOWN:
                    systems.add(classification.system)
            
            return list(systems)
            
        except Exception as e:
            self.logger.error(f"Ошибка определения систем: {e}")
            return []
    
    def _assess_fault_severity(self, classification, 
                              causal_chains: List[CausalChain]) -> str:
        """Оценка серьезности неисправности"""
        try:
            # Базовая оценка по классификации
            base_severity = classification.criticality.value
            
            # Модификация по цепочкам
            if causal_chains:
                max_chain_severity = max(
                    SEVERITY_LEVELS.get(chain.severity, {}).get('priority', 4)
                    for chain in causal_chains
                )
                
                # Если есть критичные цепочки, повышаем серьезность
                if max_chain_severity <= 2:
                    if base_severity in ['medium', 'low']:
                        base_severity = 'high'
                    elif base_severity == 'high':
                        base_severity = 'critical'
            
            return base_severity
            
        except Exception as e:
            self.logger.error(f"Ошибка оценки серьезности: {e}")
            return 'medium'
    
    def _calculate_confidence(self, root_causes: List[str],
                             effects: List[str],
                             causal_chains: List[CausalChain]) -> float:
        """Расчет уверенности в диагнозе"""
        try:
            confidence_factors = []
            
            # Фактор наличия причин
            if root_causes:
                confidence_factors.append(min(0.4, len(root_causes) * 0.1))
            
            # Фактор наличия эффектов
            if effects:
                confidence_factors.append(min(0.3, len(effects) * 0.1))
            
            # Фактор цепочек
            if causal_chains:
                avg_chain_confidence = sum(chain.confidence for chain in causal_chains) / len(causal_chains)
                confidence_factors.append(avg_chain_confidence * 0.3)
            
            # Базовая уверенность
            base_confidence = 0.2
            
            total_confidence = base_confidence + sum(confidence_factors)
            return min(1.0, max(0.0, total_confidence))
            
        except Exception as e:
            self.logger.error(f"Ошибка расчета уверенности: {e}")
            return 0.5
    
    def _generate_recommendations(self, signal_code: str,
                                 classification,
                                 root_causes: List[str],
                                 effects: List[str]) -> List[str]:
        """Генерация рекомендаций по устранению"""
        try:
            recommendations = []
            
            # Рекомендации по критичности
            if classification.criticality == SignalCriticality.CRITICAL:
                recommendations.append("НЕМЕДЛЕННО остановить поезд и вызвать ремонтную бригаду")
                recommendations.append("Проверить системы безопасности")
            elif classification.criticality == SignalCriticality.HIGH:
                recommendations.append("Снизить скорость и подготовиться к остановке")
                recommendations.append("Контролировать связанные системы")
            
            # Рекомендации по системам
            system_recommendations = {
                SignalSystem.POWER: [
                    "Проверить состояние пантографа",
                    "Контролировать напряжение 3кВ",
                    "Проверить автоматические выключатели"
                ],
                SignalSystem.BRAKES: [
                    "Проверить давление в тормозной магистрали",
                    "Контролировать работу BCU",
                    "Готовиться к ручному торможению"
                ],
                SignalSystem.DOORS: [
                    "Проверить препятствия в дверях",
                    "Контролировать блокировки движения",
                    "Осмотреть контроллеры BUD"
                ]
            }
            
            system_recs = system_recommendations.get(classification.system, [])
            recommendations.extend(system_recs)
            
            # Рекомендации по первопричинам
            if root_causes:
                recommendations.append(f"Проверить связанные сигналы: {', '.join(root_causes[:3])}")
            
            return recommendations[:5]  # Максимум 5 рекомендаций
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации рекомендаций: {e}")
            return ["Обратиться к технической документации"]
    
    def _find_related_faults(self, signal_code: str,
                            all_signals: List[Dict[str, Any]]) -> List[str]:
        """Поиск связанных неисправностей"""
        try:
            related = []
            
            # Классифицируем исходный сигнал
            classification = self.signal_classifier.classify_signal(signal_code)
            
            # Ищем сигналы того же компонента с неисправностями
            for signal in all_signals:
                other_code = signal.get('signal_code', '')
                if other_code == signal_code:
                    continue
                
                other_classification = self.signal_classifier.classify_signal(other_code)
                
                # Тот же компонент и критичность
                if (other_classification.component == classification.component and
                    other_classification.criticality in [SignalCriticality.HIGH, SignalCriticality.CRITICAL]):
                    related.append(other_code)
            
            return related[:5]  # Максимум 5 связанных
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска связанных неисправностей: {e}")
            return []
    
    def _create_fallback_result(self, signal_code: str) -> DiagnosticResult:
        """Создание fallback результата при ошибке"""
        return DiagnosticResult(
            signal_code=signal_code,
            possible_root_causes=[],
            potential_effects=[],
            causal_chains=[],
            severity_assessment='medium',
            confidence_score=0.3,
            recommendations=["Требуется дополнительная диагностика"],
            related_faults=[]
        )
    
    # === ПУБЛИЧНЫЕ МЕТОДЫ ===
    
    def analyze_system_health(self, all_signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ общего состояния систем"""
        try:
            health_report = {
                'overall_status': 'healthy',
                'systems_status': {},
                'critical_faults': [],
                'active_chains': [],
                'recommendations': []
            }
            
            # Классифицируем все сигналы
            for signal in all_signals:
                signal_code = signal.get('signal_code', '')
                if not signal_code:
                    continue
                
                classification = self.signal_classifier.classify_signal(
                    signal_code, signal.get('description', '')
                )
                
                # Проверяем критичные сигналы
                if classification.criticality == SignalCriticality.CRITICAL:
                    health_report['critical_faults'].append(signal_code)
                    health_report['overall_status'] = 'critical'
                elif (classification.criticality == SignalCriticality.HIGH and 
                      health_report['overall_status'] == 'healthy'):
                    health_report['overall_status'] = 'warning'
                
                # Статус систем
                system_key = classification.system.value
                if system_key not in health_report['systems_status']:
                    health_report['systems_status'][system_key] = {
                        'status': 'healthy',
                        'fault_count': 0,
                        'critical_count': 0
                    }
                
                if classification.criticality in [SignalCriticality.HIGH, SignalCriticality.CRITICAL]:
                    health_report['systems_status'][system_key]['fault_count'] += 1
                    if classification.criticality == SignalCriticality.CRITICAL:
                        health_report['systems_status'][system_key]['critical_count'] += 1
                        health_report['systems_status'][system_key]['status'] = 'critical'
                    elif health_report['systems_status'][system_key]['status'] == 'healthy':
                        health_report['systems_status'][system_key]['status'] = 'warning'
            
            return health_report
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа состояния систем: {e}")
            return {'overall_status': 'unknown', 'error': str(e)}
    
    def clear_cache(self):
        """Очистка кэшей анализа"""
        cache_size = len(self._analysis_cache) + len(self._causal_chains_cache)
        self._analysis_cache.clear()
        self._causal_chains_cache.clear()
        self.logger.info(f"Очищены кэши анализа ({cache_size} элементов)")
