"""
Виджет отдельной вкладки с графиком
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ..base.observable_widget import ObservableWidget
from ...adapters.matplotlib_widget_adapter import MatplotlibWidgetAdapter

class PlotTabWidget(ObservableWidget):
    """Виджет отдельной вкладки с графиком и элементами управления"""
    
    def __init__(self, parent, tab_name: str, controller):
        super().__init__()
        self.parent = parent
        self.tab_name = tab_name
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Состояние
        self.plot_params: List[Dict[str, Any]] = []
        self.is_built = False
        self.time_range: Optional[tuple[datetime, datetime]] = None
        
        # UI компоненты
        self.frame = None
        self.matplotlib_adapter = None
        self.info_panel = None
        self.statistics_panel = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создание виджетов вкладки"""
        # Основной контейнер
        self.frame = ttk.Frame(self.parent)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Создание layout
        self._create_main_layout()
        self._create_control_panel()
    
    def _create_main_layout(self):
        """Создание основного layout с графиком и панелями"""
        # PanedWindow для разделения
        self.main_paned = tk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        self.main_paned.grid(row=0, column=0, sticky="nsew")
        
        # Левая часть - график
        plot_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(plot_frame, minsize=600)
        
        # Правая часть - информация
        info_frame = ttk.Frame(self.main_paned, width=300)
        self.main_paned.add(info_frame, minsize=250)
        
        # Создание matplotlib адаптера
        self.matplotlib_adapter = MatplotlibWidgetAdapter(plot_frame)
        
        # Создание панелей информации
        self._create_info_panels(info_frame)
    
    def _create_info_panels(self, parent):
        """Создание панелей информации"""
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Заголовок
        title_label = ttk.Label(parent, text=f"График: {self.tab_name}", 
                               font=('Arial', 10, 'bold'))
        title_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Панель значений параметров
        self.info_panel = self._create_values_panel(parent)
        self.info_panel.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Панель статистики
        self.statistics_panel = self._create_statistics_panel(parent)
        self.statistics_panel.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
    
    def _create_values_panel(self, parent) -> tk.Text:
        """Создание панели значений параметров"""
        frame = ttk.LabelFrame(parent, text="Значения параметров")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        text_widget = tk.Text(
            frame,
            wrap=tk.WORD,
            height=15,
            width=35,
            font=('Consolas', 9),
            bg='#f8f8f8',
            fg='#333333',
            relief='flat',
            borderwidth=1,
            state=tk.DISABLED
        )
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        return text_widget
    
    def _create_statistics_panel(self, parent) -> ttk.LabelFrame:
        """Создание панели статистики"""
        frame = ttk.LabelFrame(parent, text="Статистика")
        frame.grid_columnconfigure(1, weight=1)
        
        # Метки статистики
        self.stats_labels = {}
        stats_items = [
            ("params_count", "Параметров:"),
            ("time_range", "Диапазон:"),
            ("data_points", "Точек данных:"),
            ("memory_usage", "Память:")
        ]
        
        for i, (key, text) in enumerate(stats_items):
            ttk.Label(frame, text=text).grid(
                row=i, column=0, sticky="w", padx=5, pady=2)
            
            label = ttk.Label(frame, text="N/A", font=('Arial', 9))
            label.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.stats_labels[key] = label
        
        return frame
    
    def _create_control_panel(self):
        """Создание панели управления"""
        control_frame = ttk.Frame(self.frame)
        control_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        control_frame.grid_columnconfigure([0, 1, 2, 3], weight=1)
        
        # Кнопки управления
        buttons_config = [
            ("Обновить", self.refresh_plot, "Обновить график с текущими параметрами"),
            ("Экспорт", self.export_plot, "Экспортировать график в файл"),
            ("Масштаб", self.reset_zoom, "Сбросить масштабирование"),
            ("Настройки", self.show_settings, "Настройки отображения графика")
        ]
        
        for i, (text, command, tooltip) in enumerate(buttons_config):
            btn = ttk.Button(control_frame, text=text, command=command)
            btn.grid(row=0, column=i, padx=2, pady=2, sticky="ew")
            # Добавить tooltip если нужно
    
    def build_plot(self, params: List[Dict[str, Any]], start_time: datetime, 
                   end_time: datetime) -> bool:
        """Построение графика с параметрами"""
        try:
            self.logger.info(f"Построение графика '{self.tab_name}' с {len(params)} параметрами")
            
            if not params:
                self._show_empty_plot()
                return False
            
            self.plot_params = params
            self.time_range = (start_time, end_time)
            
            # Построение через matplotlib адаптер
            success = self.matplotlib_adapter.build_plot(
                params, start_time, end_time, self.tab_name
            )
            
            if success:
                # Добавление интерактивности
                self.matplotlib_adapter.add_interactivity(
                    self.info_panel, params
                )
                
                self.is_built = True
                self.update_statistics()
                
                # Уведомление наблюдателей
                self.notify_observers('plot_built', {
                    'tab_name': self.tab_name,
                    'params_count': len(params)
                })
                
                self.logger.info(f"График '{self.tab_name}' успешно построен")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка построения графика '{self.tab_name}': {e}")
            self._show_error_plot(str(e))
            return False
    
    def _show_empty_plot(self):
        """Отображение пустого графика"""
        self.matplotlib_adapter.show_message(
            f'График "{self.tab_name}"\nНет данных для отображения'
        )
    
    def _show_error_plot(self, error_message: str):
        """Отображение графика с ошибкой"""
        self.matplotlib_adapter.show_message(
            f'Ошибка построения графика:\n{error_message}',
            color='red'
        )
    
    def update_statistics(self):
        """Обновление статистики графика"""
        try:
            if not self.is_built or not self.plot_params:
                return
            
            # Подсчет параметров
            self.stats_labels['params_count'].config(text=str(len(self.plot_params)))
            
            # Временной диапазон
            if self.time_range:
                duration = (self.time_range[1] - self.time_range[0]).total_seconds()
                self.stats_labels['time_range'].config(text=f"{duration:.1f}s")
            
            # Количество точек данных
            total_points = self._calculate_data_points()
            self.stats_labels['data_points'].config(text=str(total_points))
            
            # Использование памяти (приблизительно)
            memory_mb = total_points * 8 / 1024 / 1024  # 8 байт на float64
            self.stats_labels['memory_usage'].config(text=f"{memory_mb:.1f} MB")
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления статистики: {e}")
    
    def _calculate_data_points(self) -> int:
        """Подсчет количества точек данных"""
        total_points = 0
        if hasattr(self.controller, 'model') and self.controller.model.data_loader.csv_data is not None:
            df = self.controller.model.data_loader.csv_data
            for param in self.plot_params:
                col = param.get('full_column')
                if col and col in df.columns:
                    total_points += df[col].count()
        return total_points
    
    def refresh_plot(self):
        """Обновление графика"""
        if not self.plot_params:
            messagebox.showwarning("Обновление", "Нет параметров для обновления")
            return
        
        try:
            # Получаем временной диапазон из контроллера
            start_time = self.controller.validate_datetime(
                self.controller.view.time_panel.start_time_entry.get())
            end_time = self.controller.validate_datetime(
                self.controller.view.time_panel.end_time_entry.get())
            
            if start_time and end_time:
                self.build_plot(self.plot_params, start_time, end_time)
            else:
                messagebox.showerror("Ошибка", "Неверный формат времени")
        
        except Exception as e:
            self.logger.error(f"Ошибка обновления графика: {e}")
            messagebox.showerror("Ошибка", f"Ошибка обновления: {e}")
    
    def export_plot(self):
        """Экспорт графика в файл"""
        if not self.is_built:
            messagebox.showwarning("Экспорт", "График не построен")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"),
                    ("SVG files", "*.svg"),
                    ("EPS files", "*.eps")
                ],
                title=f"Экспорт графика '{self.tab_name}'"
            )
            
            if file_path:
                success = self.matplotlib_adapter.export_plot(file_path)
                if success:
                    messagebox.showinfo("Экспорт", f"График сохранен: {file_path}")
                    self.logger.info(f"График '{self.tab_name}' экспортирован в {file_path}")
                else:
                    messagebox.showerror("Ошибка", "Ошибка экспорта графика")
        
        except Exception as e:
            self.logger.error(f"Ошибка экспорта графика: {e}")
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {e}")
    
    def reset_zoom(self):
        """Сброс масштабирования"""
        if self.matplotlib_adapter:
            self.matplotlib_adapter.reset_zoom()
    
    def show_settings(self):
        """Показ настроек графика"""
        PlotSettingsDialog(self.parent, self)
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            if self.matplotlib_adapter:
                self.matplotlib_adapter.cleanup()
            
            self.logger.info(f"Ресурсы графика '{self.tab_name}' очищены")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки графика '{self.tab_name}': {e}")

