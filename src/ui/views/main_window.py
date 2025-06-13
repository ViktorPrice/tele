"""
Главное окно приложения с единой архитектурой и компактной компоновкой
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class MainWindow:
    """Главное окно с единой архитектурой и компактной компоновкой"""

    def __init__(self, root):
        self.root = root
        self.controller = None
        self.logger = logging.getLogger(self.__class__.__name__)

        # ЕДИНСТВЕННЫЙ менеджер UI
        self.ui_components: Optional['UIComponents'] = None

        # Состояние
        self.is_loading = False
        self.current_file = None

        # UI элементы
        self.status_bar = None
        self.progress_bar = None
        self.menu_bar = None
        
        # Информационная панель в заголовке
        self.info_panel = None

        # Кэш для оптимизации
        self._ui_state_cache = {}
        self._last_update_time = 0

        self._setup_window()
        self.logger.info("MainWindow инициализировано")

    def _setup_window(self):
        """Настройка главного окна с компактной информационной панелью"""
        self.root.title("Анализатор телеметрии - TRAMM v2.0")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Настройка сетки
        self.root.grid_rowconfigure(0, weight=0)  # Информационная панель
        self.root.grid_rowconfigure(1, weight=1)  # Основной контент
        self.root.grid_rowconfigure(2, weight=0)  # Статус-бар
        self.root.grid_columnconfigure(0, weight=1)
        
        # СОЗДАЕМ информационную панель в верхней части
        try:
            # Основной контейнер информационной панели
            self.info_panel = ttk.Frame(self.root, relief=tk.RAISED, borderwidth=1)
            self.info_panel.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
            self.info_panel.grid_columnconfigure(1, weight=1)
            
            # Левая часть - заголовок и статус
            left_frame = ttk.Frame(self.info_panel)
            left_frame.grid(row=0, column=0, sticky="w", padx=8, pady=4)
            
            # Заголовок приложения
            title_label = ttk.Label(
                left_frame,
                text="📊 TRAMM v2.0",
                font=('Arial', 11, 'bold'),
                foreground='#2c3e50'
            )
            title_label.grid(row=0, column=0, sticky="w")
            
            # Статус подключения рядом с заголовком
            self.connection_status = ttk.Label(
                left_frame,
                text="⚪ Готов",
                font=('Arial', 9, 'bold'),
                foreground='#27ae60'
            )
            self.connection_status.grid(row=0, column=1, sticky="w", padx=(10, 0))
            
            # Центральная часть - основная информация
            center_frame = ttk.Frame(self.info_panel)
            center_frame.grid(row=0, column=1, sticky="ew", padx=8, pady=4)
            center_frame.grid_columnconfigure(0, weight=1)
            
            # ОСНОВНАЯ информационная строка с МЦД данными
            self.main_info_label = ttk.Label(
                center_frame,
                text="📁 Файл: не загружен | 📊 Параметров: 0 | 🚄 МЦД: - | 🗺️ Маршрут: - | 🚂 Состав: - | ⏰ Голова: -",
                font=('Arial', 9),
                foreground='#34495e',
                anchor='center'
            )
            self.main_info_label.grid(row=0, column=0, sticky="ew")
            
            # Правая часть - дополнительная информация
            right_frame = ttk.Frame(self.info_panel)
            right_frame.grid(row=0, column=2, sticky="e", padx=8, pady=4)
            
            self.additional_info_label = ttk.Label(
                right_frame,
                text="💡 Загрузите CSV файл",
                font=('Arial', 8),
                foreground='#7f8c8d'
            )
            self.additional_info_label.grid(row=0, column=0, sticky="e")
            
            self.logger.info("✅ Информационная панель создана")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания информационной панели: {e}")
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)



    def update_telemetry_info(self, file_name: str = "", params_count: int = 0, selected_count: int = 0, 
                         line_mcd: str = "", route: str = "", train: str = "", leading_unit: str = ""):
        """Обновление основной информации в компактном формате с данными телеметрии"""
        try:
            self.logger.info(f"🔄 update_telemetry_info вызван: файл={file_name}, МЦД={line_mcd}, маршрут={route}, состав={train}, вагон={leading_unit}")
            
            if self.main_info_label:
                # Компактный формат с основной информацией о телеметрии
                info_parts = []
                
                # Файл и параметры
                info_parts.append(f"📁 {file_name or 'не загружен'}")
                info_parts.append(f"📊 {params_count}")
                if selected_count > 0:
                    info_parts.append(f"✅ {selected_count}")
                
                # Данные телеметрии МЦД
                info_parts.append(f"🚄 МЦД-{line_mcd or '-'}")
                info_parts.append(f"🗺️ {route or '-'}")
                info_parts.append(f"🚂 {train or '-'}")
                info_parts.append(f"⏰ {leading_unit or '-'}")
                
                info_text = " | ".join(info_parts)
                self.main_info_label.config(text=info_text)
                
                # ПРИНУДИТЕЛЬНОЕ обновление отображения
                self.main_info_label.update()
                self.root.update_idletasks()
                
                self.logger.info(f"✅ Информационная панель обновлена: {info_text}")
                
            else:
                self.logger.error("❌ main_info_label не найден! Информационная панель не создана.")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления основной информации: {e}")
            import traceback
            traceback.print_exc()

    def update_additional_info(self, message: str):
        """Обновление дополнительной информации (более краткой)"""
        try:
            if hasattr(self, 'additional_info_label') and self.additional_info_label:
                self.additional_info_label.config(text=message)
                self.additional_info_label.update()
                self.root.update_idletasks()
        except Exception as e:
            self.logger.error(f"Ошибка обновления дополнительной информации: {e}")

    def update_connection_status(self, status: str, color: str = "#27ae60"):
        """Обновление статуса подключения"""
        try:
            if hasattr(self, 'connection_status') and self.connection_status:
                self.connection_status.config(text=status, foreground=color)
                self.connection_status.update()
                self.root.update_idletasks()
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса подключения: {e}")

    def update_mcd_info(self, line_mcd: str = "", route: str = "", train: str = "", leading_unit: str = ""):
        """Обновление только информации о МЦД без изменения файла и параметров"""
        try:
            if self.main_info_label:
                # Получаем текущий текст
                current_text = self.main_info_label.cget("text")
                parts = current_text.split("|")
                # Обновляем части с МЦД
                for i, part in enumerate(parts):
                    if part.strip().startswith("🚄 МЦД-"):
                        parts[i] = f"🚄 МЦД-{line_mcd or '-'}"
                    elif part.strip().startswith("🗺️"):
                        parts[i] = f"🗺️ {route or '-'}"
                    elif part.strip().startswith("🚂"):
                        parts[i] = f"🚂 {train or '-'}"
                    elif part.strip().startswith("⏰"):
                        parts[i] = f"⏰ {leading_unit or '-'}"
                new_text = " | ".join(parts)
                self.main_info_label.config(text=new_text)
                self.main_info_label.update()
                self.root.update_idletasks()
        except Exception as e:
            self.logger.error(f"Ошибка обновления информации о МЦД: {e}")

    def update_file_info(self, file_path: str = "", records_count: int = 0):
        """Обновление информации о файле с автоматическим извлечением данных МЦД"""


    def setup(self):
        """Простая настройка без создания UI компонентов"""
        try:
            # Только меню и статус-бар
            self._create_menu_bar()
            self._create_status_bar()
            
            self.logger.info("MainWindow настроен (ожидание контроллера)")
            
        except Exception as e:
            self.logger.error(f"Ошибка настройки MainWindow: {e}")
            raise

    def set_controller(self, controller):
        """Создание UIComponents ПОСЛЕ установки контроллера"""
        try:
            self.controller = controller
            
            # Импортируем и создаем UIComponents с улучшенной компоновкой
            from ..components.ui_components import UIComponents
            self.ui_components = UIComponents(self.root, controller)
            
            # ВАЖНО: Ждем полной инициализации UI компонентов
            if hasattr(self.ui_components, 'is_initialized') and self.ui_components.is_initialized:
                # Устанавливаем ui_components в контроллер
                controller.set_ui_components(self.ui_components)
                
                # Обновляем реестр UI компонентов в контроллере
                controller.refresh_ui_registry()
                
                self.logger.info("✅ Контроллер установлен, UIComponents созданы и реестр обновлен")
            else:
                self.logger.warning("⚠️ UI компоненты созданы, но не полностью инициализированы")
            
            # Настраиваем улучшенную компоновку панели параметров
            self._configure_parameter_panel_layout()
            
            # Устанавливаем обратные связи
            controller.view = self  # Устанавливаем self как view
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка установки контроллера: {e}")
            raise

    def delayed_refresh_ui_registry(self, delay_ms: int = 100):
        """Отложенное обновление реестра UI компонентов"""
        try:
            def refresh_after_delay():
                try:
                    self.refresh_ui_registry()
                except Exception as e:
                    self.logger.error(f"Ошибка отложенного обновления реестра: {e}")
            
            # Планируем обновление через указанное время
            if hasattr(self.view, 'root'):
                self.view.root.after(delay_ms, refresh_after_delay)
            else:
                # Fallback - обновляем сразу
                refresh_after_delay()
                
        except Exception as e:
            self.logger.error(f"Ошибка планирования отложенного обновления: {e}")


    def _configure_parameter_panel_layout(self):
        """Настройка улучшенной компоновки панели параметров 50/50"""
        try:
            if not self.ui_components or not self.ui_components.parameter_panel:
                self.logger.warning("parameter_panel не найден для настройки компоновки")
                return
                
            parameter_panel = self.ui_components.parameter_panel
            
            # Проверяем, есть ли метод для настройки компоновки 50/50
            if hasattr(parameter_panel, 'configure_split_layout'):
                parameter_panel.configure_split_layout(split_ratio=0.5)
                self.logger.info("✅ Настроена компоновка панели параметров 50/50")
                
            elif hasattr(parameter_panel, 'tree_all') and hasattr(parameter_panel, 'tree_selected'):
                # Альтернативный способ через прямую настройку весов
                try:
                    # Получаем родительский контейнер
                    parent_frame = parameter_panel.master
                    if parent_frame:
                        # Настраиваем веса колонок для равного распределения
                        parent_frame.grid_columnconfigure(0, weight=1)
                        parent_frame.grid_columnconfigure(1, weight=1)
                        
                        # Если есть разделитель между панелями
                        if hasattr(parameter_panel, 'paned_window'):
                            parameter_panel.paned_window.configure(sashrelief=tk.RAISED, sashwidth=3)
                            
                        self.logger.info("✅ Настроена альтернативная компоновка панели параметров")
                        
                except Exception as e:
                    self.logger.error(f"Ошибка альтернативной настройки компоновки: {e}")
                    
            else:
                self.logger.warning("Методы настройки компоновки панели параметров не найдены")
                
        except Exception as e:
            self.logger.error(f"Ошибка настройки компоновки панели параметров: {e}")

    def _create_menu_bar(self):
        """Создание строки меню БЕЗ переключения режимов UI"""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Меню "Файл"
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Открыть CSV...", command=self._upload_csv, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт графиков...", command=self._export_all_plots)
        file_menu.add_command(label="Генерация отчета...", command=self._generate_report, accelerator="Ctrl+R")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._on_closing, accelerator="Alt+F4")

        # Меню "Вид"
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Вид", menu=view_menu)
        view_menu.add_command(label="Сбросить макет", command=self._reset_layout)
        view_menu.add_command(label="Полноэкранный режим", command=self._toggle_fullscreen)
        view_menu.add_separator()
        view_menu.add_command(label="Очистить все", command=self._clear_all_ui)
        
        # УБРАНО: view_menu.add_command(label="Переключить режим UI", command=self._toggle_ui_mode)
        
        # Подменю для настройки панели параметров
        panel_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Панель параметров", menu=panel_menu)
        panel_menu.add_command(label="Компоновка 50/50", command=lambda: self._set_parameter_layout(0.5))
        panel_menu.add_command(label="Компоновка 70/30", command=lambda: self._set_parameter_layout(0.7))
        panel_menu.add_command(label="Компоновка 30/70", command=lambda: self._set_parameter_layout(0.3))

        # Меню "Инструменты"
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Инструменты", menu=tools_menu)
        tools_menu.add_command(label="Настройки...", command=self._show_settings)
        tools_menu.add_command(label="Диагностика", command=self._show_diagnostics)

        # Меню "Справка"
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._show_about)
        help_menu.add_command(label="Горячие клавиши", command=self._show_shortcuts)

        # Горячие клавиши
        self.root.bind("<Control-o>", lambda e: self._upload_csv())
        self.root.bind("<Control-r>", lambda e: self._generate_report())
        self.root.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.root.bind("<Control-q>", lambda e: self._on_closing())

    def _set_parameter_layout(self, ratio: float):
        """Установка соотношения панелей параметров"""
        try:
            if self.ui_components and self.ui_components.parameter_panel:
                parameter_panel = self.ui_components.parameter_panel
                
                if hasattr(parameter_panel, 'configure_split_layout'):
                    parameter_panel.configure_split_layout(split_ratio=ratio)
                    self.update_status(f"Компоновка панели параметров изменена на {int(ratio*100)}/{int((1-ratio)*100)}")
                    self.logger.info(f"✅ Установлена компоновка панели параметров: {ratio}")
                else:
                    self.show_warning("Настройка компоновки панели параметров недоступна")
                    
        except Exception as e:
            self.logger.error(f"Ошибка установки компоновки панели параметров: {e}")
            self.show_error(f"Ошибка изменения компоновки: {e}")

    # УБРАН МЕТОД: _toggle_ui_mode() - больше не нужен

    def _create_status_bar(self):
        """Создание статус-бара с учетом информационной панели"""
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_bar = ttk.Label(
            status_frame, 
            text="Готов к загрузке данных", 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            font=('Arial', 9)
        )
        self.status_bar.grid(row=0, column=0, sticky="ew", padx=2, pady=1)
        
        self.progress_bar = ttk.Progressbar(status_frame, mode='determinate', length=200)
        self.progress_bar.grid(row=0, column=1, padx=5, pady=1)
        self.progress_bar.grid_remove()

        # Дополнительная информация в статус-баре
        self.file_info_label = ttk.Label(
            status_frame,
            text="",
            font=('Arial', 8),
            foreground='gray'
        )
        self.file_info_label.grid(row=0, column=2, padx=5)

    # === ДЕЛЕГИРОВАНИЕ К КОНТРОЛЛЕРУ ===
    
    def _upload_csv(self):
        """Делегирование загрузки CSV к контроллеру"""
        if self.controller:
            self.controller.upload_csv()

    def _generate_report(self):
        """Делегирование генерации отчета к контроллеру"""
        if self.controller:
            self.controller.generate_report()

    def _export_all_plots(self):
        """Делегирование экспорта графиков"""
        if self.ui_components and hasattr(self.ui_components, 'plot_panel'):
            plot_panel = self.ui_components.plot_panel
            if hasattr(plot_panel, 'export_all_plots'):
                plot_panel.export_all_plots()
            else:
                self.show_warning("Функция экспорта графиков недоступна")
        else:
            self.show_warning("Панель графиков не найдена")

    # === МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ С КОНТРОЛЛЕРОМ ===
    
    def update_status(self, message: str):
        """Обновление статусной строки с кэшированием"""
        try:
            if self._should_update_ui('status', message):
                if self.status_bar:
                    self.status_bar.config(text=message)
                    self.root.update_idletasks()
                self._cache_ui_state('status', message)
                
                # Также обновляем дополнительную информацию в заголовке
                self.update_additional_info(message)
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса: {e}")
    
    def show_progress(self, show: bool = True, value: int = 0, maximum: int = 100):
        """Показ/скрытие прогресс-бара с обновлением статуса"""
        try:
            if show:
                self.progress_bar.configure(maximum=maximum, value=value)
                self.progress_bar.grid()
                self.update_connection_status("processing", "#f39c12")
            else:
                self.progress_bar.grid_remove()
                self.update_connection_status("ready", "#27ae60")
            self.root.update_idletasks()
        except Exception as e:
            self.logger.error(f"Ошибка управления прогресс-баром: {e}")
    
    def update_progress(self, value: int):
        """Обновление прогресса"""
        try:
            self.progress_bar.configure(value=value)
            self.root.update_idletasks()
        except Exception as e:
            self.logger.error(f"Ошибка обновления прогресса: {e}")
    
    def show_info(self, title: str, message: str):
        """Показ информационного сообщения"""
        messagebox.showinfo(title, message, parent=self.root)
    
    def show_warning(self, message: str):
        """Показ предупреждения"""
        messagebox.showwarning("Предупреждение", message, parent=self.root)
    
    def show_error(self, message: str):
        """Показ ошибки"""
        messagebox.showerror("Ошибка", message, parent=self.root)
    
    def set_loading_state(self, loading: bool):
        """Установка состояния загрузки"""
        try:
            self.is_loading = loading
            if loading:
                self.root.config(cursor="wait")
                self.show_progress(True)
                self.update_connection_status("loading", "#f39c12")
            else:
                self.root.config(cursor="")
                self.show_progress(False)
                self.update_connection_status("ready", "#27ae60")
        except Exception as e:
            self.logger.error(f"Ошибка установки состояния загрузки: {e}")

    def start_processing(self, message: str = "Обработка..."):
        """Начало обработки"""
        self.set_loading_state(True)
        self.update_status(message)
        self.update_connection_status("processing", "#e74c3c")

    def stop_processing(self):
        """Завершение обработки"""
        self.set_loading_state(False)
        self.update_status("Готов")
        self.update_connection_status("ready", "#27ae60")

    def start_loading(self, message: str = "Загрузка..."):
        """Начало загрузки"""
        self.set_loading_state(True)
        self.update_status(message)

    def stop_loading(self):
        """Завершение загрузки"""
        self.set_loading_state(False)
        self.update_status("Готов")

    def update_file_info(self, file_path: str = "", records_count: int = 0):
        """Обновление информации о файле"""
        try:
            if file_path and records_count > 0:
                file_name = Path(file_path).name
                info_text = f"Файл: {file_name} | Записей: {records_count:,}"
                self.current_file = file_path
                
                # Обновляем информацию в заголовке
                self.update_additional_info(f"Загружен файл: {file_name} ({records_count:,} записей)")
                self.update_connection_status("connected", "#27ae60")
                
            else:
                info_text = ""
                self.current_file = None
                self.update_additional_info("Готов к загрузке данных")
                self.update_connection_status("ready", "#95a5a6")
            
            if self.file_info_label:
                self.file_info_label.config(text=info_text)
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления информации о файле: {e}")

    def update_parameter_count(self, count: int):
        """Обновление счетчика параметров"""
        try:
            if self._should_update_ui('parameter_count', count):
                self.update_additional_info(f"Отображается параметров: {count}")
                self._cache_ui_state('parameter_count', count)
        except Exception as e:
            self.logger.error(f"Ошибка обновления счетчика параметров: {e}")

    # === МЕТОДЫ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ ===
    
    def update_tree_all_params(self, params: list):
        """Обновление параметров через UIComponents"""
        try:
            if self.ui_components and self.ui_components.parameter_panel:
                self.logger.info(f"📊 Делегирование к parameter_panel: {len(params)} параметров")
                
                # Проверяем наличие метода update_parameters
                if hasattr(self.ui_components.parameter_panel, 'update_parameters'):
                    self.ui_components.parameter_panel.update_parameters(params)
                    self.logger.info("✅ parameter_panel.update_parameters выполнен")
                elif hasattr(self.ui_components.parameter_panel, 'update_tree_all_params'):
                    self.ui_components.parameter_panel.update_tree_all_params(params)
                    self.logger.info("✅ parameter_panel.update_tree_all_params выполнен")
                else:
                    self.logger.error("❌ Методы обновления параметров не найдены")
                    self._diagnose_parameter_panel()
                    
                # Обновляем информацию о количестве параметров в заголовке
                self.update_additional_info(f"Загружено параметров: {len(params)}")
                
            else:
                self.logger.error("❌ ui_components или parameter_panel не найдены")
                self._diagnose_ui_components()
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка update_tree_all_params: {e}")
            import traceback
            traceback.print_exc()

    def update_line_checkboxes(self, lines: list):
        """Делегирование обновления чекбоксов линий"""
        try:
            if self.ui_components and self.ui_components.filter_panel:
                if hasattr(self.ui_components.filter_panel, 'update_line_checkboxes'):
                    self.ui_components.filter_panel.update_line_checkboxes(lines)
                    self.logger.info(f"✅ Обновлены линии: {len(lines)} элементов")
                else:
                    self.logger.warning("Метод update_line_checkboxes не найден в filter_panel")
            else:
                self.logger.warning("filter_panel не найден")
        except Exception as e:
            self.logger.error(f"Ошибка обновления линий: {e}")

    def update_filtered_count(self, count: int):
        """Обновление счетчика отфильтрованных параметров"""
        try:
            if self._should_update_ui('filtered_count', count):
                self.logger.info(f"Отфильтровано параметров: {count}")
                
                # Обновляем в панели параметров если есть
                if (self.ui_components and 
                    self.ui_components.parameter_panel and 
                    hasattr(self.ui_components.parameter_panel, 'update_counters')):
                    self.ui_components.parameter_panel.update_counters(count, 0)
                
                # Обновляем информацию в заголовке
                self.update_additional_info(f"Отображается параметров: {count}")
                
                self._cache_ui_state('filtered_count', count)
        except Exception as e:
            self.logger.error(f"Ошибка обновления счетчика: {e}")

    # === СВОЙСТВА ДЛЯ СОВМЕСТИМОСТИ ===
    
    @property
    def parameter_panel(self):
        """Доступ к панели параметров"""
        if self.ui_components:
            return self.ui_components.parameter_panel
        return None

    @property
    def filter_panel(self):
        """Доступ к панели фильтров"""
        if self.ui_components:
            return self.ui_components.filter_panel
        return None

    @property
    def time_panel(self):
        """Доступ к панели времени"""
        if self.ui_components:
            return self.ui_components.time_panel
        return None

    @property
    def action_panel(self):
        """Доступ к панели действий"""
        if self.ui_components:
            return self.ui_components.action_panel
        return None

    @property
    def plot_panel(self):
        """Доступ к панели графиков"""
        if self.ui_components:
            return getattr(self.ui_components, 'plot_panel', None)
        return None

    def get_component(self, component_name: str):
        """Получение компонента по имени"""
        components = {
            'ui_components': self.ui_components,
            'time_panel': self.time_panel,
            'filter_panel': self.filter_panel,
            'parameter_panel': self.parameter_panel,
            'action_panel': self.action_panel,
            'plot_panel': self.plot_panel,
            'info_panel': self.info_panel
        }
        return components.get(component_name)

    # === МЕТОДЫ КЭШИРОВАНИЯ ДЛЯ ОПТИМИЗАЦИИ ===
    
    def _should_update_ui(self, key: str, value: Any) -> bool:
        """Проверка необходимости обновления UI"""
        import time
        current_time = time.time()
        
        # Обновляем не чаще чем раз в 50мс
        if current_time - self._last_update_time < 0.05:
            return False
        
        # Проверяем изменение значения
        if key in self._ui_state_cache:
            if self._ui_state_cache[key] == value:
                return False
        
        return True
    
    def _cache_ui_state(self, key: str, value: Any):
        """Кэширование состояния UI"""
        import time
        self._ui_state_cache[key] = value
        self._last_update_time = time.time()

    # === ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ИНТЕРФЕЙСА ===
    
    def _reset_layout(self):
        """Сброс макета к состоянию по умолчанию"""
        try:
            if self.ui_components:
                # Сбрасываем все панели
                if hasattr(self.ui_components, 'reset_all_panels'):
                    self.ui_components.reset_all_panels()
                
                # Сбрасываем компоновку панели параметров к 50/50
                self._set_parameter_layout(0.5)
                
                self.update_status("Макет сброшен")
                self.logger.info("Макет сброшен к состоянию по умолчанию")
        except Exception as e:
            self.logger.error(f"Ошибка сброса макета: {e}")
    
    def _toggle_fullscreen(self):
        """Переключение полноэкранного режима"""
        try:
            current_state = self.root.attributes('-fullscreen')
            self.root.attributes('-fullscreen', not current_state)
            
            if not current_state:
                self.update_status("Полноэкранный режим включен (F11 - выход)")
                self.update_connection_status("fullscreen", "#3498db")
            else:
                self.update_status("Обычный режим")
                self.update_connection_status("ready", "#27ae60")
        except Exception as e:
            self.logger.error(f"Ошибка переключения полноэкранного режима: {e}")
    
    def _clear_all_ui(self):
        """Очистка всего интерфейса"""
        try:
            if messagebox.askyesno("Очистка", "Очистить все данные и графики?", parent=self.root):
                if self.ui_components:
                    # Очищаем все панели
                    if hasattr(self.ui_components, 'reset_all_panels'):
                        self.ui_components.reset_all_panels()
                    
                    # Очищаем графики
                    if hasattr(self.ui_components, 'plot_panel'):
                        plot_panel = self.ui_components.plot_panel
                        if plot_panel and hasattr(plot_panel, 'clear_all_plots'):
                            plot_panel.clear_all_plots()
                
                # Очищаем кэш
                self._ui_state_cache.clear()
                
                # Сбрасываем информацию о файле и заголовке
                self.update_file_info()
                self.update_telemetry_info()
                self.update_additional_info("Интерфейс очищен. Готов к загрузке новых данных")
                
                self.update_status("Интерфейс очищен")
                self.logger.info("Весь интерфейс очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки интерфейса: {e}")
    
    def _show_settings(self):
        """Показ окна настроек БЕЗ переключения режимов UI"""
        try:
            settings_window = tk.Toplevel(self.root)
            settings_window.title("Настройки")
            settings_window.geometry("500x400")
            settings_window.transient(self.root)
            settings_window.grab_set()
            
            # Заголовок
            title_label = ttk.Label(
                settings_window, 
                text="⚙️ Настройки анализатора телеметрии",
                font=('Arial', 14, 'bold')
            )
            title_label.pack(pady=10)
            
            # Notebook для вкладок настроек
            notebook = ttk.Notebook(settings_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Вкладка "Интерфейс" - БЕЗ переключения режимов
            ui_frame = ttk.Frame(notebook)
            notebook.add(ui_frame, text="Интерфейс")
            
            # Настройки компоновки панели параметров
            layout_frame = ttk.LabelFrame(ui_frame, text="Компоновка панели параметров", padding="10")
            layout_frame.pack(fill=tk.X, padx=10, pady=5)
            
            layout_var = tk.StringVar(value="50/50")
            
            ttk.Radiobutton(layout_frame, text="50% / 50%", variable=layout_var, value="50/50").pack(anchor=tk.W)
            ttk.Radiobutton(layout_frame, text="70% / 30%", variable=layout_var, value="70/30").pack(anchor=tk.W)
            ttk.Radiobutton(layout_frame, text="30% / 70%", variable=layout_var, value="30/70").pack(anchor=tk.W)
            
            def apply_layout():
                ratio_map = {"50/50": 0.5, "70/30": 0.7, "30/70": 0.3}
                ratio = ratio_map.get(layout_var.get(), 0.5)
                self._set_parameter_layout(ratio)
            
            ttk.Button(layout_frame, text="Применить", command=apply_layout).pack(pady=5)
            
            # Кнопки
            button_frame = ttk.Frame(settings_window)
            button_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Button(
                button_frame, 
                text="Закрыть", 
                command=settings_window.destroy
            ).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            self.logger.error(f"Ошибка показа настроек: {e}")
    
    def _show_diagnostics(self):
        """Показ диагностической информации"""
        try:
            diag_window = tk.Toplevel(self.root)
            diag_window.title("Диагностика системы")
            diag_window.geometry("700x500")
            diag_window.transient(self.root)
            diag_window.grab_set()
            
            # Заголовок
            title_label = ttk.Label(
                diag_window, 
                text="🔍 Диагностика анализатора телеметрии",
                font=('Arial', 14, 'bold')
            )
            title_label.pack(pady=10)
            
            # Текстовое поле для диагностики
            text_widget = tk.Text(diag_window, wrap=tk.WORD, font=('Courier', 9))
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Собираем диагностическую информацию
            diag_info = self._collect_diagnostic_info()
            text_widget.insert(tk.END, diag_info)
            text_widget.config(state=tk.DISABLED)
            
            # Кнопки
            button_frame = ttk.Frame(diag_window)
            button_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Button(
                button_frame, 
                text="Обновить", 
                command=lambda: self._refresh_diagnostics(text_widget)
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                button_frame, 
                text="Копировать", 
                command=lambda: self._copy_diagnostics(text_widget)
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                button_frame, 
                text="Закрыть", 
                command=diag_window.destroy
            ).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            self.logger.error(f"Ошибка показа диагностики: {e}")
    
    def _collect_diagnostic_info(self) -> str:
        """Сбор диагностической информации"""
        try:
            import platform
            import sys
            from datetime import datetime
            
            info = []
            info.append("=== ДИАГНОСТИКА АНАЛИЗАТОРА ТЕЛЕМЕТРИИ TRAMM v2.0 ===")
            info.append(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            info.append("")
            
            # Системная информация
            info.append("=== СИСТЕМА ===")
            info.append(f"ОС: {platform.system()} {platform.release()}")
            info.append(f"Python: {sys.version}")
            info.append(f"Архитектура: {platform.architecture()[0]}")
            info.append("")
            
            # Состояние приложения
            info.append("=== СОСТОЯНИЕ ПРИЛОЖЕНИЯ ===")
            info.append(f"Контроллер: {'✅ Установлен' if self.controller else '❌ Не установлен'}")
            info.append(f"UI Components: {'✅ Инициализированы' if self.ui_components else '❌ Не инициализированы'}")
            info.append(f"Информационная панель: {'✅ Создана' if self.info_panel else '❌ Не создана'}")
            info.append(f"Текущий файл: {self.current_file or 'Не загружен'}")
            info.append(f"Состояние загрузки: {'🔄 Активно' if self.is_loading else '⚪ Неактивно'}")
            info.append("")
            
            # Состояние панелей
            info.append("=== СОСТОЯНИЕ ПАНЕЛЕЙ ===")
            if self.ui_components:
                panels = {
                    'TimePanel': self.ui_components.time_panel,
                    'FilterPanel': self.ui_components.filter_panel,
                    'ParameterPanel': self.ui_components.parameter_panel,
                    'ActionPanel': self.ui_components.action_panel,
                    'PlotPanel': getattr(self.ui_components, 'plot_panel', None),
                    'DiagnosticPanel': getattr(self.ui_components, 'diagnostic_panel', None)
                }
                
                for name, panel in panels.items():
                    status = "✅ Активна" if panel else "❌ Не создана"
                    info.append(f"{name}: {status}")
                    
                    if panel:
                        # Дополнительная информация о панели
                        if hasattr(panel, 'all_parameters') and hasattr(panel, 'selected_parameters'):
                            total = len(panel.all_parameters)
                            selected = len(panel.selected_parameters)
                            info.append(f"  └─ Параметров: {total}, Выбрано: {selected}")
                        elif name == 'ParameterPanel':
                            # Проверяем альтернативные атрибуты
                            if hasattr(panel, 'tree_all'):
                                tree_items = len(panel.tree_all.get_children()) if panel.tree_all else 0
                                info.append(f"  └─ Элементов в дереве: {tree_items}")
            else:
                info.append("❌ UI Components не инициализированы")
            
            info.append("")
            
            # Информация о компоновке панели параметров
            info.append("=== КОМПОНОВКА ПАНЕЛИ ПАРАМЕТРОВ ===")
            if self.ui_components and self.ui_components.parameter_panel:
                panel = self.ui_components.parameter_panel
                if hasattr(panel, 'configure_split_layout'):
                    info.append("✅ Поддерживается настройка компоновки 50/50")
                else:
                    info.append("⚠️ Настройка компоновки недоступна")
                    
                if hasattr(panel, 'tree_all') and hasattr(panel, 'tree_selected'):
                    info.append("✅ Найдены панели 'Все параметры' и 'Выбранные параметры'")
                else:
                    info.append("⚠️ Стандартные панели параметров не найдены")
            else:
                info.append("❌ Панель параметров недоступна")
            
            info.append("")
            
            # Кэш состояния
            info.append("=== КЭШ СОСТОЯНИЯ ===")
            info.append(f"Записей в кэше: {len(self._ui_state_cache)}")
            for key, value in self._ui_state_cache.items():
                info.append(f"  {key}: {str(value)[:50]}...")
            
            return "\n".join(info)
            
        except Exception as e:
            return f"❌ Ошибка сбора диагностической информации: {e}"
    
    def _refresh_diagnostics(self, text_widget):
        """Обновление диагностической информации"""
        try:
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            
            diag_info = self._collect_diagnostic_info()
            text_widget.insert(tk.END, diag_info)
            
            text_widget.config(state=tk.DISABLED)
        except Exception as e:
            self.logger.error(f"Ошибка обновления диагностики: {e}")
    
    def _copy_diagnostics(self, text_widget):
        """Копирование диагностики в буфер обмена"""
        try:
            diag_text = text_widget.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(diag_text)
            self.update_status("Диагностическая информация скопирована в буфер обмена")
        except Exception as e:
            self.logger.error(f"Ошибка копирования диагностики: {e}")
    
    def _show_about(self):
        """Показ информации о программе"""
        about_text = """
