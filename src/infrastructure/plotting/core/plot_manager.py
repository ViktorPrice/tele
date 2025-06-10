#src\infrastructure\plotting\core\plot_manager.py
"""
Главный менеджер графиков БЕЗ legacy зависимостей
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .plot_builder import PlotBuilder

class PlotManager:
    """Главный менеджер графиков (полностью новая реализация)"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Новые компоненты
        self.plot_builder = PlotBuilder(data_loader)
        self.active_plots = {}
        
        self.logger.info("PlotManager (новая архитектура) инициализирован")
    
    def build_plot_for_params(self, params: List[Dict[str, Any]], 
                             start_time: datetime, end_time: datetime, 
                             parent_widget) -> bool:
        """Построение графика для параметров"""
        try:
            # Создание графика через PlotBuilder
            figure, ax = self.plot_builder.build_plot(
                params, start_time, end_time, 
                title=f"График параметров ({len(params)} сигналов)"
            )
            
            # Отображение в parent_widget
            success = self._display_plot_in_widget(figure, parent_widget, params)
            
            if success:
                self.logger.info(f"График построен для {len(params)} параметров")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Ошибка построения графика: {e}")
            return False
    
    def _display_plot_in_widget(self, figure, parent_widget, params) -> bool:
        """Отображение графика в виджете"""
        try:
            from ..adapters.tkinter_plot_adapter import TkinterPlotAdapter
            
            # Создание адаптера для отображения
            adapter = TkinterPlotAdapter()
            
            # Создание виджета графика
            canvas, info_panel = adapter.create_plot_widget(
                parent_widget, figure, "main_plot", params
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка отображения графика: {e}")
            return False
