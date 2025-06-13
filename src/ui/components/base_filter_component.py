# src/ui/components/base_filter_component.py - НОВЫЙ ФАЙЛ
"""
Базовый компонент фильтрации для устранения всех дублирований
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod


class BaseFilterComponent(ttk.Frame, ABC):
    """Базовый класс для всех компонентов фильтрации без дублирования"""
    
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Единые переменные фильтрации (устраняет дублирование)
        self._filter_vars: Dict[str, Dict[str, tk.BooleanVar]] = {}
        self._special_vars: Dict[str, tk.Variable] = {}
        
        # Callbacks
        self.on_filter_changed: Optional[Callable] = None
        
        # Состояние
        self.is_updating = False
        
        self._initialize_unified_vars()
        self._setup_ui()
    
    def _initialize_unified_vars(self):
        """ЕДИНАЯ инициализация переменных фильтрации"""
        # Основные фильтры
        self._filter_vars = {
            'signal_types': {},
            'lines': {},
            'wagons': {},
            'components': {},
            'hardware': {},
            'systems': {},
            'criticality': {},
            'functions': {}
        }
        
        # ЕДИНСТВЕННЫЕ специальные переменные (устраняет дублирование)
        self._special_vars = {
            'changed_only': tk.BooleanVar(value=False),
            'time_filter_enabled': tk.BooleanVar(value=False),
            'diagnostic_mode': tk.BooleanVar(value=False),
            'emergency_only': tk.BooleanVar(value=False),
            'safety_critical': tk.BooleanVar(value=False)
        }
    
    @abstractmethod
    def _setup_ui(self):
        """Настройка UI - реализуется в наследниках"""
        pass
    
    def create_unified_checkbox_group(self, parent: ttk.Widget, 
                                    title: str, 
                                    filter_category: str,
                                    items: List[str],
                                    columns: int = 3,
                                    use_config: bool = False) -> ttk.LabelFrame:
        """ЕДИНЫЙ метод создания групп чекбоксов с поддержкой конфигурации"""
        try:
            frame = ttk.LabelFrame(parent, text=title, padding="5")
            frame.grid_columnconfigure(0, weight=1)
            
            # Очищаем существующие переменные
            self._filter_vars[filter_category].clear()
            
            # Если используется конфигурация диагностических фильтров
            if use_config and filter_category in ['criticality', 'systems', 'functions']:
                items = self._get_config_items(filter_category)
            
            # Создаем чекбоксы
            for i, item in enumerate(sorted(items)):
                var = tk.BooleanVar(value=True)
                self._filter_vars[filter_category][item] = var
                
                # Получаем цвет и описание из конфигурации
                item_config = self._get_item_config(filter_category, item)
                
                checkbox = ttk.Checkbutton(
                    frame,
                    text=item_config.get('display_name', item),
                    variable=var,
                    command=lambda: self._on_unified_filter_changed()
                )
                
                row = i // columns
                col = i % columns
                checkbox.grid(row=row, column=col, sticky="w", padx=3, pady=1)
                
                # Добавляем tooltip с описанием
                if item_config.get('description'):
                    self._create_tooltip(checkbox, item_config['description'])
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Ошибка создания группы чекбоксов {filter_category}: {e}")
            return ttk.LabelFrame(parent, text=title)
    
    def _get_config_items(self, filter_category: str) -> List[str]:
        """Получение элементов из конфигурации диагностических фильтров"""
        try:
            from ...config.diagnostic_filters_config import (
                CRITICAL_FILTERS, SYSTEM_FILTERS, FUNCTIONAL_FILTERS
            )
            
            if filter_category == 'criticality':
                return list(CRITICAL_FILTERS.keys())
            elif filter_category == 'systems':
                return list(SYSTEM_FILTERS.keys())
            elif filter_category == 'functions':
                return list(FUNCTIONAL_FILTERS.keys())
            
            return []
        except ImportError:
            self.logger.warning("Конфигурация диагностических фильтров недоступна")
            return []
    
    def _get_item_config(self, filter_category: str, item: str) -> Dict[str, Any]:
        """Получение конфигурации элемента"""
        try:
            from ...config.diagnostic_filters_config import (
                CRITICAL_FILTERS, SYSTEM_FILTERS, FUNCTIONAL_FILTERS
            )
            
            config_map = {
                'criticality': CRITICAL_FILTERS,
                'systems': SYSTEM_FILTERS,
                'functions': FUNCTIONAL_FILTERS
            }
            
            config = config_map.get(filter_category, {})
            return config.get(item, {'display_name': item})
            
        except ImportError:
            return {'display_name': item}
    
    def create_special_checkbox(self, parent: ttk.Widget,
                               text: str,
                               var_name: str,
                               command: Optional[Callable] = None) -> ttk.Checkbutton:
        """ЕДИНЫЙ метод создания специальных чекбоксов"""
        if var_name not in self._special_vars:
            self._special_vars[var_name] = tk.BooleanVar(value=False)
        
        checkbox = ttk.Checkbutton(
            parent,
            text=text,
            variable=self._special_vars[var_name],
            command=command or (lambda: self._on_special_filter_changed(var_name))
        )
        
        return checkbox
    
    def _on_unified_filter_changed(self):
        """ЕДИНЫЙ обработчик изменения всех типов фильтров"""
        try:
            if self.is_updating:
                return
            
            # Проверяем специальные режимы
            if self._special_vars['changed_only'].get():
                # В режиме "только изменяемые" не применяем обычные фильтры
                return
            
            if self._special_vars['diagnostic_mode'].get():
                # В диагностическом режиме применяем диагностические фильтры
                self._apply_diagnostic_filters()
                return
            
            # Применяем стандартные фильтры
            self._apply_standard_filters()
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки изменения фильтра: {e}")
    
    def _on_special_filter_changed(self, var_name: str):
        """ЕДИНЫЙ обработчик специальных фильтров"""
        try:
            value = self._special_vars[var_name].get()
            self.logger.info(f"Специальный фильтр '{var_name}' изменен: {value}")
            
            if var_name == 'changed_only':
                self._handle_changed_only_toggle(value)
            elif var_name == 'diagnostic_mode':
                self._handle_diagnostic_mode_toggle(value)
            elif var_name == 'emergency_only':
                self._handle_emergency_filter(value)
            elif var_name == 'safety_critical':
                self._handle_safety_filter(value)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки специального фильтра {var_name}: {e}")
    
    def _apply_changed_only_filter(self):
        """Применение фильтра только изменяемых параметров"""
        if self.controller and hasattr(self.controller, 'apply_changed_parameters_filter'):
            self.controller.apply_changed_parameters_filter()
        elif self.controller and hasattr(self.controller, 'apply_filters'):
            self.controller.apply_filters(changed_only=True)
    
    def _apply_diagnostic_filters(self):
        """Применение диагностических фильтров"""
        if self.controller and hasattr(self.controller, 'apply_diagnostic_filters'):
            diagnostic_criteria = self._get_diagnostic_criteria()
            self.controller.apply_diagnostic_filters(diagnostic_criteria)
    
    def _apply_standard_filters(self):
        """Применение стандартных фильтров"""
        if self.controller and hasattr(self.controller, 'apply_filters'):
            filters = self.get_selected_filters()
            self.controller.apply_filters(**filters)
    
    def _get_diagnostic_criteria(self) -> Dict[str, List[str]]:
        """Получение критериев диагностической фильтрации"""
        criteria = {}
        
        # Собираем диагностические фильтры
        for category in ['criticality', 'systems', 'functions']:
            if category in self._filter_vars:
                selected = [key for key, var in self._filter_vars[category].items() if var.get()]
                if selected:
                    criteria[category] = selected
        
        return criteria
    
    def get_selected_filters(self) -> Dict[str, Any]:
        """ЕДИНЫЙ метод получения всех выбранных фильтров"""
        filters = {}
        
        # Собираем обычные фильтры
        for category, vars_dict in self._filter_vars.items():
            if vars_dict:
                selected = [key for key, var in vars_dict.items() if var.get()]
                if selected:
                    filters[category] = selected
        
        # Добавляем специальные фильтры
        for var_name, var in self._special_vars.items():
            filters[var_name] = var.get()
        
        return filters
    
    def set_filters(self, filters: Dict[str, Any]):
        """ЕДИНЫЙ метод установки фильтров"""
        try:
            self.is_updating = True
            
            # Устанавливаем обычные фильтры
            for category, selected_items in filters.items():
                if category in self._filter_vars and isinstance(selected_items, list):
                    # Сначала сбрасываем все
                    for var in self._filter_vars[category].values():
                        var.set(False)
                    
                    # Затем включаем выбранные
                    for item in selected_items:
                        if item in self._filter_vars[category]:
                            self._filter_vars[category][item].set(True)
            
            # Устанавливаем специальные фильтры
            for var_name in self._special_vars:
                if var_name in filters:
                    self._special_vars[var_name].set(filters[var_name])
            
        finally:
            self.is_updating = False
    
    def reset_filters(self):
        """ЕДИНЫЙ метод сброса всех фильтров"""
        try:
            self.is_updating = True
            
            # Сбрасываем обычные фильтры (включаем все)
            for category_vars in self._filter_vars.values():
                for var in category_vars.values():
                    var.set(True)
            
            # Сбрасываем специальные фильтры
            for var in self._special_vars.values():
                var.set(False)
            
            # Применяем изменения
            self._on_unified_filter_changed()
            
        finally:
            self.is_updating = False
    
    def create_control_buttons(self, parent: ttk.Widget) -> ttk.Frame:
        """ЕДИНЫЙ метод создания кнопок управления"""
        button_frame = ttk.Frame(parent)
        
        ttk.Button(
            button_frame,
            text="Выбрать все",
            command=self._select_all_filters
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="Очистить все",
            command=self._clear_all_filters
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="Сброс",
            command=self.reset_filters
        ).pack(side=tk.LEFT, padx=2)
        
        return button_frame
    
    def _select_all_filters(self):
        """Выбор всех фильтров"""
        try:
            self.is_updating = True
            
            for category_vars in self._filter_vars.values():
                for var in category_vars.values():
                    var.set(True)
            
            self._on_unified_filter_changed()
            
        finally:
            self.is_updating = False
    
    def _clear_all_filters(self):
        """Очистка всех фильтров"""
        try:
            self.is_updating = True
            
            for category_vars in self._filter_vars.values():
                for var in category_vars.values():
                    var.set(False)
            
            self._on_unified_filter_changed()
            
        finally:
            self.is_updating = False
    
    def _handle_changed_only_toggle(self, is_enabled: bool):
        """Обработка переключения режима 'только изменяемые'"""
        if is_enabled:
            # Отключаем другие специальные режимы
            self._special_vars['diagnostic_mode'].set(False)
        
        self._apply_changed_only_filter()
    
    def _handle_diagnostic_mode_toggle(self, is_enabled: bool):
        """Обработка переключения диагностического режима"""
        if is_enabled:
            # Отключаем режим "только изменяемые"
            self._special_vars['changed_only'].set(False)
        
        self._apply_diagnostic_filters()
    
    def _handle_emergency_filter(self, is_enabled: bool):
        """Обработка фильтра аварийных сигналов"""
        if is_enabled:
            # Автоматически включаем критичность "emergency"
            if 'criticality' in self._filter_vars and 'emergency' in self._filter_vars['criticality']:
                self._filter_vars['criticality']['emergency'].set(True)
        
        self._apply_diagnostic_filters()
    
    def _handle_safety_filter(self, is_enabled: bool):
        """Обработка фильтра безопасности"""
        if is_enabled:
            # Автоматически включаем критичность "safety"
            if 'criticality' in self._filter_vars and 'safety' in self._filter_vars['criticality']:
                self._filter_vars['criticality']['safety'].set(True)
        
        self._apply_diagnostic_filters()
    
    def _create_tooltip(self, widget, text: str):
        """Создание всплывающей подсказки"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="lightyellow",
                           relief="solid", borderwidth=1, font=("Arial", 8))
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def set_controller(self, controller):
        """Установка контроллера"""
        self.controller = controller
        self.logger.info(f"Контроллер установлен в {self.__class__.__name__}")
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.controller = None
        self.on_filter_changed = None
        self._filter_vars.clear()
        self._special_vars.clear()
    
    def get_status_info(self) -> Dict[str, Any]:
        """Получение информации о состоянии фильтров"""
        try:
            status = {
                'filter_categories': list(self._filter_vars.keys()),
                'special_filters': list(self._special_vars.keys()),
                'active_filters': {},
                'special_states': {}
            }
            
            # Подсчитываем активные фильтры по категориям
            for category, vars_dict in self._filter_vars.items():
                if vars_dict:
                    active_count = sum(1 for var in vars_dict.values() if var.get())
                    status['active_filters'][category] = {
                        'total': len(vars_dict),
                        'active': active_count,
                        'percentage': (active_count / len(vars_dict) * 100) if vars_dict else 0
                    }
            
            # Состояния специальных фильтров
            for var_name, var in self._special_vars.items():
                status['special_states'][var_name] = var.get()
            
            return status
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса фильтров: {e}")
            return {'error': str(e)}
    
    def export_filter_settings(self) -> Dict[str, Any]:
        """Экспорт настроек фильтров"""
        try:
            settings = {
                'timestamp': tk.datetime.now().isoformat() if hasattr(tk, 'datetime') else 'unknown',
                'component_type': self.__class__.__name__,
                'filter_settings': self.get_selected_filters(),
                'status_info': self.get_status_info()
            }
            
            return settings
            
        except Exception as e:
            self.logger.error(f"Ошибка экспорта настроек фильтров: {e}")
            return {'error': str(e)}
    
    def import_filter_settings(self, settings: Dict[str, Any]) -> bool:
        """Импорт настроек фильтров"""
        try:
            if 'filter_settings' in settings:
                self.set_filters(settings['filter_settings'])
                self.logger.info(f"Настройки фильтров импортированы в {self.__class__.__name__}")
                return True
            else:
                self.logger.warning("Настройки фильтров не найдены в импортируемых данных")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка импорта настроек фильтров: {e}")
            return False
    
    def __str__(self):
        return f"{self.__class__.__name__}(categories={len(self._filter_vars)}, special={len(self._special_vars)})"
    
    def __repr__(self):
        return self.__str__()
