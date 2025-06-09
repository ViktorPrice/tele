"""
Use Case для генерации графиков (PlotGenerationUseCase)
Минимальная современная реализация для интеграции с PlotVisualizationPanel
"""
from dataclasses import dataclass
from typing import List, Any, Optional
from datetime import datetime
import logging

@dataclass
class PlotGenerationRequest:
    parameters: List[Any]
    start_time: datetime
    end_time: datetime
    title: Optional[str] = None
    strategy: str = 'step'

@dataclass
class PlotGenerationResponse:
    figure: Any
    axes: Any
    success: bool
    message: str = ''

class PlotGenerationUseCase:
    """
    Use Case для построения графика (обёртка над PlotBuilder)
    """
    def __init__(self, plot_builder):
        self.plot_builder = plot_builder
        self.logger = logging.getLogger(self.__class__.__name__)

    def execute(self, request: PlotGenerationRequest) -> PlotGenerationResponse:
        try:
            figure, axes = self.plot_builder.build_plot(
                request.parameters,
                request.start_time,
                request.end_time,
                title=request.title or "График",
                strategy=request.strategy
            )
            return PlotGenerationResponse(figure=figure, axes=axes, success=True)
        except Exception as e:
            self.logger.error(f"Ошибка построения графика: {e}")
            return PlotGenerationResponse(figure=None, axes=None, success=False, message=str(e))