📊 Анализатор телеметрии TRAMM v2.0

Система анализа и визуализации данных телеметрии
железнодорожного транспорта.

🚀 Возможности:
• Загрузка и анализ CSV файлов
• Интерактивная фильтрация параметров
• Приоритетная логика изменяемых параметров
• Построение графиков телеметрии
• Генерация отчетов и SOP
• Настраиваемая компоновка интерфейса

🔧 Улучшения v2.0:
• Информационная панель в заголовке
• Компоновка панели параметров 50/50
• Расширенная диагностика системы
• Улучшенная система статусов

© 2025 TRAMM Project
        """
        messagebox.showinfo("О программе", about_text, parent=self.root)
    
    def _show_shortcuts(self):
        """Показ горячих клавиш"""
        shortcuts_text = """
⌨️ Горячие клавиши:

📁 Файлы:
Ctrl+O - Открыть CSV файл
Ctrl+R - Генерация отчета

🖥️ Интерфейс:
F11 - Полноэкранный режим
Ctrl+Q - Выход из программы

📊 Панель параметров:
Double-click - Добавить/удалить параметр
Delete - Удалить выбранный параметр
Правый клик - Контекстное меню

🔧 Дополнительно:
Меню "Вид" → "Панель параметров" - настройка компоновки
Меню "Инструменты" → "Диагностика" - системная информация
        """
        messagebox.showinfo("Горячие клавиши", shortcuts_text, parent=self.root)

    # === ДИАГНОСТИЧЕСКИЕ МЕТОДЫ ===
    
    def _diagnose_ui_components(self):
        """ДИАГНОСТИКА состояния UI компонентов"""
        try:
            self.logger.info("=== ДИАГНОСТИКА UI КОМПОНЕНТОВ ===")
            
            self.logger.info(f"ui_components существует: {self.ui_components is not None}")
            
            if self.ui_components:
                attrs = [attr for attr in dir(self.ui_components) if not attr.startswith('_')]
                self.logger.info(f"Атрибуты ui_components: {attrs}")
                
                # Проверяем каждую панель
                panels = ['time_panel', 'filter_panel', 'parameter_panel', 'action_panel']
                for panel_name in panels:
                    panel = getattr(self.ui_components, panel_name, None)
                    self.logger.info(f"{panel_name}: {panel is not None} ({type(panel) if panel else 'None'})")
                    
                    if panel:
                        methods = [m for m in dir(panel) if not m.startswith('_') and callable(getattr(panel, m))]
                        self.logger.info(f"{panel_name} методы: {methods[:10]}...")  # Первые 10
            else:
                self.logger.error("ui_components равен None")
                
        except Exception as e:
            self.logger.error(f"Ошибка диагностики: {e}")

    def _diagnose_parameter_panel(self):
        """ДИАГНОСТИКА состояния parameter_panel"""
        try:
            self.logger.info("=== ДИАГНОСТИКА PARAMETER PANEL ===")
            
            if self.ui_components and self.ui_components.parameter_panel:
                panel = self.ui_components.parameter_panel
                self.logger.info(f"parameter_panel тип: {type(panel)}")
                
                # Проверяем методы
                methods = [m for m in dir(panel) if not m.startswith('_')]
                self.logger.info(f"Доступные методы: {methods}")
                
                # Проверяем данные
                if hasattr(panel, 'all_parameters'):
                    self.logger.info(f"all_parameters: {len(panel.all_parameters)} элементов")
                if hasattr(panel, 'tree_all'):
                    tree_items = len(panel.tree_all.get_children()) if panel.tree_all else 0
                    self.logger.info(f"tree_all элементов: {tree_items}")
                    
        except Exception as e:
            self.logger.error(f"Ошибка диагностики parameter_panel: {e}")

    # === МЕТОДЫ ОЧИСТКИ И ЗАВЕРШЕНИЯ ===
    
    def _on_closing(self):
        """Обработка закрытия приложения"""
        try:
            if self.is_loading:
                response = messagebox.askyesno(
                    "Выход", 
                    "Идет загрузка данных. Вы уверены, что хотите выйти?",
                    parent=self.root
                )
                if not response:
                    return
            
            # Проверяем несохраненные изменения
            if self.current_file and self._has_unsaved_changes():
                response = messagebox.askyesnocancel(
                    "Несохраненные изменения",
                    "Есть несохраненные изменения. Сохранить перед выходом?",
                    parent=self.root
                )
                if response is None:  # Cancel
                    return
                elif response:  # Yes - save
                    self._save_current_state()
            
            # Обновляем статус закрытия
            self.update_connection_status("closing", "#e74c3c")
            self.update_additional_info("Завершение работы...")
            
            # Очистка ресурсов
            self._cleanup_resources()
            
            # Закрытие приложения
            self.root.quit()
            self.root.destroy()
            
            self.logger.info("Приложение закрыто")
            
        except Exception as e:
            self.logger.error(f"Ошибка при закрытии: {e}")
            # Принудительное закрытие в случае ошибки
            self.root.quit()

    def _has_unsaved_changes(self) -> bool:
        """Проверка наличия несохраненных изменений"""
        try:
            # Проверяем, есть ли выбранные параметры
            if (self.ui_components and 
                self.ui_components.parameter_panel and 
                hasattr(self.ui_components.parameter_panel, 'selected_parameters')):
                return len(self.ui_components.parameter_panel.selected_parameters) > 0
            return False
        except Exception as e:
            self.logger.error(f"Ошибка проверки несохраненных изменений: {e}")
            return False

    def _save_current_state(self):
        """Сохранение текущего состояния"""
        try:
            if not self.current_file:
                return
            
            # Получаем состояние для сохранения
            state = {
                'file_path': self.current_file,
                'selected_parameters': [],
                'filter_criteria': {},
                'time_range': ('', ''),
                'ui_layout': {
                    'parameter_panel_ratio': 0.5,
                    'compact_mode': True  # Всегда компактный режим
                }
            }
            
            # Собираем данные с панелей
            if self.ui_components:
                if self.ui_components.parameter_panel:
                    if hasattr(self.ui_components.parameter_panel, 'get_selected_parameters'):
                        state['selected_parameters'] = self.ui_components.parameter_panel.get_selected_parameters()
                
                if self.ui_components.filter_panel:
                    if hasattr(self.ui_components.filter_panel, 'get_selected_filters'):
                        state['filter_criteria'] = self.ui_components.filter_panel.get_selected_filters()
                
                if self.ui_components.time_panel:
                    if hasattr(self.ui_components.time_panel, 'get_time_range'):
                        state['time_range'] = self.ui_components.time_panel.get_time_range()
            
            # Сохраняем в файл настроек
            import json
            settings_file = Path.home() / '.tramm_settings.json'
            
            try:
                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump(state, f, indent=2, ensure_ascii=False, default=str)
                
                self.logger.info(f"Состояние сохранено в {settings_file}")
                self.update_additional_info("Настройки сохранены")
                
            except Exception as e:
                self.logger.error(f"Ошибка сохранения настроек: {e}")
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения состояния: {e}")

    def _cleanup_resources(self):
        """Очистка всех ресурсов"""
        try:
            # Очищаем UI компоненты
            if self.ui_components:
                if hasattr(self.ui_components, 'cleanup'):
                    self.ui_components.cleanup()
            
            # Очищаем контроллер
            if hasattr(self.controller, 'cleanup'):
                self.controller.cleanup()
            
            # Очищаем кэш
            self._ui_state_cache.clear()
            
            # Обнуляем ссылки
            self.ui_components = None
            self.controller = None
            self.info_panel = None
            
            self.logger.info("Ресурсы очищены")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки ресурсов: {e}")

    def cleanup(self):
        """Публичный метод очистки ресурсов"""
        try:
            self._cleanup_resources()
        except Exception as e:
            self.logger.error(f"Ошибка очистки MainWindow: {e}")

    # === ДОПОЛНИТЕЛЬНЫЕ СЛУЖЕБНЫЕ МЕТОДЫ ===
    
    def get_window_state(self) -> Dict[str, Any]:
        """Получение состояния окна"""
        try:
            return {
                'geometry': self.root.geometry(),
                'state': self.root.state(),
                'is_loading': self.is_loading,
                'current_file': self.current_file,
                'ui_cache_size': len(self._ui_state_cache),
                'has_info_panel': self.info_panel is not None,
                'ui_components_initialized': self.ui_components is not None
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения состояния окна: {e}")
            return {}

    def restore_window_state(self, state: Dict[str, Any]):
        """Восстановление состояния окна"""
        try:
            if 'geometry' in state:
                self.root.geometry(state['geometry'])
            
            if 'current_file' in state:
                self.current_file = state['current_file']
                if self.current_file:
                    self.update_file_info(self.current_file)
            
            # Восстанавливаем настройки UI
            if 'ui_layout' in state:
                ui_layout = state['ui_layout']
                if 'parameter_panel_ratio' in ui_layout:
                    self._set_parameter_layout(ui_layout['parameter_panel_ratio'])
            
            self.logger.info("Состояние окна восстановлено")
            
        except Exception as e:
            self.logger.error(f"Ошибка восстановления состояния окна: {e}")

    def __str__(self):
        return f"MainWindow(controller={'Set' if self.controller else 'None'}, ui_components={'Init' if self.ui_components else 'None'}, info_panel={'Created' if self.info_panel else 'None'})"

    def __repr__(self):
        return self.__str__()
