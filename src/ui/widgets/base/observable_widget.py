"""
Базовый класс для виджетов с поддержкой паттерна Observer
"""
from typing import List, Callable, Any, Dict
import logging

class ObservableWidget:
    """Базовый класс для наблюдаемых виджетов"""
    
    def __init__(self):
        self.observers: List[Callable] = []
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def add_observer(self, observer: Callable):
        """Добавление наблюдателя"""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def remove_observer(self, observer: Callable):
        """Удаление наблюдателя"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def notify_observers(self, event_type: str, data: Any = None):
        """Уведомление всех наблюдателей"""
        for observer in self.observers:
            try:
                observer(event_type, data)
            except Exception as e:
                self.logger.error(f"Ошибка в наблюдателе: {e}")
