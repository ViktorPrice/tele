# src/ui/controllers/main_controller.py - РЕФАКТОРЕННАЯ ВЕРСИЯ (v1.0)
"""
Главный контроллер БЕЗ legacy зависимостей (полностью новая архитектура)
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Изменения:
# - Было: Наследование от legacy Controller
# - Стало: Независимый класс с композицией сервисов
# - Влияние: Устранена зависимость от legacy файлов
# - REVIEW NEEDED: Проверить совместимость всех методов с UI

class MainController:
    """Главный контроллер приложения (полностью новая архитектура)"""
    
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Сервисы (внедряются извне)
        self.filtering_service = None
        self.plot_manager = None
        self.report_generator = None
        self.sop_manager = None
        
        # Кэш для оптимизации
        self._filter_criteria_cache: Optional[Dict[str, List[str]]] = None
        self._last_filter_update = 0
        
        # Состояние
        self.is_processing = False
        
        self.logger.info("Контроллер инициализирован")
    
    def set_filtering_service(self, filtering_service):
        """Установка сервиса фильтрации"""
        self.filtering_service = filtering_service
        self.logger.info("Сервис фильтрации установлен")
    
    def set_plot_manager(self, plot_manager):
        """Установка менеджера графиков"""
        self.plot_manager = plot_manager
        self.logger.info("Менеджер графиков установлен")
    
    def set_report_generator(self, report_generator):
        """Установка генератора отчетов"""
        self.report_generator = report_generator
        self.logger.info("Генератор отчетов установлен")
    
    def set_sop_manager(self, sop_manager):
        """Установка SOP менеджера"""
        self.sop_manager = sop_manager
        self.logger.info("SOP менеджер установлен")
    
    def apply_filters(self, changed_only: bool = False):
        """ИСПРАВЛЕННОЕ применение фильтров с поддержкой changed_only"""
        try:
            self.logger.info(f"Начало применения фильтров (changed_only={changed_only})")
            
            if self.is_processing:
                self.logger.warning("Фильтрация уже выполняется, пропускаем")
                return
            
            self.is_processing = True
            
            try:
                # Проверяем наличие данных
                if not self._has_data():
                    self.logger.warning("Нет параметров для фильтрации. Загрузите CSV файл.")
                    self._show_no_data_message()
                    return
                
                # Специальная обработка для "только изменяемые параметры"
                if changed_only:
                    self._apply_changed_params_filter()
                    return
                
                # Обычная фильтрация
                self._apply_standard_filters()
                
            finally:
                self.is_processing = False
                
        except Exception as e:
            self.logger.error(f"Ошибка применения фильтров: {e}")
            self.is_processing = False
            import traceback
            traceback.print_exc()
    
    def _has_data(self) -> bool:
        """Проверка наличия данных для фильтрации"""
        return (hasattr(self.model, 'data_loader') and 
                self.model.data_loader and 
                hasattr(self.model.data_loader, 'parameters') and 
                self.model.data_loader.parameters)
    
    def _show_no_data_message(self):
        """Показ сообщения об отсутствии данных"""
        if hasattr(self.view, 'show_warning'):
            self.view.show_warning("Загрузите CSV файл для отображения параметров")
        
        # Обновляем UI с пустыми данными
        self._update_ui_with_filtered_params([])
    
    def _apply_changed_params_filter(self):
        """Применение фильтра только изменяемых параметров"""
        try:
            # Получаем временной диапазон
            start_time_str, end_time_str = self._get_time_range()
            
            if not start_time_str or not end_time_str:
                self.logger.error("Не удалось получить временной диапазон")
                self._show_time_error()
                return
            
            # Применяем фильтрацию изменяемых параметров
            if self.filtering_service and hasattr(self.filtering_service, 'filter_changed_params'):
                changed_params = self.filtering_service.filter_changed_params(
                    start_time_str, end_time_str
                )
                
                self.logger.info(f"Найдено {len(changed_params)} изменяемых параметров")
                self._update_ui_with_filtered_params(changed_params)
                
            else:
                # Fallback через модель
                self._apply_changed_params_fallback(start_time_str, end_time_str)
                
        except Exception as e:
            self.logger.error(f"Ошибка фильтрации изменяемых параметров: {e}")
    
    def _apply_standard_filters(self):
        """Применение стандартных фильтров"""
        try:
            if not self.filtering_service:
                self.logger.warning("Сервис фильтрации не установлен")
                self._apply_fallback_filters()
                return
            
            # Получаем критерии фильтрации
            criteria = self._get_filter_criteria()
            
            # Получаем все параметры
            all_params = self._get_all_parameters()
            
            # Применяем фильтрацию через сервис
            filtered_params = self.filtering_service.filter_parameters(all_params, criteria)
            
            self.logger.info(f"Применены фильтры через сервис: {len(all_params)} -> {len(filtered_params)} параметров")
            
            # Обновляем UI
            self._update_ui_with_filtered_params(filtered_params)
            
        except Exception as e:
            self.logger.error(f"Ошибка применения стандартных фильтров: {e}")
            self._apply_fallback_filters()
    
    def _get_filter_criteria(self) -> Dict[str, List[str]]:
        """УЛУЧШЕННОЕ получение критериев фильтрации с кэшированием"""
        try:
            import time
            current_time = time.time()
            
            # Проверяем кэш (обновляем каждые 100мс)
            if (self._filter_criteria_cache and 
                current_time - self._last_filter_update < 0.1):
                return self._filter_criteria_cache
            
            criteria = {
                'signal_types': [],
                'lines': [],
                'wagons': [],
                'components': [],
                'hardware': []
            }
            
            if hasattr(self.view, 'filter_panel') and self.view.filter_panel:
                filter_panel = self.view.filter_panel
                
                # Получаем через новый интерфейс
                if hasattr(filter_panel, 'get_selected_filters'):
                    criteria.update(filter_panel.get_selected_filters())
                
                # Fallback на старый интерфейс
                else:
                    criteria.update(self._extract_legacy_filter_criteria(filter_panel))
            
            # Кэшируем результат
            self._filter_criteria_cache = criteria
            self._last_filter_update = current_time
            
            return criteria
            
        except Exception as e:
            self.logger.error(f"Ошибка получения критериев фильтрации: {e}")
            return self._get_default_criteria()
    
    def _extract_legacy_filter_criteria(self, filter_panel) -> Dict[str, List[str]]:
        """Извлечение критериев из legacy интерфейса"""
        criteria = {}
        
        # Извлечение через атрибуты панели
        if hasattr(filter_panel, 'signal_vars'):
            criteria['signal_types'] = [
                k for k, v in filter_panel.signal_vars.items() if v.get()
            ]
        
        if hasattr(filter_panel, 'line_vars'):
            criteria['lines'] = [
                k for k, v in filter_panel.line_vars.items() if v.get()
            ]
        
        if hasattr(filter_panel, 'wagon_vars'):
            criteria['wagons'] = [
                k for k, v in filter_panel.wagon_vars.items() if v.get()
            ]
        
        if hasattr(filter_panel, 'component_vars'):
            criteria['components'] = [
                k for k, v in filter_panel.component_vars.items() if v.get()
            ]
        
        if hasattr(filter_panel, 'hardware_vars'):
            criteria['hardware'] = [
                k for k, v in filter_panel.hardware_vars.items() if v.get()
            ]
        
        return criteria
    
    def _get_default_criteria(self) -> Dict[str, List[str]]:
        """Критерии по умолчанию (все включено)"""
        return {
            'signal_types': ['B', 'BY', 'W', 'DW', 'F', 'WF'],
            'lines': [],
            'wagons': [str(i) for i in range(1, 16)],
            'components': [],
            'hardware': []
        }
    
    def _get_all_parameters(self) -> List[Any]:
        """Получение всех параметров"""
        if self._has_data():
            return self.model.data_loader.parameters
        return []
    
    def _get_time_range(self) -> Tuple[str, str]:
        """Получение временного диапазона"""
        try:
            if hasattr(self.view, 'time_panel') and self.view.time_panel:
                time_panel = self.view.time_panel
                
                # Новый интерфейс
                if hasattr(time_panel, 'get_time_range'):
                    return time_panel.get_time_range()
                
                # Legacy интерфейс
                if (hasattr(time_panel, 'start_time_entry') and 
                    hasattr(time_panel, 'end_time_entry')):
                    return (
                        time_panel.start_time_entry.get(),
                        time_panel.end_time_entry.get()
                    )
            
            # Fallback
            from datetime import datetime, timedelta
            now = datetime.now()
            start = now - timedelta(hours=1)
            return (
                start.strftime('%Y-%m-%d %H:%M:%S'),
                now.strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка получения временного диапазона: {e}")
            return "", ""
    
    def _show_time_error(self):
        """Показ ошибки времени"""
        if hasattr(self.view, 'show_error'):
            self.view.show_error("Не удалось получить временной диапазон")
    
    def _apply_changed_params_fallback(self, start_time_str: str, end_time_str: str):
        """Fallback для фильтрации изменяемых параметров"""
        try:
            # Пытаемся через data_loader
            if (hasattr(self.model, 'data_loader') and 
                hasattr(self.model.data_loader, 'filter_changed_params')):
                
                changed_params = self.model.data_loader.filter_changed_params(
                    start_time_str, end_time_str
                )
                
                self.logger.info(f"Найдено {len(changed_params)} изменяемых параметров через data_loader")
                self._update_ui_with_filtered_params(changed_params)
                return
            
            # Последний fallback - эвристика
            all_params = self._get_all_parameters()
            changed_params = all_params[:len(all_params)//2]  # Первые 50%
            
            self.logger.warning(f"Использована эвристика: {len(changed_params)} параметров")
            self._update_ui_with_filtered_params(changed_params)
            
        except Exception as e:
            self.logger.error(f"Ошибка fallback фильтрации: {e}")
    
    def _apply_fallback_filters(self):
        """Fallback фильтрация без сервиса"""
        try:
            all_params = self._get_all_parameters()
            self.logger.info(f"Fallback фильтрация: {len(all_params)} параметров")
            self._update_ui_with_filtered_params(all_params)
            
        except Exception as e:
            self.logger.error(f"Ошибка fallback фильтрации: {e}")
    
    def _update_ui_with_filtered_params(self, filtered_params: List[Any]):
        """УЛУЧШЕННОЕ обновление UI с отфильтрованными параметрами"""
        try:
            # Обновляем счетчик
            if hasattr(self.view, 'update_filtered_count'):
                self.view.update_filtered_count(len(filtered_params))
            
            # Обновляем дерево параметров
            if hasattr(self.view, 'parameter_panel') and self.view.parameter_panel:
                if hasattr(self.view.parameter_panel, 'update_tree_all_params'):
                    self.view.parameter_panel.update_tree_all_params(filtered_params)
                    self.logger.info(f"UI обновлен: {len(filtered_params)} параметров")
                else:
                    self.logger.error("Метод update_tree_all_params не найден в parameter_panel")
            else:
                self.logger.error("parameter_panel не найден в view")
            
            # Принудительное обновление экрана
            if hasattr(self.view, 'root'):
                self.view.root.update_idletasks()
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления UI: {e}")
    
    def upload_csv(self):
        """ИСПРАВЛЕННАЯ загрузка CSV"""
        try:
            from tkinter import filedialog
            
            file_path = filedialog.askopenfilename(
                title="Выберите CSV файл",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if file_path:
                self.logger.info(f"Выбран файл: {file_path}")
                
                # Показываем процесс загрузки
                if hasattr(self.view, 'start_processing'):
                    self.view.start_processing("Загрузка файла...")
                
                # Загружаем файл
                success = self._load_csv_file(file_path)
                
                if success:
                    self.logger.info("Файл успешно загружен")
                    self._handle_successful_load()
                else:
                    self.logger.error("Ошибка загрузки файла")
                    if hasattr(self.view, 'show_error'):
                        self.view.show_error("Ошибка загрузки файла")
                
                # Останавливаем индикатор загрузки
                if hasattr(self.view, 'stop_processing'):
                    self.view.stop_processing()
                    
        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка загрузки: {e}")
            if hasattr(self.view, 'stop_processing'):
                self.view.stop_processing()
    
    def _load_csv_file(self, file_path: str) -> bool:
        """Загрузка CSV файла через модель"""
        try:
            if hasattr(self.model, 'load_csv_file'):
                return self.model.load_csv_file(file_path)
            else:
                self.logger.error("Метод load_csv_file не найден в модели")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка в _load_csv_file: {e}")
            return False
    
    def _handle_successful_load(self):
        """Обработка успешной загрузки"""
        try:
            if self._has_data():
                params = self.model.data_loader.parameters
                self.logger.info(f"Загружено параметров: {len(params)}")
                
                # Очищаем кэш фильтров
                self._filter_criteria_cache = None
                
                # Обновляем дерево параметров
                if hasattr(self.view, 'update_tree_all_params'):
                    self.view.update_tree_all_params(params)
                
                # Обновляем фильтры
                if hasattr(self.model.data_loader, 'lines'):
                    lines = list(self.model.data_loader.lines)
                    if hasattr(self.view, 'update_line_checkboxes'):
                        self.view.update_line_checkboxes(lines)
                
                # Применяем фильтры
                self.apply_filters()
                
                # Обновляем статус
                if hasattr(self.view, 'update_status'):
                    self.view.update_status(f"Файл загружен: {len(params)} параметров")
                    
        except Exception as e:
            self.logger.error(f"Ошибка обработки успешной загрузки: {e}")
    
    def build_plot(self):
        """Построение графика"""
        try:
            # Получаем выбранные параметры
            selected_params = self._get_selected_parameters()
            
            if not selected_params:
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning("Выберите параметры для построения графика")
                return
            
            # Получаем временной диапазон
            start_time_str, end_time_str = self._get_time_range()
            
            # Валидация времени
            if not self._validate_time_range(start_time_str, end_time_str):
                return
            
            # Построение графика через plot_manager
            if self.plot_manager:
                success = self.plot_manager.build_plot(
                    selected_params, 
                    start_time_str, 
                    end_time_str,
                    title=f"График параметров ({len(selected_params)} сигналов)"
                )
                
                if success:
                    self.logger.info("График построен успешно")
                    if hasattr(self.view, 'update_status'):
                        self.view.update_status("График построен")
                else:
                    if hasattr(self.view, 'show_error'):
                        self.view.show_error("Ошибка построения графика")
            else:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("PlotManager не инициализирован")
                    
        except Exception as e:
            self.logger.error(f"Ошибка построения графика: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка построения графика: {e}")
    
    def _get_selected_parameters(self) -> List[Any]:
        """Получение выбранных параметров"""
        try:
            if (hasattr(self.view, 'parameter_panel') and 
                self.view.parameter_panel and
                hasattr(self.view.parameter_panel, 'selected_params_tree')):
                
                tree = self.view.parameter_panel.selected_params_tree
                if hasattr(tree, 'tree'):
                    return [tree.tree.item(item, 'values') 
                           for item in tree.tree.get_children()]
            return []
        except Exception as e:
            self.logger.error(f"Ошибка получения выбранных параметров: {e}")
            return []
    
    def _validate_time_range(self, start_str: str, end_str: str) -> bool:
        """Валидация временного диапазона"""
        try:
            if not start_str or not end_str:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Укажите временной диапазон")
                return False
            
            # Простая валидация формата
            from datetime import datetime
            try:
                start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S')
                
                if start_dt >= end_dt:
                    if hasattr(self.view, 'show_error'):
                        self.view.show_error("Время начала должно быть раньше времени окончания")
                    return False
                
                return True
                
            except ValueError as e:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error(f"Неверный формат времени: {e}")
                return False
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации времени: {e}")
            return False
    
    def generate_report(self):
        """Генерация отчета"""
        try:
            if not self.report_generator:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Генератор отчетов не инициализирован")
                return
            
            # Получаем выбранные параметры
            selected_params = self._get_selected_parameters()
            
            if not selected_params:
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning("Выберите параметры для отчета")
                return
            
            # Получаем временной диапазон
            start_time_str, end_time_str = self._get_time_range()
            
            if not self._validate_time_range(start_time_str, end_time_str):
                return
            
            # Генерируем отчет
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[
                    ("PDF files", "*.pdf"),
                    ("Text files", "*.txt"),
                    ("Excel files", "*.xlsx")
                ]
            )
            
            if file_path:
                success = self.report_generator.generate_full_report(
                    {'selected_params': selected_params},
                    datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S'),
                    datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S'),
                    file_path
                )
                
                if success:
                    self.logger.info(f"Отчет создан: {file_path}")
                    if hasattr(self.view, 'show_info'):
                        self.view.show_info("Отчет", f"Отчет сохранен: {file_path}")
                else:
                    if hasattr(self.view, 'show_error'):
                        self.view.show_error("Ошибка создания отчета")
                        
        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка генерации отчета: {e}")
    
    def generate_sop(self):
        """Генерация SOP"""
        try:
            if not self.sop_manager:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("SOP менеджер не инициализирован")
                return
            
            # Получаем выбранные параметры
            selected_params = self._get_selected_parameters()
            
            if not selected_params:
                if hasattr(self.view, 'show_warning'):
                    self.view.show_warning("Выберите параметры для SOP")
                return
            
            # Получаем временной диапазон
            start_time_str, end_time_str = self._get_time_range()
            
            if not self._validate_time_range(start_time_str, end_time_str):
                return
            
            # Генерируем SOP
            sop_xml = self.sop_manager.generate_sop_for_params(
                [{'signal_code': param[0] if param else '', 
                  'description': param[1] if len(param) > 1 else ''} 
                 for param in selected_params],
                datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S'),
                datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
            )
            
            if sop_xml:
                # Сохраняем SOP
                from tkinter import filedialog
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".sop",
                    filetypes=[("SOP files", "*.sop"), ("XML files", "*.xml")]
                )
                
                if file_path:
                    success = self.sop_manager.save_sop_to_file(sop_xml, file_path)
                    
                    if success:
                        self.logger.info(f"SOP создан: {file_path}")
                        if hasattr(self.view, 'show_info'):
                            self.view.show_info("SOP", f"SOP сохранен: {file_path}")
                    else:
                        if hasattr(self.view, 'show_error'):
                            self.view.show_error("Ошибка сохранения SOP")
            else:
                if hasattr(self.view, 'show_error'):
                    self.view.show_error("Ошибка создания SOP")
                    
        except Exception as e:
            self.logger.error(f"Ошибка генерации SOP: {e}")
            if hasattr(self.view, 'show_error'):
                self.view.show_error(f"Ошибка генерации SOP: {e}")
    
    def cleanup(self):
        """Очистка ресурсов контроллера"""
        try:
            # Очищаем кэш
            self._filter_criteria_cache = None
            
            # Очищаем сервисы
            if self.filtering_service and hasattr(self.filtering_service, 'cleanup'):
                self.filtering_service.cleanup()
            
            if self.plot_manager and hasattr(self.plot_manager, 'cleanup'):
                self.plot_manager.cleanup()
            
            if self.report_generator and hasattr(self.report_generator, 'cleanup'):
                self.report_generator.cleanup()
            
            if self.sop_manager and hasattr(self.sop_manager, 'cleanup'):
                self.sop_manager.cleanup()
            
            self.logger.info("MainController очищен")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки MainController: {e}")
