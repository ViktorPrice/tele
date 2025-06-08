"""
Менеджер состояния UI
"""
import logging

class StateManager:
    """Менеджер состояния UI"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.state = {}
    
    def cleanup(self):
        """Очистка состояния"""
        self.state.clear()
