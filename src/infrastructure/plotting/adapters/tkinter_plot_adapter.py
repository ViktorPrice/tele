"""
Адаптер для интеграции matplotlib с tkinter
"""
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

# Добавляем корневую папку в путь для импорта оригинальных модулей
root_path = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(root_path))

# ИСПОЛЬЗУЕМ ваш полноценный InteractivePlot
from interactive_plot import InteractivePlot

class TkinterPlotAdapter:
    """Адаптер для отображения matplotlib графиков в tkinter"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.canvases = {}
        self.interactors = {}
    
    def create_plot_widget(self, parent, figure: Figure, tab_name: str, 
                          plot_params=None) -> Tuple[FigureCanvasTkAgg, Optional[tk.Text]]:
        """Создание виджета графика с полной интерактивностью"""
        try:
            # Создание основного контейнера
            plot_container = ttk.Frame(parent)
            plot_container.grid(row=0, column=0, sticky="nsew")
            plot_container.grid_rowconfigure(0, weight=1)
            plot_container.grid_columnconfigure(0, weight=1)
            
            # PanedWindow для разделения графика и панели информации
            paned = tk.PanedWindow(plot_container, orient=tk.HORIZONTAL)
            paned.grid(row=0, column=0, sticky="nsew")
            
            # Левая часть - график
            plot_frame = ttk.Frame(paned)
            paned.add(plot_frame, minsize=600)
            
            # Правая часть - панель информации
            info_frame = ttk.Frame(paned, width=300)
            paned.add(info_frame, minsize=250)
            
            # Создание canvas
            canvas = self._create_canvas(plot_frame, figure)
            
            # Создание панели информации (как в вашем InteractivePlot)
            info_panel = self._create_info_panel(info_frame)
            
            # ПОЛНАЯ интерактивность с вашим InteractivePlot
            interactor = InteractivePlot(canvas, figure, info_panel, plot_params)
            
            # Сохранение ссылок
            self.canvases[tab_name] = canvas
            self.interactors[tab_name] = interactor
            
            self.logger.info(f"Создан полноценный интерактивный график для вкладки '{tab_name}'")
            return canvas, info_panel
            
        except Exception as e:
            self.logger.error(f"Ошибка создания виджета графика: {e}")
            raise
    
    def _create_canvas(self, parent, figure: Figure) -> FigureCanvasTkAgg:
        """Создание canvas для matplotlib"""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Создание canvas
        canvas = FigureCanvasTkAgg(figure, parent)
        canvas.draw()
        
        # Размещение canvas
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        
        # Создание toolbar
        toolbar = NavigationToolbar2Tk(canvas, parent)
        toolbar.grid(row=1, column=0, sticky="ew")
        
        return canvas
    
    def _create_info_panel(self, parent) -> tk.Text:
        """Создание панели информации (точно как в InteractivePlot)"""
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Заголовок
        title_label = ttk.Label(parent, text="Значения параметров", 
                               font=('Arial', 10, 'bold'))
        title_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Текстовое поле с прокруткой (как в InteractivePlot)
        text_frame = ttk.Frame(parent)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            height=15,
            width=35,
            font=('Consolas', 9),
            bg='#f8f8f8',
            fg='#333333',
            relief='flat',
            borderwidth=1,
            state=tk.DISABLED  # Как в InteractivePlot
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        return text_widget
    
    def update_plot(self, tab_name: str, figure: Figure):
        """Обновление существующего графика"""
        if tab_name in self.canvases:
            canvas = self.canvases[tab_name]
            canvas.figure = figure
            canvas.draw()
            
            # Обновляем интерактивность
            if tab_name in self.interactors:
                interactor = self.interactors[tab_name]
                interactor.figure = figure
                interactor.ax = figure.axes[0] if figure.axes else None
                interactor._setup_line_picking()  # Переустанавливаем picker для новых линий
            
            self.logger.info(f"График '{tab_name}' обновлен с сохранением интерактивности")
    
    def remove_plot(self, tab_name: str):
        """Удаление графика и очистка ресурсов"""
        if tab_name in self.interactors:
            interactor = self.interactors[tab_name]
            # Ваш InteractivePlot может не иметь cleanup, но имеет clear_annotations
            if hasattr(interactor, 'clear_annotations'):
                interactor.clear_annotations()
            if hasattr(interactor, 'cleanup'):
                interactor.cleanup()
            del self.interactors[tab_name]
        
        if tab_name in self.canvases:
            del self.canvases[tab_name]
        
        self.logger.info(f"График '{tab_name}' удален")
    
    def cleanup_all(self):
        """Очистка всех ресурсов"""
        for interactor in self.interactors.values():
            if hasattr(interactor, 'clear_annotations'):
                interactor.clear_annotations()
            if hasattr(interactor, 'cleanup'):
                interactor.cleanup()
        
        self.canvases.clear()
        self.interactors.clear()
        
        self.logger.info("Все ресурсы TkinterPlotAdapter очищены")
    
    def get_interactor(self, tab_name: str) -> Optional[InteractivePlot]:
        """Получение интерактивного объекта для графика"""
        return self.interactors.get(tab_name)
    
    def reset_zoom_all(self):
        """Сброс масштабирования для всех графиков"""
        for interactor in self.interactors.values():
            if hasattr(interactor, 'reset_zoom'):
                interactor.reset_zoom()
    
    def clear_annotations_all(self):
        """Очистка аннотаций для всех графиков"""
        for interactor in self.interactors.values():
            if hasattr(interactor, 'clear_annotations'):
                interactor.clear_annotations()
