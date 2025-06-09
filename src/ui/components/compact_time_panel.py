"""
Компактная панель времени в 2 строки с кнопками быстрой настройки
"""
import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime, timedelta

class CompactTimePanel(ttk.Frame):
    """Компактная панель времени"""

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

        # UI элементы
        self.quick_buttons = {}
        self.from_entry = None
        self.to_entry = None

        self._setup_compact_ui()
        self.logger.info("CompactTimePanel инициализирован")

    def _setup_compact_ui(self):
        """Компактный UI в 2 строки"""
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)

        # СТРОКА 1: Поля времени + кнопки быстрой настройки + чекбокс
        row1_frame = ttk.Frame(self)
        row1_frame.grid(row=0, column=0, sticky="ew", pady=(0, 3))
        row1_frame.grid_columnconfigure(1, weight=1)
        row1_frame.grid_columnconfigure(3, weight=1)

        # От:
        ttk.Label(row1_frame, text="От:", font=('Arial', 9)).grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.from_entry = tk.Entry(row1_frame, textvariable=self.from_time_var, width=20, font=('Arial', 9))
        self.from_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        # До:
        ttk.Label(row1_frame, text="До:", font=('Arial', 9)).grid(row=0, column=2, sticky="w", padx=(0, 5))
        
        self.to_entry = tk.Entry(row1_frame, textvariable=self.to_time_var, width=20, font=('Arial', 9))
        self.to_entry.grid(row=0, column=3, sticky="ew", padx=(0, 10))

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

        # Чекбокс "Изменяемые параметры"
        changed_checkbox = ttk.Checkbutton(
            row1_frame,
            text="☑ Изменяемые",
            variable=self.changed_only_var,
            command=self._on_changed_only_toggle
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

        # Кнопки управления
        controls_frame = ttk.Frame(row2_frame)
        controls_frame.grid(row=0, column=1, sticky="e")

        ttk.Button(controls_frame, text="Применить", command=self._apply_filters, width=10).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(controls_frame, text="Сброс", command=self._reset_time, width=8).grid(row=0, column=1)

    def _on_changed_only_toggle(self):
        """Переключение чекбокса изменяемых параметров"""
        is_enabled = self.changed_only_var.get()
        
        # Включаем/отключаем кнопки быстрой настройки
        state = tk.NORMAL if is_enabled else tk.DISABLED
        for btn in self.quick_buttons.values():
            btn.config(state=state)

        if self.controller:
            self.controller.apply_filters(changed_only=is_enabled)

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
                self.controller.apply_filters(changed_only=True)

        except ValueError as e:
            self.logger.error(f"Ошибка парсинга времени: {e}")

    def _apply_filters(self):
        if self.controller:
            self.controller.apply_filters(changed_only=self.changed_only_var.get())

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
                        
                        self.params_count_var.set(f"Параметров: {time_fields.get('total_records', 0)}")
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
            
            self.from_time_var.set(from_time)
            self.to_time_var.set(to_time)
            
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

    def get_time_range(self) -> tuple[str, str]:
        return self.from_time_var.get(), self.to_time_var.get()

    def set_loading_state(self, loading: bool):
        """Установка состояния загрузки"""
        state = tk.DISABLED if loading else tk.NORMAL
        
        if self.from_entry:
            self.from_entry.config(state=state)
        if self.to_entry:
            self.to_entry.config(state=state)

    def cleanup(self):
        self.controller = None
        self.logger.info("CompactTimePanel очищен")
