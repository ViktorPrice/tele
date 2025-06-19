import logging
from typing import List, Dict, Any, Optional

class FilterController:
    """Контроллер для фильтрации параметров и управления фильтрами"""

    def __init__(self, model, view, event_emitter, ui_controller=None):
        self.model = model
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_emitter = event_emitter  # Функция или объект для эмиссии событий
        self.ui_controller = ui_controller  # Контроллер для работы с UI
        self._filter_criteria_cache: Optional[Dict[str, Any]] = None
        self.find_changed_params_use_case = None  # Можно внедрить через сеттер

    def apply_filters(self, changed_only: bool = False, **kwargs):
        """Применение фильтров с поддержкой приоритетного режима"""
        try:
            self.logger.info(
                f"Применение фильтров (changed_only={changed_only}): {kwargs}"
            )

            if not self._has_data():
                self._show_no_data_message()
                return

            priority_mode_active = self._is_priority_mode_active()

            if changed_only or priority_mode_active:
                self.logger.info(
                    "Приоритетный режим активен, применяем фильтр изменяемых параметров"
                )
                filter_panel = self.get_ui_component("filter_panel")
                if filter_panel and hasattr(filter_panel, "get_selected_filters"):
                    selected_filters = filter_panel.get_selected_filters()
                    combined_criteria = kwargs.copy()

                    def merge_lists(key):
                        vals1 = set(combined_criteria.get(key, []))
                        vals2 = set(selected_filters.get(key, []))
                        combined_criteria[key] = list(vals1.union(vals2))

                    for key in ["signal_types", "lines", "wagons"]:
                        merge_lists(key)

                else:
                    combined_criteria = kwargs

                self.logger.info(f"Приоритетные фильтры: {combined_criteria}")

                self._apply_priority_filters_with_criteria(combined_criteria)
                return

            self.logger.info("Применение обычных фильтров")
            all_params = self._get_all_parameters()
            filtered_params = self._detailed_filter_parameters(all_params, kwargs)
            self._update_ui_with_filtered_params(filtered_params)

            self.logger.info(
                f"Обычная фильтрация завершена: {len(filtered_params)} из {len(all_params)} параметров"
            )

        except Exception as e:
            self.logger.error(f"Ошибка применения фильтров: {e}")

    def _is_priority_mode_active(self) -> bool:
        """Проверка активности приоритетного режима"""
        try:
            filter_panel = self.get_ui_component("filter_panel")
            if filter_panel:
                if hasattr(filter_panel, "is_changed_only_active"):
                    return filter_panel.is_changed_only_active()
                if hasattr(filter_panel, "changed_only_var"):
                    return filter_panel.changed_only_var.get()
                if hasattr(filter_panel, "state") and hasattr(
                    filter_panel.state, "changed_only"
                ):
                    return filter_panel.state.changed_only

            time_panel = self.get_ui_component("time_panel")
            if time_panel:
                if hasattr(time_panel, "is_changed_only_enabled"):
                    return time_panel.is_changed_only_enabled()
                if hasattr(time_panel, "changed_only_var"):
                    return time_panel.changed_only_var.get()

            self.logger.debug("Приоритетный режим не активен")
            return False

        except Exception as e:
            self.logger.error(f"Ошибка проверки приоритетного режима: {e}")
            return False

    def _apply_priority_filters_with_criteria(self, filter_criteria: Dict[str, Any]):
        """Применение приоритетных фильтров с дополнительными критериями"""
        try:
            self.logger.info(f"Применение приоритетных фильтров с критериями: {filter_criteria}")

            start_time, end_time = self._get_time_range_unified()
            if not start_time or not end_time:
                self._show_time_error()
                return

            session_id = self.get_session_id()

            changed_params = self._get_changed_parameters(start_time, end_time, session_id)
            if not changed_params:
                self.logger.warning("Изменяемые параметры не найдены")
                if hasattr(self.view, "show_warning"):
                    self.view.show_warning("Изменяемые параметры не найдены в указанном диапазоне")
                return

            self.logger.info(f"Найдено {len(changed_params)} изменяемых параметров")

            if filter_criteria:
                filtered_changed_params = self._detailed_filter_parameters(changed_params, filter_criteria)
                self.logger.info(f"После применения фильтров: {len(filtered_changed_params)} из {len(changed_params)} параметров")
            else:
                filtered_changed_params = changed_params

            self._update_ui_with_filtered_params(filtered_changed_params)

            self._emit_event(
                "changed_params_filter_applied",
                {
                    "count": len(filtered_changed_params),
                    "total_changed": len(changed_params),
                    "time_range": {"start": start_time, "end": end_time},
                    "filter_criteria": filter_criteria,
                },
            )

            self.logger.info(f"Приоритетная фильтрация завершена: {len(filtered_changed_params)} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка приоритетной фильтрации с критериями: {e}")

    def _get_changed_parameters(self, start_time: str, end_time: str, session_id: str) -> List[Dict[str, Any]]:
        """Получение изменяемых параметров"""
        try:
            if hasattr(self, "find_changed_params_use_case") and self.find_changed_params_use_case:
                request = FindChangedParametersRequest(session_id=session_id, from_time=start_time, to_time=end_time)
                response = self.find_changed_params_use_case.execute(request)
                if response.success and response.changed_parameters:
                    self.logger.info(f"Use Case: найдено {len(response.changed_parameters)} изменяемых параметров")
                    return response.changed_parameters

            if hasattr(self.model, "data_loader") and self.model.data_loader and hasattr(self.model.data_loader, "filter_changed_params"):
                changed_params = self.model.data_loader.filter_changed_params(start_time, end_time)
                if changed_params:
                    self.logger.info(f"CSV Loader: найдено {len(changed_params)} изменяемых параметров")
                    return changed_params

            if hasattr(self.model, "data_model") and hasattr(self.model.data_model, "find_changed_parameters_in_range"):
                changed_params = self.model.data_model.find_changed_parameters_in_range(start_time, end_time)
                if changed_params:
                    self.logger.info(f"DataModel: найдено {len(changed_params)} изменяемых параметров")
                    return changed_params

            self.logger.warning("Все методы поиска изменяемых параметров не сработали")
            return []

        except Exception as e:
            self.logger.error(f"Ошибка получения изменяемых параметров: {e}")
            return []

    def _detailed_filter_parameters(
        self, parameters: List[Dict[str, Any]], criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Детальная фильтрация параметров с логированием"""
        try:
            filtered = parameters.copy()
            original_count = len(filtered)

            if criteria.get("signal_types"):
                signal_types = set(criteria["signal_types"])
                self.logger.info(f"Фильтр по типам сигналов: {signal_types}")

                before_count = len(filtered)
                filtered = [p for p in filtered if p.get("signal_type") in signal_types]
                after_count = len(filtered)

                self.logger.info(
                    f"Фильтр по типам: {before_count} → {after_count} параметров"
                )

            if criteria.get("lines"):
                lines = set(criteria["lines"])
                self.logger.info(f"Фильтр по линиям: {len(lines)} линий")

                before_count = len(filtered)
                filtered = [p for p in filtered if p.get("line") in lines]
                after_count = len(filtered)

                self.logger.info(
                    f"Фильтр по линиям: {before_count} → {after_count} параметров"
                )

            if criteria.get("wagons"):
                wagons = set(str(w) for w in criteria["wagons"])
                self.logger.info(f"Фильтр по вагонам: {wagons}")

                before_count = len(filtered)
                filtered = [p for p in filtered if str(p.get("wagon", "")) in wagons]
                after_count = len(filtered)

                self.logger.info(
                    f"Фильтр по вагонам: {before_count} → {after_count} параметров"
                )

            self.logger.info(
                f"Итоговая фильтрация: {original_count} → {len(filtered)} параметров"
            )
            return filtered

        except Exception as e:
            self.logger.error(f"Ошибка детальной фильтрации: {e}")
            return parameters

    def clear_all_filters(self):
        """Очистка всех фильтров"""
        try:
            self.logger.info("Очистка всех фильтров")

            filter_panel = self.get_ui_component("filter_panel")
            if filter_panel:
                if hasattr(filter_panel, "clear_all_filters"):
                    filter_panel.clear_all_filters()
                elif hasattr(filter_panel, "reset_filters"):
                    filter_panel.reset_filters()
                else:
                    self.logger.warning("Метод очистки фильтров не найден")

            self._filter_criteria_cache = None

            all_params = self._get_all_parameters()
            self._update_ui_with_filtered_params(all_params)

            self.logger.info(f"Фильтры очищены, показано {len(all_params)} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка очистки фильтров: {e}")

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

    def _show_no_data_message(self):
        """Показ сообщения об отсутствии данных"""
        if hasattr(self.view, "show_warning"):
            self.view.show_warning("Нет загруженных данных. Загрузите CSV файл.")

    def _show_time_error(self):
        """Показ ошибки времени"""
        if hasattr(self.view, "show_error"):
            self.view.show_error("Ошибка получения временного диапазона")

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

    def get_ui_component(self, component_name: str):
        """Получение UI компонента из view"""
        # Используем UtilsController для получения компонента
        if hasattr(self, "utils_controller") and self.utils_controller:
            return self.utils_controller.get_ui_component(self.view, component_name)
        # fallback к старой логике
        if hasattr(self.view, "ui_components") and self.view.ui_components:
            return getattr(self.view.ui_components, component_name, None)
        if hasattr(self.view, component_name):
            return getattr(self.view, component_name, None)
        return None

    def _emit_event(self, event_name: str, data: dict):
        """Эмитирование события через event_emitter"""
        if self.event_emitter:
            try:
                self.event_emitter(event_name, data)
                self.logger.info(f"Событие '{event_name}' эмитировано с данными: {data}")
            except Exception as e:
                self.logger.error(f"Ошибка эмитирования события '{event_name}': {e}")

    def _get_time_range_unified(self):
        """Получение временного диапазона из UI"""
        time_panel = self.get_ui_component("time_panel")
        if time_panel and hasattr(time_panel, "get_time_range"):
            return time_panel.get_time_range()
        return None, None

    def get_session_id(self) -> str:
        """Получение идентификатора сессии"""
        if hasattr(self.model, "get_session_id"):
            return self.model.get_session_id()
        return ""

    def _get_all_parameters(self) -> List[Dict[str, Any]]:
        """Получение всех параметров из модели"""
        try:
            if hasattr(self.model, "data_loader") and self.model.data_loader:
                if hasattr(self.model.data_loader, "get_parameters"):
                    return self.model.data_loader.get_parameters()
                elif hasattr(self.model.data_loader, "data") and self.model.data_loader.data is not None:
                    # Если есть данные, но нет метода get_parameters, возвращаем пустой список
                    self.logger.warning("data_loader.data существует, но метод get_parameters не найден")
                    return []
            
            if hasattr(self.model, "get_parameters"):
                return self.model.get_parameters()
                
            self.logger.warning("Не найден способ получения всех параметров")
            return []
            
        except Exception as e:
            self.logger.error(f"Ошибка получения всех параметров: {e}")
            return []
