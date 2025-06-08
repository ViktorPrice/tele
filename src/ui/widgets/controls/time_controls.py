"""
Элементы управления временем
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import logging
from typing import Callable, Optional

class TimeAdjustmentControls:
    """Элементы управления для регулировки времени"""
    
    def __init__(self, parent, entry_widget: ttk.Entry, 
                 adjustment_callback: Callable[[ttk.Entry, int], None]):
        self.parent = parent
        self.entry_widget = entry_widget
        self.adjustment_callback = adjustment_callback
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.frame = None
        self.create_controls()
    
    def create_controls(self) -> None:
        """Создание кнопок регулировки времени"""
        self.frame = ttk.Frame(self.parent)
        
        # Конфигурация кнопок: (текст, секунды)
        buttons_config = [
            ("-10с", -10),
            ("-1с", -1),
            ("+1с", 1),
            ("+10с", 10)
        ]
        
        for i, (text, seconds) in enumerate(buttons_config):
            btn = ttk.Button(
                self.frame,
                text=text,
                width=5,
                command=lambda s=seconds: self.adjustment_callback(self.entry_widget, s)
            )
            btn.grid(row=0, column=i, padx=1)
    
    def grid(self, **kwargs) -> None:
        """Размещение элементов управления"""
        if self.frame:
            self.frame.grid(**kwargs)

class TimeRangeValidator:
    """Валидатор временного диапазона"""
    
    @staticmethod
    def validate_datetime_string(value: str) -> tuple[bool, Optional[datetime], str]:
        """Валидация строки даты и времени"""
        if not value or not isinstance(value, str):
            return False, None, "Пустое значение"
        
        try:
            value = value.strip()
            if not value:
                return False, None, "Пустое значение"
            
            # Поддерживаемые форматы
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%d.%m.%Y %H:%M:%S',
                '%d/%m/%Y %H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    return True, dt, ""
                except ValueError:
                    continue
            
            return False, None, "Неверный формат даты и времени"
            
        except Exception as e:
            return False, None, f"Ошибка валидации: {e}"
    
    @staticmethod
    def validate_time_range(start_str: str, end_str: str) -> tuple[bool, str]:
        """Валидация временного диапазона"""
        start_valid, start_dt, start_error = TimeRangeValidator.validate_datetime_string(start_str)
        if not start_valid:
            return False, f"Время начала: {start_error}"
        
        end_valid, end_dt, end_error = TimeRangeValidator.validate_datetime_string(end_str)
        if not end_valid:
            return False, f"Время окончания: {end_error}"
        
        if start_dt >= end_dt:
            return False, "Время начала должно быть раньше времени окончания"
        
        # Проверка разумности диапазона
        duration = (end_dt - start_dt).total_seconds()
        if duration > 24 * 3600:  # Больше суток
            return False, "Временной диапазон слишком большой (максимум 24 часа)"
        
        if duration < 0.1:  # Меньше 0.1 секунды
            return False, "Временной диапазон слишком маленький (минимум 0.1 секунды)"
        
        return True, ""

class TimeEntryWidget:
    """Виджет ввода времени с валидацией"""
    
    def __init__(self, parent, label_text: str, 
                 validation_callback: Optional[Callable] = None):
        self.parent = parent
        self.label_text = label_text
        self.validation_callback = validation_callback
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Виджеты
        self.label: Optional[ttk.Label] = None
        self.entry: Optional[ttk.Entry] = None
        self.error_label: Optional[ttk.Label] = None
        
        self.create_widgets()
    
    def create_widgets(self) -> None:
        """Создание виджетов ввода времени"""
        # Метка
        self.label = ttk.Label(self.parent, text=self.label_text)
        
        # Поле ввода
        self.entry = ttk.Entry(self.parent, width=20)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<KeyRelease>', self._on_key_release)
        
        # Метка ошибки (скрыта по умолчанию)
        self.error_label = ttk.Label(
            self.parent, 
            text="", 
            foreground="red", 
            font=('Arial', 8)
        )
    
    def _on_focus_out(self, event) -> None:
        """Обработчик потери фокуса"""
        self.validate()
    
    def _on_key_release(self, event) -> None:
        """Обработчик отпускания клавиши"""
        # Валидация в реальном времени (с задержкой)
        self.parent.after(500, self.validate)
    
    def validate(self) -> bool:
        """Валидация введенного значения"""
        if not self.entry:
            return False
        
        value = self.entry.get()
        is_valid, dt, error_msg = TimeRangeValidator.validate_datetime_string(value)
        
        if is_valid:
            self.entry.config(style='TEntry')
            self.error_label.config(text="")
            self.error_label.grid_remove()
        else:
            if value:  # Показываем ошибку только если поле не пустое
                self.entry.config(style='Error.TEntry')
                self.error_label.config(text=error_msg)
                self.error_label.grid()
        
        # Вызываем callback если есть
        if self.validation_callback:
            self.validation_callback(is_valid, dt)
        
        return is_valid
    
    def get_value(self) -> str:
        """Получение значения"""
        return self.entry.get() if self.entry else ""
    
    def set_value(self, value: str) -> None:
        """Установка значения"""
        if self.entry:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, value)
            self.validate()
    
    def get_datetime(self) -> Optional[datetime]:
        """Получение значения как datetime"""
        is_valid, dt, _ = TimeRangeValidator.validate_datetime_string(self.get_value())
        return dt if is_valid else None
    
    def grid_widgets(self, start_row: int, column: int) -> int:
        """Размещение виджетов на сетке"""
        if self.label:
            self.label.grid(row=start_row, column=column, sticky="w", padx=5, pady=2)
        
        if self.entry:
            self.entry.grid(row=start_row+1, column=column, sticky="ew", padx=5, pady=2)
        
        # Метка ошибки размещается при необходимости
        return start_row + 2
