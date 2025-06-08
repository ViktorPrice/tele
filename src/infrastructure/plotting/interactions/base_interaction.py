"""
Базовый класс для всех типов интерактивности графиков
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

class BaseInteraction(ABC):
    """Абстрактный базовый класс для интерактивных элементов графика"""
    
    def __init__(self, canvas, figure, config: Dict[str, Any] = None):
        self.canvas = canvas
        self.figure = figure
        self.ax = figure.axes[0] if figure.axes else None
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_enabled = True
        
        # Элементы интерфейса, управляемые этим взаимодействием
        self.ui_elements = []
        
    @abstractmethod
    def setup_handlers(self) -> None:
        """Настройка обработчиков событий"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Очистка ресурсов"""
        pass
    
    def enable(self) -> None:
        """Включение интерактивности"""
        self.is_enabled = True
        self.setup_handlers()
    
    def disable(self) -> None:
        """Отключение интерактивности"""
        self.is_enabled = False
        self.cleanup()
    
    def clear_ui_elements(self) -> None:
        """Очистка UI элементов"""
        for element in self.ui_elements:
            try:
                element.remove()
            except Exception as e:
                self.logger.debug(f"Ошибка удаления UI элемента: {e}")
        self.ui_elements.clear()

class CursorInteraction(BaseInteraction):
    """Интерактивность курсора и отображения времени"""
    
    def __init__(self, canvas, figure, config: Dict[str, Any] = None):
        super().__init__(canvas, figure, config)
        self.cursor_line = None
        self.time_text = None
        self.cursor_color = config.get('cursor_color', 'red')
        self.time_format = config.get('time_format', '%H:%M:%S.%f')[:-3]
        
    def setup_handlers(self) -> None:
        """Настройка обработчика движения мыши"""
        if self.ax:
            self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            self.canvas.mpl_connect('figure_leave_event', self.on_mouse_leave)
    
    def on_mouse_move(self, event):
        """Обработчик движения мыши"""
        if not self.is_enabled or not event.inaxes:
            return
        
        self.update_cursor(event)
        self.canvas.draw_idle()
    
    def update_cursor(self, event):
        """Обновление позиции курсора"""
        # Удаляем предыдущие элементы
        self.clear_ui_elements()
        
        # Создаем вертикальную линию курсора
        self.cursor_line = self.ax.axvline(
            x=event.xdata, 
            color=self.cursor_color, 
            alpha=0.7, 
            linewidth=1, 
            linestyle='--'
        )
        self.ui_elements.append(self.cursor_line)
        
        # Добавляем текст времени
        import matplotlib.dates as mdates
        try:
            time_str = mdates.num2date(event.xdata).strftime(self.time_format)
            self.time_text = self.ax.text(
                event.xdata, self.ax.get_ylim()[1], f" {time_str} ",
                ha='center', va='bottom',
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', pad=2)
            )
            self.ui_elements.append(self.time_text)
        except (ValueError, OverflowError):
            pass  # Игнорируем ошибки форматирования времени
    
    def on_mouse_leave(self, event):
        """Обработчик ухода мыши с графика"""
        self.clear_ui_elements()
        self.canvas.draw_idle()
    
    def cleanup(self) -> None:
        """Очистка ресурсов"""
        self.clear_ui_elements()

class TooltipInteraction(BaseInteraction):
    """Интерактивность всплывающих подсказок"""
    
    def __init__(self, canvas, figure, plot_params=None, config: Dict[str, Any] = None):
        super().__init__(canvas, figure, config)
        self.plot_params = plot_params or []
        self.tooltip = None
        self.highlighted_line = None
        self.original_linewidths = {}
        
    def setup_handlers(self) -> None:
        """Настройка обработчиков для подсказок"""
        if self.ax:
            self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            self.canvas.mpl_connect('figure_leave_event', self.on_mouse_leave)
            self._setup_line_picking()
    
    def _setup_line_picking(self):
        """Настройка возможности выбора линий"""
        for line in self.ax.get_lines():
            line.set_picker(True)
            line.set_pickradius(5)
            self.original_linewidths[line] = line.get_linewidth()
    
    def on_mouse_move(self, event):
        """Обработчик движения мыши для подсказок"""
        if not self.is_enabled or not event.inaxes:
            return
        
        self.handle_line_hover(event)
        self.canvas.draw_idle()
    
    def handle_line_hover(self, event):
        """Обработка наведения на линии"""
        found_line = None
        
        # Поиск линии под курсором
        for line in self.ax.get_lines():
            if line.contains(event)[0]:
                found_line = line
                break
        
        # Сброс предыдущей подсветки
        if self.highlighted_line and self.highlighted_line != found_line:
            self.highlighted_line.set_linewidth(
                self.original_linewidths.get(self.highlighted_line, 1.5)
            )
            self.highlighted_line = None
            self.hide_tooltip()
        
        # Подсветка новой линии
        if found_line and found_line != self.highlighted_line:
            self.highlighted_line = found_line
            found_line.set_linewidth(
                self.original_linewidths.get(found_line, 1.5) * 2
            )
            
            # Показ подсказки
            param = next(
                (p for p in self.plot_params 
                 if p.get('signal_code') == found_line.get_label()), 
                None
            )
            if param:
                self.show_tooltip(event, param.get('description', 'Нет описания'))
    
    def show_tooltip(self, event, text: str):
        """Показ всплывающей подсказки"""
        self.hide_tooltip()
        
        try:
            import tkinter as tk
            self.tooltip = tk.Toplevel(self.canvas.get_tk_widget())
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root+20}+{event.y_root+15}")
            
            label = tk.Label(
                self.tooltip, 
                text=text, 
                justify='left',
                background="#ffffe0", 
                relief='solid', 
                borderwidth=1, 
                wraplength=400
            )
            label.pack(ipadx=1)
        except Exception as e:
            self.logger.error(f"Ошибка создания подсказки: {e}")
    
    def hide_tooltip(self):
        """Скрытие подсказки"""
        if self.tooltip:
            try:
                self.tooltip.destroy()
            except:
                pass
            self.tooltip = None
    
    def on_mouse_leave(self, event):
        """Обработчик ухода мыши"""
        if self.highlighted_line:
            self.highlighted_line.set_linewidth(
                self.original_linewidths.get(self.highlighted_line, 1.5)
            )
            self.highlighted_line = None
        self.hide_tooltip()
        self.canvas.draw_idle()
    
    def cleanup(self) -> None:
        """Очистка ресурсов"""
        self.hide_tooltip()
        if self.highlighted_line:
            self.highlighted_line.set_linewidth(
                self.original_linewidths.get(self.highlighted_line, 1.5)
            )

