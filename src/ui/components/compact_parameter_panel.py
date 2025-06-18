# compact_parameter_panel.py

import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Optional

class CompactParameterPanel(ttk.Frame):
    """
    Универсальная компактная панель отображения и выбора параметров.
    Объединяет логику оригинальных вертикальной и горизонтальной панелей.
    """

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Список всех параметров и выделенных
        self._all_params: List[Dict[str, Any]] = []
        self._selected_ids: set = set()

        # Конфигурация сетки
        self._cols = 4  # по умолчанию 4 колонки; адаптируется в resize
        self._rows = 0

        # Создаём контейнер для элементов
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner_frame = ttk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Инициализация элементов
        self._render_grid()
        self.bind("<Configure>", self._on_resize)

    def _render_grid(self):
        """Отрисовка сетки кнопок/чёкбоксов по параметрам."""
        # Очищаем старые виджеты
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        # Вычисляем строки
        count = len(self._all_params)
        self._cols = min(self._cols, max(1, count))
        self._rows = (count + self._cols - 1) // self._cols

        # Размещение
        for idx, param in enumerate(self._all_params):
            row, col = divmod(idx, self._cols)
            var = tk.BooleanVar(value=(param['id'] in self._selected_ids))
            chk = ttk.Checkbutton(
                self.inner_frame,
                text=param.get('name', param.get('signal_code', '')),
                variable=var,
                command=lambda p=param, v=var: self._on_toggle(p, v)
            )
            chk.grid(row=row, column=col, sticky="w", padx=5, pady=2)

    def _on_toggle(self, param: Dict[str, Any], var: tk.BooleanVar):
        """Обработчик выбора/снятия параметра."""
        pid = param['id']
        if var.get():
            self._selected_ids.add(pid)
        else:
            self._selected_ids.discard(pid)
        if self.controller and hasattr(self.controller, 'selection_changed'):
            self.controller.selection_changed(self.get_selected_parameters())

    def set_parameters(self, params: List[Dict[str, Any]]):
        """
        Устанавливает полный список параметров в панели
        и выполняет перерисовку.
        """
        self._all_params = params.copy()
        # Сброс выделения при обновлении списка
        self._selected_ids.clear()
        self._render_grid()

    def update_parameters(self, params: List[Dict[str, Any]]):
        """
        Обновление списка параметров без очистки выбора:
        если старый параметр остаётся в новом списке — сохраняем его выбор.
        """
        old_selected = self._selected_ids.copy()
        self._all_params = params.copy()
        self._selected_ids = {p['id'] for p in params if p['id'] in old_selected}
        self._render_grid()

    def get_selected_parameters(self) -> List[Dict[str, Any]]:
        """Возвращает список словарей параметров, отмеченных пользователем."""
        return [p for p in self._all_params if p['id'] in self._selected_ids]

    def select_all(self):
        """Отметить все параметры."""
        self._selected_ids = {p['id'] for p in self._all_params}
        self._render_grid()

    def deselect_all(self):
        """Снять выделение со всех параметров."""
        self._selected_ids.clear()
        self._render_grid()

    def get_selected_count(self) -> int:
        """Возвращает количество выбранных параметров."""
        return len(self._selected_ids)

    def clear(self):
        """Полностью очищает панель параметров."""
        self._all_params = []
        self._selected_ids.clear()
        self._render_grid()

    def _on_resize(self, event):
        """
        Автоматически адаптировать число колонок
        при изменении размеров панели.
        """
        width = event.width
        # допустим каждый элемент ~150px
        new_cols = max(1, width // 150)
        if new_cols != self._cols:
            self._cols = new_cols
            self._render_grid()

    def cleanup(self):
        """Очистка ресурсов и удаление виджетов."""
        self.controller = None
        self.canvas.destroy()
        self.scrollbar.destroy()
        self.inner_frame.destroy()
        super().destroy()
