"""
Адаптер для интеграции matplotlib с tkinter виджетами
"""
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...infrastructure.plotting.interactions.plot_interactor import PlotInteractor

class MatplotlibWidgetAdapter:
    """Адаптер для создания matplotlib виджетов в tkinter"""
    
    def __init__(self, parent):
        self.parent = parent
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Компоненты matplotlib
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.toolbar: Optional[NavigationToolbar2Tk] = None
        self.ax = None
        self.interactor: Optional[PlotInteractor] = None
        
        self._setup_layout()
    
    def _setup_layout(self):
        """Настройка layout для matplotlib компонентов"""
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
    
    def build_plot(self, params: List[Dict[str, Any]], start_time: datetime, 
                   end_time: datetime, title: str = "") -> bool:
        """Построение графика"""
        try:
            # Создание новой фигуры
            self.figure = Figure(figsize=(10, 6), dpi=100, facecolor='white')
            self.ax = self.figure.add_subplot(111)
            
            # Получение данных (здесь нужна интеграция с data_loader)
            # Это заглушка - в реальности данные получаются из контроллера
            success = self._plot_parameters(params, start_time, end_time)
            
            if success:
                # Настройка внешнего вида
                self._configure_plot_appearance(title, start_time, end_time)
                
                # Создание canvas если еще не создан
                if not self.canvas:
                    self._create_canvas()
                else:
                    # Обновление существующего canvas
                    self.canvas.figure = self.figure
                
                self.canvas.draw()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка построения графика: {e}")
            return False
    
    def _create_canvas(self):
        """Создание canvas и toolbar"""
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.figure, self.parent)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        
        # Toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.parent)
        self.toolbar.grid(row=1, column=0, sticky="ew")
    
    def _plot_parameters(self, params: List[Dict[str, Any]], 
                        start_time: datetime, end_time: datetime) -> bool:
        """Построение параметров на графике"""
        # Заглушка - в реальности здесь интеграция с DataLoader
        # Для демонстрации создаем тестовые данные
        
        if not params:
            return False
        
        # Создание тестовых временных меток
        time_range = pd.date_range(start_time, end_time, periods=100)
        timestamps_num = mdates.date2num(time_range)
        
        colors = plt.cm.tab20(np.linspace(0, 1, len(params)))
        
        for idx, param in enumerate(params):
            # Тестовые данные
            values = np.random.randn(100).cumsum()
            
            label = param.get('signal_code', f'Param_{idx}')
            color = colors[idx % len(colors)]
            
            self.ax.step(timestamps_num, values, label=label, 
                        color=color, linewidth=1.5, where='post')
        
        return True
    
    def _configure_plot_appearance(self, title: str, start_time: datetime, end_time: datetime):
        """Настройка внешнего вида графика"""
        # Заголовок и подписи
        self.ax.set_title(title, fontsize=12, fontweight='bold')
        self.ax.set_xlabel("Время", fontsize=10)
        self.ax.set_ylabel("Значение", fontsize=10)
        
        # Сетка
        self.ax.grid(True, alpha=0.3)
        
        # Настройка оси времени
        duration = (end_time - start_time).total_seconds()
        if duration <= 60:
            locator = mdates.SecondLocator(interval=5)
            formatter = mdates.DateFormatter("%H:%M:%S")
        else:
            locator = mdates.AutoDateLocator()
            formatter = mdates.DateFormatter("%H:%M:%S")
        
        self.ax.xaxis.set_major_locator(locator)
        self.ax.xaxis.set_major_formatter(formatter)
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Легенда
        if self.ax.get_lines():
            self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        
        # Улучшение внешнего вида
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        self.figure.tight_layout()
    
    def add_interactivity(self, info_panel, params: List[Dict[str, Any]]):
        """Добавление интерактивности к графику"""
        if self.canvas and self.figure:
            self.interactor = PlotInteractor(self.canvas, self.figure, params)
    
    def show_message(self, message: str, color: str = 'gray'):
        """Отображение сообщения на графике"""
        if not self.figure:
            self.figure = Figure(figsize=(10, 6), dpi=100, facecolor='white')
            self.ax = self.figure.add_subplot(111)
        
        self.ax.clear()
        self.ax.text(0.5, 0.5, message, ha='center', va='center', 
                    transform=self.ax.transAxes, fontsize=12, color=color)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis('off')
        
        if not self.canvas:
            self._create_canvas()
        else:
            self.canvas.draw()
    
    def export_plot(self, file_path: str, dpi: int = 300) -> bool:
        """Экспорт графика в файл"""
        try:
            if self.figure:
                self.figure.savefig(file_path, dpi=dpi, bbox_inches='tight',
                                  facecolor='white', edgecolor='none')
                return True
            return False
        except Exception as e:
            self.logger.error(f"Ошибка экспорта: {e}")
            return False
    
    def reset_zoom(self):
        """Сброс масштабирования"""
        if self.interactor:
            self.interactor.reset_zoom()
        elif self.ax:
            self.ax.autoscale()
            if self.canvas:
                self.canvas.draw()
    
    def apply_settings(self, settings: Dict[str, Any]):
        """Применение настроек к графику"""
        if not self.ax:
            return
        
        # Сетка
        if 'grid' in settings:
            self.ax.grid(settings['grid'])
        
        # Легенда
        if 'legend' in settings:
            legend = self.ax.get_legend()
            if legend:
                legend.set_visible(settings['legend'])
        
        # Интерактивность
        if self.interactor:
            if 'cursor' in settings:
                if settings['cursor']:
                    self.interactor.enable_interaction('cursor')
                else:
                    self.interactor.disable_interaction('cursor')
            
            if 'tooltips' in settings:
                if settings['tooltips']:
                    self.interactor.enable_interaction('tooltip')
                else:
                    self.interactor.disable_interaction('tooltip')
        
        if self.canvas:
            self.canvas.draw()
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.interactor:
            self.interactor.cleanup()
        
        if self.figure:
            plt.close(self.figure)
        
        self.logger.info("MatplotlibWidgetAdapter очищен")
