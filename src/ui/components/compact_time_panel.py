# src/ui/components/compact_time_panel.py - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Компактная панель времени в 2 строки с кнопками быстрой настройки и приоритетной логикой
"""
import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

class CompactTimePanel(ttk.Frame):
    """Компактная панель времени с приоритетной логикой изменяемых параметров"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

        # Переменные
        self.from_time_var = tk.StringVar()
        self.to_time_var = tk.StringVar()
        self.duration_var = tk.StringVar(value="Длительность: --")
        self.params_count_var = tk.StringVar(value="Параметров: 0")
        self.changed_only_var = tk.BooleanVar()

        # НОВЫЕ атрибуты для приоритетной логики
        self.has_priority_for_changed_filter = True  # Приоритет по умолчанию
        self.on_time_range_changed = None  # Callback для изменения времени
        self.on_changed_only_toggle = None  # Callback для переключения приоритетного фильтра

        # UI элементы
        self.quick_buttons = {}
        self.from_entry = None
        self.to_entry = None

        self._setup_compact_ui()
        self.logger.info("CompactTimePanel инициализирован с приоритетной логикой")

    def _setup_compact_ui(self):
        """Компактный UI в 2 строки с приоритетной логикой"""
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)

        # СТРОКА 1: Поля времени + кнопки быстрой настройки + ПРИОРИТЕТНЫЙ чекбокс
        row1_frame = ttk.Frame(self)
        row1_frame.grid(row=0, column=0, sticky="ew", pady=(0, 3))
        row1_frame.grid_columnconfigure(1, weight=1)
        row1_frame.grid_columnconfigure(3, weight=1)

        # От:
        ttk.Label(row1_frame, text="От:", font=('Arial', 9)).grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.from_entry = tk.Entry(row1_frame, textvariable=self.from_time_var, width=20, font=('Arial', 9))
        self.from_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.from_entry.bind('<FocusOut>', self._on_time_field_changed)
        self.from_entry.bind('<Return>', self._on_time_field_changed)

        # До:
        ttk.Label(row1_frame, text="До:", font=('Arial', 9)).grid(row=0, column=2, sticky="w", padx=(0, 5))
        
        self.to_entry = tk.Entry(row1_frame, textvariable=self.to_time_var, width=20, font=('Arial', 9))
        self.to_entry.grid(row=0, column=3, sticky="ew", padx=(0, 10))
        self.to_entry.bind('<FocusOut>', self._on_time_field_changed)
        self.to_entry.bind('<Return>', self._on_time_field_changed)

        # Кнопки быстрой настройки
        buttons_frame = ttk.Frame(row1_frame)
        buttons_frame.grid(row=0, column=4, sticky="w", padx=(10, 10))

        quick_buttons_config = [("-5с", -5), ("-1с", -1), ("+1с", +1), ("+5с", +5)]

        for i, (text, delta) in enumerate(quick_buttons_config):
            btn = ttk.Button(
                buttons_frame,
                text=text,
                width=4,
                command=lambda d=delta: self._shift_time(d),
                state=tk.DISABLED  # По умолчанию отключены
            )
            btn.grid(row=0, column=i, padx=1)
            self.quick_buttons[text] = btn

        # ПРИОРИТЕТНЫЙ чекбокс "Изменяемые параметры"
        changed_checkbox = ttk.Checkbutton(
            row1_frame,
            text="🔥 Изменяемые",
            variable=self.changed_only_var,
            command=self._on_changed_only_toggle_priority
        )
        changed_checkbox.grid(row=0, column=5, sticky="w", padx=(10, 0))

        # СТРОКА 2: Длительность + количество параметров + кнопки управления
        row2_frame = ttk.Frame(self)
        row2_frame.grid(row=1, column=0, sticky="ew")
        row2_frame.grid_columnconfigure(0, weight=1)

        info_frame = ttk.Frame(row2_frame)
        info_frame.grid(row=0, column=0, sticky="w")

        # Длительность
        duration_label = ttk.Label(info_frame, textvariable=self.duration_var, font=('Arial', 9))
        duration_label.grid(row=0, column=0, sticky="w", padx=(0, 20))

        # Количество параметров
        params_label = ttk.Label(info_frame, textvariable=self.params_count_var, font=('Arial', 9))
        params_label.grid(row=0, column=1, sticky="w", padx=(0, 20))

        # Приоритетный индикатор
        priority_label = ttk.Label(info_frame, text="⚡ Приоритет", font=('Arial', 8), foreground='red')
        priority_label.grid(row=0, column=2, sticky="w", padx=(0, 20))

        # Кнопки управления
        controls_frame = ttk.Frame(row2_frame)
        controls_frame.grid(row=0, column=1, sticky="e")

        ttk.Button(controls_frame, text="Применить", command=self._apply_filters_priority, width=10).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(controls_frame, text="Сброс", command=self._reset_time, width=8).grid(row=0, column=1)

    def _on_changed_only_toggle_priority(self):
        """ПРИОРИТЕТНОЕ переключение чекбокса изменяемых параметров"""
        is_enabled = self.changed_only_var.get()
        
        self.logger.info(f"🔥 ПРИОРИТЕТНЫЙ фильтр изменяемых параметров: {is_enabled}")
        
        # Включаем/отключаем кнопки быстрой настройки
        state = tk.NORMAL if is_enabled else tk.DISABLED
        for btn in self.quick_buttons.values():
            btn.config(state=state)

        # Вызываем callback если установлен
        if self.on_changed_only_toggle:
            self.on_changed_only_toggle(is_enabled)

        # Применяем через контроллер с приоритетной логикой
        if self.controller:
            if hasattr(self.controller, 'apply_changed_parameters_filter') and is_enabled:
                self.controller.apply_changed_parameters_filter()
            else:
                self.controller.apply_filters(changed_only=is_enabled)

    def _on_time_field_changed(self, event=None):
        """Обработка изменения полей времени"""
        try:
            self._update_duration()
            
            # Вызываем callback если установлен
            if self.on_time_range_changed:
                from_time = self.from_time_var.get()
                to_time = self.to_time_var.get()
                self.on_time_range_changed(from_time, to_time)
            
            # Если активен приоритетный режим, автоматически применяем
            if self.changed_only_var.get() and self.controller:
                if hasattr(self.controller, 'apply_changed_parameters_filter'):
                    self.controller.apply_changed_parameters_filter()
                    
        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения времени: {e}")

    def _shift_time(self, delta_seconds: int):
        """Смещение времени на заданное количество секунд"""
        try:
            if not self.changed_only_var.get():
                return

            from_str = self.from_time_var.get()
            to_str = self.to_time_var.get()

            if not from_str or not to_str:
                return

            from_time = datetime.strptime(from_str, '%Y-%m-%d %H:%M:%S')
            to_time = datetime.strptime(to_str, '%Y-%m-%d %H:%M:%S')

            delta = timedelta(seconds=delta_seconds)
            new_from_time = from_time + delta
            new_to_time = to_time + delta

            self.from_time_var.set(new_from_time.strftime('%Y-%m-%d %H:%M:%S'))
            self.to_time_var.set(new_to_time.strftime('%Y-%m-%d %H:%M:%S'))

            self._update_duration()

            # Автоматически применяем фильтры для пересчета
            if self.controller:
                if hasattr(self.controller, 'apply_changed_parameters_filter'):
                    self.controller.apply_changed_parameters_filter()

        except ValueError as e:
            self.logger.error(f"Ошибка парсинга времени: {e}")

    def _apply_filters_priority(self):
        """ПРИОРИТЕТНОЕ применение фильтров"""
        try:
            if self.controller:
                if self.changed_only_var.get():
                    # Приоритетный режим
                    if hasattr(self.controller, 'apply_changed_parameters_filter'):
                        self.controller.apply_changed_parameters_filter()
                    else:
                        self.controller.apply_filters(changed_only=True)
                else:
                    # Обычный режим
                    self.controller.apply_filters(changed_only=False)
                    
        except Exception as e:
            self.logger.error(f"Ошибка применения приоритетных фильтров: {e}")

    def _reset_time(self):
        """ИСПРАВЛЕННЫЙ сброс времени к данным из CSV"""
        try:
            # Получаем данные из контроллера
            if self.controller and hasattr(self.controller, 'model'):
                model = self.controller.model
                if hasattr(model, 'get_time_range_fields'):
                    time_fields = model.get_time_range_fields()
                    if time_fields:
                        self.from_time_var.set(time_fields['from_time'])
                        self.to_time_var.set(time_fields['to_time'])
                        
                        if time_fields.get('duration'):
                            self.duration_var.set(f"Длительность: {time_fields['duration']}")
                        else:
                            self._update_duration()
                        
                        self.params_count_var.set(f"Записей: {time_fields.get('total_records', 0)}")
                        self.changed_only_var.set(False)
                        
                        for btn in self.quick_buttons.values():
                            btn.config(state=tk.DISABLED)
                        
                        self.logger.info("Время сброшено к данным CSV")
                        return

            # Fallback
            self.from_time_var.set("")
            self.to_time_var.set("")
            self.duration_var.set("Длительность: --")
            self.params_count_var.set("Параметров: 0")
            self.changed_only_var.set(False)
            
            for btn in self.quick_buttons.values():
                btn.config(state=tk.DISABLED)

        except Exception as e:
            self.logger.error(f"Ошибка сброса времени: {e}")

    def _update_duration(self):
        """Обновление длительности"""
        try:
            from_str = self.from_time_var.get()
            to_str = self.to_time_var.get()

            if from_str and to_str:
                from_time = datetime.strptime(from_str, '%Y-%m-%d %H:%M:%S')
                to_time = datetime.strptime(to_str, '%Y-%m-%d %H:%M:%S')
                
                duration = to_time - from_time
                days = duration.days
                hours, remainder = divmod(duration.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                if days > 0:
                    duration_str = f"{days} дн. {hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                self.duration_var.set(f"Длительность: {duration_str}")
        except ValueError:
            self.duration_var.set("Длительность: Ошибка")

    def update_time_fields(self, from_time: str, to_time: str, duration: str = "", total_records: int = 0):
        """ОСНОВНОЙ МЕТОД: Обновление полей времени"""
        try:
            self.logger.info(f"CompactTimePanel.update_time_fields: {from_time} - {to_time}")

            # Проверка и форматирование времени
            def format_time(t):
                if not t:
                    return ""
                if isinstance(t, str):
                    try:
                        # Проверяем, можно ли распарсить строку
                        dt = datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        self.logger.warning(f"Неверный формат времени: {t}")
                        return t
                return str(t)

            formatted_from = format_time(from_time)
            formatted_to = format_time(to_time)

            self.from_time_var.set(formatted_from)
            self.to_time_var.set(formatted_to)

            if duration:
                self.duration_var.set(f"Длительность: {duration}")
            else:
                self._update_duration()

            if total_records > 0:
                self.params_count_var.set(f"Записей: {total_records}")

            # Принудительное обновление UI
            self.update_idletasks()

            self.logger.info("✅ CompactTimePanel поля времени обновлены")

        except Exception as e:
            self.logger.error(f"Ошибка обновления полей времени в CompactTimePanel: {e}")

    def get_time_range(self) -> Tuple[str, str]:
        """Получение временного диапазона"""
        return self.from_time_var.get(), self.to_time_var.get()

    def set_loading_state(self, loading: bool):
        """Установка состояния загрузки"""
        state = tk.DISABLED if loading else tk.NORMAL
        
        if self.from_entry:
            self.from_entry.config(state=state)
        if self.to_entry:
            self.to_entry.config(state=state)

    # === НОВЫЕ МЕТОДЫ ПРИОРИТЕТНОЙ ЛОГИКИ ===

    def set_changed_params_priority(self, has_priority: bool):
        """НОВЫЙ МЕТОД: Установка приоритета для изменяемых параметров"""
        self.has_priority_for_changed_filter = has_priority
        if has_priority:
            self.logger.info("🔥 CompactTimePanel получил приоритет для изменяемых параметров")
        
        # Обновляем состояние кнопок быстрой настройки
        if hasattr(self, 'quick_buttons'):
            state = tk.NORMAL if self.changed_only_var.get() else tk.DISABLED
            for btn in self.quick_buttons.values():
                btn.config(state=state)

    def get_filter_settings(self) -> Dict[str, Any]:
        """НОВЫЙ МЕТОД: Получение настроек фильтрации"""
        return {
            'changed_only': self.changed_only_var.get() if self.changed_only_var else False,
            'has_priority': getattr(self, 'has_priority_for_changed_filter', True),
            'source_panel': 'compact_time_panel',
            'time_range': {
                'from_time': self.from_time_var.get(),
                'to_time': self.to_time_var.get()
            }
        }

    def disable_changed_only_checkbox(self):
        """УСТАРЕВШИЙ МЕТОД: Для обратной совместимости"""
        self.logger.warning("Метод disable_changed_only_checkbox устарел - CompactTimePanel имеет приоритет")

    def _sync_with_time_panel(self):
        """УСТАРЕВШИЙ МЕТОД: CompactTimePanel сам является time_panel"""
        pass

    def enable_priority_mode(self):
        """НОВЫЙ МЕТОД: Включение приоритетного режима"""
        try:
            self.changed_only_var.set(True)
            self._on_changed_only_toggle_priority()
            self.logger.info("🔥 Приоритетный режим включен в CompactTimePanel")
        except Exception as e:
            self.logger.error(f"Ошибка включения приоритетного режима: {e}")

    def disable_priority_mode(self):
        """НОВЫЙ МЕТОД: Отключение приоритетного режима"""
        try:
            self.changed_only_var.set(False)
            self._on_changed_only_toggle_priority()
            self.logger.info("Приоритетный режим отключен в CompactTimePanel")
        except Exception as e:
            self.logger.error(f"Ошибка отключения приоритетного режима: {e}")

    def is_priority_mode_active(self) -> bool:
        """НОВЫЙ МЕТОД: Проверка активности приоритетного режима"""
        return self.changed_only_var.get() and self.has_priority_for_changed_filter

    def set_controller(self, controller):
        """Установка контроллера"""
        self.controller = controller
        self.logger.info("Контроллер установлен в CompactTimePanel")

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.controller = None
            self.on_time_range_changed = None
            self.on_changed_only_toggle = None
            self.logger.info("CompactTimePanel очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки CompactTimePanel: {e}")

    def __str__(self):
        return f"CompactTimePanel(priority={self.has_priority_for_changed_filter}, active={self.is_priority_mode_active()})"

    def __repr__(self):
        return self.__str__()
