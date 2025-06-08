"""
Event Bus для слабой связанности между компонентами
"""
import logging
from typing import Dict, List, Callable, Any
from collections import defaultdict

class EventBus:
    """Простая реализация Event Bus"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
    
    def subscribe(self, event_type: str, handler: Callable):
        """Подписка на событие"""
        self._subscribers[event_type].append(handler)
        self.logger.debug(f"Подписка на событие '{event_type}': {handler.__name__}")
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """Отписка от события"""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            self.logger.debug(f"Отписка от события '{event_type}': {handler.__name__}")
    
    def publish(self, event_type: str, data: Any = None):
        """Публикация события"""
        self.logger.debug(f"Публикация события '{event_type}' с данными: {type(data)}")
        
        for handler in self._subscribers[event_type]:
            try:
                if data is not None:
                    handler(data)
                else:
                    handler()
            except Exception as e:
                self.logger.error(f"Ошибка в обработчике {handler.__name__} для события '{event_type}': {e}")
    
    def clear(self):
        """Очистка всех подписок"""
        self._subscribers.clear()
        self.logger.info("Все подписки очищены")
