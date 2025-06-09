# src/ui/components/filter_panel.py - ИСПРАВЛЕННЫЙ КОМПОНЕНТ
"""
Панель фильтров с поддержкой изменяемых параметров
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, List


class FilterPanel(ttk.Frame):
    """ОБНОВЛЕННАЯ панель фильтров с чекбоксом изменяемых параметров"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Переменные для чекбоксов
        self.signal_vars = {}
        self.line_vars = {}
        self.wagon_vars = {}
        self.component_vars = {}
        self.hardware_vars = {}

        # НОВОЕ: Переменная для фильтра изменяемых параметров
        self.changed_only_var = tk.BooleanVar()

        # UI элементы
        self.changed_only_checkbox = None

        self._setup_ui()
        self.logger.info("FilterPanel инициализирован")

    def _setup_ui(self):
        """Настройка пользовательского интерфейса"""
        try:
            self.grid_columnconfigure(0, weight=1)

            # Заголовок
            title_label = ttk.Label(
                self, text="Фильтры", font=('Arial', 10, 'bold'))
            title_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

            # НОВОЕ: Чекбокс для изменяемых параметров
            changed_frame = ttk.LabelFrame(
                self, text="Тип параметров", padding="5")
            changed_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
            changed_frame.grid_columnconfigure(0, weight=1)

            self.changed_only_checkbox = ttk.Checkbutton(
                changed_frame,
                text="Только изменяемые параметры",
                variable=self.changed_only_var,
                command=self._on_changed_only_toggle
            )
            self.changed_only_checkbox.grid(row=0, column=0, sticky="w")

            # Фильтры типов сигналов
            self._create_signal_type_filters()

            # Фильтры линий
            self._create_line_filters()

            # Фильтры вагонов
            self._create_wagon_filters()

            # Дополнительные фильтры
            self._create_additional_filters()

            # Кнопки управления
            self._create_control_buttons()

            self.logger.info("UI FilterPanel настроен")

        except Exception as e:
            self.logger.error(f"Ошибка настройки UI FilterPanel: {e}")

    def _create_signal_type_filters(self):
        """Создание фильтров типов сигналов"""
        try:
            signal_frame = ttk.LabelFrame(
                self, text="Типы сигналов", padding="5")
            signal_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=2)

            signal_types = ['B', 'BY', 'W', 'DW', 'F', 'WF']

            for i, signal_type in enumerate(signal_types):
                var = tk.BooleanVar()
                var.set(True)  # По умолчанию все включены
                self.signal_vars[signal_type] = var

                checkbox = ttk.Checkbutton(
                    signal_frame,
                    text=signal_type,
                    variable=var,
                    command=self._on_filter_changed
                )
                checkbox.grid(row=i//3, column=i %
                              3, sticky="w", padx=5, pady=2)

        except Exception as e:
            self.logger.error(f"Ошибка создания фильтров типов сигналов: {e}")

    def _create_line_filters(self):
        """Создание фильтров линий"""
        try:
            line_frame = ttk.LabelFrame(self, text="Линии связи", padding="5")
            line_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=2)

            # Создаем скролируемый фрейм для линий
            canvas = tk.Canvas(line_frame, height=100)
            scrollbar = ttk.Scrollbar(
                line_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.bind('<Configure>', lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Сохраняем ссылку на scrollable_frame для обновления
            self.line_scrollable_frame = scrollable_frame

        except Exception as e:
            self.logger.error(f"Ошибка создания фильтров линий: {e}")

    def _create_wagon_filters(self):
        """Создание фильтров вагонов"""
        try:
            wagon_frame = ttk.LabelFrame(
                self, text="Номера вагонов", padding="5")
            wagon_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=2)

            for i in range(1, 16):  # Вагоны 1-15
                var = tk.BooleanVar()
                var.set(True)  # По умолчанию все включены
                self.wagon_vars[str(i)] = var

                checkbox = ttk.Checkbutton(
                    wagon_frame,
                    text=str(i),
                    variable=var,
                    command=self._on_filter_changed
                )
                checkbox.grid(row=i//8, column=i %
                              8, sticky="w", padx=3, pady=1)

        except Exception as e:
            self.logger.error(f"Ошибка создания фильтров вагонов: {e}")

    def _create_additional_filters(self):
        """Создание дополнительных фильтров"""
        try:
            # Фрейм для компонентов
            component_frame = ttk.LabelFrame(
                self, text="Компоненты", padding="5")
            component_frame.grid(row=5, column=0, sticky="ew", padx=5, pady=2)

            components = ['DOOR', 'BRAKE', 'HVAC', 'TRACTION', 'SAFETY', 'AUX']

            for i, component in enumerate(components):
                var = tk.BooleanVar()
                var.set(True)
                self.component_vars[component] = var

                checkbox = ttk.Checkbutton(
                    component_frame,
                    text=component,
                    variable=var,
                    command=self._on_filter_changed
                )
                checkbox.grid(row=i//3, column=i %
                              3, sticky="w", padx=5, pady=2)

        except Exception as e:
            self.logger.error(f"Ошибка создания дополнительных фильтров: {e}")

    def _create_control_buttons(self):
        """Создание кнопок управления"""
        try:
            button_frame = ttk.Frame(self)
            button_frame.grid(row=6, column=0, sticky="ew", padx=5, pady=5)

            # Кнопка "Выбрать все"
            select_all_btn = ttk.Button(
                button_frame,
                text="Выбрать все",
                command=self._select_all_filters
            )
            select_all_btn.pack(side=tk.LEFT, padx=2)

            # Кнопка "Очистить все"
            clear_all_btn = ttk.Button(
                button_frame,
                text="Очистить все",
                command=self._clear_all_filters
            )
            clear_all_btn.pack(side=tk.LEFT, padx=2)

            # Кнопка "Сброс"
            reset_btn = ttk.Button(
                button_frame,
                text="Сброс",
                command=self.reset_filters
            )
            reset_btn.pack(side=tk.LEFT, padx=2)

        except Exception as e:
            self.logger.error(f"Ошибка создания кнопок управления: {e}")

    def _on_changed_only_toggle(self):
        """НОВЫЙ обработчик: Переключение фильтра изменяемых параметров"""
        try:
            is_changed_only = self.changed_only_var.get()
            self.logger.info(
                f"Чекбокс 'Только изменяемые параметры' переключен: {is_changed_only}")

            # Уведомляем контроллер о изменении
            if self.controller and hasattr(self.controller, 'apply_filters'):
                self.controller.apply_filters(changed_only=is_changed_only)

        except Exception as e:
            self.logger.error(f"Ошибка обработки переключения фильтра: {e}")

    def _on_filter_changed(self):
        """Обработчик изменения обычных фильтров"""
        try:
            # Применяем фильтры только если не активен "только изменяемые"
            if not self.changed_only_var.get():
                if self.controller and hasattr(self.controller, 'apply_filters'):
                    self.controller.apply_filters(changed_only=False)

        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения фильтра: {e}")

    def update_line_checkboxes(self, lines: List[str]):
        """Обновление чекбоксов линий на основе загруженных данных"""
        try:
            # Очищаем существующие чекбоксы линий
            for widget in self.line_scrollable_frame.winfo_children():
                widget.destroy()

            self.line_vars.clear()

            # Создаем новые чекбоксы
            for i, line in enumerate(sorted(lines)):
                var = tk.BooleanVar()
                var.set(True)  # По умолчанию все включены
                self.line_vars[line] = var

                checkbox = ttk.Checkbutton(
                    self.line_scrollable_frame,
                    text=line,
                    variable=var,
                    command=self._on_filter_changed
                )
                checkbox.grid(row=i, column=0, sticky="w", padx=5, pady=1)

            self.logger.info(f"Обновлены чекбоксы линий: {len(lines)} линий")

        except Exception as e:
            self.logger.error(f"Ошибка обновления чекбоксов линий: {e}")

    def get_selected_filters(self) -> Dict[str, Any]:
        """ОБНОВЛЕННЫЙ метод: Получение выбранных фильтров"""
        try:
            return {
                'signal_types': [k for k, v in self.signal_vars.items() if v.get()],
                'lines': [k for k, v in self.line_vars.items() if v.get()],
                'wagons': [k for k, v in self.wagon_vars.items() if v.get()],
                'components': [k for k, v in self.component_vars.items() if v.get()],
                'hardware': [k for k, v in self.hardware_vars.items() if v.get()],
                'changed_only': self.changed_only_var.get()  # НОВОЕ поле
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения фильтров: {e}")
            return {'changed_only': False}

    def _select_all_filters(self):
        """Выбор всех фильтров"""
        try:
            for var in self.signal_vars.values():
                var.set(True)
            for var in self.line_vars.values():
                var.set(True)
            for var in self.wagon_vars.values():
                var.set(True)
            for var in self.component_vars.values():
                var.set(True)

            self.logger.info("Выбраны все фильтры")
            self._on_filter_changed()

        except Exception as e:
            self.logger.error(f"Ошибка выбора всех фильтров: {e}")

    def _clear_all_filters(self):
        """Очистка всех фильтров"""
        try:
            for var in self.signal_vars.values():
                var.set(False)
            for var in self.line_vars.values():
                var.set(False)
            for var in self.wagon_vars.values():
                var.set(False)
            for var in self.component_vars.values():
                var.set(False)

            self.logger.info("Очищены все фильтры")
            self._on_filter_changed()

        except Exception as e:
            self.logger.error(f"Ошибка очистки всех фильтров: {e}")

    def reset_filters(self):
        """ОБНОВЛЕННЫЙ сброс всех фильтров"""
        try:
            # Сбрасываем все чекбоксы к значениям по умолчанию
            for var in self.signal_vars.values():
                var.set(True)
            for var in self.line_vars.values():
                var.set(True)
            for var in self.wagon_vars.values():
                var.set(True)
            for var in self.component_vars.values():
                var.set(True)
            for var in self.hardware_vars.values():
                var.set(True)

            # НОВОЕ: Сбрасываем фильтр изменяемых параметров
            self.changed_only_var.set(False)

            self.logger.info("Все фильтры сброшены")

            # Применяем изменения
            if self.controller:
                self.controller.apply_filters()

        except Exception as e:
            self.logger.error(f"Ошибка сброса фильтров: {e}")

    def set_controller(self, controller):
        """Установка контроллера"""
        self.controller = controller
        self.logger.info("Контроллер установлен в FilterPanel")

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.controller = None
            self.logger.info("FilterPanel очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки FilterPanel: {e}")
