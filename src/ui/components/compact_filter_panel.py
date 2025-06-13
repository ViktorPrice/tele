# src/ui/components/compact_filter_panel.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Компактная панель фильтров с синхронизацией с TimePanel
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, List

class CompactFilterPanel(ttk.Frame):
    """Компактная панель фильтров с синхронизацией с TimePanel"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Переменные для чекбоксов
        self.signal_vars = {}
        self.line_vars = {}
        self.wagon_vars = {}
        self.component_vars = {}

        # Состояние синхронизации
        self.is_updating = False
        self.has_priority_for_changed_filter = False  # TimePanel имеет приоритет

        self._setup_compact_ui()
        self.logger.info("CompactFilterPanel инициализирован с синхронизацией")

    def _setup_compact_ui(self):
        """Настройка компактного UI в одну строку"""
        # Настройка сетки
        self.grid_columnconfigure(1, weight=0)  # Типы сигналов
        self.grid_columnconfigure(3, weight=1)  # Линии (растягиваются)
        self.grid_columnconfigure(5, weight=0)  # Вагоны

        row = 0

        # Информация о синхронизации
        info_frame = ttk.Frame(self)
        info_frame.grid(row=row, column=0, columnspan=6, sticky="ew", pady=(0, 3))
        
        info_label = ttk.Label(
            info_frame, 
            text="💡 Фильтр 'Только изменяемые' находится в панели времени",
            font=('Arial', 8),
            foreground='blue'
        )
        info_label.pack(anchor="w")

        row += 1

        # Типы сигналов
        ttk.Label(self, text="Типы:", font=('Arial', 9)).grid(row=row, column=0, sticky="w")

        types_frame = ttk.Frame(self)
        types_frame.grid(row=row, column=1, sticky="w", padx=(5, 10))

        signal_types = ['B', 'BY', 'W', 'DW', 'F', 'WF']
        for i, signal_type in enumerate(signal_types):
            var = tk.BooleanVar()
            var.set(True)
            self.signal_vars[signal_type] = var

            checkbox = ttk.Checkbutton(
                types_frame,
                text=signal_type,
                variable=var,
                command=self._on_filter_changed
            )
            checkbox.grid(row=0, column=i, sticky="w", padx=2)

        # Разделитель
        ttk.Separator(self, orient='vertical').grid(row=row, column=2, sticky="ns", padx=5)

        # Линии связи
        ttk.Label(self, text="Линии:", font=('Arial', 9)).grid(row=row, column=3, sticky="w")

        self.lines_frame = ttk.Frame(self)
        self.lines_frame.grid(row=row, column=3, sticky="ew", padx=(5, 10))

        # Разделитель
        ttk.Separator(self, orient='vertical').grid(row=row, column=4, sticky="ns", padx=5)

        # Вагоны
        ttk.Label(self, text="Вагоны:", font=('Arial', 9)).grid(row=row, column=5, sticky="w")

        wagons_frame = ttk.Frame(self)
        wagons_frame.grid(row=row, column=5, sticky="w", padx=(5, 0))

        for i in range(1, 9):  # Вагоны 1-8
            var = tk.BooleanVar()
            var.set(True)
            self.wagon_vars[str(i)] = var

            checkbox = ttk.Checkbutton(
                wagons_frame,
                text=str(i),
                variable=var,
                command=self._on_filter_changed
            )
            checkbox.grid(row=0, column=i-1, sticky="w", padx=1)

    def _on_filter_changed(self):
        """Обработка изменения фильтров с проверкой приоритета TimePanel"""
        try:
            if self.is_updating:
                return

            # Проверяем приоритет TimePanel
            if self._is_time_panel_priority_active():
                self.logger.info("TimePanel имеет приоритет, обычные фильтры неактивны")
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

    def update_line_checkboxes(self, lines: List[str]):
        """Обновление чекбоксов линий на основе загруженных данных"""
        try:
            # Очищаем существующие чекбоксы линий
            for widget in self.lines_frame.winfo_children():
                widget.destroy()

            self.line_vars.clear()

            # Создаем новые чекбоксы (максимум 6 для компактности)
            display_lines = lines[:6] if len(lines) > 6 else lines
            
            for i, line in enumerate(sorted(display_lines)):
                var = tk.BooleanVar()
                var.set(True)  # По умолчанию все включены
                self.line_vars[line] = var

                # Сокращаем название для компактности
                short_name = line.replace('L_CAN_', '').replace('L_TV_', '').replace('_CH', '')[:8]
                
                checkbox = ttk.Checkbutton(
                    self.lines_frame,
                    text=short_name,
                    variable=var,
                    command=self._on_filter_changed
                )
                checkbox.grid(row=0, column=i, sticky="w", padx=2)

            # Если линий больше 6, показываем индикатор
            if len(lines) > 6:
                more_label = ttk.Label(self.lines_frame, text=f"+{len(lines)-6}", font=('Arial', 8))
                more_label.grid(row=0, column=6, sticky="w", padx=2)

            self.logger.info(f"Обновлены чекбоксы линий: {len(display_lines)} из {len(lines)}")

        except Exception as e:
            self.logger.error(f"Ошибка обновления чекбоксов линий: {e}")

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
            
            # Добавляем информацию о приоритете TimePanel
            filters['time_panel_priority'] = self._is_time_panel_priority_active()
            
            return filters
            
        except Exception as e:
            self.logger.error(f"Ошибка получения фильтров: {e}")
            return {'time_panel_priority': False}

    def disable_changed_only_checkbox(self):
        """УСТАРЕВШИЙ МЕТОД: Для обратной совместимости"""
        self.logger.warning("Метод disable_changed_only_checkbox устарел - чекбокс только в TimePanel")

    def _sync_with_time_panel(self):
        """Синхронизация с TimePanel"""
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
                    self.logger.info("Синхронизация: отключены фильтры (приоритет TimePanel)")
                else:
                    # TimePanel в обычном режиме - включаем наши фильтры
                    self._enable_all_filters()
                    self.logger.info("Синхронизация: включены фильтры")
            else:
                self.logger.warning("TimePanel не найден для синхронизации")

        except Exception as e:
            self.logger.error(f"Ошибка синхронизации с TimePanel: {e}")

    def _disable_all_filters(self):
        """Отключение всех фильтров (когда активен приоритет TimePanel)"""
        try:
            # Отключаем все чекбоксы типов сигналов
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Checkbutton):
                            child.config(state='disabled')

        except Exception as e:
            self.logger.error(f"Ошибка отключения фильтров: {e}")

    def _enable_all_filters(self):
        """Включение всех фильтров"""
        try:
            # Включаем все чекбоксы
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Checkbutton):
                            child.config(state='normal')

        except Exception as e:
            self.logger.error(f"Ошибка включения фильтров: {e}")

    def set_controller(self, controller):
        """Установка контроллера"""
        self.controller = controller
        self.logger.info("Контроллер установлен в CompactFilterPanel")

        # Автоматическая синхронизация при установке контроллера
        if controller:
            self._sync_with_time_panel()

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.controller = None
            self.signal_vars.clear()
            self.line_vars.clear()
            self.wagon_vars.clear()
            self.component_vars.clear()
            self.logger.info("CompactFilterPanel очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки CompactFilterPanel: {e}")

    def __str__(self):
        return f"CompactFilterPanel(priority={self.has_priority_for_changed_filter}, time_panel_priority={self._is_time_panel_priority_active()})"

    def __repr__(self):
        return self.__str__()
