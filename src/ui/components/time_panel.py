# src/ui/components/time_panel.py - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Панель управления временным диапазоном с приоритетной логикой изменяемых параметров
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta


class TimePanel(ttk.Frame):
    """Панель управления временным диапазоном с приоритетной логикой изменяемых параметров"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("TimePanel: __init__ вызван")

        # Виджеты времени
        self.from_time_entry: Optional[tk.Entry] = None
        self.to_time_entry: Optional[tk.Entry] = None
        self.duration_label: Optional[ttk.Label] = None
        self.records_label: Optional[ttk.Label] = None
        self.apply_button: Optional[ttk.Button] = None
        self.reset_button: Optional[ttk.Button] = None

        # ПРИОРИТЕТНЫЙ чекбокс изменяемых параметров (единственный в системе)
        self.changed_only_var: Optional[tk.BooleanVar] = None
        self.changed_only_checkbox: Optional[ttk.Checkbutton] = None

        # Состояние
        self.is_updating = False
        self.has_priority_for_changed_filter = True  # Приоритет для изменяемых параметров

        self._setup_ui()
        self.logger.info("TimePanel инициализирован с приоритетной логикой")

    def _setup_ui(self):
        """Настройка UI с приоритетной логикой"""
        self.logger.info("TimePanel: создание UI с приоритетной логикой")
        try:
            # Конфигурация сетки
            self.grid_columnconfigure(1, weight=1)

            # Заголовок с иконкой приоритета
            title_frame = ttk.Frame(self)
            title_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
            title_frame.grid_columnconfigure(1, weight=1)

            # Иконка приоритета
            priority_label = ttk.Label(title_frame, text="⏰", font=('Arial', 12))
            priority_label.grid(row=0, column=0, padx=(0, 5))

            title_label = ttk.Label(title_frame, text="Временной диапазон",
                                    font=('Arial', 10, 'bold'))
            title_label.grid(row=0, column=1, sticky="w")

            # Поля времени "От"
            from_frame = ttk.Frame(self)
            from_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
            from_frame.grid_columnconfigure(1, weight=1)

            ttk.Label(from_frame, text="От:", width=8).grid(row=0, column=0, sticky="w")
            self.from_time_entry = tk.Entry(from_frame, font=('Consolas', 9))
            self.from_time_entry.grid(row=0, column=1, sticky="ew", padx=5)
            self.from_time_entry.bind('<FocusOut>', self._on_time_changed)
            self.from_time_entry.bind('<Return>', self._on_time_changed)

            # Поля времени "До"
            to_frame = ttk.Frame(self)
            to_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
            to_frame.grid_columnconfigure(1, weight=1)

            ttk.Label(to_frame, text="До:", width=8).grid(row=0, column=0, sticky="w")
            self.to_time_entry = tk.Entry(to_frame, font=('Consolas', 9))
            self.to_time_entry.grid(row=0, column=1, sticky="ew", padx=5)
            self.to_time_entry.bind('<FocusOut>', self._on_time_changed)
            self.to_time_entry.bind('<Return>', self._on_time_changed)

            # ПРИОРИТЕТНАЯ секция фильтрации изменяемых параметров
            priority_filter_frame = ttk.LabelFrame(self, text="🔥 Приоритетная фильтрация")
            priority_filter_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
            priority_filter_frame.grid_columnconfigure(0, weight=1)

            self.changed_only_var = tk.BooleanVar()
            self.changed_only_checkbox = ttk.Checkbutton(
                priority_filter_frame,
                text="⚡ Только изменяемые параметры (приоритет)",
                variable=self.changed_only_var,
                command=self._on_changed_only_toggle_priority
            )
            self.changed_only_checkbox.grid(row=0, column=0, sticky="w", padx=5, pady=5)

            # Информационная подсказка
            info_label = ttk.Label(
                priority_filter_frame,
                text="💡 Этот фильтр имеет приоритет над всеми остальными",
                font=('Arial', 8),
                foreground='blue'
            )
            info_label.grid(row=1, column=0, sticky="w", padx=5, pady=(0, 5))

            # Информационные поля
            info_frame = ttk.Frame(self)
            info_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

            self.duration_label = ttk.Label(info_frame, text="Длительность: не определена",
                                            font=('Arial', 8))
            self.duration_label.pack(anchor="w")

            self.records_label = ttk.Label(info_frame, text="Записей: 0",
                                           font=('Arial', 8))
            self.records_label.pack(anchor="w")

            # Кнопки управления
            button_frame = ttk.Frame(self)
            button_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

            self.apply_button = ttk.Button(button_frame, text="🚀 Применить",
                                           command=self._apply_time_range_priority)
            self.apply_button.pack(side=tk.LEFT, padx=2)

            self.reset_button = ttk.Button(button_frame, text="🔄 Сброс",
                                           command=self._reset_time_range_priority)
            self.reset_button.pack(side=tk.LEFT, padx=2)

            # Кнопки быстрой настройки
            quick_frame = ttk.LabelFrame(self, text="⚡ Быстрая настройка")
            quick_frame.grid(row=6, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

            quick_buttons = [
                ("1 мин", 60),
                ("5 мин", 300),
                ("10 мин", 600),
                ("30 мин", 1800),
                ("1 час", 3600)
            ]

            for text, seconds in quick_buttons:
                ttk.Button(quick_frame, text=text,
                           command=lambda s=seconds: self._quick_range_priority(s)).pack(
                    side=tk.LEFT, padx=2, pady=2)

            self.logger.info("TimePanel: UI создан с приоритетной логикой")

        except Exception as e:
            self.logger.error(f"TimePanel: ошибка в _setup_ui: {e}")

    def _on_changed_only_toggle_priority(self):
        """ПРИОРИТЕТНЫЙ обработчик: Переключение фильтра изменяемых параметров"""
        try:
            is_changed_only = self.changed_only_var.get()
            self.logger.info(f"🔥 ПРИОРИТЕТНЫЙ фильтр 'Только изменяемые параметры': {is_changed_only}")

            # Синхронизируем с другими панелями (отключаем их чекбоксы)
            self._sync_with_other_panels(is_changed_only)

            # ПРИОРИТЕТНОЕ применение через контроллер
            if self.controller and hasattr(self.controller, 'apply_changed_parameters_filter'):
                if is_changed_only:
                    # Применяем приоритетный фильтр изменяемых параметров
                    self.controller.apply_changed_parameters_filter()
                    self.logger.info("✅ Применен приоритетный фильтр изменяемых параметров")
                else:
                    # Возвращаемся к стандартным фильтрам
                    self.controller.apply_filters(changed_only=False)
                    self.logger.info("✅ Возврат к стандартным фильтрам")
            elif self.controller and hasattr(self.controller, 'apply_filters'):
                # Fallback для старой версии контроллера
                self.controller.apply_filters(changed_only=is_changed_only)
                self.logger.warning("⚠️ Использован fallback метод apply_filters")
            else:
                self.logger.error("❌ Контроллер не поддерживает фильтрацию")

        except Exception as e:
            self.logger.error(f"Ошибка приоритетного переключения фильтра: {e}")

    def _sync_with_other_panels(self, is_enabled: bool):
        """Синхронизация с другими панелями фильтрации"""
        try:
            if not self.controller:
                return

            # Отключаем чекбокс в FilterPanel если он есть
            filter_panel = self.controller.get_ui_component('filter_panel')
            if filter_panel and hasattr(filter_panel, '_special_vars'):
                if 'changed_only' in filter_panel._special_vars:
                    filter_panel._special_vars['changed_only'].set(is_enabled)
                    self.logger.debug("Синхронизирован чекбокс в FilterPanel")

            # Уведомляем об изменении приоритета
            if hasattr(self.controller, '_emit_event'):
                self.controller._emit_event('priority_filter_changed', {
                    'source': 'time_panel',
                    'changed_only': is_enabled
                })

        except Exception as e:
            self.logger.error(f"Ошибка синхронизации с другими панелями: {e}")

    def update_time_fields(self, from_time: str, to_time: str,
                           duration: str = "", total_records: int = 0):
        """ОСНОВНОЙ МЕТОД: Обновление полей времени из внешнего источника"""
        try:
            self.is_updating = True

            # Обновляем поля времени
            if self.from_time_entry:
                self.from_time_entry.delete(0, tk.END)
                self.from_time_entry.insert(0, from_time)

            if self.to_time_entry:
                self.to_time_entry.delete(0, tk.END)
                self.to_time_entry.insert(0, to_time)

            # Обновляем информационные поля
            if self.duration_label:
                duration_text = f"Длительность: {duration}" if duration else "Длительность: не определена"
                self.duration_label.config(text=duration_text)

            if self.records_label:
                self.records_label.config(text=f"Записей: {total_records}")

            # Принудительное обновление отображения
            self.update_idletasks()

            self.logger.info(f"✅ Поля времени обновлены: {from_time} - {to_time}")

        except Exception as e:
            self.logger.error(f"Ошибка обновления полей времени: {e}")
        finally:
            self.is_updating = False

    def get_time_range(self) -> Tuple[str, str]:
        """Получение временного диапазона из полей ввода"""
        try:
            from_time = self.from_time_entry.get().strip() if self.from_time_entry else ""
            to_time = self.to_time_entry.get().strip() if self.to_time_entry else ""
            return from_time, to_time

        except Exception as e:
            self.logger.error(f"Ошибка получения временного диапазона: {e}")
            return "", ""

    def set_time_range(self, from_time: str, to_time: str):
        """Альтернативный метод установки времени"""
        try:
            self.update_time_fields(from_time, to_time)
        except Exception as e:
            self.logger.error(f"Ошибка set_time_range: {e}")

    def get_filter_settings(self) -> Dict[str, Any]:
        """Получение настроек приоритетной фильтрации"""
        try:
            return {
                'changed_only': self.changed_only_var.get() if self.changed_only_var else False,
                'has_priority': self.has_priority_for_changed_filter,
                'source_panel': 'time_panel'
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения настроек фильтрации: {e}")
            return {'changed_only': False, 'has_priority': False}

    def set_changed_params_priority(self, has_priority: bool):
        """Установка приоритета для изменяемых параметров"""
        self.has_priority_for_changed_filter = has_priority
        if has_priority:
            self.logger.info("🔥 TimePanel получил приоритет для изменяемых параметров")
        else:
            self.logger.info("TimePanel потерял приоритет для изменяемых параметров")

    def disable_changed_only_checkbox(self):
        """Отключение чекбокса (используется если приоритет у другой панели)"""
        if self.changed_only_checkbox:
            self.changed_only_checkbox.config(state='disabled')
            self.logger.info("Чекбокс изменяемых параметров отключен")

    def enable_changed_only_checkbox(self):
        """Включение чекбокса"""
        if self.changed_only_checkbox:
            self.changed_only_checkbox.config(state='normal')
            self.logger.info("Чекбокс изменяемых параметров включен")

    def _on_time_changed(self, event=None):
        """Обработчик изменения времени пользователем"""
        if self.is_updating:
            return

        try:
            from_time, to_time = self.get_time_range()

            if from_time and to_time:
                # Валидация через контроллер
                if self.controller and hasattr(self.controller, '_validate_time_range'):
                    is_valid = self.controller._validate_time_range(from_time, to_time)
                    if not is_valid:
                        self.logger.warning("Введен некорректный временной диапазон")
                        return

                # Обновляем информацию о длительности
                self._update_duration_info(from_time, to_time)

                # Если включен фильтр изменяемых параметров, автоматически применяем
                if self.changed_only_var and self.changed_only_var.get():
                    self._apply_changed_params_auto()

            self.logger.debug(f"Время изменено пользователем: {from_time} - {to_time}")

        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения времени: {e}")

    def _apply_changed_params_auto(self):
        """Автоматическое применение фильтра изменяемых параметров при изменении времени"""
        try:
            if self.controller and hasattr(self.controller, 'apply_changed_parameters_filter'):
                self.controller.apply_changed_parameters_filter()
                self.logger.info("🚀 Автоматически применен фильтр изменяемых параметров")
        except Exception as e:
            self.logger.error(f"Ошибка автоматического применения фильтра: {e}")

    def _update_duration_info(self, from_time_str: str, to_time_str: str):
        """Обновление информации о длительности"""
        try:
            from_time = datetime.strptime(from_time_str, '%Y-%m-%d %H:%M:%S')
            to_time = datetime.strptime(to_time_str, '%Y-%m-%d %H:%M:%S')

            duration = to_time - from_time
            
            # Форматируем длительность
            days = duration.days
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            if days > 0:
                duration_str = f"{days} дн. {hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            if self.duration_label:
                self.duration_label.config(text=f"Длительность: {duration_str}")

        except ValueError:
            if self.duration_label:
                self.duration_label.config(text="Длительность: неверный формат времени")
        except Exception as e:
            self.logger.error(f"Ошибка обновления длительности: {e}")

    def _apply_time_range_priority(self):
        """ПРИОРИТЕТНОЕ применение временного диапазона"""
        try:
            from_time, to_time = self.get_time_range()

            if not from_time or not to_time:
                self._show_error("Укажите временной диапазон")
                return

            # Проверяем приоритетный режим
            filter_settings = self.get_filter_settings()
            
            if filter_settings['changed_only']:
                # ПРИОРИТЕТНОЕ применение изменяемых параметров
                if self.controller and hasattr(self.controller, 'apply_changed_parameters_filter'):
                    self.controller.apply_changed_parameters_filter()
                    self.logger.info("🔥 Применен ПРИОРИТЕТНЫЙ фильтр изменяемых параметров")
                else:
                    self.logger.error("❌ Контроллер не поддерживает приоритетную фильтрацию")
            else:
                # Стандартное применение
                if self.controller and hasattr(self.controller, 'apply_filters'):
                    self.controller.apply_filters()
                    self.logger.info("✅ Применены стандартные фильтры")

        except Exception as e:
            self.logger.error(f"Ошибка приоритетного применения временного диапазона: {e}")
            self._show_error(f"Ошибка применения: {e}")

    def _reset_time_range_priority(self):
        """ПРИОРИТЕТНЫЙ сброс к полному временному диапазону"""
        try:
            # Сбрасываем приоритетный чекбокс
            if self.changed_only_var:
                self.changed_only_var.set(False)
                self.logger.info("🔄 Сброшен приоритетный чекбокс")

            # Синхронизируем с другими панелями
            self._sync_with_other_panels(False)

            # Сброс через контроллер
            if self.controller and hasattr(self.controller, 'model'):
                model = self.controller.model
                if hasattr(model, 'get_time_range_fields'):
                    time_fields = model.get_time_range_fields()
                    if time_fields:
                        self.update_time_fields(
                            time_fields['from_time'],
                            time_fields['to_time'],
                            time_fields.get('duration', ''),
                            time_fields.get('total_records', 0)
                        )
                        self.logger.info("✅ Временной диапазон сброшен к полному")

                        # Применяем стандартные фильтры
                        if self.controller and hasattr(self.controller, 'apply_filters'):
                            self.controller.apply_filters()
                        return

            # Fallback
            self._clear_time_fields()
            self.logger.warning("⚠️ Сброс выполнен через очистку полей")

        except Exception as e:
            self.logger.error(f"Ошибка приоритетного сброса временного диапазона: {e}")

    def _quick_range_priority(self, seconds: int):
        """ПРИОРИТЕТНАЯ быстрая настройка диапазона"""
        try:
            if not self.controller or not hasattr(self.controller, 'model'):
                self._show_error("Контроллер не установлен")
                return

            model = self.controller.model
            if hasattr(model, 'get_time_range_fields'):
                time_fields = model.get_time_range_fields()
                if time_fields and time_fields.get('to_time'):
                    to_time = datetime.strptime(time_fields['to_time'], '%Y-%m-%d %H:%M:%S')
                    from_time = to_time - timedelta(seconds=seconds)

                    self.update_time_fields(
                        from_time.strftime('%Y-%m-%d %H:%M:%S'),
                        to_time.strftime('%Y-%m-%d %H:%M:%S'),
                        f"{seconds // 60} мин" if seconds >= 60 else f"{seconds} сек",
                        0
                    )

                    # ПРИОРИТЕТНОЕ автоприменение
                    if self.changed_only_var and self.changed_only_var.get():
                        self._apply_changed_params_auto()
                    else:
                        self._apply_time_range_priority()

                    self.logger.info(f"⚡ Установлен приоритетный быстрый диапазон: последние {seconds} сек")

        except Exception as e:
            self.logger.error(f"Ошибка приоритетной быстрой настройки: {e}")

    def _clear_time_fields(self):
        """Очистка полей времени"""
        if self.from_time_entry:
            self.from_time_entry.delete(0, tk.END)
        if self.to_time_entry:
            self.to_time_entry.delete(0, tk.END)
        if self.duration_label:
            self.duration_label.config(text="Длительность: не определена")
        if self.records_label:
            self.records_label.config(text="Записей: 0")

    def _show_error(self, message: str):
        """Показ сообщения об ошибке"""
        try:
            import tkinter.messagebox as msgbox
            msgbox.showerror("Ошибка", message)
        except Exception:
            self.logger.error(f"Ошибка отображения сообщения: {message}")

    def set_controller(self, controller):
        """Установка контроллера"""
        self.controller = controller
        self.logger.info("✅ Контроллер установлен в TimePanel")

    def enable(self):
        """Включение панели"""
        widgets = [
            self.from_time_entry, self.to_time_entry,
            self.apply_button, self.reset_button, self.changed_only_checkbox
        ]
        for widget in widgets:
            if widget:
                widget.config(state='normal')

    def disable(self):
        """Отключение панели"""
        widgets = [
            self.from_time_entry, self.to_time_entry,
            self.apply_button, self.reset_button, self.changed_only_checkbox
        ]
        for widget in widgets:
            if widget:
                widget.config(state='disabled')

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.controller = None
            self.logger.info("TimePanel очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки TimePanel: {e}")

    def __str__(self):
        return f"TimePanel(priority={self.has_priority_for_changed_filter}, changed_only={self.changed_only_var.get() if self.changed_only_var else False})"

    def __repr__(self):
        return self.__str__()
