# src/ui/components/time_panel.py - ПОЛНАЯ ВЕРСИЯ С ИНТЕГРАЦИЕЙ
"""
Панель управления временным диапазоном с интеграцией с DataModel
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional, Tuple, Dict
from datetime import datetime, timedelta


class TimePanel(ttk.Frame):
    """Панель управления временным диапазоном"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Виджеты времени
        self.from_time_entry: Optional[tk.Entry] = None
        self.to_time_entry: Optional[tk.Entry] = None
        self.duration_label: Optional[ttk.Label] = None
        self.records_label: Optional[ttk.Label] = None
        self.apply_button: Optional[ttk.Button] = None
        self.reset_button: Optional[ttk.Button] = None

        # ИСПРАВЛЕНИЕ: Добавляем чекбокс изменяемых параметров
        self.changed_only_var: Optional[tk.BooleanVar] = None
        self.changed_only_checkbox: Optional[ttk.Checkbutton] = None

        # Состояние
        self.is_updating = False

        self._setup_ui()
        self.logger.info("TimePanel инициализирован")

    def _setup_ui(self):
        """Настройка пользовательского интерфейса"""
        try:
            # Конфигурация сетки
            self.grid_columnconfigure(1, weight=1)

            # Заголовок
            title_frame = ttk.Frame(self)
            title_frame.grid(row=0, column=0, columnspan=3,
                             sticky="ew", padx=5, pady=5)

            title_label = ttk.Label(title_frame, text="Временной диапазон",
                                    font=('Arial', 10, 'bold'))
            title_label.pack(side=tk.LEFT)

            # Поля времени "От"
            from_frame = ttk.Frame(self)
            from_frame.grid(row=1, column=0, columnspan=3,
                            sticky="ew", padx=5, pady=2)
            from_frame.grid_columnconfigure(1, weight=1)

            ttk.Label(from_frame, text="От:", width=8).grid(
                row=0, column=0, sticky="w")
            self.from_time_entry = tk.Entry(from_frame, font=('Consolas', 9))
            self.from_time_entry.grid(row=0, column=1, sticky="ew", padx=5)
            self.from_time_entry.bind('<FocusOut>', self._on_time_changed)
            self.from_time_entry.bind('<Return>', self._on_time_changed)

            # Поля времени "До"
            to_frame = ttk.Frame(self)
            to_frame.grid(row=2, column=0, columnspan=3,
                          sticky="ew", padx=5, pady=2)
            to_frame.grid_columnconfigure(1, weight=1)

            ttk.Label(to_frame, text="До:", width=8).grid(
                row=0, column=0, sticky="w")
            self.to_time_entry = tk.Entry(to_frame, font=('Consolas', 9))
            self.to_time_entry.grid(row=0, column=1, sticky="ew", padx=5)
            self.to_time_entry.bind('<FocusOut>', self._on_time_changed)
            self.to_time_entry.bind('<Return>', self._on_time_changed)

            # НОВОЕ: Чекбокс для изменяемых параметров
            filter_frame = ttk.LabelFrame(self, text="Фильтрация параметров")
            filter_frame.grid(row=3, column=0, columnspan=3,
                              sticky="ew", padx=5, pady=5)
            filter_frame.grid_columnconfigure(0, weight=1)

            self.changed_only_var = tk.BooleanVar()
            self.changed_only_checkbox = ttk.Checkbutton(
                filter_frame,
                text="Только изменяемые параметры",
                variable=self.changed_only_var,
                command=self._on_changed_only_toggle
            )
            self.changed_only_checkbox.grid(
                row=0, column=0, sticky="w", padx=5, pady=5)

            # Информационные поля
            info_frame = ttk.Frame(self)
            info_frame.grid(row=4, column=0, columnspan=3,
                            sticky="ew", padx=5, pady=5)

            self.duration_label = ttk.Label(info_frame, text="Длительность: не определена",
                                            font=('Arial', 8))
            self.duration_label.pack(anchor="w")

            self.records_label = ttk.Label(info_frame, text="Записей: 0",
                                           font=('Arial', 8))
            self.records_label.pack(anchor="w")

            # Кнопки управления
            button_frame = ttk.Frame(self)
            button_frame.grid(row=5, column=0, columnspan=3,
                              sticky="ew", padx=5, pady=5)

            self.apply_button = ttk.Button(button_frame, text="Применить",
                                           command=self._apply_time_range)
            self.apply_button.pack(side=tk.LEFT, padx=2)

            self.reset_button = ttk.Button(button_frame, text="Сброс",
                                           command=self._reset_time_range)
            self.reset_button.pack(side=tk.LEFT, padx=2)

            # Кнопки быстрой настройки
            quick_frame = ttk.LabelFrame(self, text="Быстрая настройка")
            quick_frame.grid(row=6, column=0, columnspan=3,
                             sticky="ew", padx=5, pady=5)

            ttk.Button(quick_frame, text="1 мин",
                       command=lambda: self._quick_range(60)).pack(side=tk.LEFT, padx=2, pady=2)
            ttk.Button(quick_frame, text="5 мин",
                       command=lambda: self._quick_range(300)).pack(side=tk.LEFT, padx=2, pady=2)
            ttk.Button(quick_frame, text="10 мин",
                       command=lambda: self._quick_range(600)).pack(side=tk.LEFT, padx=2, pady=2)

            self.logger.info("UI TimePanel настроен")

        except Exception as e:
            self.logger.error(f"Ошибка настройки UI TimePanel: {e}")

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

            self.logger.info(
                f"Поля времени обновлены: {from_time} - {to_time}")

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

    def get_filter_settings(self) -> Dict[str, bool]:
        """НОВЫЙ МЕТОД: Получение настроек фильтрации"""
        try:
            return {
                'changed_only': self.changed_only_var.get() if self.changed_only_var else False
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения настроек фильтрации: {e}")
            return {'changed_only': False}

    def _on_time_changed(self, event=None):
        """Обработчик изменения времени пользователем"""
        if self.is_updating:
            return

        try:
            from_time, to_time = self.get_time_range()

            if from_time and to_time:
                # Валидация через контроллер
                if self.controller and hasattr(self.controller, '_validate_time_range'):
                    is_valid = self.controller._validate_time_range(
                        from_time, to_time)
                    if not is_valid:
                        self.logger.warning(
                            "Введен некорректный временной диапазон")
                        return

                # Обновляем информацию о длительности
                self._update_duration_info(from_time, to_time)

            self.logger.debug(
                f"Время изменено пользователем: {from_time} - {to_time}")

        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения времени: {e}")

    def _update_duration_info(self, from_time_str: str, to_time_str: str):
        """Обновление информации о длительности"""
        try:
            from_time = datetime.strptime(from_time_str, '%Y-%m-%d %H:%M:%S')
            to_time = datetime.strptime(to_time_str, '%Y-%m-%d %H:%M:%S')

            duration = to_time - from_time
            duration_str = str(duration)

            if self.duration_label:
                self.duration_label.config(
                    text=f"Длительность: {duration_str}")

        except ValueError:
            if self.duration_label:
                self.duration_label.config(
                    text="Длительность: неверный формат времени")
        except Exception as e:
            self.logger.error(f"Ошибка обновления длительности: {e}")

    def _apply_time_range(self):
        """Применение временного диапазона через контроллер"""
        try:
            from_time, to_time = self.get_time_range()

            if not from_time or not to_time:
                self._show_error("Укажите временной диапазон")
                return

            # Применяем через контроллер
            if self.controller and hasattr(self.controller, 'apply_filters'):
                # Учитываем настройки фильтрации
                filter_settings = self.get_filter_settings()
                self.controller.apply_filters(
                    changed_only=filter_settings['changed_only'])
                self.logger.info("Временной диапазон применен")
            else:
                self.logger.warning(
                    "Контроллер не установлен или не поддерживает apply_filters")

        except Exception as e:
            self.logger.error(f"Ошибка применения временного диапазона: {e}")
            self._show_error(f"Ошибка применения: {e}")

    def _reset_time_range(self):
        """Сброс к полному временному диапазону"""
        try:
            # Сбрасываем чекбокс
            if self.changed_only_var:
                self.changed_only_var.set(False)

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
                        self.logger.info(
                            "Временной диапазон сброшен к полному")

                        # Применяем изменения
                        self._apply_time_range()
                        return

            # Fallback
            self._clear_time_fields()
            self.logger.warning("Сброс выполнен через очистку полей")

        except Exception as e:
            self.logger.error(f"Ошибка сброса временного диапазона: {e}")

    def _quick_range(self, seconds: int):
        """Быстрая настройка диапазона (последние N секунд)"""
        try:
            if not self.controller or not hasattr(self.controller, 'model'):
                self._show_error("Контроллер не установлен")
                return

            model = self.controller.model
            if hasattr(model, 'get_time_range_fields'):
                time_fields = model.get_time_range_fields()
                if time_fields and time_fields.get('to_time'):
                    to_time = datetime.strptime(
                        time_fields['to_time'], '%Y-%m-%d %H:%M:%S')
                    from_time = to_time - timedelta(seconds=seconds)

                    self.update_time_fields(
                        from_time.strftime('%Y-%m-%d %H:%M:%S'),
                        to_time.strftime('%Y-%m-%d %H:%M:%S'),
                        f"{seconds} сек",
                        0
                    )

                    # Автоприменение
                    self._apply_time_range()

                    self.logger.info(
                        f"Установлен быстрый диапазон: последние {seconds} сек")

        except Exception as e:
            self.logger.error(f"Ошибка быстрой настройки диапазона: {e}")

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
        self.logger.info("Контроллер установлен в TimePanel")

    def enable(self):
        """Включение панели"""
        for widget in [self.from_time_entry, self.to_time_entry,
                       self.apply_button, self.reset_button, self.changed_only_checkbox]:
            if widget:
                widget.config(state='normal')

    def disable(self):
        """Отключение панели"""
        for widget in [self.from_time_entry, self.to_time_entry,
                       self.apply_button, self.reset_button, self.changed_only_checkbox]:
            if widget:
                widget.config(state='disabled')

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.controller = None
            self.logger.info("TimePanel очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки TimePanel: {e}")
