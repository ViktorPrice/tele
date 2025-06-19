"""
Панель визуализации графиков с интеграцией Use Cases и Clean Architecture
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Импорты из архитектуры
from ...core.application.use_cases.filter_parameters_use_case import (
    FilterParametersUseCase,
    FilterParametersRequest,
    FilterParametersResponse,
)
from ...core.application.use_cases.plot_generation_use_case import (
    PlotGenerationUseCase,
    PlotGenerationRequest,
)
from ...infrastructure.plotting.adapters.tkinter_plot_adapter import TkinterPlotAdapter
from ...infrastructure.plotting.core.plot_builder import PlotBuilder
from ...infrastructure.plotting.interactions.base_interaction import ZoomInteraction

class PlotVisualizationPanel(ttk.Frame):
    """Панель визуализации графиков с полной интеграцией архитектуры"""

    class TimeAxisZoomInteraction:
        def __init__(self, canvas, figure):
            self.canvas = canvas
            self.figure = figure
            self._scroll_cid = None
            self.logger = logging.getLogger(self.__class__.__name__)

        def setup_handlers(self):
            self._scroll_cid = self.canvas.mpl_connect('scroll_event', self._on_scroll)

        def _on_scroll(self, event):
            try:
                if event.inaxes is None:
                    return

                ax = event.inaxes

                # Улучшенное логирование для диагностики
                self.logger.debug(f"Scroll event: step={event.step}, x={event.x}, y={event.y}")
                self.logger.debug(f"Event inaxes: {event.inaxes}")
                self.logger.debug(f"Event xdata: {event.xdata}")
                self.logger.debug(f"Current xlim: {ax.get_xlim()}")

                # Определяем направление масштабирования
                zoom_factor = 1.2 if event.step < 0 else 1 / 1.2

                xdata = event.xdata
                if xdata is None:
                    return

                xlim = ax.get_xlim()
                x_center = xdata
                x_range = xlim[1] - xlim[0]

                new_x_range = x_range * zoom_factor
                new_xlim = (x_center - new_x_range / 2, x_center + new_x_range / 2)

                ax.set_xlim(new_xlim)
                self.canvas.draw_idle()
            except Exception as e:
                self.logger.error(f"Ошибка масштабирования колесом мыши: {e}")

        def cleanup(self):
            if self._scroll_cid:
                self.canvas.mpl_disconnect(self._scroll_cid)

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Use Cases
        self.filter_use_case: Optional[FilterParametersUseCase] = None
        self.plot_use_case: Optional[PlotGenerationUseCase] = None

        # Компоненты архитектуры
        self.plot_adapter = TkinterPlotAdapter()
        self.plot_builder: Optional[PlotBuilder] = None

        # UI компоненты
        self.notebook: Optional[ttk.Notebook] = None
        self.control_frame: Optional[ttk.Frame] = None
        self.plot_tabs: Dict[str, Dict[str, Any]] = {}

        # Состояние
        self.current_session_id: Optional[str] = None
        self.is_building_plots = False

        # Инициализация max_params_var здесь, чтобы гарантировать наличие атрибута
        self.max_params_var = tk.IntVar(value=10)
        self.plot_type_var = tk.StringVar(value="step")

        self._setup_ui()
        self._setup_use_cases()

        # Создаем приветственную вкладку при инициализации, если нет других вкладок
        if self.notebook and len(self.notebook.tabs()) == 0:
            self._create_welcome_tab()

        self.logger.info("PlotVisualizationPanel инициализирован")

    def _setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Настройка сетки
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Панель управления
        self._create_control_panel()

        # Основная область с вкладками графиков
        self._create_plot_area()

        # Контекстное меню для вкладок
        self._create_context_menu()

    def _create_control_panel(self):
        """Создание панели управления графиками"""
        self.control_frame = ttk.LabelFrame(
            self, text="Управление графиками", padding="10"
        )
        self.control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.control_frame.grid_columnconfigure(1, weight=1)

        # Кнопки управления
        buttons_frame = ttk.Frame(self.control_frame)
        buttons_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 10))

        # Основные кнопки
        ttk.Button(
            buttons_frame, text="🔄 Обновить графики", command=self._refresh_all_plots
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            buttons_frame, text="📊 Авто-группировка", command=self._auto_group_plots
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            buttons_frame, text="💾 Экспорт всех", command=self._export_all_plots
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            buttons_frame, text="🗑️ Очистить все", command=self._clear_all_plots
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            buttons_frame, text="🔍 Сброс масштабирования", command=self._reset_zoom_current_plot
        ).pack(side=tk.LEFT, padx=(0, 5))

    def _reset_zoom_current_plot(self):
        """Сброс масштабирования для текущего графика"""
        try:
            current_tab = self.notebook.select()
            if not current_tab:
                return
            tab_text = self.notebook.tab(current_tab, "text")
            if tab_text in self.plot_tabs and "time_zoom_interaction" in self.plot_tabs[tab_text]:
                tab_info = self.plot_tabs[tab_text]
                figure = tab_info.get("figure")
                if figure and figure.axes:
                    ax = figure.axes[0]
                    ax.autoscale()
                    figure.canvas.draw_idle()
                self.logger.info(f"Сброс масштабирования для графика '{tab_text}' выполнен")
        except Exception as e:
            self.logger.error(f"Ошибка сброса масштабирования: {e}")

        # Настройки отображения
        settings_frame = ttk.Frame(self.control_frame)
        settings_frame.grid(row=1, column=0, columnspan=4, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        # Тип графика
        ttk.Label(settings_frame, text="Тип:").grid(row=0, column=0, sticky="w")
        # Инициализация plot_type_var здесь, чтобы избежать ошибки отсутствия атрибута
        if not hasattr(self, 'plot_type_var') or self.plot_type_var is None:
            self.plot_type_var = tk.StringVar(value="step")
        plot_type_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.plot_type_var,
            values=["line", "step", "scatter"],
            state="readonly",
            width=10,
        )
        plot_type_combo.grid(row=0, column=1, sticky="w", padx=(5, 0))

        # Максимум параметров на график
        ttk.Label(settings_frame, text="Макс. параметров:").grid(
            row=0, column=2, sticky="w", padx=(20, 0)
        )
        # Инициализация max_params_var один раз
        if not hasattr(self, 'max_params_var') or self.max_params_var is None:
            self.max_params_var = tk.IntVar(value=10)
        max_params_spin = tk.Spinbox(
            settings_frame, from_=1, to=50, textvariable=self.max_params_var, width=5
        )
        max_params_spin.grid(row=0, column=3, sticky="w", padx=(5, 0))

        # Автообновление
        self.auto_update_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            settings_frame, text="Автообновление", variable=self.auto_update_var
        ).grid(row=0, column=4, sticky="w", padx=(20, 0))

    def _create_plot_area(self):
        """Создание области с вкладками графиков"""
        # Notebook для вкладок
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Привязка событий
        self.notebook.bind("<Button-3>", self._on_tab_right_click)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        """Обработчик изменения вкладки"""
        try:
            selected_tab = event.widget.select()
            tab_text = event.widget.tab(selected_tab, "text")
            self.logger.info(f"Вкладка изменена: {tab_text}")
            # Можно добавить логику обновления состояния или данных при смене вкладки
        except Exception as e:
            self.logger.error(f"Ошибка в обработчике изменения вкладки: {e}")

        # Создаем стартовую вкладку
        self._create_welcome_tab()

    def _on_tab_right_click(self, event):
        """Обработчик правого клика по вкладке"""
        try:
            # Определяем вкладку под курсором
            x, y = event.x, event.y
            element = self.notebook.identify(x, y)
            if element != "label":
                return

            tab_index = self.notebook.index(f"@{x},{y}")
            if tab_index < 0:
                return

            # Выделяем вкладку
            self.notebook.select(tab_index)

            # Показываем контекстное меню
            if hasattr(self, "context_menu"):
                self.context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            self.logger.error(f"Ошибка обработки правого клика по вкладке: {e}")

    def _create_welcome_tab(self):
        """Создание приветственной вкладки"""
        welcome_frame = ttk.Frame(self.notebook)
        self.notebook.add(welcome_frame, text="Добро пожаловать")

        # Центрированное содержимое
        content_frame = ttk.Frame(welcome_frame)
        content_frame.pack(expand=True, fill=tk.BOTH)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        # Информационный текст
        info_text = """
        🎯 АНАЛИЗАТОР ТЕЛЕМЕТРИИ TRAMM
        
        📊 Интерактивная визуализация данных
        🔧 Выберите параметры в левой панели
        📈 Нажмите "Построить график" для создания графиков
        
        ⚡ Возможности:
        • Интерактивные графики с подсказками
        • Масштабирование и панорамирование
        • Группировка параметров по типам
        • Экспорт в различных форматах
        • Аннотации и измерения
        
        🚀 Начните с загрузки CSV файла!
        Не забудте добавить в csv параметры:
        W_BUIK_TRAIN_NUM - для автоматической подстановки маршрута и линии МЦД
        DW_CURRENT_ID_WAGON - для определения ведущей головы и правильной расстановки вагонов
        W_TIMESTAMP_YEAR_
        BY_TIMESTAMP_DAY_
        BY_TIMESTAMP_MONTH_
        BY_TIMESTAMP_MINUTE_
        BY_TIMESTAMP_HOUR_
        BY_TIMESTAMP_SMALLSECOND_
        BY_TIMESTAMP_SECOND_
        Для отображения времени
        """

        info_label = tk.Label(
            content_frame,
            text=info_text,
            font=("Arial", 11),
            justify=tk.CENTER,
            fg="#555555",
            bg="white",
        )
        info_label.grid(row=0, column=0, padx=20, pady=20)

    def _create_context_menu(self):
        """Создание контекстного меню для вкладок"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="🔄 Обновить", command=self._refresh_current_plot
        )
        self.context_menu.add_command(
            label="💾 Экспорт", command=self._export_current_plot
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="📋 Дублировать", command=self._duplicate_current_plot
        )
        self.context_menu.add_command(
            label="⚙️ Настройки", command=self._configure_current_plot
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="❌ Закрыть", command=self._close_current_plot
        )

    def _duplicate_current_plot(self):
        """Дублирование текущей вкладки графика"""
        try:
            current_tab = self.notebook.select()
            if not current_tab:
                self.logger.warning("Нет выбранной вкладки для дублирования")
                return

            tab_text = self.notebook.tab(current_tab, "text")
            if tab_text not in self.plot_tabs:
                self.logger.warning(f"Вкладка '{tab_text}' не найдена в plot_tabs")
                return

            tab_info = self.plot_tabs[tab_text]
            parameters = tab_info.get("parameters", [])
            start_time = tab_info.get("start_time")
            end_time = tab_info.get("end_time")

            # Создаем новую вкладку с суффиксом " (копия)"
            new_tab_name = f"{tab_text} (копия)"
            suffix_index = 1
            while new_tab_name in self.plot_tabs:
                suffix_index += 1
                new_tab_name = f"{tab_text} (копия {suffix_index})"

            self._create_plot_tab(new_tab_name, parameters, start_time, end_time)
            self.logger.info(f"Вкладка графика '{tab_text}' дублирована как '{new_tab_name}'")

        except Exception as e:
            self.logger.error(f"Ошибка дублирования вкладки графика: {e}")

    def _setup_use_cases(self):
        """Настройка Use Cases"""
        try:
            if self.controller and hasattr(self.controller, "model"):
                model = self.controller.model

                # Инициализация Use Cases
                if hasattr(model, "parameter_repository") and hasattr(
                    model, "filtering_service"
                ):
                    self.filter_use_case = FilterParametersUseCase(
                        model.parameter_repository, model.filtering_service
                    )

                if hasattr(model, "data_loader"):
                    self.plot_builder = PlotBuilder(model.data_loader)

                self.logger.info("Use Cases инициализированы")
            else:
                self.logger.warning(
                    "Контроллер или модель недоступны для инициализации Use Cases"
                )

        except Exception as e:
            self.logger.error(f"Ошибка настройки Use Cases: {e}")

    # === ОСНОВНЫЕ МЕТОДЫ ПОСТРОЕНИЯ ГРАФИКОВ ===

    def build_plots_for_parameters(
        self, parameters: List[Dict[str, Any]], start_time: datetime, end_time: datetime
    ):
        """ИСПРАВЛЕННОЕ построение графиков для параметров"""
        try:
            if self.is_building_plots:
                self.logger.warning("Построение графиков уже выполняется")
                return

            if not parameters:
                self._show_warning("Нет выбранных параметров для построения графиков")
                return

            self.is_building_plots = True
            self._show_building_progress(True)

            # ДИАГНОСТИКА: Проверяем данные
            self.logger.info(
                f"Начало построения графиков для {len(parameters)} параметров"
            )
            self.logger.info(f"Временной диапазон: {start_time} - {end_time}")

            # Проверяем PlotBuilder
            if not self.plot_builder:
                self.logger.error("PlotBuilder не инициализирован")
                self._show_error("PlotBuilder не инициализирован")
                return

            # Проверяем data_loader
            if (
                not hasattr(self.plot_builder, "data_loader")
                or not self.plot_builder.data_loader
            ):
                self.logger.error("DataLoader не найден в PlotBuilder")
                self._show_error("DataLoader не найден")
                return

            # ДИАГНОСТИКА: Проверяем наличие данных
            has_data = self.plot_builder._has_data()
            self.logger.info(f"Проверка данных: {has_data}")

            if not has_data:
                # Пытаемся диагностировать проблему
                data_loader = self.plot_builder.data_loader
                self.logger.info(f"DataLoader тип: {type(data_loader)}")
                self.logger.info(
                    f"DataLoader атрибуты: {[attr for attr in dir(data_loader) if not attr.startswith('_')]}"
                )
                if hasattr(data_loader, "data"):
                    self.logger.info(f"data_loader.data: {type(data_loader.data)}")
                    if hasattr(data_loader.data, "shape"):
                        self.logger.info(f"Размер данных: {data_loader.data.shape}")

                if hasattr(data_loader, "parameters"):
                    self.logger.info(
                        f"Количество параметров: {len(data_loader.parameters) if data_loader.parameters else 0}"
                    )
                self._show_error("Нет данных для построения графиков")
                return

            # Удаляем приветственную вкладку если есть
            self._remove_welcome_tab()

            # Группируем параметры для создания графиков
            plot_groups = self._group_parameters_for_plots(parameters)
            self.logger.info(f"Создано групп графиков: {len(plot_groups)}")

            # Создаем графики для каждой группы
            success_count = 0
            for group_name, group_params in plot_groups.items():
                try:
                    self.logger.info(f"Создание вкладки графика: {group_name} с {len(group_params)} параметрами")
                    self._create_plot_tab(
                        group_name, group_params, start_time, end_time
                    )
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"Ошибка создания графика '{group_name}': {e}")
                    continue

            if success_count > 0:
                self.logger.info(
                    f"Успешно создано {success_count} графиков из {len(plot_groups)}"
                )
            else:
                self._show_error(
                    "Не удалось создать ни одного графика. Проверьте данные и логи."
                )

        except Exception as e:
            self.logger.error(f"Ошибка построения графиков: {e}")
            import traceback

            traceback.print_exc()
            self._show_error(f"Ошибка построения графиков: {e}")
        finally:
            self.is_building_plots = False
            self._show_building_progress(False)

    def _group_parameters_for_plots(
        self, parameters: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Группировка параметров для создания графиков"""
        try:
            max_params = self.max_params_var.get()
            groups = {}

            # Группировка по типу данных
            type_groups = {}
            for param in parameters:
                signal_type = param.get("signal_type", "Unknown")
                if signal_type not in type_groups:
                    type_groups[signal_type] = []
                type_groups[signal_type].append(param)

            # Создание финальных групп с ограничением по количеству
            for signal_type, type_params in type_groups.items():
                if len(type_params) <= max_params:
                    # Группа помещается в один график
                    groups[f"{signal_type} сигналы"] = type_params
                else:
                    # Разбиваем на подгруппы
                    for i in range(0, len(type_params), max_params):
                        subgroup = type_params[i : i + max_params]
                        group_num = (i // max_params) + 1
                        groups[f"{signal_type} сигналы (часть {group_num})"] = subgroup

            return groups

        except Exception as e:
            self.logger.error(f"Ошибка группировки параметров: {e}")
            # Fallback - один график со всеми параметрами
            return {"Все параметры": parameters[: self.max_params_var.get()]}

    def _create_plot_tab(
        self,
        tab_name: str,
        parameters: List[Dict[str, Any]],
        start_time: datetime,
        end_time: datetime,
    ):
        """Создание вкладки с графиком"""
        try:
            if not self.plot_builder:
                self.logger.error("PlotBuilder не инициализирован")
                return

            # Проверяем и инициализируем plot_type_var, если отсутствует
            if not hasattr(self, 'plot_type_var') or self.plot_type_var is None:
                self.plot_type_var = tk.StringVar(value="step")

            # Создание графика через PlotBuilder
            figure, ax = self.plot_builder.build_plot(
                parameters,
                start_time,
                end_time,
                title=tab_name,
                strategy=self.plot_type_var.get() if self.plot_type_var and self.plot_type_var.get() else "step",
            )

            # Создание UI виджета через адаптер
            canvas, info_panel = self.plot_adapter.create_plot_widget(
                self.notebook, figure, tab_name, parameters
            )

            # Получение родительского контейнера для canvas
            plot_container = canvas.get_tk_widget().master

            # Добавление вкладки в notebook
            self.notebook.add(plot_container, text=tab_name)

            # Создаем TimeAxisZoomInteraction для масштабирования по оси времени
            time_zoom = self.TimeAxisZoomInteraction(canvas, figure)
            time_zoom.setup_handlers()

            # Сохранение информации о вкладке
            self.plot_tabs[tab_name] = {
                "parameters": parameters,
                "start_time": start_time,
                "end_time": end_time,
                "figure": figure,
                "canvas": canvas,
                "info_panel": info_panel,
                "container": plot_container,
                "time_zoom_interaction": time_zoom,
            }

            # Переключение на новую вкладку
            self.notebook.select(plot_container)

            self.logger.info(f"Создана вкладка графика: {tab_name}")

        except Exception as e:
            self.logger.error(f"Ошибка создания вкладки графика: {e}")

    def _remove_welcome_tab(self):
        """Удаление приветственной вкладки"""
        try:
            for i, tab_id in enumerate(self.notebook.tabs()):
                tab_text = self.notebook.tab(tab_id, "text")
                if tab_text == "Добро пожаловать":
                    self.logger.info("Удаление приветственной вкладки")
                    self.notebook.forget(i)
                    break
        except Exception as e:
            self.logger.debug(f"Ошибка удаления приветственной вкладки: {e}")

    # === МЕТОДЫ УПРАВЛЕНИЯ ГРАФИКАМИ ===

    def _refresh_all_plots(self):
        """Обновление всех графиков"""
        try:
            if not self.plot_tabs:
                return

            for tab_name, tab_info in self.plot_tabs.items():
                self._refresh_plot(tab_name, tab_info)

            self.logger.info("Все графики обновлены")

        except Exception as e:
            self.logger.error(f"Ошибка обновления графиков: {e}")

    def _refresh_current_plot(self):
        """Обновление текущего графика"""
        try:
            current_tab = self.notebook.select()
            if not current_tab:
                return

            tab_text = self.notebook.tab(current_tab, "text")
            if tab_text not in self.plot_tabs:
                return

            tab_info = self.plot_tabs[tab_text]
            self._refresh_plot(tab_text, tab_info)
            self.logger.info(f"Текущий график '{tab_text}' обновлен")

        except Exception as e:
            self.logger.error(f"Ошибка обновления текущего графика: {e}")

    def _refresh_plot(self, tab_name: str, tab_info: Dict[str, Any]):
        """Обновление конкретного графика"""
        try:
            if not self.plot_builder:
                return

            # Перестроение графика
            figure, ax = self.plot_builder.build_plot(
                tab_info["parameters"],
                tab_info["start_time"],
                tab_info["end_time"],
                title=tab_name,
                strategy=self.plot_type_var.get(),
            )

            # Обновление через адаптер
            self.plot_adapter.update_plot(tab_name, figure)

            # Обновление сохраненной информации
            tab_info["figure"] = figure

        except Exception as e:
            self.logger.error(f"Ошибка обновления графика {tab_name}: {e}")

    def _auto_group_plots(self):
        """Автоматическая группировка графиков"""
        try:
            if not self.controller:
                return

            # Получаем выбранные параметры
            selected_params = self._get_selected_parameters()
            if not selected_params:
                self._show_warning("Нет выбранных параметров")
                return

            # Получаем временной диапазон
            start_time, end_time = self._get_time_range()
            if not start_time or not end_time:
                self._show_warning("Не удалось получить временной диапазон")
                return

            # Очищаем существующие графики
            self._clear_all_plots()

            # Создаем новые группированные графики
            self.build_plots_for_parameters(selected_params, start_time, end_time)

        except Exception as e:
            self.logger.error(f"Ошибка автогруппировки: {e}")

    def _export_current_plot(self):
        """Экспорт текущего графика"""
        try:
            current_tab = self.notebook.select()
            if not current_tab:
                return

            tab_text = self.notebook.tab(current_tab, "text")
            if tab_text not in self.plot_tabs:
                return

            # Выбор файла для сохранения
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"),
                    ("SVG files", "*.svg"),
                    ("EPS files", "*.eps"),
                ],
                title=f"Экспорт графика: {tab_text}",
            )

            if file_path:
                tab_info = self.plot_tabs[tab_text]
                tab_info["figure"].savefig(file_path, dpi=300, bbox_inches="tight")
                self._show_info(f"График сохранен: {file_path}")

        except Exception as e:
            self.logger.error(f"Ошибка экспорта текущего графика: {e}")
            self._show_error(f"Ошибка экспорта: {str(e)}")

    def _export_all_plots(self):
        """Экспорт всех графиков в выбранную папку"""
        try:
            if not self.plot_tabs:
                self._show_warning("Нет графиков для экспорта")
                return

            folder_path = filedialog.askdirectory(title="Выберите папку для экспорта всех графиков")
            if not folder_path:
                return

            for tab_name, tab_info in self.plot_tabs.items():
                safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in tab_name)
                file_path = f"{folder_path}/{safe_name}.png"
                tab_info["figure"].savefig(file_path, dpi=300, bbox_inches="tight")
                self.logger.info(f"График '{tab_name}' экспортирован в {file_path}")

            self._show_info(f"Все графики успешно экспортированы в {folder_path}")

        except Exception as e:
            self.logger.error(f"Ошибка экспорта всех графиков: {e}")
            self._show_error(f"Ошибка экспорта всех графиков: {str(e)}")

    def _clear_all_plots(self):
        """Очистка всех графиков и вкладок"""
        try:
            if not self.plot_tabs:
                return

            for tab_name in list(self.plot_tabs.keys()):
                tab_info = self.plot_tabs[tab_name]
                container = tab_info.get("container")
                if container:
                    self.notebook.forget(container)
                # Очистка ресурсов
                time_zoom = tab_info.get("time_zoom_interaction")
                if time_zoom:
                    time_zoom.cleanup()

            self.plot_tabs.clear()
            self._create_welcome_tab()
            self.logger.info("Все графики очищены")

        except Exception as e:
            self.logger.error(f"Ошибка очистки графиков: {e}")

    def _configure_current_plot(self):
        """Настройка текущего графика"""
        try:
            current_tab = self.notebook.select()
            if not current_tab:
                self.logger.warning("Нет выбранной вкладки для настройки")
                return

            tab_text = self.notebook.tab(current_tab, "text")
            if tab_text not in self.plot_tabs:
                self.logger.warning(f"Вкладка '{tab_text}' не найдена в plot_tabs")
                return

            # Создаем окно настроек
            config_window = tk.Toplevel(self)
            config_window.title(f"Настройки графика: {tab_text}")
            config_window.geometry("400x300")
            config_window.transient(self)
            config_window.grab_set()

            # Основной фрейм
            main_frame = ttk.Frame(config_window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Настройки отображения
            display_frame = ttk.LabelFrame(main_frame, text="Отображение", padding="5")
            display_frame.pack(fill=tk.X, pady=(0, 10))

            # Тип графика
            ttk.Label(display_frame, text="Тип графика:").grid(row=0, column=0, sticky="w")
            plot_type_var = tk.StringVar(value=self.plot_type_var.get() if self.plot_type_var else "step")
            plot_type_combo = ttk.Combobox(
                display_frame,
                textvariable=plot_type_var,
                values=["line", "step", "scatter"],
                state="readonly"
            )
            plot_type_combo.grid(row=0, column=1, sticky="ew", padx=(5, 0))

            # Цветовая схема
            ttk.Label(display_frame, text="Цветовая схема:").grid(row=1, column=0, sticky="w", pady=(5, 0))
            color_scheme_var = tk.StringVar(value="default")
            color_scheme_combo = ttk.Combobox(
                display_frame,
                textvariable=color_scheme_var,
                values=["default", "viridis", "plasma", "coolwarm"],
                state="readonly"
            )
            color_scheme_combo.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(5, 0))

            display_frame.grid_columnconfigure(1, weight=1)

            # Кнопки
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))

            def apply_settings():
                try:
                    # Применяем настройки
                    self.plot_type_var.set(plot_type_var.get())
                    
                    # Перестраиваем график
                    tab_info = self.plot_tabs[tab_text]
                    self._refresh_plot(tab_text, tab_info)
                    
                    config_window.destroy()
                    self.logger.info(f"Настройки графика '{tab_text}' применены")
                except Exception as e:
                    self.logger.error(f"Ошибка применения настроек: {e}")

            ttk.Button(button_frame, text="Применить", command=apply_settings).pack(side=tk.RIGHT, padx=(5, 0))
            ttk.Button(button_frame, text="Отмена", command=config_window.destroy).pack(side=tk.RIGHT)

        except Exception as e:
            self.logger.error(f"Ошибка настройки графика: {e}")

    def _close_current_plot(self):
        """Закрытие текущей вкладки графика"""
        try:
            current_tab = self.notebook.select()
            if not current_tab:
                return

            tab_text = self.notebook.tab(current_tab, "text")
            if tab_text == "Добро пожаловать":
                return  # Не закрываем приветственную вкладку

            if tab_text in self.plot_tabs:
                tab_info = self.plot_tabs[tab_text]
                
                # Очистка ресурсов
                time_zoom = tab_info.get("time_zoom_interaction")
                if time_zoom:
                    time_zoom.cleanup()
                
                # Удаляем из словаря
                del self.plot_tabs[tab_text]

            # Закрываем вкладку
            self.notebook.forget(current_tab)
            
            # Если не осталось вкладок, создаем приветственную
            if len(self.notebook.tabs()) == 0:
                self._create_welcome_tab()

            self.logger.info(f"Вкладка графика '{tab_text}' закрыта")

        except Exception as e:
            self.logger.error(f"Ошибка закрытия вкладки графика: {e}")

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def _get_selected_parameters(self) -> List[Dict[str, Any]]:
        """Получение выбранных параметров из контроллера"""
        try:
            if self.controller and hasattr(self.controller, 'get_selected_parameters'):
                return self.controller.get_selected_parameters()
            return []
        except Exception as e:
            self.logger.error(f"Ошибка получения выбранных параметров: {e}")
            return []

    def _get_time_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Получение временного диапазона"""
        try:
            if self.controller and hasattr(self.controller, 'get_time_range'):
                time_range = self.controller.get_time_range()
                return time_range.get('start'), time_range.get('end')
            return None, None
        except Exception as e:
            self.logger.error(f"Ошибка получения временного диапазона: {e}")
            return None, None

    def _show_building_progress(self, show: bool):
        """Показ/скрытие индикатора построения графиков"""
        try:
            if show:
                # Можно добавить прогресс-бар или изменить курсор
                self.config(cursor="wait")
            else:
                self.config(cursor="")
        except Exception as e:
            self.logger.debug(f"Ошибка изменения индикатора прогресса: {e}")

    def _show_info(self, message: str):
        """Показ информационного сообщения"""
        messagebox.showinfo("Информация", message)

    def _show_warning(self, message: str):
        """Показ предупреждения"""
        messagebox.showwarning("Предупреждение", message)

    def _show_error(self, message: str):
        """Показ ошибки"""
        messagebox.showerror("Ошибка", message)

    # === ПУБЛИЧНЫЕ МЕТОДЫ ===

    def set_controller(self, controller):
        """Установка контроллера"""
        self.controller = controller
        self._setup_use_cases()
        self.logger.info("Контроллер установлен в PlotVisualizationPanel")

    def update_plots(self):
        """Обновление всех графиков"""
        if self.auto_update_var.get():
            self._refresh_all_plots()

    def clear_plots(self):
        """Публичный метод очистки графиков"""
        self._clear_all_plots()

    def get_current_plot_info(self) -> Optional[Dict[str, Any]]:
        """Получение информации о текущем графике"""
        try:
            current_tab = self.notebook.select()
            if not current_tab:
                return None

            tab_text = self.notebook.tab(current_tab, "text")
            return self.plot_tabs.get(tab_text)
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о текущем графике: {e}")
            return None
