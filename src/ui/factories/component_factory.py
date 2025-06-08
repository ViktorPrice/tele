# src/ui/factories/component_factory.py - ИСПРАВЛЕННАЯ ВЕРСИЯ БЕЗ ЦИКЛИЧЕСКИХ ИМПОРТОВ
"""
Фабрика для создания UI компонентов БЕЗ циклических зависимостей
"""
import logging
import sys
import os
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

# Добавляем текущую папку в путь
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..', '..', '..', '..')
root_dir = os.path.abspath(root_dir)
sys.path.insert(0, root_dir)

class ComponentFactory:
    """Фабрика для создания UI компонентов БЕЗ циклических зависимостей"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_upload_panel(self, parent, controller):
        """ИСПРАВЛЕННОЕ создание панели загрузки"""
        try:
            # Создаем рабочую панель загрузки
            return self._create_working_upload_panel(parent, controller)
        except Exception as e:
            self.logger.error(f"Ошибка создания панели загрузки: {e}")
            return self._create_simple_panel(parent, "Панель загрузки")
    
    def create_time_panel(self, parent, controller):
        """ИСПРАВЛЕННОЕ создание панели времени БЕЗ legacy зависимостей"""
        try:
            # Создаем рабочую панель времени
            return self._create_working_time_panel_with_changed_params(parent, controller)
        except Exception as e:
            self.logger.error(f"Ошибка создания панели времени: {e}")
            return self._create_simple_panel(parent, "Панель времени")
    
    def create_filter_panel(self, parent, controller):
        """ИСПРАВЛЕННОЕ создание панели фильтров БЕЗ legacy зависимостей"""
        try:
            # Создаем рабочую панель фильтров
            return self._create_working_filter_panel(parent, controller)
        except Exception as e:
            self.logger.error(f"Ошибка создания панели фильтров: {e}")
            return self._create_simple_panel(parent, "Панель фильтров")
    
    def create_parameter_panel(self, parent, controller):
        """ИСПРАВЛЕННОЕ создание панели параметров БЕЗ legacy зависимостей"""
        try:
            # Создаем рабочую панель параметров
            return self._create_working_parameter_panel(parent, controller)
        except Exception as e:
            self.logger.error(f"Ошибка создания панели параметров: {e}")
            return self._create_simple_panel(parent, "Панель параметров")
    
    def create_action_panel(self, parent, controller):
        """ИСПРАВЛЕННОЕ создание панели действий БЕЗ legacy зависимостей"""
        try:
            # Создаем рабочую панель действий
            return self._create_working_action_panel(parent, controller)
        except Exception as e:
            self.logger.error(f"Ошибка создания панели действий: {e}")
            return self._create_simple_panel(parent, "Панель действий")
    
    def create_visualization_area(self, parent, controller):
        """ИСПРАВЛЕННОЕ создание области визуализации"""
        try:
            # Создаем Notebook для графиков
            notebook = ttk.Notebook(parent)
            
            # Добавляем стартовую вкладку
            start_frame = ttk.Frame(notebook)
            notebook.add(start_frame, text="Графики")
            
            start_label = ttk.Label(
                start_frame, 
                text="Загрузите данные и выберите параметры\nдля построения графиков",
                font=('Arial', 12),
                justify='center'
            )
            start_label.pack(expand=True)
            
            # Добавляем методы для совместимости
            self._add_compatibility_methods(notebook)
            
            return notebook
            
        except Exception as e:
            self.logger.error(f"Ошибка создания области визуализации: {e}")
            return None
    
    def _create_working_upload_panel(self, parent, controller):
        """РАБОЧАЯ панель загрузки"""
        # Основной контейнер
        main_frame = ttk.Frame(parent)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Кнопка загрузки
        upload_btn = ttk.Button(
            main_frame,
            text="Загрузить CSV",
            command=lambda: self._safe_call(controller, 'upload_csv'),
            style='Accent.TButton'
        )
        upload_btn.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Статус
        status_label = ttk.Label(main_frame, text="Готов к загрузке файла")
        status_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Прогресс-бар (скрыт по умолчанию)
        progress = ttk.Progressbar(main_frame, mode='determinate', length=200)
        
        # Создаем объект-обертку
        class UploadPanelWrapper:
            def __init__(self, frame, upload_btn, status_label, progress):
                self.frame = frame
                self.upload_btn = upload_btn
                self.status_label = status_label
                self.progress = progress
                self.is_loading = False
            
            def grid(self, **kwargs):
                self.frame.grid(**kwargs)
            
            def update_status(self, message):
                self.status_label.config(text=message)
            
            def set_loading_state(self, loading):
                self.is_loading = loading
                if loading:
                    self.upload_btn.config(state='disabled')
                    self.progress.grid(row=0, column=2, padx=5, pady=5)
                else:
                    self.upload_btn.config(state='normal')
                    self.progress.grid_remove()
            
            def update_progress(self, value):
                self.progress['value'] = value
        
        return UploadPanelWrapper(main_frame, upload_btn, status_label, progress)
    
    def _create_working_time_panel_with_changed_params(self, parent, controller):
        """РАБОЧАЯ панель времени с поддержкой 'только изменяемые параметры'"""
        # Основной контейнер
        main_frame = ttk.LabelFrame(parent, text="Временной диапазон")
        main_frame.grid_columnconfigure([1, 3], weight=1)
        
        # Время начала
        ttk.Label(main_frame, text="Время начала:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        start_time_entry = ttk.Entry(main_frame, width=20)
        start_time_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Время окончания
        ttk.Label(main_frame, text="Время окончания:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        end_time_entry = ttk.Entry(main_frame, width=20)
        end_time_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        # Кнопки регулировки времени
        self._create_time_adjustment_buttons(main_frame, start_time_entry, end_time_entry)
        
        # КРИТИЧЕСКИ ВАЖНО: Чекбокс "Только изменяемые параметры"
        changed_var = tk.BooleanVar()
        changed_cb = ttk.Checkbutton(
            main_frame, 
            text="Только изменяемые параметры", 
            variable=changed_var,
            command=lambda: self._on_changed_params_toggle(changed_var.get(), controller)
        )
        changed_cb.grid(row=2, column=0, columnspan=4, pady=5, sticky="w")
        
        # Установка значений по умолчанию
        now = datetime.now()
        start_default = now - timedelta(hours=1)
        start_time_entry.insert(0, start_default.strftime('%Y-%m-%d %H:%M:%S'))
        end_time_entry.insert(0, now.strftime('%Y-%m-%d %H:%M:%S'))
        
        # Создаем объект-обертку
        class TimePanelWrapper:
            def __init__(self, frame, start_entry, end_entry, changed_var):
                self.frame = frame
                self.start_time_entry = start_entry
                self.end_time_entry = end_entry
                self.changed_var = changed_var
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
        
        self.logger.info("Создана РАБОЧАЯ панель времени с поддержкой изменяемых параметров")
        return TimePanelWrapper(main_frame, start_time_entry, end_time_entry, changed_var)
    
    def _create_time_adjustment_buttons(self, parent, start_entry, end_entry):
        """Создание кнопок регулировки времени"""
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=5)
        
        def adjust_time(entry, seconds):
            try:
                current_value = entry.get()
                if current_value:
                    dt = datetime.strptime(current_value, '%Y-%m-%d %H:%M:%S')
                    new_dt = dt + timedelta(seconds=seconds)
                    entry.delete(0, tk.END)
                    entry.insert(0, new_dt.strftime('%Y-%m-%d %H:%M:%S'))
            except Exception as e:
                self.logger.error(f"Ошибка регулировки времени: {e}")
        
        # Кнопки для времени начала
        ttk.Label(btn_frame, text="Начало:").grid(row=0, column=0, padx=5)
        for i, (text, seconds) in enumerate([("-10с", -10), ("-1с", -1), ("+1с", 1), ("+10с", 10)]):
            ttk.Button(btn_frame, text=text, width=5, 
                      command=lambda s=seconds: adjust_time(start_entry, s)).grid(row=0, column=i+1, padx=1)
        
        # Кнопки для времени окончания
        ttk.Label(btn_frame, text="Конец:").grid(row=1, column=0, padx=5)
        for i, (text, seconds) in enumerate([("-10с", -10), ("-1с", -1), ("+1с", 1), ("+10с", 10)]):
            ttk.Button(btn_frame, text=text, width=5,
                      command=lambda s=seconds: adjust_time(end_entry, s)).grid(row=1, column=i+1, padx=1)
    
    def _on_changed_params_toggle(self, is_checked, controller):
        """Обработчик переключения чекбокса"""
        try:
            self.logger.info(f"Чекбокс 'Только изменяемые параметры' переключен: {is_checked}")
            if hasattr(controller, 'apply_filters'):
                controller.apply_filters(changed_only=is_checked)
        except Exception as e:
            self.logger.error(f"Ошибка обработки переключения: {e}")
    
    def _create_working_filter_panel(self, parent, controller):
        """РАБОЧАЯ панель фильтров"""
        # Основной контейнер
        main_frame = ttk.LabelFrame(parent, text="Фильтры")
        main_frame.grid_columnconfigure([0, 1, 2, 3, 4], weight=1)
        
        # Фильтры типов сигналов
        signal_frame = ttk.LabelFrame(main_frame, text="Типы сигналов")
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
                command=lambda: self._safe_call(controller, 'apply_filters')
            )
            cb.grid(row=i//3, column=i%3, sticky="w", padx=2, pady=1)
        
        # Фильтры линий
        line_frame = ttk.LabelFrame(main_frame, text="Линии")
        line_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        line_vars = {}
        
        # Фильтры вагонов
        wagon_frame = ttk.LabelFrame(main_frame, text="Вагоны")
        wagon_frame.grid(row=0, column=2, sticky="nsew", padx=2, pady=2)
        wagon_vars = {}
        
        for i in range(1, 9):
            var = tk.BooleanVar(value=True)
            wagon_vars[str(i)] = var
            
            cb = ttk.Checkbutton(
                wagon_frame, 
                text=str(i), 
                variable=var,
                command=lambda: self._safe_call(controller, 'apply_filters')
            )
            cb.grid(row=(i-1)//4, column=(i-1)%4, sticky="w", padx=2, pady=1)
        
        # Кнопки управления
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, columnspan=5, pady=5)
        
        def toggle_all():
            for var in list(signal_vars.values()) + list(line_vars.values()) + list(wagon_vars.values()):
                var.set(True)
            self._safe_call(controller, 'apply_filters')
        
        def invert_all():
            for var in list(signal_vars.values()) + list(line_vars.values()) + list(wagon_vars.values()):
                var.set(not var.get())
            self._safe_call(controller, 'apply_filters')
        
        ttk.Button(btn_frame, text="Сбросить все", command=toggle_all).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Инвертировать", command=invert_all).grid(row=0, column=1, padx=5)
        
        # Создаем объект-обертку
        class FilterPanelWrapper:
            def __init__(self, frame, signal_vars, line_vars, wagon_vars, line_frame):
                self.frame = frame
                self.signal_vars = signal_vars
                self.line_vars = line_vars
                self.wagon_vars = wagon_vars
                self.component_vars = {}
                self.hardware_vars = {}
                self.line_frame = line_frame
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
                # Очищаем существующие
                for widget in self.line_frame.winfo_children():
                    widget.destroy()
                
                self.line_vars.clear()
                
                # Создаем новые
                for i, line in enumerate(lines):
                    var = tk.BooleanVar(value=True)
                    self.line_vars[line] = var
                    
                    cb = ttk.Checkbutton(
                        self.line_frame, 
                        text=line[:10] + "..." if len(line) > 10 else line, 
                        variable=var,
                        command=lambda: controller.apply_filters() if hasattr(controller, 'apply_filters') else None
                    )
                    cb.grid(row=i//2, column=i%2, sticky="w", padx=2, pady=1)
                
                self.logger.info(f"Обновлены чекбоксы линий: {len(lines)} линий")
        
        self.logger.info("Создана РАБОЧАЯ панель фильтров")
        return FilterPanelWrapper(main_frame, signal_vars, line_vars, wagon_vars, line_frame)
    
    def _create_working_parameter_panel(self, parent, controller):
        """РАБОЧАЯ панель параметров с полной функциональностью"""
        # Основной контейнер
        main_frame = ttk.Frame(parent)
        main_frame.grid_columnconfigure([0, 2], weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Панель параметров", font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=5)
        
        # Дерево всех параметров
        all_frame = ttk.LabelFrame(main_frame, text="Все параметры")
        all_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        all_frame.grid_rowconfigure(0, weight=1)
        all_frame.grid_columnconfigure(0, weight=1)
        
        all_tree = ttk.Treeview(all_frame, columns=("signal", "desc", "line", "wagon"), show="headings")
        all_tree.heading("signal", text="Код сигнала")
        all_tree.heading("desc", text="Описание")
        all_tree.heading("line", text="Линия")
        all_tree.heading("wagon", text="Вагон")
        
        all_tree.column("signal", width=150)
        all_tree.column("desc", width=250)
        all_tree.column("line", width=120)
        all_tree.column("wagon", width=80)
        
        all_tree.grid(row=0, column=0, sticky="nsew")
        
        # Скроллбар для дерева всех параметров
        all_scroll = ttk.Scrollbar(all_frame, orient="vertical", command=all_tree.yview)
        all_tree.configure(yscrollcommand=all_scroll.set)
        all_scroll.grid(row=0, column=1, sticky="ns")
        
        # Кнопки управления
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=1, sticky="ns", padx=10, pady=5)
        
        def add_selected_params():
            self._add_selected_params(all_tree, selected_tree)
        
        def remove_selected_params():
            self._remove_selected_params(selected_tree)
        
        def clear_selected_params():
            self._clear_selected_params(selected_tree)
        
        ttk.Button(btn_frame, text="Добавить →", command=add_selected_params).grid(row=0, column=0, pady=5, sticky="ew")
        ttk.Button(btn_frame, text="← Удалить", command=remove_selected_params).grid(row=1, column=0, pady=5, sticky="ew")
        ttk.Button(btn_frame, text="Очистить", command=clear_selected_params).grid(row=2, column=0, pady=5, sticky="ew")
        
        # Дерево выбранных параметров
        selected_frame = ttk.LabelFrame(main_frame, text="Выбранные параметры")
        selected_frame.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)
        selected_frame.grid_rowconfigure(0, weight=1)
        selected_frame.grid_columnconfigure(0, weight=1)
        
        selected_tree = ttk.Treeview(selected_frame, columns=("signal", "desc", "line", "wagon"), show="headings")
        selected_tree.heading("signal", text="Код сигнала")
        selected_tree.heading("desc", text="Описание")
        selected_tree.heading("line", text="Линия")
        selected_tree.heading("wagon", text="Вагон")
        
        selected_tree.column("signal", width=150)
        selected_tree.column("desc", width=250)
        selected_tree.column("line", width=120)
        selected_tree.column("wagon", width=80)
        
        selected_tree.grid(row=0, column=0, sticky="nsew")
        
        # Скроллбар для дерева выбранных параметров
        selected_scroll = ttk.Scrollbar(selected_frame, orient="vertical", command=selected_tree.yview)
        selected_tree.configure(yscrollcommand=selected_scroll.set)
        selected_scroll.grid(row=0, column=1, sticky="ns")
        
        # Создаем объект-обертку
        class ParameterPanelWrapper:
            def __init__(self, frame, all_tree, selected_tree):
                self.frame = frame
                self.all_params_tree = type('Tree', (), {'tree': all_tree})()
                self.selected_params_tree = type('Tree', (), {'tree': selected_tree})()
                self.logger = logging.getLogger('ParameterPanel')
            
            def update_tree_all_params(self, params):
                # Очищаем дерево
                for item in self.all_params_tree.tree.get_children():
                    self.all_params_tree.tree.delete(item)
                
                # Заполняем новыми данными
                if not params:
                    # Показываем сообщение о том, что нет данных
                    self.all_params_tree.tree.insert('', 'end', values=(
                        'Нет данных', 
                        'Загрузите CSV файл для отображения параметров',
                        '',
                        ''
                    ))
                    return
                
                for param in params:
                    if isinstance(param, dict):
                        values = (
                            param.get('signal_code', ''),
                            param.get('description', ''),
                            param.get('line', ''),
                            param.get('wagon', '')
                        )
                    else:
                        values = param
                    self.all_params_tree.tree.insert('', 'end', values=values)
                
                self.logger.info(f"Обновлено дерево всех параметров: {len(params)} параметров")
            
            def update_tree_selected_params(self, params):
                # Очищаем дерево
                for item in self.selected_params_tree.tree.get_children():
                    self.selected_params_tree.tree.delete(item)
                
                # Заполняем новыми данными
                for param in params:
                    if isinstance(param, dict):
                        values = (
                            param.get('signal_code', ''),
                            param.get('description', ''),
                            param.get('line', ''),
                            param.get('wagon', '')
                        )
                    else:
                        values = param
                    self.selected_params_tree.tree.insert('', 'end', values=values)
            
            def grid(self, **kwargs):
                self.frame.grid(**kwargs)
            
            def clear_all(self):
                for item in self.all_params_tree.tree.get_children():
                    self.all_params_tree.tree.delete(item)
                for item in self.selected_params_tree.tree.get_children():
                    self.selected_params_tree.tree.delete(item)
        
        self.logger.info("Создана РАБОЧАЯ панель параметров с логированием")
        return ParameterPanelWrapper(main_frame, all_tree, selected_tree)
    
    def _create_working_action_panel(self, parent, controller):
        """РАБОЧАЯ панель действий"""
        # Основной контейнер
        main_frame = ttk.Frame(parent)
        main_frame.grid_columnconfigure([0, 1, 2], weight=1)
        
        # Кнопки действий
        build_btn = ttk.Button(
            main_frame,
            text="Построить график",
            command=lambda: self._safe_call(controller, 'build_plot'),
            style='Accent.TButton'
        )
        build_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        report_btn = ttk.Button(
            main_frame,
            text="Генерировать отчет",
            command=lambda: self._safe_call(controller, 'generate_report')
        )
        report_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        sop_btn = ttk.Button(
            main_frame,
            text="Создать SOP",
            command=lambda: self._safe_call(controller, 'generate_sop')
        )
        sop_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # Создаем объект-обертку
        class ActionPanelWrapper:
            def __init__(self, frame):
                self.frame = frame
            
            def grid(self, **kwargs):
                self.frame.grid(**kwargs)
        
        self.logger.info("Создана РАБОЧАЯ панель действий")
        return ActionPanelWrapper(main_frame)
    
    def _add_compatibility_methods(self, notebook):
        """Добавление методов совместимости к notebook"""
        def create_plot_tabs_from_sop(plot_groups):
            # Очищаем существующие вкладки
            for tab in notebook.tabs():
                notebook.forget(tab)
            
            # Создаем новые вкладки для каждого графика
            for plot_name, params in plot_groups.items():
                tab_frame = ttk.Frame(notebook)
                notebook.add(tab_frame, text=plot_name)
                
                # Добавляем информацию о параметрах
                info_text = f"График: {plot_name}\nПараметров: {len(params)}\n\n"
                for param in params[:5]:  # Показываем первые 5
                    info_text += f"• {param}\n"
                if len(params) > 5:
                    info_text += f"... и еще {len(params) - 5} параметров"
                
                label = tk.Label(tab_frame, text=info_text, justify='left')
                label.pack(expand=True, padx=20, pady=20)
        
        # Добавляем методы для совместимости
        notebook.create_plot_tabs_from_sop = create_plot_tabs_from_sop
        notebook.auto_build_plots = lambda: None
        notebook.clear_all = lambda: None
    
    def _safe_call(self, controller, method_name):
        """Безопасный вызов метода контроллера"""
        try:
            if hasattr(controller, method_name):
                getattr(controller, method_name)()
            else:
                self.logger.warning(f"Метод {method_name} не найден в контроллере")
        except Exception as e:
            self.logger.error(f"Ошибка вызова {method_name}: {e}")
    
    def _create_simple_panel(self, parent, title):
        """Создание простой панели-заглушки"""
        frame = ttk.LabelFrame(parent, text=title)
        label = ttk.Label(frame, text=f"{title} (заглушка)")
        label.pack(padx=20, pady=20)
        
        def grid(**kwargs):
            frame.grid(**kwargs)
        frame.grid = grid
        
        return frame
    
    def _add_selected_params(self, all_tree, selected_tree):
        """Добавление выбранных параметров"""
        try:
            selected_items = all_tree.selection()
            existing_items = set()
            
            # Получаем уже существующие параметры
            for item in selected_tree.get_children():
                values = selected_tree.item(item, 'values')
                if values:
                    existing_items.add(values[0])  # signal_code
            
            # Добавляем новые параметры
            for item in selected_items:
                values = all_tree.item(item, 'values')
                if values and values[0] not in existing_items:
                    selected_tree.insert('', 'end', values=values)
                    existing_items.add(values[0])
        
        except Exception as e:
            self.logger.error(f"Ошибка добавления параметров: {e}")
    
    def _remove_selected_params(self, selected_tree):
        """Удаление выбранных параметров"""
        try:
            selected_items = selected_tree.selection()
            for item in selected_items:
                selected_tree.delete(item)
        except Exception as e:
            self.logger.error(f"Ошибка удаления параметров: {e}")
    
    def _clear_selected_params(self, selected_tree):
        """Очистка всех выбранных параметров"""
        try:
            for item in selected_tree.get_children():
                selected_tree.delete(item)
        except Exception as e:
            self.logger.error(f"Ошибка очистки параметров: {e}")
