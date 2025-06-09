"""
Вспомогательные функции для MainController
"""
import re
import time
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Callable, Optional, Tuple

def has_data(controller) -> bool:
    """Проверка наличия данных для работы"""
    return (hasattr(controller.model, 'data_loader') and
            controller.model.data_loader and
            hasattr(controller.model.data_loader, 'parameters') and
            controller.model.data_loader.parameters)

def get_all_parameters(controller) -> List[Any]:
    """Получение всех параметров"""
    if has_data(controller):
        return controller.model.data_loader.parameters
    return []

def show_no_data_message(controller):
    """Показ сообщения об отсутствии данных"""
    if hasattr(controller.view, 'show_warning'):
        controller.view.show_warning("Загрузите CSV файл для отображения параметров")
    update_ui_with_filtered_params(controller, [])

def show_time_error(controller):
    """Показ ошибки времени"""
    if hasattr(controller.view, 'show_error'):
        controller.view.show_error("Не удалось получить временной диапазон")

def start_loading(controller, message: str = "Загрузка..."):
    """Начало процесса загрузки"""
    controller.is_loading = True
    if hasattr(controller.view, 'start_processing'):
        controller.view.start_processing(message)

def stop_loading(controller):
    """Завершение процесса загрузки"""
    controller.is_loading = False
    if hasattr(controller.view, 'stop_processing'):
        controller.view.stop_processing()

# ...другие вспомогательные методы по аналогии...

def update_ui_with_filtered_params(controller, filtered_params: List[Any]):
    """Обновление UI с отфильтрованными параметрами"""
    try:
        cleaned_params = clean_parameter_descriptions(controller, filtered_params)
        if hasattr(controller.view, 'update_filtered_count'):
            controller.view.update_filtered_count(len(cleaned_params))
        update_parameters_in_ui(controller, cleaned_params)
        if hasattr(controller.view, 'root'):
            controller.view.root.update_idletasks()
        controller._emit_event('filters_applied', {'count': len(cleaned_params)})
        controller.logger.info(f"UI обновлен с отфильтрованными параметрами: {len(cleaned_params)}")
    except Exception as e:
        controller.logger.error(f"Ошибка обновления UI с отфильтрованными параметрами: {e}")

def clean_parameter_descriptions(controller, params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Очистка описаний параметров от артефактов"""
    try:
        cleaned_params = []
        for param in params:
            if isinstance(param, dict):
                clean_param = param.copy()
                description = clean_param.get('description', '')
                if description:
                    description = description.replace('|0', '').replace('|', '').strip()
                    description = re.sub(r'\s+', ' ', description).strip()
                    if not description and clean_param.get('signal_code'):
                        description = clean_param['signal_code']
                    clean_param['description'] = description
                cleaned_params.append(clean_param)
            else:
                cleaned_params.append(param)
        controller.logger.debug(f"Очищены описания {len(cleaned_params)} параметров")
        return cleaned_params
    except Exception as e:
        controller.logger.error(f"Ошибка очистки описаний параметров: {e}")
        return params

def update_parameters_in_ui(controller, parameters: List[Dict[str, Any]]):
    """УНИВЕРСАЛЬНОЕ обновление параметров в UI"""
    try:
        controller.logger.info(f"Обновление {len(parameters)} параметров в UI")
        if (hasattr(controller.view, 'ui_components') and 
            controller.view.ui_components and 
            hasattr(controller.view.ui_components, 'parameter_panel')):
            parameter_panel = controller.view.ui_components.parameter_panel
            if hasattr(parameter_panel, 'update_parameters'):
                parameter_panel.update_parameters(parameters)
                controller.logger.info("✅ Параметры обновлены через ui_components.parameter_panel.update_parameters")
                return
            elif hasattr(parameter_panel, 'update_tree_all_params'):
                parameter_panel.update_tree_all_params(parameters)
                controller.logger.info("✅ Параметры обновлены через ui_components.parameter_panel.update_tree_all_params")
                return
        if hasattr(controller.view, 'update_tree_all_params'):
            controller.view.update_tree_all_params(parameters)
            controller.logger.info("✅ Параметры обновлены через view.update_tree_all_params")
            return
        if hasattr(controller.view, 'parameter_panel') and controller.view.parameter_panel:
            parameter_panel = controller.view.parameter_panel
            if hasattr(parameter_panel, 'update_parameters'):
                parameter_panel.update_parameters(parameters)
                controller.logger.info("✅ Параметры обновлены через view.parameter_panel.update_parameters")
                return
        controller.logger.error("❌ Не найден способ обновления параметров в UI")
    except Exception as e:
        controller.logger.error(f"Ошибка обновления параметров в UI: {e}")
