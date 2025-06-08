"""
Главный класс для управления интерактивностью графиков
"""
import logging
from typing import List, Dict, Any, Optional
from .interactions.base_interaction import CursorInteraction, TooltipInteraction, ZoomInteraction

class PlotInteractor:
    """Композитный класс для управления всеми типами интерактивности"""
    
    def __init__(self, canvas, figure, plot_params=None, config: Dict[str, Any] = None):
        self.canvas = canvas
        self.figure = figure
        self.plot_params = plot_params or []
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Интерактивные компоненты
        self.interactions: List[BaseInteraction] = []
        
        self._setup_interactions()
        
    def _setup_interactions(self):
        """Настройка всех типов интерактивности"""
        # Курсор и время
        if self.config.get('enable_cursor', True):
            cursor_config = self.config.get('cursor', {})
            self.interactions.append(
                CursorInteraction(self.canvas, self.figure, cursor_config)
            )
        
        # Подсказки
        if self.config.get('enable_tooltips', True):
            tooltip_config = self.config.get('tooltips', {})
            self.interactions.append(
                TooltipInteraction(self.canvas, self.figure, self.plot_params, tooltip_config)
            )
        
        # Масштабирование
        if self.config.get('enable_zoom', True):
            zoom_config = self.config.get('zoom', {})
            self.interactions.append(
                ZoomInteraction(self.canvas, self.figure, zoom_config)
            )
        
        # Включение всех интерактивностей
        for interaction in self.interactions:
            interaction.enable()
    
    def enable_interaction(self, interaction_type: str):
        """Включение конкретного типа интерактивности"""
        for interaction in self.interactions:
            if interaction.__class__.__name__.lower().startswith(interaction_type.lower()):
                interaction.enable()
                break
    
    def disable_interaction(self, interaction_type: str):
        """Отключение конкретного типа интерактивности"""
        for interaction in self.interactions:
            if interaction.__class__.__name__.lower().startswith(interaction_type.lower()):
                interaction.disable()
                break
    
    def cleanup(self):
        """Очистка всех ресурсов"""
        for interaction in self.interactions:
            interaction.cleanup()
        self.interactions.clear()
        self.logger.info("PlotInteractor очищен")
