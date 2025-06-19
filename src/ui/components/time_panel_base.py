# time_panel_base.py

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import logging
from typing import Tuple, Callable, Optional, Any
from .base_ui_component import BaseUIComponent

class TimePanelBase(BaseUIComponent):
    """Базовый класс для панелей управления временными диапазонами."""

    def __init__(self, parent: ttk.Widget, controller: Any = None):
        super().__init__(parent, controller)
        self.from_time_var = tk.StringVar()
        self.to_time_var = tk.StringVar()
        self.duration_var = tk.StringVar(value="--:--:--")
        self.changed_only_var = tk.BooleanVar(value=False)
        self.on_time_range_changed: Optional[Callable[[str, str], None]] = None
        self.on_changed_only_toggle: Optional[Callable[[bool], None]] = None

        self.set_default_time_range()

    def setup_ui(self):
        """Задаёт базовые виджеты для управления временем."""
        frame = ttk.LabelFrame(self, text="Временной диапазон", padding=5)
        frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(frame, text="От:").grid(row=0, column=0, sticky="w")
        self.from_entry = ttk.Entry(frame, textvariable=self.from_time_var, width=20)
        self.from_entry.grid(row=0, column=1, padx=5)
        self.from_entry.bind("<FocusOut>", self.on_time_field_changed)
        self.from_entry.bind("<Return>", self.on_time_field_changed)

        ttk.Label(frame, text="До:").grid(row=0, column=2, sticky="w")
        self.to_entry = ttk.Entry(frame, textvariable=self.to_time_var, width=20)
        self.to_entry.grid(row=0, column=3, padx=5)
        self.to_entry.bind("<FocusOut>", self.on_time_field_changed)
        self.to_entry.bind("<Return>", self.on_time_field_changed)

        ttk.Label(frame, text="Длительность:").grid(row=1, column=0, sticky="w", pady=(5, 0))
        ttk.Label(frame, textvariable=self.duration_var).grid(row=1, column=1, sticky="w", pady=(5, 0))

        chk = ttk.Checkbutton(frame, text="Только изменённые",
                              variable=self.changed_only_var,
                              command=self._handle_changed_only_toggle)
        chk.grid(row=1, column=2, columnspan=2, sticky="w", pady=(5, 0))

    def set_default_time_range(self):
        """Устанавливает диапазон по умолчанию: от NOW-1h до NOW."""
        now = datetime.now()
        start = now - timedelta(hours=1)
        self.from_time_var.set(start.strftime("%Y-%m-%d %H:%M:%S"))
        self.to_time_var.set(now.strftime("%Y-%m-%d %H:%M:%S"))
        self._update_duration()

    def get_time_range(self) -> Tuple[str, str]:
        """Возвращает кортеж (from_time, to_time)."""
        return self.from_time_var.get(), self.to_time_var.get()

    def set_time_range(self, from_time: str, to_time: str):
        """Устанавливает новый временной диапазон и обновляет длительность."""
        self.from_time_var.set(from_time)
        self.to_time_var.set(to_time)
        self._update_duration()
        self._emit_time_change()

    def _update_duration(self):
        """Пересчитывает и отображает длительность периода."""
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            t0 = datetime.strptime(self.from_time_var.get(), fmt)
            t1 = datetime.strptime(self.to_time_var.get(), fmt)
            delta = t1 - t0
            if delta.total_seconds() >= 0:
                h, rem = divmod(int(delta.total_seconds()), 3600)
                m, s = divmod(rem, 60)
                self.duration_var.set(f"{h:02d}:{m:02d}:{s:02d}")
            else:
                self.duration_var.set("0:00:00")
        except Exception as e:
            self.logger.error(f"Error updating duration: {e}")
            self.duration_var.set("--:--:--")

    def _emit_time_change(self):
        """Генерирует событие изменения времени."""
        fr, to = self.get_time_range()
        if self.on_time_range_changed:
            self.on_time_range_changed(fr, to)
        self.emit_event("time_range_changed", {"from": fr, "to": to})

    def on_time_field_changed(self, event: Any = None):
        """Обработчик изменения поля времени."""
        self._update_duration()
        self._emit_time_change()

    def shift_time(self, minutes: int):
        """Сдвиг диапазона на указанное количество минут."""
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            t0 = datetime.strptime(self.from_time_var.get(), fmt) + timedelta(minutes=minutes)
            t1 = datetime.strptime(self.to_time_var.get(), fmt) + timedelta(minutes=minutes)
            self.set_time_range(t0.strftime(fmt), t1.strftime(fmt))
        except Exception as e:
            self.logger.error(f"Error shifting time: {e}")

    def _handle_changed_only_toggle(self):
        """Обработчик переключения режима 'только изменённые'."""
        val = self.changed_only_var.get()
        if self.on_changed_only_toggle:
            self.on_changed_only_toggle(val)
        self.emit_event("changed_only_toggled", val)

    def cleanup(self):
        """Очистка ресурсов панели времени."""
        super().cleanup()
