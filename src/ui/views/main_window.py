# src/ui/views/main_window.py - РЕФАКТОРЕННАЯ ВЕРСИЯ (v1.0)
"""
Главное окно приложения БЕЗ legacy зависимостей и с упрощенной архитектурой
"""
from ..utils.styles import StyleManager
from ..services.state_manager import StateManager
from ..services.ui_coordinator import UICoordinator
from ..factories.component_factory import ComponentFactory
from ..layout.layout_manager import LayoutManager
import tkinter as tk
from tkinter import ttk
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from queue import Queue
import time

# Добавляем корневую папку в путь
root_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_path))


# ИСПРАВЛЕНО: Используем новый StyleManager вместо legacy

# Изменения:
# - Было: Зависимость от legacy base_ui.StyleManager
# - Стало: Использование нового StyleManager из utils
# - Влияние: Устранена legacy зависимость
# - REVIEW NEEDED: Проверить совместимость методов StyleManager


class MainWindow:
    """Главное окно приложения с упрощенной архитектурой"""

    def __init__(self, root):
        self.root = root
        self.controller = None
        self.logger = logging.getLogger(self.__class__.__name__)

        # Сервисы
        self.layout_manager = LayoutManager(root)
        self.component_factory = ComponentFactory()
        self.ui_coordinator = UICoordinator()
        self.state_manager = StateManager()

        # UIComponents менеджер
        self.ui_components: Optional[UIComponents] = None

        # Компоненты UI
        self.components: Dict[str, Any] = {}

        # Очередь для обработки событий
        self.event_queue = Queue()

        # Кэш состояния UI
        self._ui_state_cache = {}
        self._last_state_update = 0

        self.logger.info("MainWindow инициализировано")

    def setup(self):
        """УПРОЩЕННАЯ настройка и создание компонентов UI"""
        try:
            # ИСПРАВЛЕНО: Используем новый StyleManager
            style_manager = StyleManager()
            style_manager.apply_theme('light')
            self.logger.info("Стили UI настроены")

            # Настройка главного окна
            self._configure_main_window()

            # Создание основного layout
            self.layout_manager.create_main_layout()

            # Создаем заглушки компонентов сразу
            self._create_placeholder_components()

            # Запуск обработки событий
            self._start_event_processing()

            self.logger.info("UI настроен с заглушками компонентов")

        except Exception as e:
            self.logger.error(f"Ошибка настройки UI: {e}")
            raise

    def _configure_main_window(self):
        """Настройка главного окна"""
        self.root.state('zoomed')
        self.root.title("Анализатор телеметрии")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def _create_placeholder_components(self):
        """ОПТИМИЗИРОВАННОЕ создание заглушек компонентов"""
        try:
            # Конфигурация заглушек
            placeholder_config = {
                'upload': {'text': 'Панель загрузки (ожидание...)', 'row': 0},
                'time': {'text': 'Временной диапазон (ожидание...)', 'row': 1},
                'filters': {'text': 'Фильтры (ожидание...)', 'row': 2},
                'parameters': {'text': 'Параметры (ожидание...)', 'row': 3},
                'actions': {'text': 'Действия (ожидание...)', 'row': 4},
                'visualization': {'text': 'Графики (ожидание...)', 'row': 5}
            }

            # Создание заглушек
            for name, config in placeholder_config.items():
                container = self.layout_manager.get_container(name)
                if container:
                    placeholder = ttk.Label(
                        container,
                        text=config['text'],
                        font=('Arial', 10),
                        foreground='gray'
                    )
                    placeholder.grid(row=0, column=0, padx=20, pady=20)
                    self.components[f'{name}_placeholder'] = placeholder

                    # Размещение контейнера
                    container.grid(
                        row=config['row'],
                        sticky='ew' if name not in [
                            'parameters', 'visualization'] else 'nsew',
                        padx=10,
                        pady=5
                    )

            self.logger.info(
                f"Создано {len(self.components)} заглушек компонентов")

        except Exception as e:
            self.logger.error(f"Ошибка создания заглушек: {e}")

    def _create_real_components(self):
        """УЛУЧШЕННОЕ создание настоящих UI компонентов"""
        if self.controller is None:
            self.logger.error("Контроллер не установлен")
            return

        try:
            # Удаляем заглушки
            self._remove_placeholders()

            # Создание компонентов через фабрику
            component_creators = {
                'upload_panel': (self.component_factory.create_upload_panel, 'upload'),
                'time_panel': (self.component_factory.create_time_panel, 'time'),
                'filter_panel': (self.component_factory.create_filter_panel, 'filters'),
                'parameter_panel': (self.component_factory.create_parameter_panel, 'parameters'),
                'action_panel': (self.component_factory.create_action_panel, 'actions'),
                'visualization': (self.component_factory.create_visualization_area, 'visualization')
            }

            # Создание и размещение компонентов
            for component_name, (creator_func, container_name) in component_creators.items():
                container = self.layout_manager.get_container(container_name)
                if container:
                    component = creator_func(container, self.controller)
                    if component:
                        component.grid(row=0, column=0, sticky="nsew")
                        self.components[component_name] = component
                        self.logger.debug(
                            f"Создан компонент: {component_name}")

            self.logger.info(
                f"Создано {len(self.components)} настоящих компонентов UI")

        except Exception as e:
            self.logger.error(f"Ошибка создания настоящих компонентов: {e}")

    def _remove_placeholders(self):
        """Удаление заглушек"""
        for name, placeholder in list(self.components.items()):
            if name.endswith('_placeholder'):
                placeholder.destroy()
                del self.components[name]

    def _setup_coordination(self):
        """УПРОЩЕННАЯ настройка координации между компонентами"""
        # Регистрация компонентов в координаторе
        for name, component in self.components.items():
            if not name.endswith('_placeholder'):
                self.ui_coordinator.register_component(name, component)

        # Настройка связей между компонентами
        self.ui_coordinator.setup_component_links()

    def _start_event_processing(self):
        """Запуск обработки очереди событий"""
        self.root.after(100, self._process_event_queue)

    def set_controller(self, controller):
        """ИСПРАВЛЕННАЯ установка контроллера с заменой заглушек"""
        self.controller = controller

        # Создаем UIComponents менеджер с контроллером
        from ..components.ui_components import UIComponents
        self.ui_components = UIComponents(self.root, controller)

        # Создаем настоящие компоненты вместо заглушек
        self._create_real_components()

        # Настройка координации
        self._setup_coordination()

        # Передача контроллера всем компонентам
        self._setup_controller_links()

        self.logger.info(
            "Контроллер установлен, заглушки заменены на настоящие компоненты")

    def _setup_controller_links(self):
        """Установка связей с контроллером"""
        for component in self.components.values():
            if hasattr(component, 'set_controller'):
                component.set_controller(self.controller)
            elif hasattr(component, 'controller'):
                component.controller = self.controller

    # УПРОЩЕННЫЕ методы для обновления UI с кэшированием
    def update_status(self, message: str):
        """КЭШИРОВАННОЕ обновление статуса"""
        if self._should_update_ui('status', message):
            if 'upload_panel' in self.components:
                upload_panel = self.components['upload_panel']
                if hasattr(upload_panel, 'update_status'):
                    upload_panel.update_status(message)
            self._cache_ui_state('status', message)

    def update_progress(self, value: int):
        """КЭШИРОВАННОЕ обновление прогресса"""
        if self._should_update_ui('progress', value):
            if 'upload_panel' in self.components:
                upload_panel = self.components['upload_panel']
                if hasattr(upload_panel, 'update_progress'):
                    upload_panel.update_progress(value)
            self._cache_ui_state('progress', value)

    def start_processing(self, message: str = "Обработка..."):
        """Начало обработки"""
        if 'upload_panel' in self.components:
            upload_panel = self.components['upload_panel']
            if hasattr(upload_panel, 'set_loading_state'):
                upload_panel.set_loading_state(True)
            if hasattr(upload_panel, 'update_status'):
                upload_panel.update_status(message)

    def stop_processing(self):
        """Завершение обработки"""
        if 'upload_panel' in self.components:
            upload_panel = self.components['upload_panel']
            if hasattr(upload_panel, 'set_loading_state'):
                upload_panel.set_loading_state(False)

    def show_error(self, message: str):
        """Показ ошибки"""
        from tkinter import messagebox
        messagebox.showerror("Ошибка", message)

    def show_warning(self, message: str):
        """Показ предупреждения"""
        from tkinter import messagebox
        messagebox.showwarning("Предупреждение", message)

    def show_info(self, title: str, message: str):
        """Показ информации"""
        from tkinter import messagebox
        messagebox.showinfo(title, message)

    # ОПТИМИЗИРОВАННЫЕ методы для работы с параметрами
    def update_filtered_count(self, count: int):
        """КЭШИРОВАННОЕ обновление счетчика параметров"""
        if self._should_update_ui('filtered_count', count):
            if 'filter_panel' in self.components:
                filter_panel = self.components['filter_panel']
                if hasattr(filter_panel, 'update_filtered_count'):
                    filter_panel.update_filtered_count(count)
            self._cache_ui_state('filtered_count', count)

    def update_tree_all_params(self, params: list):
        """ОПТИМИЗИРОВАННОЕ обновление дерева всех параметров"""
        params_hash = hash(str(len(params)))  # Простой хэш для сравнения

        if self._should_update_ui('all_params', params_hash):
            if 'parameter_panel' in self.components:
                parameter_panel = self.components['parameter_panel']
                if hasattr(parameter_panel, 'update_tree_all_params'):
                    parameter_panel.update_tree_all_params(params)
                    self.logger.debug(
                        f"Обновлено дерево всех параметров: {len(params)} элементов")
            self._cache_ui_state('all_params', params_hash)

    def update_tree_selected_params(self, params: list):
        """Обновление дерева выбранных параметров"""
        if 'parameter_panel' in self.components:
            parameter_panel = self.components['parameter_panel']
            if hasattr(parameter_panel, 'update_tree_selected_params'):
                parameter_panel.update_tree_selected_params(params)

    def update_line_checkboxes(self, lines: list):
        """КЭШИРОВАННОЕ обновление чекбоксов линий"""
        lines_hash = hash(tuple(sorted(lines)))

        if self._should_update_ui('line_checkboxes', lines_hash):
            if 'filter_panel' in self.components:
                filter_panel = self.components['filter_panel']
                if hasattr(filter_panel, 'update_line_checkboxes'):
                    filter_panel.update_line_checkboxes(lines)
            self._cache_ui_state('line_checkboxes', lines_hash)

    # Методы для работы с графиками
    def create_plot_tabs_from_sop(self, plot_groups: Dict[str, list]):
        """Создание вкладок графиков из SOP данных"""
        if 'visualization' in self.components:
            visualization = self.components['visualization']
            if hasattr(visualization, 'create_plot_tabs_from_sop'):
                visualization.create_plot_tabs_from_sop(plot_groups)

    def auto_build_plots(self):
        """Автоматическое построение всех графиков"""
        if 'visualization' in self.components:
            visualization = self.components['visualization']
            if hasattr(visualization, 'auto_build_plots'):
                visualization.auto_build_plots()

    # НОВЫЕ методы кэширования для оптимизации
    def _should_update_ui(self, key: str, value: Any) -> bool:
        """Проверка необходимости обновления UI"""
        current_time = time.time()

        # Обновляем не чаще чем раз в 50мс
        if current_time - self._last_state_update < 0.05:
            return False

        # Проверяем изменение значения
        if key in self._ui_state_cache:
            if self._ui_state_cache[key] == value:
                return False

        return True

    def _cache_ui_state(self, key: str, value: Any):
        """Кэширование состояния UI"""
        self._ui_state_cache[key] = value
        self._last_state_update = time.time()

    def _process_event_queue(self):
        """ОПТИМИЗИРОВАННАЯ обработка очереди событий"""
        try:
            processed = 0
            max_events_per_cycle = 5  # Ограничиваем количество событий за цикл

            while not self.event_queue.empty() and processed < max_events_per_cycle:
                task, data = self.event_queue.get_nowait()
                self._handle_event(task, data)
                processed += 1

        except Exception as e:
            self.logger.error(f"Ошибка в очереди событий: {e}")

        # Повторный запуск через 100мс
        self.root.after(100, self._process_event_queue)

    def _handle_event(self, task: str, data: Any):
        """УПРОЩЕННАЯ обработка отдельного события"""
        event_handlers = {
            'error': self.show_error,
            'warning': self.show_warning,
            'update_status': self.update_status,
            'progress': self.update_progress,
            'stop_progress': self.stop_processing,
            'update_filtered_count': self.update_filtered_count,
            'update_tree_all_params': self.update_tree_all_params,
            'update_tree_selected_params': self.update_tree_selected_params,
            'update_line_checkboxes': self.update_line_checkboxes,
            'create_plot_tabs': self.create_plot_tabs_from_sop
        }

        handler = event_handlers.get(task)
        if handler:
            try:
                handler(data)
            except Exception as e:
                self.logger.error(f"Ошибка в обработчике {task}: {e}")
        else:
            self.logger.warning(f"Неизвестное событие: {task}")

    def queue_update(self, task: str, data: Any):
        """Добавление задачи в очередь"""
        try:
            self.event_queue.put((task, data))
        except Exception as e:
            self.logger.error(f"Ошибка добавления в очередь: {e}")

    # УПРОЩЕННЫЕ методы очистки
    def clear_all_ui(self):
        """ОПТИМИЗИРОВАННАЯ очистка всего интерфейса"""
        try:
            # Очистка параметров
            if 'parameter_panel' in self.components:
                parameter_panel = self.components['parameter_panel']
                if hasattr(parameter_panel, 'clear_all'):
                    parameter_panel.clear_all()

            # Очистка графиков
            if 'visualization' in self.components:
                visualization = self.components['visualization']
                if hasattr(visualization, 'clear_all'):
                    visualization.clear_all()

            # Очистка кэша
            self._ui_state_cache.clear()

            # Сброс счетчиков
            self.update_filtered_count(0)
            self.update_status("Интерфейс очищен")

            self.logger.info("UI очищен")

        except Exception as e:
            self.logger.error(f"Ошибка очистки UI: {e}")

    def cleanup(self):
        """УЛУЧШЕННАЯ очистка ресурсов UI"""
        try:
            # Очистка компонентов
            for component in self.components.values():
                if hasattr(component, 'cleanup'):
                    component.cleanup()

            # Очистка очереди
            while not self.event_queue.empty():
                try:
                    self.event_queue.get_nowait()
                except:
                    break

            # Очистка кэша
            self._ui_state_cache.clear()

            # Очистка сервисов
            self.ui_coordinator.cleanup()
            self.state_manager.cleanup()

            self.logger.info("Ресурсы UI очищены")

        except Exception as e:
            self.logger.error(f"Ошибка очистки ресурсов UI: {e}")

    # УПРОЩЕННЫЕ свойства для обратной совместимости
    @property
    def upload_panel(self):
        return self.components.get('upload_panel')

    @property
    def time_panel(self):
        return self.components.get('time_panel')

    @property
    def filter_panel(self):
        return self.components.get('filter_panel')

    @property
    def parameter_panel(self):
        return self.components.get('parameter_panel')

    @property
    def action_panel(self):
        return self.components.get('action_panel')

    @property
    def plots_notebook(self):
        visualization = self.components.get('visualization')
        return getattr(visualization, 'plots_notebook', None) if visualization else None

    def __str__(self):
        return f"MainWindow(components={len(self.components)}, cached_states={len(self._ui_state_cache)})"

    def __repr__(self):
        return self.__str__()

    # Дополнение к src/ui/views/main_window.py
    """
    Интеграция TimePanel в MainWindow
    """

    def _create_time_panel_frame(self, parent):
        """Создание фрейма панели времени"""
        time_frame = ttk.LabelFrame(
            parent, text="Временной диапазон", padding="5")

        # Создаем time_panel через factory
        if hasattr(self, 'component_factory'):
            self.time_panel = self.component_factory.create_time_panel(
                time_frame, self.controller
            )
        else:
            # Fallback
            from ..components.time_panel import TimePanel
            self.time_panel = TimePanel(time_frame, self.controller)

        self.time_panel.pack(fill="both", expand=True)

        return time_frame

    def get_component(self, component_name: str):
        """Получение компонента по имени"""
        components = {
            'time_panel': getattr(self, 'time_panel', None),
            'filter_panel': getattr(self, 'filter_panel', None),
            'parameter_panel': getattr(self, 'parameter_panel', None),
            'action_panel': getattr(self, 'action_panel', None)
        }

        return components.get(component_name)
