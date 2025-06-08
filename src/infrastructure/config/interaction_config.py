"""
Конфигурация интерактивности графиков
"""
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class InteractionConfig:
    """Конфигурация интерактивных элементов графика"""
    
    enable_cursor: bool = True
    enable_tooltips: bool = True
    enable_zoom: bool = True
    enable_annotations: bool = True
    
    cursor_color: str = 'red'
    cursor_alpha: float = 0.7
    time_format: str = '%H:%M:%S.%f'
    
    zoom_factor: float = 1.2
    max_zoom_history: int = 20
    
    tooltip_background: str = '#ffffe0'
    tooltip_wrap_length: int = 400
    
    @classmethod
    def get_default(cls) -> 'InteractionConfig':
        """Конфигурация по умолчанию"""
        return cls()
    
    @classmethod
    def get_minimal(cls) -> 'InteractionConfig':
        """Минимальная конфигурация для производительности"""
        return cls(
            enable_cursor=True,
            enable_tooltips=False,
            enable_zoom=True,
            enable_annotations=False
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'enable_cursor': self.enable_cursor,
            'enable_tooltips': self.enable_tooltips,
            'enable_zoom': self.enable_zoom,
            'cursor': {
                'cursor_color': self.cursor_color,
                'cursor_alpha': self.cursor_alpha,
                'time_format': self.time_format
            },
            'zoom': {
                'zoom_factor': self.zoom_factor,
                'max_zoom_history': self.max_zoom_history
            },
            'tooltips': {
                'tooltip_background': self.tooltip_background,
                'tooltip_wrap_length': self.tooltip_wrap_length
            }
        }
