# src/ui/components/__init__.py
"""
UI компоненты для анализатора телеметрии
"""

# Импорт всех панелей
from .ui_components import UIComponents
from .time_panel import TimePanel
from .compact_time_panel import CompactTimePanel
from .filter_panel import FilterPanel
from .compact_filter_panel import CompactFilterPanel
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
    'FilterPanel',
    'CompactFilterPanel',
    'ParameterPanel',
    'HorizontalParameterPanel',
    'ActionPanel',
    'HorizontalActionPanel',
    'PlotVisualizationPanel'
]
