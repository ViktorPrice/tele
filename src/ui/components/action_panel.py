# src/ui/components/action_panel.py - ПОЛНАЯ РЕАЛИЗАЦИЯ
"""
Панель действий с кнопками для работы с параметрами
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional


class ActionPanel(ttk.Frame):
    """Панель действий для работы с параметрами телеметрии"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("ActionPanel: __init__ вызван")

        # UI элементы
        self.load_btn: Optional[ttk.Button] = None
        self.plot_btn: Optional[ttk.Button] = None
        self.report_btn: Optional[ttk.Button] = None
        self.sop_btn: Optional[ttk.Button] = None
        self.status_label: Optional[ttk.Label] = None

        # Состояние
        self.has_parameters_selected = False
        self.is_loading = False

        self._setup_ui()
        self.logger.info("ActionPanel: _setup_ui завершён")
        self.logger.info("ActionPanel инициализирован")

    def _setup_ui(self):
        self.logger.info("ActionPanel: _setup_ui вызван")
        """Настройка пользовательского интерфейса"""
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)

        # 1. Кнопка загрузки данных
        self._create_load_section()

        # 2. Кнопки действий с параметрами
        self._create_action_buttons()

        # 3. Статусная информация
        self._create_status_section()

        self.logger.info("ActionPanel: _setup_ui завершён")

    def _create_load_section(self):
        """Создание секции загрузки"""
        load_frame = ttk.LabelFrame(self, text="Загрузка данных", padding="10")
        load_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        load_frame.grid_columnconfigure(0, weight=1)

        self.load_btn = ttk.Button(
            load_frame,
            text="📁 Загрузить CSV файл",
            command=self._on_load_csv,
            style="Accent.TButton"
        )
        self.load_btn.grid(row=0, column=0, sticky="ew")

    def _create_action_buttons(self):
        """Создание кнопок действий"""
        actions_frame = ttk.LabelFrame(
            self, text="Действия с параметрами", padding="10")
        actions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        actions_frame.grid_columnconfigure(0, weight=1)

        # Кнопка построения графика
        self.plot_btn = ttk.Button(
            actions_frame,
            text="📊 Построить график",
            command=self._on_build_plot,
            state=tk.DISABLED
        )
        self.plot_btn.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        # Кнопка генерации отчета
        self.report_btn = ttk.Button(
            actions_frame,
            text="📄 Создать отчет",
            command=self._on_generate_report,
            state=tk.DISABLED
        )
        self.report_btn.grid(row=1, column=0, sticky="ew", pady=(0, 5))

        # Кнопка генерации SOP
        self.sop_btn = ttk.Button(
            actions_frame,
            text="⚙️ Создать SOP",
            command=self._on_generate_sop,
            state=tk.DISABLED
        )
        self.sop_btn.grid(row=2, column=0, sticky="ew")

        # Кнопка тестирования
        test_btn = ttk.Button(
            actions_frame,
            text="🧪 Тест данных",
            command=self._on_load_test_data,
            style="Warning.TButton"
        )
        test_btn.grid(row=3, column=0, sticky="ew", pady=(0, 5))

    def _create_status_section(self):
        """Создание секции статуса"""
        status_frame = ttk.Frame(self)
        status_frame.grid(row=2, column=0, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ttk.Label(
            status_frame,
            text="Готов к работе",
            font=('Arial', 8),
            foreground='gray'
        )
        self.status_label.grid(row=0, column=0, sticky="ew")

    # === ОБРАБОТЧИКИ СОБЫТИЙ ===

    def _on_load_csv(self):
        """Обработка загрузки CSV файла"""
        try:
            if self.controller:
                self.controller.upload_csv()
        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV: {e}")

    def _on_build_plot(self):
        """Обработка построения графика"""
        try:
            if self.controller:
                self.controller.build_plot()
        except Exception as e:
            self.logger.error(f"Ошибка построения графика: {e}")

    def _on_generate_report(self):
        """Обработка генерации отчета"""
        try:
            if self.controller:
                self.controller.generate_report()
        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета: {e}")

    def _on_generate_sop(self):
        """Обработка генерации SOP"""
        try:
            if self.controller:
                self.controller.generate_sop()
        except Exception as e:
            self.logger.error(f"Ошибка генерации SOP: {e}")

    # === ПУБЛИЧНЫЕ МЕТОДЫ ===

    def update_action_buttons_state(self, has_parameters: bool):
        """Обновление состояния кнопок действий"""
        try:
            self.has_parameters_selected = has_parameters
            state = tk.NORMAL if (
                has_parameters and not self.is_loading) else tk.DISABLED

            action_buttons = [self.plot_btn, self.report_btn, self.sop_btn]
            for btn in action_buttons:
                if btn:
                    btn.config(state=state)

        except Exception as e:
            self.logger.error(f"Ошибка обновления состояния кнопок: {e}")

    def update_status(self, message: str):
        """Обновление статусного сообщения"""
        try:
            if self.status_label:
                self.status_label.config(text=message)
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса: {e}")

    def set_loading_state(self, loading: bool):
        """Установка состояния загрузки"""
        try:
            self.is_loading = loading

            # Состояние кнопки загрузки
            load_state = tk.DISABLED if loading else tk.NORMAL
            if self.load_btn:
                self.load_btn.config(state=load_state)

            # Состояние кнопок действий
            self.update_action_buttons_state(self.has_parameters_selected)

        except Exception as e:
            self.logger.error(f"Ошибка установки состояния загрузки: {e}")

    def enable(self):
        """Включение панели"""
        self.set_loading_state(False)

    def disable(self):
        """Отключение панели"""
        self.set_loading_state(True)

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.controller = None
            self.logger.info("ActionPanel очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки ActionPanel: {e}")

    def _on_load_test_data(self):
        """Загрузка тестовых данных"""
        try:
            if self.controller and hasattr(self.controller, 'load_test_data'):
                self.controller.load_test_data()
        except Exception as e:
            self.logger.error(f"Ошибка загрузки тестовых данных: {e}")
