"""
Базовый класс для всех панелей управления
"""
from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional, Callable

class BasePanel(ABC):
    """Абстрактный базовый класс для панелей управления"""
    
    def __init__(self, parent, controller, config: Dict[str, Any] = None):
        self.parent = parent
        self.controller = controller
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # UI компоненты
        self.frame: Optional[ttk.Frame] = None
        self.widgets: Dict[str, tk.Widget] = {}
        
        # Состояние
        self.is_enabled = True
        self.is_visible = True
        
    @abstractmethod
    def create_widgets(self) -> None:
        """Создание виджетов панели"""
        pass
    
    @abstractmethod
    def update_state(self, **kwargs) -> None:
        """Обновление состояния панели"""
        pass
    
    def enable(self) -> None:
        """Включение панели"""
        self.is_enabled = True
        self._update_widget_states()
    
    def disable(self) -> None:
        """Отключение панели"""
        self.is_enabled = False
        self._update_widget_states()
    
    def show(self) -> None:
        """Показ панели"""
        if self.frame:
            self.frame.grid()
            self.is_visible = True
    
    def hide(self) -> None:
        """Скрытие панели"""
        if self.frame:
            self.frame.grid_remove()
            self.is_visible = False
    
    def _update_widget_states(self) -> None:
        """Обновление состояния виджетов"""
        state = tk.NORMAL if self.is_enabled else tk.DISABLED
        for widget in self.widgets.values():
            if hasattr(widget, 'config'):
                try:
                    widget.config(state=state)
                except tk.TclError:
                    pass  # Некоторые виджеты не поддерживают state
    
    def get_widget(self, name: str) -> Optional[tk.Widget]:
        """Получение виджета по имени"""
        return self.widgets.get(name)
    
    def set_widget(self, name: str, widget: tk.Widget) -> None:
        """Установка виджета"""
        self.widgets[name] = widget
    
    def grid(self, **kwargs) -> None:
        """Размещение панели"""
        if self.frame:
            self.frame.grid(**kwargs)

class UploadPanel(BasePanel):
    """Панель загрузки файлов с прогрессом"""
    
    def __init__(self, parent, controller, config: Dict[str, Any] = None):
        super().__init__(parent, controller, config)
        self.is_loading = False
        self.create_widgets()
    
    def create_widgets(self) -> None:
        """Создание виджетов панели загрузки"""
        self.frame = ttk.Frame(self.parent)
        self.frame.grid_columnconfigure(1, weight=1)
        
        # Кнопка загрузки
        upload_btn = ttk.Button(
            self.frame,
            text="Загрузить CSV",
            command=self._handle_upload,
            style='Accent.TButton'
        )
        upload_btn.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.set_widget('upload_btn', upload_btn)
        
        # Метка статуса
        status_label = ttk.Label(
            self.frame,
            text="Готов к загрузке файла",
            font=('Arial', 9)
        )
        status_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.set_widget('status_label', status_label)
        
        # Прогресс-бар (скрыт по умолчанию)
        progress = ttk.Progressbar(
            self.frame,
            mode='determinate',
            length=200
        )
        self.set_widget('progress', progress)
        
        # Кнопка отмены (создается при необходимости)
        self._create_cancel_button()
    
    def _create_cancel_button(self) -> None:
        """Создание кнопки отмены"""
        cancel_btn = ttk.Button(
            self.frame,
            text="Отмена",
            command=self._handle_cancel,
            style='Error.TButton'
        )
        self.set_widget('cancel_btn', cancel_btn)
    
    def _handle_upload(self) -> None:
        """Обработка загрузки файла"""
        if hasattr(self.controller, 'upload_csv'):
            self.controller.upload_csv()
    
    def _handle_cancel(self) -> None:
        """Обработка отмены операции"""
        if hasattr(self.controller, 'cancel_operation'):
            self.controller.cancel_operation()
    
    def set_loading_state(self, is_loading: bool) -> None:
        """Установка состояния загрузки"""
        self.is_loading = is_loading
        
        upload_btn = self.get_widget('upload_btn')
        progress = self.get_widget('progress')
        cancel_btn = self.get_widget('cancel_btn')
        
        if is_loading:
            if upload_btn:
                upload_btn.config(state=tk.DISABLED)
            if progress:
                progress.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
            if cancel_btn:
                cancel_btn.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        else:
            if upload_btn:
                upload_btn.config(state=tk.NORMAL)
            if progress:
                progress.grid_remove()
            if cancel_btn:
                cancel_btn.grid_remove()
    
    def update_status(self, message: str) -> None:
        """Обновление статуса"""
        status_label = self.get_widget('status_label')
        if status_label:
            status_label.config(text=message)
    
    def update_progress(self, value: int) -> None:
        """Обновление прогресса"""
        progress = self.get_widget('progress')
        if progress:
            progress['value'] = value
    
    def update_state(self, **kwargs) -> None:
        """Обновление состояния панели"""
        if 'loading' in kwargs:
            self.set_loading_state(kwargs['loading'])
        if 'status' in kwargs:
            self.update_status(kwargs['status'])
        if 'progress' in kwargs:
            self.update_progress(kwargs['progress'])