class ZoomInteraction(BaseInteraction):
    """Интерактивность масштабирования"""
    
    def __init__(self, canvas, figure, config: Dict[str, Any] = None):
        super().__init__(canvas, figure, config)
        self.zoom_history = []
        self.max_history = config.get('max_zoom_history', 20)
        self.zoom_factor = config.get('zoom_factor', 1.2)
        self._save_original_limits()
    
    def setup_handlers(self) -> None:
        """Настройка обработчиков масштабирования"""
        if self.ax:
            self.canvas.mpl_connect('scroll_event', self.on_mouse_scroll)
            self.canvas.mpl_connect('key_press_event', self.on_key_press)
    
    def _save_original_limits(self):
        """Сохранение исходных пределов"""
        if self.ax:
            self.original_xlim = self.ax.get_xlim()
            self.original_ylim = self.ax.get_ylim()
    
    def on_mouse_scroll(self, event):
        """Обработчик масштабирования колесом мыши"""
        if not self.is_enabled or not event.inaxes:
            return
        
        self._save_zoom_state()
        
        # Определение коэффициента масштабирования
        scale = 1/self.zoom_factor if event.step > 0 else self.zoom_factor
        
        # Масштабирование относительно позиции курсора
        if event.xdata and event.ydata:
            self._zoom_around_point(event.xdata, event.ydata, scale)
            self.canvas.draw_idle()
    
    def _zoom_around_point(self, x_center: float, y_center: float, scale: float):
        """Масштабирование вокруг точки"""
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        
        # Вычисление новых пределов
        x_range = (cur_xlim[1] - cur_xlim[0]) * scale
        y_range = (cur_ylim[1] - cur_ylim[0]) * scale
        
        x_rel = (x_center - cur_xlim[0]) / (cur_xlim[1] - cur_xlim[0])
        y_rel = (y_center - cur_ylim[0]) / (cur_ylim[1] - cur_ylim[0])
        
        new_xlim = [
            x_center - x_range * x_rel,
            x_center + x_range * (1 - x_rel)
        ]
        new_ylim = [
            y_center - y_range * y_rel,
            y_center + y_range * (1 - y_rel)
        ]
        
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
    
    def on_key_press(self, event):
        """Обработчик горячих клавиш"""
        if event.key == 'r':
            self.reset_zoom()
        elif event.key == 'z':
            self.undo_zoom()
    
    def _save_zoom_state(self):
        """Сохранение состояния масштабирования"""
        if self.ax:
            state = {
                'xlim': self.ax.get_xlim(),
                'ylim': self.ax.get_ylim()
            }
            self.zoom_history.append(state)
            
            # Ограничение размера истории
            if len(self.zoom_history) > self.max_history:
                self.zoom_history.pop(0)
    
    def reset_zoom(self):
        """Сброс масштабирования"""
        if hasattr(self, 'original_xlim'):
            self.ax.set_xlim(self.original_xlim)
            self.ax.set_ylim(self.original_ylim)
            self.canvas.draw_idle()
    
    def undo_zoom(self):
        """Отмена последнего масштабирования"""
        if self.zoom_history:
            last_state = self.zoom_history.pop()
            self.ax.set_xlim(last_state['xlim'])
            self.ax.set_ylim(last_state['ylim'])
            self.canvas.draw_idle()
    
    def cleanup(self) -> None:
        """Очистка ресурсов"""
        self.zoom_history.clear()
