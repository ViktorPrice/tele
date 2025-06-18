# compact_diagnostic_panel.py

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, List, Any, Callable, Optional
from .base_ui_component import BaseUIComponent

class CompactDiagnosticPanel(BaseUIComponent):
    """
    Компактная панель диагностики: объединяет 
    фильтрацию по критичности, системам и функциям.
    """

    def __init__(self, parent: ttk.Widget, controller: Any = None):
        super().__init__(parent, controller)
        self.logger = logging.getLogger(self.__class__.__name__)
        # Переменные для групп фильтров
        self.critical_vars: Dict[str, tk.BooleanVar] = {}
        self.system_vars: Dict[str, tk.BooleanVar] = {}
        self.function_vars: Dict[str, tk.BooleanVar] = {}
        # Инициализация интерфейса
        self.setup_ui()
        self.logger.info("CompactDiagnosticPanel initialized")

    def setup_ui(self):
        """Создаёт UI: секции фильтров и кнопку применения."""
        self.grid(sticky="nsew")
        container = ttk.LabelFrame(self, text="Диагностические фильтры", padding=5)
        container.grid(row=0, column=0, sticky="ew")
        container.grid_columnconfigure(0, weight=1)
        
        # Секции фильтров
        self._create_group(container, "Критичность", self.critical_vars, 
                           self.controller.get_critical_levels())
        self._create_group(container, "Системы", self.system_vars, 
                           self.controller.get_system_list())
        self._create_group(container, "Функции", self.function_vars, 
                           self.controller.get_function_list())
        
        # Кнопка применения
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=1, column=0, pady=5)
        ttk.Button(btn_frame, text="Применить", command=self._on_apply).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Сброс", command=self._on_reset).pack(side="left", padx=5)

    def _create_group(self, parent: ttk.Widget, title: str, 
                      var_dict: Dict[str, tk.BooleanVar], items: List[str]):
        """
        Создаёт группу чекбоксов внутри LabelFrame.
        """
        frame = ttk.LabelFrame(parent, text=title, padding=5)
        frame.grid(sticky="ew", pady=2)
        for i, item in enumerate(sorted(items)):
            var = tk.BooleanVar(value=True)
            var_dict[item] = var
            chk = ttk.Checkbutton(frame, text=item, variable=var)
            chk.grid(row=i//3, column=i%3, sticky="w", padx=3, pady=1)

    def _on_apply(self):
        """
        Собирает выбранные критерии и передает контроллеру.
        """
        criteria = {
            'criticality': [k for k,v in self.critical_vars.items() if v.get()],
            'systems':     [k for k,v in self.system_vars.items() if v.get()],
            'functions':   [k for k,v in self.function_vars.items() if v.get()]
        }
        if self.controller and hasattr(self.controller, 'apply_diagnostic_filters'):
            self.controller.apply_diagnostic_filters(criteria)

    def _on_reset(self):
        """
        Сбрасывает все чекбоксы в активное состояние.
        """
        for d in (self.critical_vars, self.system_vars, self.function_vars):
            for var in d.values():
                var.set(True)
        self._on_apply()

    def get_status_info(self) -> Dict[str, Any]:
        """
        Возвращает состояние включённых фильтров панелей.
        """
        return {
            **super().get_status_info(),
            'critical_selected': sum(v.get() for v in self.critical_vars.values()),
            'systems_selected':  sum(v.get() for v in self.system_vars.values()),
            'functions_selected':sum(v.get() for v in self.function_vars.values())
        }

    def cleanup(self):
        """Очистка ресурсов панели."""
        self.critical_vars.clear()
        self.system_vars.clear()
        self.function_vars.clear()
        super().cleanup()
