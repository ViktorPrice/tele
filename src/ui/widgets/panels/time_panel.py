"""
Панель управления временным диапазоном
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import logging
from typing import Optional, Tuple

from .base_panel import BasePanel
from ..controls.time_controls import TimeAdjustmentControls, TimeEntryWidget, TimeRangeValidator

class TimePanel(BasePanel):
    """Панель управления временным диапазоном с валидацией"""
    
    def __init__(self, parent, controller, config=None):
        super().__init__(parent, controller, config)
        
        # Виджеты времени
        self.start_time_widget: Optional[TimeEntryWidget] = None
        self.end_time_widget: Optional[TimeEntryWidget] = None
        self.start_controls: Optional[TimeAdjustmentControls] = None
        self.end_controls: Optional[TimeAdjustmentControls] = None
        
        # Переменные
        self.changed_var = tk.BooleanVar()
        
        self.create_widgets()
    
    def create_widgets(self) -> None:
        """Создание виджетов панели времени"""
        self.frame = ttk.Frame(self.parent)
        self.frame.grid_columnconfigure([1, 3], weight=1)
        
        # Время начала
        self.start_time_widget = TimeEntryWidget(
            self.frame, 
            "Время начала:",
            self._on_time_validation
        )
        self.start_time_widget.grid_widgets(0, 0)
        
        # Элементы управления временем начала
        self.start_controls = TimeAdjustmentControls(
            self.frame,
            self.start_time_widget.entry,
            self._adjust_time
        )
        self.start_controls.grid(row=1, column=1, padx=5, pady=2)
        
        # Время окончания
        self.end_time_widget = TimeEntryWidget(
            self.frame,
            "Время окончания:",
            self._on_time_validation
        )
        self.end_time_widget.grid_widgets(0, 2)
        
        # Элементы управления временем окончания
        self.end_controls = TimeAdjustmentControls(
            self.frame,
            self.end_time_widget.entry,
            self._adjust_time
        )
        self.end_controls.grid(row=1, column=3, padx=5, pady=2)
        
        # Чекбокс "Только изменяемые параметры"
        changed_cb = ttk.Checkbutton(
            self.frame,
            text="Только изменяемые параметры",
            variable=self.changed_var,
            command=self._on_changed_filter_toggle
        )
        changed_cb.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Кнопка автозаполнения
        auto_fill_btn = ttk.Button(
            self.frame,
            text="Автозаполнение",
            command=self._handle_auto_fill
        )
        auto_fill_btn.grid(row=2, column=3, padx=5, pady=5, sticky="e")
        
        # Сохранение виджетов
        self.set_widget('start_time_widget', self.start_time_widget)
        self.set_widget('end_time_widget', self.end_time_widget)
        self.set_widget('changed_checkbox', changed_cb)
        self.set_widget('auto_fill_btn', auto_fill_btn)
    
    def _on_time_validation(self, is_valid: bool, dt: Optional[datetime]) -> None:
        """Обработчик валидации времени"""
        # Проверяем весь диапазон при изменении любого поля
        self._validate_time_range()
    
    def _validate_time_range(self) -> bool:
        """Валидация всего временного диапазона"""
        if not self.start_time_widget or not self.end_time_widget:
            return False
        
        start_str = self.start_time_widget.get_value()
        end_str = self.end_time_widget.get_value()
        
        is_valid, error_msg = TimeRangeValidator.validate_time_range(start_str, end_str)
        
        # Уведомляем контроллер о валидности диапазона
        if hasattr(self.controller, 'on_time_range_validated'):
            self.controller.on_time_range_validated(is_valid, error_msg)
        
        return is_valid
    
    def _adjust_time(self, entry: ttk.Entry, seconds: int) -> None:
        """Регулировка времени на заданное количество секунд"""
        try:
            current_value = entry.get()
            is_valid, current_dt, _ = TimeRangeValidator.validate_datetime_string(current_value)
            
            if not is_valid:
                if hasattr(self.controller, 'show_error'):
                    self.controller.show_error("Неверный формат времени")
                return
            
            new_time = current_dt + timedelta(seconds=seconds)
            entry.delete(0, tk.END)
            entry.insert(0, new_time.strftime("%Y-%m-%d %H:%M:%S"))
            
            # Валидируем новое значение
            self._validate_time_range()
            
        except Exception as e:
            self.logger.error(f"Ошибка регулировки времени: {e}")
            if hasattr(self.controller, 'show_error'):
                self.controller.show_error(f"Ошибка регулировки времени: {e}")
    
    def _on_changed_filter_toggle(self) -> None:
        """Обработчик переключения фильтра изменяемых параметров"""
        self.logger.info(f"Чекбокс 'Только изменяемые параметры' переключен: {self.changed_var.get()}")
        if hasattr(self.controller, 'apply_filters'):
            self.controller.apply_filters()
    
    def _handle_auto_fill(self) -> None:
        """Обработка автозаполнения"""
        if hasattr(self.controller, 'auto_fill_time_range'):
            self.controller.auto_fill_time_range()
    
    def set_time_range(self, start_time: datetime, end_time: datetime) -> None:
        """Установка временного диапазона"""
        if self.start_time_widget:
            self.start_time_widget.set_value(start_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        if self.end_time_widget:
            self.end_time_widget.set_value(end_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        self.logger.info(f"Установлен временной диапазон: {start_time} - {end_time}")
    
    def get_time_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Получение временного диапазона"""
        start_dt = self.start_time_widget.get_datetime() if self.start_time_widget else None
        end_dt = self.end_time_widget.get_datetime() if self.end_time_widget else None
        return start_dt, end_dt
    
    def update_state(self, **kwargs) -> None:
        """Обновление состояния панели"""
        if 'time_range' in kwargs:
            start_time, end_time = kwargs['time_range']
            self.set_time_range(start_time, end_time)
        
        if 'changed_only' in kwargs:
            self.changed_var.set(kwargs['changed_only'])
    
    # Свойства для обратной совместимости
    @property
    def start_time_entry(self) -> Optional[ttk.Entry]:
        """Доступ к полю времени начала"""
        return self.start_time_widget.entry if self.start_time_widget else None
    
    @property
    def end_time_entry(self) -> Optional[ttk.Entry]:
        """Доступ к полю времени окончания"""
        return self.end_time_widget.entry if self.end_time_widget else None
