"""
UI компоненты для анализатора телеметрии
"""

# Импорт всех панелей
from .ui_components import UIComponents
from .time_panel import TimePanel
from .compact_time_panel import CompactTimePanel
# from .filter_panel import FilterPanel  # Удалено, так как модуль удалён
from .smart_filter_panel import SmartFilterPanel  # Добавлено вместо filter_panel
# from .compact_filter_panel import CompactFilterPanel  # Удалено, так как модуль удалён
from .parameter_panel import ParameterPanel
from .horizontal_parameter_panel import HorizontalParameterPanel
from .action_panel import ActionPanel
from .horizontal_action_panel import HorizontalActionPanel

try:
    from .plot_visualization_panel import PlotVisualizationPanel
except ImportError:
    PlotVisualizationPanel = None

__all__ = [
    'UIComponents',
    'TimePanel',
    'CompactTimePanel', 
    'SmartFilterPanel',  # Добавлено
#    'CompactFilterPanel',
    'ParameterPanel',
    'HorizontalParameterPanel',
    'ActionPanel',
    'HorizontalActionPanel',
    'PlotVisualizationPanel'
]
