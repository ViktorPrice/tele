"""
Специализированные фабрики панелей
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import logging

from .base_component_factory import BaseComponentFactory

class TimePanelFactory(BaseComponentFactory):
    """Фабрика для создания панелей времени"""
    
    def create_panel(self, parent, controller):
        """Создание панели времени БЕЗ дублирования кода"""
        try:
            # Основной контейнер
            main_frame = self.create_labeled_frame(parent, "Временной диапазон")
            main_frame.grid_columnconfigure([1, 3], weight=1)
            
            # Время начала
            start_label, start_entry = self.create_entry_with_label(main_frame, "Время начала:")
            start_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
            start_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            # Время окончания
            end_label, end_entry = self.create_entry_with_label(main_frame, "Время окончания:")
            end_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
            end_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
            
            # Кнопки регулировки времени
            self._create_time_adjustment_buttons(main_frame, start_entry, end_entry)
            
            # Чекбокс "Только изменяемые параметры"
            changed_var = tk.BooleanVar()
            changed_cb = ttk.Checkbutton(
                main_frame, 
                text="Только изменяемые параметры", 
                variable=changed_var,
                command=lambda: self._on_changed_params_toggle(changed_var.get(), controller)
            )
            changed_cb.grid(row=2, column=0, columnspan=4, pady=5, sticky="w")
            
            # Установка значений по умолчанию
            self._set_default_times(start_entry, end_entry)
            
            # Создание объекта-обертки
            return self._create_time_panel_wrapper(main_frame, start_entry, end_entry, changed_var, controller)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания панели времени: {e}")
            return self._create_fallback_panel(parent, "Панель времени")
    
    def _create_time_adjustment_buttons(self, parent, start_entry, end_entry):
        """Создание кнопок регулировки времени"""
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=5)
        
        # Кнопки для времени начала
        start_buttons = [("-10с", -10), ("-1с", -1), ("+1с", 1), ("+10с", 10)]
        ttk.Label(btn_frame, text="Начало:").grid(row=0, column=0, padx=5)
        for i, (text, seconds) in enumerate(start_buttons):
            btn = ttk.Button(btn_frame, text=text, width=5, 
                           command=lambda s=seconds: self._adjust_time(start_entry, s))
            btn.grid(row=0, column=i+1, padx=1)
        
        # Кнопки для времени окончания
        end_buttons = [("-10с", -10), ("-1с", -1), ("+1с", 1), ("+10с", 10)]
        ttk.Label(btn_frame, text="Конец:").grid(row=1, column=0, padx=5)
        for i, (text, seconds) in enumerate(end_buttons):
            btn = ttk.Button(btn_frame, text=text, width=5,
                           command=lambda s=seconds: self._adjust_time(end_entry, s))
            btn.grid(row=1, column=i+1, padx=1)
    
    def _adjust_time(self, entry, seconds):
        """Регулировка времени"""
        try:
            current_value = entry.get()
            if current_value:
                dt = datetime.strptime(current_value, '%Y-%m-%d %H:%M:%S')
                new_dt = dt + timedelta(seconds=seconds)
                entry.delete(0, tk.END)
                entry.insert(0, new_dt.strftime('%Y-%m-%d %H:%M:%S'))
        except Exception as e:
            self.logger.error(f"Ошибка регулировки времени: {e}")
    
    def _set_default_times(self, start_entry, end_entry):
        """Установка времени по умолчанию"""
        now = datetime.now()
        start_default = now - timedelta(hours=1)
        start_entry.insert(0, start_default.strftime('%Y-%m-%d %H:%M:%S'))
        end_entry.insert(0, now.strftime('%Y-%m-%d %H:%M:%S'))
    
    def _on_changed_params_toggle(self, is_checked: bool, controller):
        """Обработчик переключения чекбокса"""
        try:
            self.logger.info(f"Чекбокс 'Только изменяемые параметры' переключен: {is_checked}")
            if hasattr(controller, 'apply_filters'):
                controller.apply_filters(changed_only=is_checked)
        except Exception as e:
            self.logger.error(f"Ошибка обработки переключения: {e}")
    
    def _create_time_panel_wrapper(self, frame, start_entry, end_entry, changed_var, controller):
        """Создание объекта-обертки для панели времени"""
        class TimePanelWrapper:
            def __init__(self, frame, start_entry, end_entry, changed_var, controller):
                self.frame = frame
                self.start_time_entry = start_entry
                self.end_time_entry = end_entry
                self.changed_var = changed_var
                self.controller = controller
                self.logger = logging.getLogger('TimePanel')
            
            def get_time_range(self):
                return self.start_time_entry.get(), self.end_time_entry.get()
            
            def grid(self, **kwargs):
                self.frame.grid(**kwargs)
            
            def set_time_range(self, start_time, end_time):
                self.start_time_entry.delete(0, tk.END)
                self.start_time_entry.insert(0, start_time)
                self.end_time_entry.delete(0, tk.END)
                self.end_time_entry.insert(0, end_time)
        
        return TimePanelWrapper(frame, start_entry, end_entry, changed_var, controller)

class FilterPanelFactory(BaseComponentFactory):
    """Фабрика для создания панелей фильтров"""
    
    def create_panel(self, parent, controller):
        """Создание панели фильтров БЕЗ дублирования кода"""
        try:
            # Основной контейнер
            main_frame = self.create_labeled_frame(parent, "Фильтры")
            main_frame.grid_columnconfigure([0, 1, 2, 3, 4], weight=1)
            
            # Создание фильтров
            signal_vars = self._create_signal_type_filter(main_frame, controller)
            line_vars = self._create_line_filter(main_frame, controller)
            wagon_vars = self._create_wagon_filter(main_frame, controller)
            
            # Кнопки управления
            self._create_filter_control_buttons(main_frame, signal_vars, line_vars, wagon_vars, controller)
            
            # Создание объекта-обертки
            return self._create_filter_panel_wrapper(main_frame, signal_vars, line_vars, wagon_vars, controller)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания панели фильтров: {e}")
            return self._create_fallback_panel(parent, "Панель фильтров")
    
    def _create_signal_type_filter(self, parent, controller):
        """Создание фильтра типов сигналов"""
        signal_frame = self.create_labeled_frame(parent, "Типы сигналов")
        signal_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        signal_vars = {}
        signal_types = ['B', 'BY', 'W', 'DW', 'F', 'WF']
        
        for i, signal_type in enumerate(signal_types):
            var = tk.BooleanVar(value=True)
            signal_vars[signal_type] = var
            
            cb = ttk.Checkbutton(
                signal_frame, 
                text=signal_type, 
                variable=var,
                command=lambda: self._on_filter_change(controller)
            )
            cb.grid(row=i//3, column=i%3, sticky="w", padx=2, pady=1)
        
        return signal_vars
    
    def _create_line_filter(self, parent, controller):
        """Создание фильтра линий"""
        line_frame = self.create_labeled_frame(parent, "Линии")
        line_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        
        # Будут обновлены динамически
        line_vars = {}
        return line_vars
    
    def _create_wagon_filter(self, parent, controller):
        """Создание фильтра вагонов"""
        wagon_frame = self.create_labeled_frame(parent, "Вагоны")
        wagon_frame.grid(row=0, column=2, sticky="nsew", padx=2, pady=2)
        
        wagon_vars = {}
        for i in range(1, 9):
            var = tk.BooleanVar(value=True)
            wagon_vars[str(i)] = var
            
            cb = ttk.Checkbutton(
                wagon_frame, 
                text=str(i), 
                variable=var,
                command=lambda: self._on_filter_change(controller)
            )
            cb.grid(row=(i-1)//4, column=(i-1)%4, sticky="w", padx=2, pady=1)
        
        return wagon_vars
    
    def _create_filter_control_buttons(self, parent, signal_vars, line_vars, wagon_vars, controller):
        """Создание кнопок управления фильтрами"""
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=1, column=0, columnspan=5, pady=5)
        
        def toggle_all():
            for var in list(signal_vars.values()) + list(line_vars.values()) + list(wagon_vars.values()):
                var.set(True)
            self._on_filter_change(controller)
        
        def invert_all():
            for var in list(signal_vars.values()) + list(line_vars.values()) + list(wagon_vars.values()):
                var.set(not var.get())
            self._on_filter_change(controller)
        
        ttk.Button(btn_frame, text="Сбросить все", command=toggle_all).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Инвертировать", command=invert_all).grid(row=0, column=1, padx=5)
    
    def _on_filter_change(self, controller):
        """Обработчик изменения фильтров"""
        if hasattr(controller, 'apply_filters'):
            controller.apply_filters()
    
    def _create_filter_panel_wrapper(self, frame, signal_vars, line_vars, wagon_vars, controller):
        """Создание объекта-обертки для панели фильтров"""
        class FilterPanelWrapper:
            def __init__(self, frame, signal_vars, line_vars, wagon_vars, controller):
                self.frame = frame
                self.signal_vars = signal_vars
                self.line_vars = line_vars
                self.wagon_vars = wagon_vars
                self.component_vars = {}
                self.hardware_vars = {}
                self.controller = controller
                self.logger = logging.getLogger('FilterPanel')
            
            def grid(self, **kwargs):
                self.frame.grid(**kwargs)
            
            def get_selected_filters(self):
                return {
                    'signal_types': [k for k, v in self.signal_vars.items() if v.get()],
                    'lines': [k for k, v in self.line_vars.items() if v.get()],
                    'wagons': [k for k, v in self.wagon_vars.items() if v.get()],
                    'components': [k for k, v in self.component_vars.items() if v.get()],
                    'hardware': [k for k, v in self.hardware_vars.items() if v.get()]
                }
            
            def update_line_checkboxes(self, lines):
                # Реализация обновления чекбоксов линий
                pass
        
        return FilterPanelWrapper(frame, signal_vars, line_vars, wagon_vars, controller)

class ParameterPanelFactory(BaseComponentFactory):
    """Фабрика для создания панелей параметров"""
    
    def create_panel(self, parent, controller):
        """Создание панели параметров БЕЗ дублирования кода"""
        try:
            # Основной контейнер
            main_frame = ttk.Frame(parent)
            main_frame.grid_columnconfigure([0, 2], weight=1)
            main_frame.grid_rowconfigure(1, weight=1)
            
            # Заголовок
            title_label = ttk.Label(main_frame, text="Панель параметров", font=('Arial', 12, 'bold'))
            title_label.grid(row=0, column=0, columnspan=3, pady=5)
            
            # Дерево всех параметров
            all_tree = self._create_parameter_tree(main_frame, "Все параметры")
            all_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
            
            # Кнопки управления
            btn_frame = self._create_parameter_control_buttons(main_frame)
            btn_frame.grid(row=1, column=1, sticky="ns", padx=10, pady=5)
            
            # Дерево выбранных параметров
            selected_tree = self._create_parameter_tree(main_frame, "Выбранные параметры")
            selected_tree.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
            
            # Создание объекта-обертки
            return self._create_parameter_panel_wrapper(main_frame, all_tree, selected_tree, controller)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания панели параметров: {e}")
            return self._create_fallback_panel(parent, "Панель параметров")
    
    def _create_parameter_tree(self, parent, title):
        """Создание дерева параметров"""
        frame = self.create_labeled_frame(parent, title)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Дерево
        columns = ("signal", "desc", "line", "wagon")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        tree.heading("signal", text="Код сигнала")
        tree.heading("desc", text="Описание")
        tree.heading("line", text="Линия")
        tree.heading("wagon", text="Вагон")
        
        tree.column("signal", width=150)
        tree.column("desc", width=250)
        tree.column("line", width=120)
        tree.column("wagon", width=80)
        
        tree.grid(row=0, column=0, sticky="nsew")
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        return frame, tree
    
    def _create_parameter_control_buttons(self, parent):
        """Создание кнопок управления параметрами"""
        btn_frame = ttk.Frame(parent)
        
        buttons = [
            ("Добавить →", None),
            ("← Удалить", None),
            ("Очистить", None)
        ]
        
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(btn_frame, text=text, command=command)
            btn.grid(row=i, column=0, pady=5, sticky="ew")
        
        return btn_frame
    
    def _create_parameter_panel_wrapper(self, frame, all_tree_data, selected_tree_data, controller):
        """Создание объекта-обертки для панели параметров"""
        all_frame, all_tree = all_tree_data
        selected_frame, selected_tree = selected_tree_data
        
        class ParameterPanelWrapper:
            def __init__(self, frame, all_tree, selected_tree, controller):
                self.frame = frame
                self.all_params_tree = type('Tree', (), {'tree': all_tree})()
                self.selected_params_tree = type('Tree', (), {'tree': selected_tree})()
                self.controller = controller
                self.logger = logging.getLogger('ParameterPanel')
            
            def grid(self, **kwargs):
                self.frame.grid(**kwargs)
            
            def update_tree_all_params(self, params):
                # Очищаем дерево
                for item in self.all_params_tree.tree.get_children():
                    self.all_params_tree.tree.delete(item)
                
                # Заполняем новыми данными
                for param in params:
                    if isinstance(param, dict):
                        values = (
                            param.get('signal_code', ''),
                            param.get('description', ''),
                            param.get('line', ''),
                            param.get('wagon', '')
                        )
                        self.all_params_tree.tree.insert('', 'end', values=values)
                
                self.logger.info(f"Обновлено дерево параметров: {len(params)} параметров")
        
        return ParameterPanelWrapper(frame, all_tree, selected_tree, controller)

class ActionPanelFactory(BaseComponentFactory):
    """Фабрика для создания панелей действий"""
    
    def create_panel(self, parent, controller):
        """Создание панели действий БЕЗ дублирования кода"""
        try:
            # Основной контейнер
            main_frame = ttk.Frame(parent)
            main_frame.grid_columnconfigure([0, 1, 2], weight=1)
            
            # Кнопки действий
            buttons_config = [
                {
                    'text': 'Построить график',
                    'command': lambda: self._safe_call(controller, 'build_plot'),
                    'style': 'Accent.TButton'
                },
                {
                    'text': 'Генерировать отчет',
                    'command': lambda: self._safe_call(controller, 'generate_report'),
                    'style': 'TButton'
                },
                {
                    'text': 'Создать SOP',
                    'command': lambda: self._safe_call(controller, 'generate_sop'),
                    'style': 'TButton'
                }
            ]
            
            for i, btn_config in enumerate(buttons_config):
                btn = ttk.Button(
                    main_frame,
                    text=btn_config['text'],
                    command=btn_config['command'],
                    style=btn_config['style']
                )
                btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            
            # Создание объекта-обертки
            return self._create_action_panel_wrapper(main_frame, controller)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания панели действий: {e}")
            return self._create_fallback_panel(parent, "Панель действий")
    
    def _safe_call(self, controller, method_name):
        """Безопасный вызов метода контроллера"""
        try:
            if hasattr(controller, method_name):
                getattr(controller, method_name)()
            else:
                self.logger.warning(f"Метод {method_name} не найден в контроллере")
        except Exception as e:
            self.logger.error(f"Ошибка вызова {method_name}: {e}")
    
    def _create_action_panel_wrapper(self, frame, controller):
        """Создание объекта-обертки для панели действий"""
        class ActionPanelWrapper:
            def __init__(self, frame, controller):
                self.frame = frame
                self.controller = controller
            
            def grid(self, **kwargs):
                self.frame.grid(**kwargs)
        
        return ActionPanelWrapper(frame, controller)