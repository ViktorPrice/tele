# src/ui/components/filter_panel.py - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Панель фильтров без дублирования чекбокса изменяемых параметров
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, List, Optional


class FilterPanel(ttk.Frame):
    """Панель фильтров с синхронизацией с TimePanel для изменяемых параметров"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("FilterPanel: __init__ вызван")

        # Переменные для чекбоксов фильтрации
        self.signal_vars = {}
        self.line_vars = {}
        self.wagon_vars = {}
        self.component_vars = {}
        self.hardware_vars = {}

        # УБРАНО: changed_only_var - теперь только в TimePanel
        # Вместо этого синхронизируемся с TimePanel
        self.time_panel_sync = None

        # UI элементы
        self.line_scrollable_frame = None

        # Состояние
        self.is_updating = False
        self.has_priority_for_changed_filter = False  # TimePanel имеет приоритет

        self._setup_ui()
        self.logger.info("FilterPanel инициализирован без дублирования")

    def _setup_ui(self):
        """Настройка UI без дублирования чекбокса изменяемых параметров"""
        self.logger.info("FilterPanel: создание UI без дублирования")
        try:
            self.grid_columnconfigure(0, weight=1)

            # Заголовок
            title_frame = ttk.Frame(self)
            title_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
            title_frame.grid_columnconfigure(1, weight=1)

            # Иконка обычного фильтра
            icon_label = ttk.Label(title_frame, text="🔍", font=('Arial', 12))
            icon_label.grid(row=0, column=0, padx=(0, 5))

            title_label = ttk.Label(title_frame, text="Фильтры параметров", 
                                   font=('Arial', 10, 'bold'))
            title_label.grid(row=0, column=1, sticky="w")

            # УБРАНО: Секция "Только изменяемые параметры" - теперь только в TimePanel
            # Вместо этого показываем информацию о приоритете
            priority_info_frame = ttk.LabelFrame(self, text="ℹ️ Информация о фильтрации")
            priority_info_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)

            info_text = ("💡 Фильтр 'Только изменяемые параметры' находится в панели времени\n"
                        "и имеет приоритет над всеми фильтрами этой панели")
            info_label = ttk.Label(priority_info_frame, text=info_text, 
                                  font=('Arial', 8), foreground='blue')
            info_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

            # Динамические фильтры (создаются после загрузки данных)
            self.dynamic_row_start = 2

            # Фильтры линий
            self._create_line_filters()

            # Кнопки управления
            self._create_control_buttons()

            self.logger.info("FilterPanel: UI создан без дублирования")

        except Exception as e:
            self.logger.error(f"FilterPanel: ошибка в _setup_ui: {e}")

    def _create_line_filters(self):
        """Создание фильтров линий"""
        try:
            line_frame = ttk.LabelFrame(self, text="📡 Линии связи", padding="5")
            line_frame.grid(row=self.dynamic_row_start + 1, column=0, sticky="ew", padx=5, pady=2)

            # Создаем скролируемый фрейм для линий
            canvas = tk.Canvas(line_frame, height=100)
            scrollbar = ttk.Scrollbar(line_frame, orient="vertical", command=canvas.yview)
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

    def _create_control_buttons(self):
        """Создание кнопок управления"""
        try:
            button_frame = ttk.Frame(self)
            button_frame.grid(row=self.dynamic_row_start + 6, column=0, sticky="ew", padx=5, pady=5)

            # Кнопка "Выбрать все"
            select_all_btn = ttk.Button(
                button_frame,
                text="✅ Выбрать все",
                command=self._select_all_filters
            )
            select_all_btn.pack(side=tk.LEFT, padx=2)

            # Кнопка "Очистить все"
            clear_all_btn = ttk.Button(
                button_frame,
                text="❌ Очистить все",
                command=self._clear_all_filters
            )
            clear_all_btn.pack(side=tk.LEFT, padx=2)

            # Кнопка "Сброс"
            reset_btn = ttk.Button(
                button_frame,
                text="🔄 Сброс",
                command=self.reset_filters
            )
            reset_btn.pack(side=tk.LEFT, padx=2)

            # Кнопка синхронизации с TimePanel
            sync_btn = ttk.Button(
                button_frame,
                text="🔗 Синхронизация",
                command=self._sync_with_time_panel
            )
            sync_btn.pack(side=tk.LEFT, padx=2)

        except Exception as e:
            self.logger.error(f"Ошибка создания кнопок управления: {e}")

    def update_signal_type_checkboxes(self, signal_types: List[str]):
        """Динамическое обновление чекбоксов типов сигналов"""
        try:
            if not hasattr(self, 'signal_type_frame'):
                self.signal_type_frame = ttk.LabelFrame(self, text="📊 Типы сигналов", padding="5")
                self.signal_type_frame.grid(row=self.dynamic_row_start, column=0, sticky="ew", padx=5, pady=2)
            
            frame = self.signal_type_frame
            
            # Очистить старые чекбоксы
            for widget in frame.winfo_children():
                widget.destroy()
            self.signal_vars.clear()
            
            # Создать новые чекбоксы только по реально найденным типам
            for i, signal_type in enumerate(sorted(signal_types)):
                var = tk.BooleanVar()
                var.set(True)
                self.signal_vars[signal_type] = var
                
                checkbox = ttk.Checkbutton(
                    frame,
                    text=signal_type,
                    variable=var,
                    command=self._on_filter_changed
                )
                checkbox.grid(row=i//3, column=i % 3, sticky="w", padx=5, pady=2)
            
            self.logger.info(f"Обновлены чекбоксы типов сигналов: {len(signal_types)} типов")
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления чекбоксов типов сигналов: {e}")

    def update_line_checkboxes(self, lines: List[str]):
        """Обновление чекбоксов линий на основе загруженных данных"""
        try:
            if not self.line_scrollable_frame:
                self.logger.error("line_scrollable_frame не инициализирован")
                return

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

    def update_wagon_checkboxes(self, wagons: List[str]):
        """Динамическое обновление чекбоксов вагонов"""
        try:
            if not hasattr(self, 'wagon_frame'):
                self.wagon_frame = ttk.LabelFrame(self, text="🚃 Номера вагонов", padding="5")
                self.wagon_frame.grid(row=self.dynamic_row_start + 2, column=0, sticky="ew", padx=5, pady=2)
            
            frame = self.wagon_frame
            for widget in frame.winfo_children():
                widget.destroy()
            self.wagon_vars.clear()
            
            for i, wagon in enumerate(sorted(wagons, key=lambda x: int(x) if x.isdigit() else x)):
                var = tk.BooleanVar()
                var.set(True)
                self.wagon_vars[wagon] = var
                
                checkbox = ttk.Checkbutton(
                    frame,
                    text=wagon,
                    variable=var,
                    command=self._on_filter_changed
                )
                checkbox.grid(row=i//8, column=i % 8, sticky="w", padx=3, pady=1)
            
            self.logger.info(f"Обновлены чекбоксы вагонов: {len(wagons)} вагонов")
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления чекбоксов вагонов: {e}")

    def update_component_checkboxes(self, components: List[str]):
        """Динамическое обновление чекбоксов компонентов"""
        try:
            if not hasattr(self, 'component_frame'):
                self.component_frame = ttk.LabelFrame(self, text="⚙️ Компоненты", padding="5")
                self.component_frame.grid(row=self.dynamic_row_start + 3, column=0, sticky="ew", padx=5, pady=2)
            
            frame = self.component_frame
            for widget in frame.winfo_children():
                widget.destroy()
            self.component_vars.clear()
            
            for i, component in enumerate(sorted(components)):
                var = tk.BooleanVar()
                var.set(True)
                self.component_vars[component] = var
                
                checkbox = ttk.Checkbutton(
                    frame,
                    text=component,
                    variable=var,
                    command=self._on_filter_changed
                )
                checkbox.grid(row=i//3, column=i % 3, sticky="w", padx=5, pady=2)
            
            self.logger.info(f"Обновлены чекбоксы компонентов: {len(components)} компонентов")
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления чекбоксов компонентов: {e}")

    def _on_filter_changed(self):
        """Обработчик изменения фильтров с проверкой приоритета TimePanel"""
        try:
            if self.is_updating:
                return

            # Проверяем приоритет TimePanel
            if self._is_time_panel_priority_active():
                self.logger.info("⚠️ TimePanel имеет приоритет, обычные фильтры неактивны")
                return

            # Применяем стандартные фильтры
            if self.controller and hasattr(self.controller, 'apply_filters'):
                self.controller.apply_filters(changed_only=False)
                self.logger.debug("Применены стандартные фильтры")

        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения фильтра: {e}")

    def _is_time_panel_priority_active(self) -> bool:
        """Проверка активности приоритетного режима в TimePanel"""
        try:
            if not self.controller:
                return False

            time_panel = self.controller.get_ui_component('time_panel')
            if time_panel and hasattr(time_panel, 'get_filter_settings'):
                settings = time_panel.get_filter_settings()
                return settings.get('changed_only', False) and settings.get('has_priority', False)

            return False

        except Exception as e:
            self.logger.error(f"Ошибка проверки приоритета TimePanel: {e}")
            return False

    def _sync_with_time_panel(self):
        """НОВЫЙ МЕТОД: Синхронизация с TimePanel"""
        try:
            if not self.controller:
                self.logger.warning("Контроллер не установлен для синхронизации")
                return

            time_panel = self.controller.get_ui_component('time_panel')
            if time_panel and hasattr(time_panel, 'get_filter_settings'):
                settings = time_panel.get_filter_settings()
                
                if settings.get('changed_only', False):
                    # TimePanel в режиме изменяемых параметров - отключаем наши фильтры
                    self._disable_all_filters()
                    self.logger.info("🔗 Синхронизация: отключены фильтры (приоритет TimePanel)")
                else:
                    # TimePanel в обычном режиме - включаем наши фильтры
                    self._enable_all_filters()
                    self.logger.info("🔗 Синхронизация: включены фильтры")
            else:
                self.logger.warning("TimePanel не найден для синхронизации")

        except Exception as e:
            self.logger.error(f"Ошибка синхронизации с TimePanel: {e}")

    def _disable_all_filters(self):
        """Отключение всех фильтров (когда активен приоритет TimePanel)"""
        try:
            # Отключаем все чекбоксы
            for frame_name in ['signal_type_frame', 'wagon_frame', 'component_frame']:
                if hasattr(self, frame_name):
                    frame = getattr(self, frame_name)
                    for widget in frame.winfo_children():
                        if isinstance(widget, ttk.Checkbutton):
                            widget.config(state='disabled')

            # Отключаем чекбоксы линий
            if self.line_scrollable_frame:
                for widget in self.line_scrollable_frame.winfo_children():
                    if isinstance(widget, ttk.Checkbutton):
                        widget.config(state='disabled')

        except Exception as e:
            self.logger.error(f"Ошибка отключения фильтров: {e}")

    def _enable_all_filters(self):
        """Включение всех фильтров"""
        try:
            # Включаем все чекбоксы
            for frame_name in ['signal_type_frame', 'wagon_frame', 'component_frame']:
                if hasattr(self, frame_name):
                    frame = getattr(self, frame_name)
                    for widget in frame.winfo_children():
                        if isinstance(widget, ttk.Checkbutton):
                            widget.config(state='normal')

            # Включаем чекбоксы линий
            if self.line_scrollable_frame:
                for widget in self.line_scrollable_frame.winfo_children():
                    if isinstance(widget, ttk.Checkbutton):
                        widget.config(state='normal')

        except Exception as e:
            self.logger.error(f"Ошибка включения фильтров: {e}")

    def get_selected_filters(self) -> Dict[str, Any]:
        """Получение выбранных фильтров без поля changed_only"""
        try:
            filters = {}
            
            if self.signal_vars:
                filters['signal_types'] = [k for k, v in self.signal_vars.items() if v.get()]
            if self.line_vars:
                filters['lines'] = [k for k, v in self.line_vars.items() if v.get()]
            if self.wagon_vars:
                filters['wagons'] = [k for k, v in self.wagon_vars.items() if v.get()]
            if self.component_vars:
                filters['components'] = [k for k, v in self.component_vars.items() if v.get()]
            if self.hardware_vars:
                filters['hardware'] = [k for k, v in self.hardware_vars.items() if v.get()]
            
            # УБРАНО: changed_only - теперь только в TimePanel
            # Вместо этого проверяем приоритет TimePanel
            filters['time_panel_priority'] = self._is_time_panel_priority_active()
            
            return filters
            
        except Exception as e:
            self.logger.error(f"Ошибка получения фильтров: {e}")
            return {'time_panel_priority': False}

    def set_filter_settings(self, settings: Dict[str, Any]):
        """НОВЫЙ МЕТОД: Установка настроек фильтров"""
        try:
            self.is_updating = True

            # Устанавливаем фильтры типов сигналов
            if 'signal_types' in settings and self.signal_vars:
                selected_types = settings['signal_types']
                for signal_type, var in self.signal_vars.items():
                    var.set(signal_type in selected_types)

            # Устанавливаем фильтры линий
            if 'lines' in settings and self.line_vars:
                selected_lines = settings['lines']
                for line, var in self.line_vars.items():
                    var.set(line in selected_lines)

            # Устанавливаем фильтры вагонов
            if 'wagons' in settings and self.wagon_vars:
                selected_wagons = settings['wagons']
                for wagon, var in self.wagon_vars.items():
                    var.set(wagon in selected_wagons)

            # Устанавливаем фильтры компонентов
            if 'components' in settings and self.component_vars:
                selected_components = settings['components']
                for component, var in self.component_vars.items():
                    var.set(component in selected_components)

            self.logger.info("Настройки фильтров установлены")

        except Exception as e:
            self.logger.error(f"Ошибка установки настроек фильтров: {e}")
        finally:
            self.is_updating = False

    def _select_all_filters(self):
        """Выбор всех фильтров"""
        try:
            if self._is_time_panel_priority_active():
                self.logger.warning("⚠️ Нельзя изменять фильтры при активном приоритете TimePanel")
                return

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
            if self._is_time_panel_priority_active():
                self.logger.warning("⚠️ Нельзя изменять фильтры при активном приоритете TimePanel")
                return

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
        """Сброс всех фильтров к значениям по умолчанию"""
        try:
            # Сбрасываем все чекбоксы к значениям по умолчанию (включены)
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

            self.logger.info("Все фильтры сброшены к значениям по умолчанию")

            # Применяем изменения только если нет приоритета TimePanel
            if not self._is_time_panel_priority_active():
                if self.controller and hasattr(self.controller, 'apply_filters'):
                    self.controller.apply_filters(changed_only=False)

        except Exception as e:
            self.logger.error(f"Ошибка сброса фильтров: {e}")

    def disable_changed_only_checkbox(self):
        """УСТАРЕВШИЙ МЕТОД: Для обратной совместимости"""
        self.logger.warning("Метод disable_changed_only_checkbox устарел - чекбокс теперь только в TimePanel")

    def enable_changed_only_checkbox(self):
        """УСТАРЕВШИЙ МЕТОД: Для обратной совместимости"""
        self.logger.warning("Метод enable_changed_only_checkbox устарел - чекбокс теперь только в TimePanel")

    def set_controller(self, controller):
        """Установка контроллера"""
        self.controller = controller
        self.logger.info("✅ Контроллер установлен в FilterPanel")

        # Автоматическая синхронизация при установке контроллера
        if controller:
            self._sync_with_time_panel()

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.controller = None
            self.time_panel_sync = None
            self.logger.info("FilterPanel очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки FilterPanel: {e}")

    def get_status_info(self) -> Dict[str, Any]:
        """НОВЫЙ МЕТОД: Получение информации о состоянии панели"""
        try:
            return {
                'has_priority': self.has_priority_for_changed_filter,
                'time_panel_priority_active': self._is_time_panel_priority_active(),
                'total_signal_types': len(self.signal_vars),
                'total_lines': len(self.line_vars),
                'total_wagons': len(self.wagon_vars),
                'total_components': len(self.component_vars),
                'selected_signal_types': len([v for v in self.signal_vars.values() if v.get()]),
                'selected_lines': len([v for v in self.line_vars.values() if v.get()]),
                'selected_wagons': len([v for v in self.wagon_vars.values() if v.get()]),
                'selected_components': len([v for v in self.component_vars.values() if v.get()])
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о состоянии: {e}")
            return {}

    def __str__(self):
        return f"FilterPanel(priority={self.has_priority_for_changed_filter}, time_panel_priority={self._is_time_panel_priority_active()})"

    def __repr__(self):
        return self.__str__()