class PlotSettingsDialog:
    """Диалог настроек графика"""
    
    def __init__(self, parent, plot_widget: PlotTabWidget):
        self.parent = parent
        self.plot_widget = plot_widget
        self.dialog = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """Создание диалога настроек"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Настройки графика '{self.plot_widget.tab_name}'")
        self.dialog.geometry("400x300")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Основной фрейм
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Настройки отображения
        display_frame = ttk.LabelFrame(main_frame, text="Отображение")
        display_frame.pack(fill=tk.X, pady=5)
        
        # Сетка
        self.grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(display_frame, text="Показать сетку", 
                       variable=self.grid_var).pack(anchor='w', padx=5, pady=2)
        
        # Легенда
        self.legend_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(display_frame, text="Показать легенду", 
                       variable=self.legend_var).pack(anchor='w', padx=5, pady=2)
        
        # Интерактивность
        interaction_frame = ttk.LabelFrame(main_frame, text="Интерактивность")
        interaction_frame.pack(fill=tk.X, pady=5)
        
        self.cursor_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(interaction_frame, text="Курсор", 
                       variable=self.cursor_var).pack(anchor='w', padx=5, pady=2)
        
        self.tooltips_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(interaction_frame, text="Подсказки", 
                       variable=self.tooltips_var).pack(anchor='w', padx=5, pady=2)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Применить", 
                  command=self.apply_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", 
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def apply_settings(self):
        """Применение настроек"""
        try:
            settings = {
                'grid': self.grid_var.get(),
                'legend': self.legend_var.get(),
                'cursor': self.cursor_var.get(),
                'tooltips': self.tooltips_var.get()
            }
            
            if self.plot_widget.matplotlib_adapter:
                self.plot_widget.matplotlib_adapter.apply_settings(settings)
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка применения настроек: {e}")
