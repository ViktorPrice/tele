"""
Координатор взаимодействия между UI компонентами
"""
import logging
from typing import Dict, Any, Callable
from collections import defaultdict

class UICoordinator:
    """Координатор для управления взаимодействием между UI компонентами"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.components: Dict[str, Any] = {}
        self.event_handlers: Dict[str, list] = defaultdict(list)
    
    def register_component(self, name: str, component: Any):
        """Регистрация компонента"""
        self.components[name] = component
        self.logger.debug(f"Зарегистрирован компонент: {name}")
    
    def setup_component_links(self):
        """Настройка связей между компонентами"""
        # Связь фильтров с параметрами
        if 'filter_panel' in self.components and 'parameter_panel' in self.components:
            self._link_filters_to_parameters()
        
        # Связь параметров с визуализацией
        if 'parameter_panel' in self.components and 'visualization' in self.components:
            self._link_parameters_to_visualization()
        
        # Связь времени с фильтрами
        if 'time_panel' in self.components and 'filter_panel' in self.components:
            self._link_time_to_filters()
    
    def _link_filters_to_parameters(self):
        """Связь фильтров с панелью параметров"""
        filter_panel = self.components['filter_panel']
        parameter_panel = self.components['parameter_panel']
        
        # При изменении фильтров обновляем параметры
        if hasattr(filter_panel, 'add_change_listener'):
            filter_panel.add_change_listener(parameter_panel.on_filters_changed)
    
    def _link_parameters_to_visualization(self):
        """Связь параметров с визуализацией"""
        parameter_panel = self.components['parameter_panel']
        visualization = self.components['visualization']
        
        # При изменении выбранных параметров обновляем графики
        if hasattr(parameter_panel, 'add_selection_listener'):
            parameter_panel.add_selection_listener(visualization.on_parameters_changed)
    
    def _link_time_to_filters(self):
        """Связь панели времени с фильтрами"""
        time_panel = self.components['time_panel']
        filter_panel = self.components['filter_panel']
        
        # При изменении времени обновляем фильтры
        if hasattr(time_panel, 'add_time_listener'):
            time_panel.add_time_listener(filter_panel.on_time_changed)
    
    def broadcast_event(self, event_type: str, data: Any = None):
        """Рассылка события всем заинтересованным компонентам"""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                self.logger.error(f"Ошибка в обработчике события {event_type}: {e}")
    
    def subscribe_to_event(self, event_type: str, handler: Callable):
        """Подписка на событие"""
        self.event_handlers[event_type].append(handler)
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.components.clear()
        self.event_handlers.clear()
        self.logger.info("UICoordinator очищен")
