import logging
from datetime import datetime
from typing import List, Dict, Any

class DiagnosticController:
    """Контроллер для диагностики и анализа параметров"""

    def __init__(self, model, view, event_emitter, ui_controller=None):
        self.model = model
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_emitter = event_emitter  # Функция или объект для эмиссии событий
        self.ui_controller = ui_controller  # Контроллер для работы с UI

    def apply_diagnostic_filters(self, diagnostic_criteria: Dict[str, List[str]]):
        """Применение диагностических фильтров"""
        try:
            self.logger.info(f"Применение диагностических фильтров: {diagnostic_criteria}")

            if not self._has_data():
                self.logger.warning("Нет данных для диагностической фильтрации")
                if hasattr(self.view, "show_warning"):
                    self.view.show_warning("Нет данных для диагностического анализа")
                return

            all_params = self._get_all_parameters()

            from src.config.diagnostic_filters_config import (
                CRITICAL_FILTERS,
                SYSTEM_FILTERS,
                FUNCTIONAL_FILTERS,
            )

            def matches_patterns(param, patterns):
                text = f"{param.get('signal_code', '').upper()} {param.get('description', '').upper()}"
                return any(pat in text for pat in patterns)

            filtered = []

            for param in all_params:
                match = False

                for crit_key in diagnostic_criteria.get("criticality", []):
                    crit_conf = CRITICAL_FILTERS.get(crit_key)
                    if crit_conf and matches_patterns(param, crit_conf["patterns"]):
                        match = True
                        break

                if not match:
                    for sys_key in diagnostic_criteria.get("systems", []):
                        sys_conf = SYSTEM_FILTERS.get(sys_key)
                        if sys_conf and matches_patterns(param, sys_conf["patterns"]):
                            match = True
                            break

                if not match:
                    for func_key in diagnostic_criteria.get("functions", []):
                        func_conf = FUNCTIONAL_FILTERS.get(func_key)
                        if func_conf and matches_patterns(param, func_conf["patterns"]):
                            match = True
                            break

                if match:
                    filtered.append(param)

            self._update_ui_with_filtered_params(filtered)
            if self.event_emitter:
                self.event_emitter(
                    "diagnostic_filters_applied",
                    {"count": len(filtered), "criteria": diagnostic_criteria},
                )

            self.logger.info(f"Диагностическая фильтрация завершена: {len(filtered)} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка применения диагностических фильтров: {e}")

    def reset_diagnostic_filters(self):
        """Сброс диагностических фильтров"""
        try:
            self.logger.info("Сброс диагностических фильтров")

            if self._has_data():
                all_params = self._get_all_parameters()
                self._update_ui_with_filtered_params(all_params)

            if self.event_emitter:
                self.event_emitter("diagnostic_filters_applied", {"count": 0, "criteria": {}})

            self.logger.info("Диагностические фильтры сброшены")

        except Exception as e:
            self.logger.error(f"Ошибка сброса диагностических фильтров: {e}")

    def perform_diagnostic_analysis(self):
        """Выполнение диагностического анализа"""
        try:
            self.logger.info("Выполнение диагностического анализа")

            if not self._has_data():
                self.logger.warning("Нет данных для диагностического анализа")
                if hasattr(self.view, "show_warning"):
                    self.view.show_warning("Нет данных для анализа")
                return

            all_params = self._get_all_parameters()

            critical_faults = []
            systems_status = {}
            recommendations = []

            from src.config.diagnostic_filters_config import (
                CRITICAL_FILTERS,
                SYSTEM_FILTERS,
                COMPONENT_MAPPING,
            )

            for param in all_params:
                text = f"{param.get('signal_code', '').upper()} {param.get('description', '').upper()}"
                for crit_key, crit_conf in CRITICAL_FILTERS.items():
                    if any(pat in text for pat in crit_conf["patterns"]):
                        critical_faults.append(param.get("signal_code", ""))
                        break

            for sys_key in SYSTEM_FILTERS.keys():
                count_faults = sum(
                    1
                    for param in all_params
                    if any(
                        pat
                        in f"{param.get('signal_code', '').upper()} {param.get('description', '').upper()}"
                        for pat in SYSTEM_FILTERS[sys_key]["patterns"]
                    )
                )
                systems_status[sys_key] = {
                    "fault_count": count_faults,
                    "status": "critical" if count_faults > 0 else "normal",
                }

            if critical_faults:
                recommendations.append("Проверьте критичные неисправности и примите меры.")
            else:
                recommendations.append("Система работает в нормальном режиме.")

            results = {
                "total_parameters": len(all_params),
                "critical_faults": critical_faults,
                "systems_status": systems_status,
                "recommendations": recommendations,
                "overall_status": "critical" if critical_faults else "normal",
                "timestamp": datetime.now().isoformat(),
            }

            if hasattr(self.view, "show_info"):
                message = f"Диагностический анализ завершен. Статус: {results['overall_status'].upper()}"
                self.view.show_info("Диагностический анализ", message)

            if self.event_emitter:
                self.event_emitter("diagnostic_analysis_completed", results)

            self.logger.info(f"Диагностический анализ завершен: {results['overall_status']}")

        except Exception as e:
            self.logger.error(f"Ошибка диагностического анализа: {e}")

    def _update_ui_with_filtered_params(self, parameters: List[Dict[str, Any]]):
        """Обновление UI с отфильтрованными параметрами через UIController"""
        try:
            if self.ui_controller:
                self.ui_controller.update_parameters(parameters, emit_event=True)
                self.logger.info(f"✅ Параметры обновлены через UIController: {len(parameters)} элементов")
            else:
                self.logger.error("❌ UIController не доступен для обновления параметров")
                # Fallback к старому способу
                parameter_panel = self.get_ui_component("parameter_panel")
                if parameter_panel and hasattr(parameter_panel, "update_parameters"):
                    parameter_panel.update_parameters(parameters)
                    self.logger.info(f"Параметры обновлены через fallback: {len(parameters)} элементов")

        except Exception as e:
            self.logger.error(f"Ошибка обновления UI с параметрами: {e}")

    def _get_all_parameters(self) -> List[Dict[str, Any]]:
        """Получение всех параметров из модели"""
        try:
            if hasattr(self.model, "get_all_parameters"):
                params = self.model.get_all_parameters()
            elif hasattr(self.model, "data_loader") and hasattr(
                self.model.data_loader, "get_parameters"
            ):
                params = self.model.data_loader.get_parameters()
            else:
                self.logger.warning("Не удалось получить параметры из модели")
                return []

            if params and hasattr(params[0], "to_dict"):
                return [param.to_dict() for param in params]
            return params or []

        except Exception as e:
            self.logger.error(f"Ошибка получения всех параметров: {e}")
            return []

    def _has_data(self) -> bool:
        """Проверка наличия загруженных данных"""
        try:
            if hasattr(self.model, "data_loader") and self.model.data_loader:
                return (
                    hasattr(self.model.data_loader, "data")
                    and self.model.data_loader.data is not None
                )
            return False
        except Exception as e:
            self.logger.error(f"Ошибка проверки данных: {e}")
            return False

    def get_ui_component(self, component_name: str):
        """Получение UI компонента из view"""
        if hasattr(self.view, "ui_components") and self.view.ui_components:
            return getattr(self.view.ui_components, component_name, None)
        if hasattr(self.view, component_name):
            return getattr(self.view, component_name, None)
        return None
