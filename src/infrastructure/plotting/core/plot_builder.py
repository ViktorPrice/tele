"""
Построитель графиков с поддержкой различных стратегий
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Optional, Protocol
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.axes import Axes

class PlotStrategy(Protocol):
    """Протокол для стратегий построения графиков"""
    
    def plot(self, ax: Axes, x_data: np.ndarray, y_data: np.ndarray, 
             label: str, **kwargs) -> Any:
        """Построение графика по стратегии"""
        ...

class LinePlotStrategy:
    """Стратегия линейных графиков"""
    
    def plot(self, ax: Axes, x_data: np.ndarray, y_data: np.ndarray, 
             label: str, **kwargs) -> Any:
        return ax.plot(x_data, y_data, label=label, **kwargs)

class StepPlotStrategy:
    """Стратегия ступенчатых графиков (для дискретных сигналов)"""
    
    def plot(self, ax: Axes, x_data: np.ndarray, y_data: np.ndarray, 
             label: str, **kwargs) -> Any:
        return ax.step(x_data, y_data, label=label, where='post', **kwargs)

class ScatterPlotStrategy:
    """Стратегия точечных графиков"""
    
    def plot(self, ax: Axes, x_data: np.ndarray, y_data: np.ndarray, 
             label: str, **kwargs) -> Any:
        return ax.scatter(x_data, y_data, label=label, **kwargs)

class PlotBuilder:
    """Построитель графиков с использованием стратегий"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Стратегии построения
        self.strategies = {
            'line': LinePlotStrategy(),
            'step': StepPlotStrategy(),
            'scatter': ScatterPlotStrategy()
        }
        
        # Настройки по умолчанию
        self.default_colors = plt.cm.tab20(np.linspace(0, 1, 20))
        self.max_params_per_plot = 20
    
    def build_plot(self, params: List[Dict[str, Any]], start_time: datetime, 
                   end_time: datetime, title: str = "", 
                   strategy: str = 'step') -> tuple[Figure, Axes]:
        """Построение графика с заданными параметрами"""
        try:
            # Создание фигуры
            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            fig.patch.set_facecolor('white')
            
            # Получение данных
            filtered_df = self.data_loader.filter_by_time_range(start_time, end_time)
            if filtered_df.empty:
                self._show_no_data_message(ax, "Нет данных в указанном диапазоне")
                return fig, ax
            
            # Ограничение количества параметров
            params = params[:self.max_params_per_plot]
            
            # Построение линий для каждого параметра
            lines_plotted = self._plot_parameters(ax, params, filtered_df, strategy)
            
            if lines_plotted == 0:
                self._show_no_data_message(ax, "Нет валидных данных для отображения")
                return fig, ax
            
            # Настройка внешнего вида
            self._configure_plot_appearance(ax, title, start_time, end_time)
            
            # Финальная настройка
            fig.tight_layout()
            
            self.logger.info(f"График построен: {lines_plotted} параметров")
            return fig, ax
            
        except Exception as e:
            self.logger.error(f"Ошибка построения графика: {e}")
            raise
    
    def _plot_parameters(self, ax: Axes, params: List[Dict[str, Any]], 
                        filtered_df: pd.DataFrame, strategy: str) -> int:
        """Построение параметров на графике"""
        if 'timestamp' not in filtered_df.columns:
            self.logger.error("Отсутствует столбец времени")
            return 0
        
        # Преобразование времени в числовой формат для matplotlib
        timestamps_num = mdates.date2num(filtered_df['timestamp'])
        
        plot_strategy = self.strategies.get(strategy, self.strategies['step'])
        lines_plotted = 0
        
        for idx, param in enumerate(params):
            try:
                col_name = param.get('full_column')
                if not col_name or col_name not in filtered_df.columns:
                    continue
                
                # Преобразование значений в числовой формат
                values = pd.to_numeric(filtered_df[col_name], errors='coerce')
                if values.dropna().empty:
                    continue
                
                # Создание метки для легенды
                label = self._create_parameter_label(param, idx)
                
                # Выбор цвета
                color = self.default_colors[idx % len(self.default_colors)]
                
                # Построение линии с использованием стратегии
                plot_strategy.plot(
                    ax, timestamps_num, values, label=label,
                    color=color, linewidth=1.5, alpha=0.8
                )
                
                lines_plotted += 1
                
            except Exception as e:
                self.logger.warning(f"Ошибка построения параметра {param.get('signal_code', 'Unknown')}: {e}")
                continue
        
        return lines_plotted
    
    def _create_parameter_label(self, param: Dict[str, Any], index: int) -> str:
        """Создание метки для параметра"""
        signal_code = param.get('signal_code', f'Param_{index}')
        description = param.get('description', '')
        
        if description:
            # Ограничиваем длину описания
            max_desc_length = 30
            if len(description) > max_desc_length:
                description = description[:max_desc_length] + '...'
            return f"{signal_code} - {description}"
        else:
            return signal_code
    
    def _configure_plot_appearance(self, ax: Axes, title: str, 
                                  start_time: datetime, end_time: datetime):
        """Настройка внешнего вида графика"""
        # Заголовок и подписи осей
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel("Время", fontsize=12)
        ax.set_ylabel("Значение", fontsize=12)
        
        # Сетка
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Настройка оси времени
        self._configure_time_axis(ax, start_time, end_time)
        
        # Легенда
        if ax.get_lines():
            legend = ax.legend(
                bbox_to_anchor=(1.05, 1), loc='upper left',
                fontsize=8, frameon=True, fancybox=True, shadow=True
            )
            legend.get_frame().set_alpha(0.9)
        
        # Автоматическое масштабирование по Y
        ax.autoscale(axis='y', tight=True)
        
        # Улучшение внешнего вида
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')
    
    def _configure_time_axis(self, ax: Axes, start_time: datetime, end_time: datetime):
        """Настройка оси времени"""
        duration = (end_time - start_time).total_seconds()
        
        if duration <= 1:
            locator = mdates.MicrosecondLocator(interval=100000)
            formatter = mdates.DateFormatter("%H:%M:%S.%f")
        elif duration <= 10:
            locator = mdates.SecondLocator(interval=1)
            formatter = mdates.DateFormatter("%H:%M:%S")
        elif duration <= 60:
            locator = mdates.SecondLocator(interval=5)
            formatter = mdates.DateFormatter("%H:%M:%S")
        else:
            locator = mdates.AutoDateLocator()
            formatter = mdates.DateFormatter("%H:%M:%S")
        
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        
        # Поворот меток времени
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Установка пределов времени
        ax.set_xlim(mdates.date2num(start_time), mdates.date2num(end_time))
    
    def _show_no_data_message(self, ax: Axes, message: str):
        """Отображение сообщения об отсутствии данных"""
        ax.text(0.5, 0.5, message, ha='center', va='center', 
                transform=ax.transAxes, fontsize=12, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
