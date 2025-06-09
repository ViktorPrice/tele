# src/ui/components/ui_components.py - ПОЛНАЯ РЕАЛИЗАЦИЯ
"""
Главный класс управления UI компонентами (интеграция с Clean Architecture)
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .time_panel import TimePanel
from .filter_panel import FilterPanel
from .parameter_panel import ParameterPanel
from .action_panel import ActionPanel
from ..controllers.main_controller import MainController


class UIComponents:
    """Главный менеджер UI компонентов (ПОЛНАЯ ВЕРСИЯ)"""

    def __init__(self, root: tk.Tk, controller: MainController):
        self.root = root
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # UI панели
        self.time_panel: Optional[TimePanel] = None
        self.filter_panel: Optional[FilterPanel] = None
        self.parameter_panel: Optional[ParameterPanel] = None
        self.action_panel: Optional[ActionPanel] = None

        # Основные контейнеры
        self.main_content_frame: Optional[ttk.Frame] = None
        self.left_panel_frame: Optional[ttk.Frame] = None
        self.right_panel_frame: Optional[ttk.Frame] = None

        # Состояние UI
        self.is_initialized = False

        self._setup_main_layout()
        self._create_ui_panels()
        self._setup_bindings()

        self.is_initialized = True
        self.logger.info("UIComponents инициализированы")

    def _setup_main_layout(self):
        """Создание основного макета приложения"""
        # Главный контейнер
        self.main_content_frame = ttk.Frame(self.root)
        self.main_content_frame.grid(
            row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Настройка сетки главного окна
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Настройка сетки главного контейнера
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(
            0, weight=1)  # Левая панель
        self.main_content_frame.grid_columnconfigure(
            1, weight=3)  # Правая панель (графики)

        # Левая панель управления
        self.left_panel_frame = ttk.Frame(self.main_content_frame)
        self.left_panel_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.left_panel_frame.grid_columnconfigure(0, weight=1)

        # Правая панель (для графиков - будет заполнена PlotVisualizationPanel)
        self.right_panel_frame = ttk.Frame(self.main_content_frame)
        self.right_panel_frame.grid(row=0, column=1, sticky="nsew")
        self.right_panel_frame.grid_rowconfigure(0, weight=1)
        self.right_panel_frame.grid_columnconfigure(0, weight=1)

        self.logger.info("Основной макет создан")

    def _create_ui_panels(self):
        """Создание всех UI панелей"""
        try:
            # 1. Панель времени
            self._create_time_panel()

            # 2. Панель фильтров
            self._create_filter_panel()

            # 3. Панель параметров
            self._create_parameter_panel()

            # 4. Панель действий
            self._create_action_panel()

            self.logger.info("Все UI панели созданы")

        except Exception as e:
            self.logger.error(f"Ошибка создания UI панелей: {e}")
            raise

    def _create_time_panel(self):
        """Создание панели управления временем"""
        time_frame = ttk.LabelFrame(
            self.left_panel_frame,
            text="Временной диапазон",
            padding="10"
        )
        time_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        time_frame.grid_columnconfigure(0, weight=1)

        self.time_panel = TimePanel(time_frame, self.controller)
        self.time_panel.grid(row=0, column=0, sticky="ew")

        self.logger.debug("Панель времени создана")

    def _create_filter_panel(self):
        """Создание панели фильтров"""
        filter_frame = ttk.LabelFrame(
            self.left_panel_frame,
            text="Фильтры параметров",
            padding="10"
        )
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        filter_frame.grid_columnconfigure(0, weight=1)

        self.filter_panel = FilterPanel(filter_frame, self.controller)
        self.filter_panel.grid(row=0, column=0, sticky="ew")

        self.logger.debug("Панель фильтров создана")

    def _create_parameter_panel(self):
        """Создание панели параметров"""
        parameter_frame = ttk.LabelFrame(
            self.left_panel_frame,
            text="Параметры телеметрии",
            padding="10"
        )
        parameter_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        parameter_frame.grid_columnconfigure(0, weight=1)
        parameter_frame.grid_rowconfigure(0, weight=1)

        # Устанавливаем вес для растягивания панели параметров
        self.left_panel_frame.grid_rowconfigure(2, weight=1)

        self.parameter_panel = ParameterPanel(parameter_frame, self.controller)
        self.parameter_panel.grid(row=0, column=0, sticky="nsew")

        self.logger.debug("Панель параметров создана")

    def _create_action_panel(self):
        """Создание панели действий"""
        action_frame = ttk.LabelFrame(
            self.left_panel_frame,
            text="Действия",
            padding="10"
        )
        action_frame.grid(row=3, column=0, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        self.action_panel = ActionPanel(action_frame, self.controller)
        self.action_panel.grid(row=0, column=0, sticky="ew")

        self.logger.debug("Панель действий создана")

    def _setup_bindings(self):
        """Настройка связей между компонентами"""
        try:
            # Связь между фильтрами и параметрами
            if self.filter_panel and self.parameter_panel:
                # При изменении фильтров обновляем список параметров
                self.filter_panel.on_filter_changed = self._on_filters_changed

            # Связь между временной панелью и контроллером
            if self.time_panel:
                self.time_panel.on_time_range_changed = self._on_time_range_changed

            # Связь между параметрами и действиями
            if self.parameter_panel and self.action_panel:
                self.parameter_panel.on_selection_changed = self._on_parameter_selection_changed

            self.logger.debug("Связи между компонентами настроены")

        except Exception as e:
            self.logger.error(f"Ошибка настройки связей: {e}")

    # === ОБРАБОТЧИКИ СОБЫТИЙ ===

    def _on_filters_changed(self):
        """Обработка изменения фильтров"""
        try:
            if self.controller:
                self.controller.apply_filters()
        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения фильтров: {e}")

    def _on_time_range_changed(self, from_time: str, to_time: str):
        """Обработка изменения временного диапазона"""
        try:
            if self.controller:
                # Можно добавить валидацию временного диапазона
                self.logger.info(
                    f"Временной диапазон изменен: {from_time} - {to_time}")
        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения времени: {e}")

    def _on_parameter_selection_changed(self, selected_count: int):
        """Обработка изменения выбора параметров"""
        try:
            # Обновляем состояние кнопок действий
            if self.action_panel:
                self.action_panel.update_action_buttons_state(
                    selected_count > 0)

            self.logger.debug(f"Выбрано параметров: {selected_count}")

        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения выбора: {e}")

    # === ПУБЛИЧНЫЕ МЕТОДЫ ===

    def update_parameters(self, parameters: List[Dict[str, Any]]):
        """Обновление списка параметров во всех панелях"""
        try:
            if self.parameter_panel:
                self.parameter_panel.update_parameters(parameters)

            if self.filter_panel:
                self.filter_panel.update_available_options(parameters)

            self.logger.info(
                f"Параметры обновлены: {len(parameters)} элементов")

        except Exception as e:
            self.logger.error(f"Ошибка обновления параметров: {e}")

    def update_time_range(self, from_time: str, to_time: str,
                          duration: str = "", total_records: int = 0):
        """Обновление временного диапазона"""
        try:
            if self.time_panel:
                self.time_panel.update_time_fields(
                    from_time, to_time, duration, total_records
                )

            self.logger.info(
                f"Временной диапазон обновлен: {from_time} - {to_time}")

        except Exception as e:
            self.logger.error(f"Ошибка обновления временного диапазона: {e}")

    def get_selected_parameters(self) -> List[Dict[str, Any]]:
        """Получение выбранных параметров"""
        try:
            if self.parameter_panel:
                return self.parameter_panel.get_selected_parameters()
            return []
        except Exception as e:
            self.logger.error(f"Ошибка получения выбранных параметров: {e}")
            return []

    def get_filter_criteria(self) -> Dict[str, Any]:
        """Получение критериев фильтрации"""
        try:
            if self.filter_panel:
                return self.filter_panel.get_selected_filters()
            return {}
        except Exception as e:
            self.logger.error(f"Ошибка получения критериев фильтрации: {e}")
            return {}

    def get_time_range(self) -> tuple[str, str]:
        """Получение временного диапазона"""
        try:
            if self.time_panel:
                return self.time_panel.get_time_range()
            return "", ""
        except Exception as e:
            self.logger.error(f"Ошибка получения временного диапазона: {e}")
            return "", ""

    def set_loading_state(self, loading: bool):
        """Установка состояния загрузки для всех панелей"""
        try:
            panels = [self.time_panel, self.filter_panel,
                      self.parameter_panel, self.action_panel]

            for panel in panels:
                if panel and hasattr(panel, 'set_loading_state'):
                    panel.set_loading_state(loading)

            self.logger.debug(f"Состояние загрузки установлено: {loading}")

        except Exception as e:
            self.logger.error(f"Ошибка установки состояния загрузки: {e}")

    def enable_all_panels(self):
        """Включение всех панелей"""
        try:
            panels = [self.time_panel, self.filter_panel,
                      self.parameter_panel, self.action_panel]

            for panel in panels:
                if panel and hasattr(panel, 'enable'):
                    panel.enable()

        except Exception as e:
            self.logger.error(f"Ошибка включения панелей: {e}")

    def disable_all_panels(self):
        """Отключение всех панелей"""
        try:
            panels = [self.time_panel, self.filter_panel,
                      self.parameter_panel, self.action_panel]

            for panel in panels:
                if panel and hasattr(panel, 'disable'):
                    panel.disable()

        except Exception as e:
            self.logger.error(f"Ошибка отключения панелей: {e}")

    def reset_all_panels(self):
        """Сброс всех панелей к состоянию по умолчанию"""
        try:
            if self.filter_panel:
                self.filter_panel.reset_filters()

            if self.parameter_panel:
                self.parameter_panel.clear_selection()

            if self.time_panel:
                self.time_panel.clear_time_fields()

            self.logger.info("Все панели сброшены")

        except Exception as e:
            self.logger.error(f"Ошибка сброса панелей: {e}")

    def update_status_info(self, message: str, params_count: int = 0,
                           selected_count: int = 0):
        """Обновление статусной информации во всех панелях"""
        try:
            # Обновляем счетчики в панели параметров
            if self.parameter_panel:
                self.parameter_panel.update_counters(
                    params_count, selected_count)

            # Обновляем статус в панели действий
            if self.action_panel:
                self.action_panel.update_status(message)

        except Exception as e:
            self.logger.error(f"Ошибка обновления статусной информации: {e}")

    def show_loading_indicator(self, message: str = "Загрузка..."):
        """Показ индикатора загрузки"""
        try:
            self.set_loading_state(True)
            self.update_status_info(message)

            # Принудительное обновление UI
            self.root.update_idletasks()

        except Exception as e:
            self.logger.error(f"Ошибка показа индикатора загрузки: {e}")

    def hide_loading_indicator(self):
        """Скрытие индикатора загрузки"""
        try:
            self.set_loading_state(False)
            self.update_status_info("Готов")

        except Exception as e:
            self.logger.error(f"Ошибка скрытия индикатора загрузки: {e}")

    def cleanup(self):
        """Очистка ресурсов UI компонентов"""
        try:
            # Очищаем все панели
            panels = [self.time_panel, self.filter_panel,
                      self.parameter_panel, self.action_panel]

            for panel in panels:
                if panel and hasattr(panel, 'cleanup'):
                    panel.cleanup()

            # Обнуляем ссылки
            self.time_panel = None
            self.filter_panel = None
            self.parameter_panel = None
            self.action_panel = None
            self.controller = None

            self.logger.info("UIComponents очищены")

        except Exception as e:
            self.logger.error(f"Ошибка очистки UIComponents: {e}")
