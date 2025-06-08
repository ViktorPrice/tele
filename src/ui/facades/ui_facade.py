"""
Фасад для операций с UI
"""
import logging
from typing import List, Dict, Any

class UIFacade:
    """Фасад для упрощения операций с UI"""
    
    def __init__(self, view):
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def start_processing(self, message: str = "Обработка..."):
        """Начало обработки"""
        if hasattr(self.view, 'start_processing'):
            self.view.start_processing(message)
    
    def stop_processing(self):
        """Завершение обработки"""
        if hasattr(self.view, 'stop_processing'):
            self.view.stop_processing()
    
    def update_status(self, message: str):
        """Обновление статуса"""
        if hasattr(self.view, 'update_status'):
            self.view.update_status(message)
    
    def show_error(self, message: str):
        """Показ ошибки"""
        if hasattr(self.view, 'show_error'):
            self.view.show_error(message)
    
    def show_warning(self, message: str):
        """Показ предупреждения"""
        if hasattr(self.view, 'show_warning'):
            self.view.show_warning(message)
    
    def update_filtered_count(self, count: int):
        """Обновление счетчика отфильтрованных параметров"""
        if hasattr(self.view, 'update_filtered_count'):
            self.view.update_filtered_count(count)
    
    def get_selected_parameters(self) -> List[tuple]:
        """Получение выбранных параметров"""
        try:
            if hasattr(self.view, 'parameter_panel') and self.view.parameter_panel:
                tree = self.view.parameter_panel.selected_params_tree.tree
                return [tree.item(item, 'values') for item in tree.get_children()]
        except Exception as e:
            self.logger.error(f"Ошибка получения выбранных параметров: {e}")
        return []
    
    def get_time_range(self) -> tuple:
        """Получение временного диапазона"""
        try:
            if hasattr(self.view, 'time_panel') and self.view.time_panel:
                start_time = self.view.time_panel.start_time_entry.get()
                end_time = self.view.time_panel.end_time_entry.get()
                return start_time, end_time
        except Exception as e:
            self.logger.error(f"Ошибка получения временного диапазона: {e}")
        return "", ""
    
    def get_filter_states(self) -> Dict[str, List[str]]:
        """Получение состояния фильтров"""
        try:
            if hasattr(self.view, 'filter_panel') and self.view.filter_panel:
                return {
                    'signal_types': [k for k, v in self.view.filter_panel.signal_vars.items() if v.get()],
                    'lines': [k for k, v in self.view.filter_panel.line_vars.items() if v.get()],
                    'wagons': [k for k, v in self.view.filter_panel.wagon_vars.items() if v.get()],
                    'components': [k for k, v in self.view.filter_panel.component_vars.items() if v.get()],
                    'hardware': [k for k, v in self.view.filter_panel.hardware_vars.items() if v.get()]
                }
        except Exception as e:
            self.logger.error(f"Ошибка получения состояния фильтров: {e}")
        return {}
