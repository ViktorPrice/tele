"""
Компактная панель времени в 2 строки с интерактивными стрелочками и приоритетной логикой
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

        # Таймер для отложенного пересчета
        self._recalc_timer = None

        # НОВЫЕ атрибуты для приоритетной логики
        self.has_priority_for_changed_filter = True  # Приоритет по умолчанию
        self.on_time_range_changed = None  # Callback для изменения времени
        self.on_changed_only_toggle = None  # Callback для переключения приоритетного фильтра

        # UI элементы
        self.quick_buttons = {}
        self.time_spinners = {}  # Для хранения стрелочек
        self.from_entry = None
        self.to_entry = None

        self._setup_compact_ui()

        # Подписка на событие приоритетной фильтрации изменяемых параметров
        if self.controller:
            self.controller._ui_callbacks.setdefault('changed_params_filter_applied', []).append(self._on_changed_params_filter_applied)

        self.logger.info("CompactTimePanel инициализирован с приоритетной логикой")

    def _on_changed_params_filter_applied(self, data):
        """Обработчик события применения приоритетного фильтра изменяемых параметров"""
        try:
            count = data.get('count', 0)
            self.params_count_var.set(f"Параметров: {count}")
            self.logger.info(f"Обновлено количество параметров: {count}")
        except Exception as e:
            self.logger.error(f"Ошибка обработки события changed_params_filter_applied: {e}")

    def _setup_compact_ui(self):
        """Компактный UI с интерактивными стрелочками времени"""
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)

        # СТРОКА 1: Интерактивные поля времени с стрелочками
        row1_frame = ttk.Frame(self)
        row1_frame.grid(row=0, column=0, sticky="ew", pady=(0, 3))
        row1_frame.grid_columnconfigure(1, weight=1)
        row1_frame.grid_columnconfigure(3, weight=1)

        # От: с интерактивными стрелочками
        ttk.Label(row1_frame, text="От:", font=('Arial', 9)).grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.from_time_frame = self._create_time_spinner_frame(row1_frame, self.from_time_var, "from")
        self.from_time_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        # До: с интерактивными стрелочками
        ttk.Label(row1_frame, text="До:", font=('Arial', 9)).grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.to_time_frame = self._create_time_spinner_frame(row1_frame, self.to_time_var, "to")
        self.to_time_frame.grid(row=0, column=3, sticky="ew", padx=(0, 10))

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
                state=tk.DISABLED
            )
            btn.grid(row=0, column=i, padx=1)
            self.quick_buttons[text] = btn

        # ПРИОРИТЕТНЫЙ чекбокс
        changed_checkbox = ttk.Checkbutton(
            row1_frame,
            text="🔥 Изменяемые",
            variable=self.changed_only_var,
            command=self._on_changed_only_toggle_priority
        )
        changed_checkbox.grid(row=0, column=5, sticky="w", padx=(10, 0))

        # СТРОКА 2: остается как есть
        self._setup_row2()

    def _create_time_spinner_frame(self, parent, time_var, prefix):
        """Создание фрейма с интерактивными стрелочками для времени"""
        frame = ttk.Frame(parent)
        frame.grid_columnconfigure(0, weight=1)
        
        # Основное поле ввода времени
        time_entry = tk.Entry(frame, textvariable=time_var, width=20, font=('Arial', 9))
        time_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        time_entry.bind('<FocusOut>', self._on_time_field_changed)
        time_entry.bind('<Return>', self._on_time_field_changed)
        
        # Сохраняем ссылку на entry
        if prefix == "from":
            self.from_entry = time_entry
        else:
            self.to_entry = time_entry
        
        # Контейнер для стрелочек
        spinners_frame = ttk.Frame(frame)
        spinners_frame.grid(row=0, column=1, sticky="w")
        
        # Создаем стрелочки для часов, минут, секунд
        self._create_time_component_spinner(spinners_frame, "Час.", 0, prefix, "hours")
        self._create_time_component_spinner(spinners_frame, "Мин.", 1, prefix, "minutes") 
        self._create_time_component_spinner(spinners_frame, "Сек.", 2, prefix, "seconds")
        
        return frame

    def _create_time_component_spinner(self, parent, label, column, time_prefix, component):
        """Создание стрелочек для конкретного компонента времени (часы/минуты/секунды)"""
        # Контейнер для одного компонента
        comp_frame = ttk.Frame(parent)
        comp_frame.grid(row=0, column=column, padx=2)
        
        # Подпись (H/M/S)
        ttk.Label(comp_frame, text=label, font=('Arial', 8)).grid(row=0, column=0, columnspan=2)
        
        # Стрелочка вверх
        up_btn = ttk.Button(
            comp_frame,
            text="▲",
            width=2,
            command=lambda: self._increment_time_component(time_prefix, component, 1)
        )
        up_btn.grid(row=1, column=0, sticky="ew")
        
        # Стрелочка вниз
        down_btn = ttk.Button(
            comp_frame,
            text="▼", 
            width=2,
            command=lambda: self._increment_time_component(time_prefix, component, -1)
        )
        down_btn.grid(row=1, column=1, sticky="ew")
        
        # Сохраняем кнопки для управления состоянием
        spinner_key = f"{time_prefix}_{component}"
        self.time_spinners[spinner_key] = {'up': up_btn, 'down': down_btn}

    def _increment_time_component(self, time_prefix, component, delta):
        """Изменение конкретного компонента времени"""
        try:
            # Получаем текущее значение времени
            if time_prefix == "from":
                current_time_str = self.from_time_var.get()
                time_var = self.from_time_var
            else:
                current_time_str = self.to_time_var.get()
                time_var = self.to_time_var
            
            if not current_time_str:
                return
            
            # Парсим текущее время
            current_time = datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S')
            
            # Применяем изменение в зависимости от компонента
            if component == "hours":
                new_time = current_time + timedelta(hours=delta)
            elif component == "minutes":
                new_time = current_time + timedelta(minutes=delta)
            elif component == "seconds":
                new_time = current_time + timedelta(seconds=delta)
            else:
                return
            
            # Обновляем значение
            time_var.set(new_time.strftime('%Y-%m-%d %H:%M:%S'))
            
            # Обновляем длительность
            self._update_duration()
            
            # Если активен приоритетный режим, автоматически пересчитываем
            if self.changed_only_var.get() and self.controller:
                root = self.winfo_toplevel()
                if hasattr(self, '_recalc_timer') and self._recalc_timer:
                    root.after_cancel(self._recalc_timer)
                self._recalc_timer = root.after(300, self._auto_recalculate)
            
            # Вызываем callback
            if self.on_time_range_changed:
                from_time = self.from_time_var.get()
                to_time = self.to_time_var.get()
                self.on_time_range_changed(from_time, to_time)
                
            self.logger.debug(f"Изменен {component} на {delta} для {time_prefix}: {new_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except ValueError as e:
            self.logger.error(f"Ошибка парсинга времени при изменении {component}: {e}")
        except Exception as e:
            self.logger.error(f"Ошибка изменения компонента времени: {e}")

    def _setup_row2(self):
        """Настройка второй строки"""
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
        """ПРИОРИТЕТНОЕ переключение с управлением стрелочками"""
        is_enabled = self.changed_only_var.get()
        
        self.logger.info(f"🔥 ПРИОРИТЕТНЫЙ фильтр изменяемых параметров: {is_enabled}")
        
        # Включаем/отключаем кнопки быстрой настройки
        state = tk.NORMAL if is_enabled else tk.DISABLED
        for btn in self.quick_buttons.values():
            btn.config(state=state)
        
        # Включаем/отключаем стрелочки времени
        for spinner_data in self.time_spinners.values():
            spinner_data['up'].config(state=state)
            spinner_data['down'].config(state=state)

        # Вызываем callback если установлен
        if self.on_changed_only_toggle:
            self.on_changed_only_toggle(is_enabled)

        # Применяем через контроллер с приоритетной логикой
        if self.controller:
            if hasattr(self.controller, 'apply_changed_parameters_filter') and is_enabled:
                self.controller.apply_changed_parameters_filter()
            else:
                self.controller.apply_filters(changed_only=is_enabled)

    def on_changed_only_toggled(self):
        """ИСПРАВЛЕННЫЙ обработчик переключения чекбокса 'только изменяемые'"""
        try:
            is_enabled = self.changed_only_var.get()
            self.logger.info(f"🔄 Чекбокс 'только изменяемые' переключен: {is_enabled}")
            
            # Синхронизируем с SmartFilterPanel
            if self.controller:
                filter_panel = self.controller.get_ui_component('filter_panel')
                if filter_panel:
                    if hasattr(filter_panel, 'set_changed_only_mode'):
                        filter_panel.set_changed_only_mode(is_enabled)
                    elif hasattr(filter_panel, 'sync_changed_only_state'):
                        filter_panel.sync_changed_only_state(is_enabled)
            
            # Если чекбокс включен, применяем фильтр изменяемых немедленно
            if is_enabled and self.controller:
                self.controller.apply_changed_parameters_filter(auto_recalc=False)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка обработки переключения 'только изменяемые': {e}")

    def is_changed_only_enabled(self) -> bool:
        """НОВЫЙ МЕТОД: Проверка состояния чекбокса 'только изменяемые'"""
        try:
            return self.changed_only_var.get() if hasattr(self, 'changed_only_var') else False
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки состояния 'только изменяемые': {e}")
            return False

    def _on_time_field_changed(self, event=None):
        """Обработка изменения полей времени"""
        try:
            self._update_duration()
            
            # Вызываем callback если установлен
            if self.on_time_range_changed:
                from_time = self.from_time_var.get()
                to_time = self.to_time_var.get()
                self.on_time_range_changed(from_time, to_time)
            
            # Если активен приоритетный режим, автоматически применяем с отложенным вызовом
            if self.changed_only_var.get() and self.controller:
                root = self.winfo_toplevel()
                if hasattr(self, '_recalc_timer') and self._recalc_timer:
                    root.after_cancel(self._recalc_timer)
                self._recalc_timer = root.after(500, self._auto_recalculate)
                    
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
                        
                        # Отключаем кнопки и стрелочки
                        for btn in self.quick_buttons.values():
                            btn.config(state=tk.DISABLED)
                        for spinner_data in self.time_spinners.values():
                            spinner_data['up'].config(state=tk.DISABLED)
                            spinner_data['down'].config(state=tk.DISABLED)
                        
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
            for spinner_data in self.time_spinners.values():
                spinner_data['up'].config(state=tk.DISABLED)
                spinner_data['down'].config(state=tk.DISABLED)

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
        """Установка состояния загрузки для всех элементов включая стрелочки"""
        state = tk.DISABLED if loading else tk.NORMAL
        
        # Основные поля ввода
        if self.from_entry:
            self.from_entry.config(state=state)
        if self.to_entry:
            self.to_entry.config(state=state)
        
        # Стрелочки времени
        for spinner_data in self.time_spinners.values():
            spinner_data['up'].config(state=state)
            spinner_data['down'].config(state=state)
        
        # Кнопки быстрой настройки
        for btn in self.quick_buttons.values():
            if self.changed_only_var.get():
                btn.config(state=state)

    # === НОВЫЕ МЕТОДЫ ПРИОРИТЕТНОЙ ЛОГИКИ ===

    def set_changed_params_priority(self, has_priority: bool):
        """НОВЫЙ МЕТОД: Установка приоритета для изменяемых параметров"""
        self.has_priority_for_changed_filter = has_priority
        if has_priority:
            self.logger.info("🔥 CompactTimePanel получил приоритет для изменяемых параметров")
        
        # Обновляем состояние кнопок быстрой настройки и стрелочек
        if hasattr(self, 'quick_buttons'):
            state = tk.NORMAL if self.changed_only_var.get() else tk.DISABLED
            for btn in self.quick_buttons.values():
                btn.config(state=state)
            for spinner_data in self.time_spinners.values():
                spinner_data['up'].config(state=state)
                spinner_data['down'].config(state=state)

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

    def _auto_recalculate(self):
        """Автоматический пересчет изменяемых параметров"""
        try:
            if self.controller and hasattr(self.controller, 'apply_changed_parameters_filter'):
                self.controller.apply_changed_parameters_filter(auto_recalc=True)
                self.logger.info("✅ Автоматический пересчет выполнен")
        except Exception as e:
            self.logger.error(f"Ошибка автоматического пересчета: {e}")
