# base_ui_component.py

import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional, Dict, Any, Callable, List
from abc import ABC, abstractmethod

class BaseUIComponent(ttk.Frame, ABC):
    """Базовый класс для всех UI-компонентов."""

    def __init__(self, parent: ttk.Widget, controller: Any = None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        self._is_initialized = False
        self._is_loading = False
        self._callbacks: Dict[str, List[Callable]] = {}
        self._initialize()

    def _initialize(self):
        """Инициализация компонента: UI и привязки."""
        try:
            self.setup_ui()
            self.setup_bindings()
            self._is_initialized = True
            self.logger.info(f"{self.__class__.__name__} initialized")
        except Exception as e:
            self.logger.error(f"Init error in {self.__class__.__name__}: {e}")
            raise

    @abstractmethod
    def setup_ui(self):
        """Настройка интерфейса (обязательный метод)."""
        pass

    def setup_bindings(self):
        """Настройка привязок событий (по умолчанию пусто)."""
        pass

    def register_callback(self, event: str, callback: Callable):
        """Регистрация callback для события."""
        self._callbacks.setdefault(event, []).append(callback)
        self.logger.debug(f"Callback registered for {event}")

    def emit_event(self, event: str, data: Any = None):
        """Вызов всех callback для события."""
        for cb in self._callbacks.get(event, []):
            try:
                cb(data)
            except Exception as e:
                self.logger.error(f"Error in callback {cb}: {e}")

    def set_controller(self, controller: Any):
        """Установка контроллера."""
        self.controller = controller
        self.logger.info(f"Controller set for {self.__class__.__name__}")

    def set_loading_state(self, loading: bool):
        """Переключение состояния загрузки и блокировка виджетов."""
        self._is_loading = loading
        state = tk.DISABLED if loading else tk.NORMAL
        self._update_widget_states(state)

    def _update_widget_states(self, state: str):
        """Обновление состояния всех дочерних виджетов."""
        for child in self.winfo_children():
            try:
                child.configure(state=state)
            except Exception:
                pass

    def get_status_info(self) -> Dict[str, Any]:
        """Информация о состоянии компонента."""
        return {
            'component': self.__class__.__name__,
            'initialized': self._is_initialized,
            'loading': self._is_loading
        }

    def cleanup(self):
        """Очистка ресурсов и callback."""
        try:
            self.controller = None
            self._callbacks.clear()
            self._is_initialized = False
            self.logger.info(f"{self.__class__.__name__} cleaned up")
        except Exception as e:
            self.logger.error(f"Cleanup error in {self.__class__.__name__}: {e}")
