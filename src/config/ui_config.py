# src/config/ui_config.py - НОВЫЙ ФАЙЛ
"""
Конфигурация UI компонентов для устранения дублирований и приоритетной логики
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


# === КОНФИГУРАЦИЯ UI КОМПОНЕНТОВ ===

UI_COMPONENT_REGISTRY = {
    'time_panel': {
        'has_changed_only_checkbox': True,
        'priority_for_changed_filter': True,
        'class_name': 'TimePanel',
        'module_path': 'src.ui.components.time_panel',
        'description': 'Панель управления временным диапазоном с приоритетной логикой',
        'features': ['time_range_control', 'changed_params_priority', 'quick_range_buttons'],
        'dependencies': ['main_controller', 'data_model']
    },
    'filter_panel': {
        'has_changed_only_checkbox': False,  # Убираем дублирование
        'priority_for_changed_filter': False,
        'sync_with_time_panel': True,
        'class_name': 'FilterPanel',
        'module_path': 'src.ui.components.filter_panel',
        'description': 'Панель фильтров без дублирования чекбокса изменяемых параметров',
        'features': ['signal_type_filters', 'line_filters', 'wagon_filters', 'component_filters'],
        'dependencies': ['main_controller', 'time_panel_sync']
    },
    'parameter_panel': {
        'class_name': 'ParameterPanel',
        'module_path': 'src.ui.components.parameter_panel',
        'description': 'Панель отображения параметров',
        'features': ['parameter_tree', 'selection', 'search'],
        'dependencies': ['main_controller']
    },
    'action_panel': {
        'class_name': 'ActionPanel',
        'module_path': 'src.ui.components.action_panel',
        'description': 'Панель действий пользователя',
        'features': ['csv_upload', 'plot_build', 'report_generate'],
        'dependencies': ['main_controller']
    },
    'plot_panel': {
        'class_name': 'PlotVisualizationPanel',
        'module_path': 'src.ui.components.plot_visualization_panel',
        'description': 'Панель визуализации графиков',
        'features': ['plot_display', 'zoom', 'export'],
        'dependencies': ['plot_manager']
    },
    'diagnostic_panel': {
        'class_name': 'DiagnosticFilterPanel',
        'module_path': 'src.ui.components.diagnostic_filter_panel',
        'description': 'Панель диагностических фильтров',
        'features': ['criticality_filters', 'system_filters', 'function_filters'],
        'dependencies': ['main_controller', 'diagnostic_filters_config'],
        'optional': True  # Может отсутствовать в некоторых конфигурациях
    }
}

# === ПРИОРИТЕТЫ ФИЛЬТРАЦИИ ===

FILTER_PRIORITIES = {
    'changed_only': {
        'priority': 1,  # Высший приоритет
        'owner_component': 'time_panel',
        'description': 'Фильтр изменяемых параметров имеет приоритет над всеми остальными',
        'blocks_other_filters': True,
        'auto_apply': True
    },
    'diagnostic': {
        'priority': 2,
        'owner_component': 'diagnostic_panel',
        'description': 'Диагностические фильтры',
        'blocks_other_filters': False,
        'auto_apply': False
    },
    'standard': {
        'priority': 3,
        'owner_component': 'filter_panel',
        'description': 'Стандартные фильтры по типам, линиям, вагонам',
        'blocks_other_filters': False,
        'auto_apply': True
    }
}

# === КОНФИГУРАЦИЯ ИНТЕГРАЦИИ С MAIN.PY ===

MAIN_INTEGRATION_CONFIG = {
    'dependency_injection': {
        'controller_setters': {
            'time_panel': 'set_time_panel',
            'filter_panel': 'set_filter_panel',
            'parameter_panel': 'set_parameter_panel',
            'action_panel': 'set_action_panel'
        },
        'fallback_attributes': {
            'filter_panel': 'filterpanel',
            'parameter_panel': 'parameterpanel',
            'action_panel': 'actionpanel'
        },
        'ui_components_setup': True,
        'controller_setup_order': [
            'ui_components',
            'time_panel',
            'filter_panel', 
            'parameter_panel',
            'action_panel'
        ]
    },
    'priority_setup': {
        'changed_params_priority_component': 'time_panel',
        'disable_duplicated_checkboxes': ['filter_panel'],
        'sync_components': [
            {
                'source': 'time_panel',
                'target': 'filter_panel',
                'sync_type': 'priority_override'
            }
        ]
    }
}

# === КОНФИГУРАЦИЯ LAYOUT ===

LAYOUT_CONFIG = {
    'compact_mode': {
        'enabled': True,
        'components': ['time_panel', 'filter_panel', 'parameter_panel'],
        'diagnostic_panel_visible': False,
        'description': 'Компактный режим для небольших экранов'
    },
    'standard_mode': {
        'enabled': True,
        'components': ['time_panel', 'filter_panel', 'parameter_panel', 'action_panel', 'plot_panel'],
        'diagnostic_panel_visible': True,
        'description': 'Стандартный режим со всеми панелями'
    },
    'diagnostic_mode': {
        'enabled': True,
        'components': ['time_panel', 'diagnostic_panel', 'parameter_panel'],
        'filter_panel_disabled': True,
        'description': 'Режим диагностики с приоритетом диагностических фильтров'
    }
}

# === КОНФИГУРАЦИЯ СОБЫТИЙ ===

UI_EVENTS_CONFIG = {
    'priority_events': [
        'changed_params_filter_applied',
        'time_range_changed',
        'priority_mode_activated'
    ],
    'standard_events': [
        'filters_applied',
        'parameters_updated',
        'data_loaded'
    ],
    'event_handlers': {
        'changed_params_filter_applied': {
            'components': ['filter_panel', 'parameter_panel'],
            'action': 'sync_priority_state'
        },
        'time_range_changed': {
            'components': ['filter_panel'],
            'action': 'check_priority_mode'
        }
    }
}

# === КОНФИГУРАЦИЯ СОВМЕСТИМОСТИ ===

COMPATIBILITY_CONFIG = {
    'legacy_support': {
        'enabled': True,
        'deprecated_methods': [
            '_get_time_panel',
            '_get_filter_panel', 
            '_get_parameter_panel',
            '_get_action_panel'
        ],
        'replacement_method': 'get_ui_component',
        'warning_level': 'WARNING'
    },
    'fallback_strategies': {
        'ui_component_not_found': 'log_warning_and_continue',
        'controller_method_missing': 'use_setattr_fallback',
        'dependency_injection_failed': 'continue_with_warnings'
    }
}

# === НАСТРОЙКИ ПРОИЗВОДИТЕЛЬНОСТИ ===

PERFORMANCE_CONFIG = {
    'ui_update_throttling': {
        'enabled': True,
        'min_update_interval_ms': 100,
        'batch_updates': True
    },
    'component_caching': {
        'enabled': True,
        'cache_ui_components': True,
        'cache_ttl_seconds': 300
    },
    'lazy_loading': {
        'enabled': True,
        'components': ['diagnostic_panel', 'plot_panel'],
        'load_on_demand': True
    }
}

# === НАСТРОЙКИ ОТЛАДКИ ===

DEBUG_CONFIG = {
    'ui_structure_logging': {
        'enabled': True,
        'log_component_discovery': True,
        'log_dependency_injection': True,
        'log_priority_changes': True
    },
    'validation': {
        'validate_component_availability': True,
        'validate_controller_methods': True,
        'validate_priority_consistency': True
    },
    'diagnostics': {
        'component_health_check': True,
        'performance_monitoring': True,
        'memory_usage_tracking': False
    }
}

# === ФУНКЦИИ КОНФИГУРАЦИИ ===

def get_component_config(component_name: str) -> Optional[Dict[str, Any]]:
    """Получение конфигурации компонента"""
    return UI_COMPONENT_REGISTRY.get(component_name)

def get_priority_config(filter_type: str) -> Optional[Dict[str, Any]]:
    """Получение конфигурации приоритета фильтра"""
    return FILTER_PRIORITIES.get(filter_type)

def get_layout_config(mode: str) -> Optional[Dict[str, Any]]:
    """Получение конфигурации layout"""
    return LAYOUT_CONFIG.get(mode)

def is_component_optional(component_name: str) -> bool:
    """Проверка является ли компонент опциональным"""
    config = get_component_config(component_name)
    return config.get('optional', False) if config else True

def get_component_dependencies(component_name: str) -> List[str]:
    """Получение зависимостей компонента"""
    config = get_component_config(component_name)
    return config.get('dependencies', []) if config else []

def has_priority_for_changed_filter(component_name: str) -> bool:
    """Проверка имеет ли компонент приоритет для фильтра изменяемых параметров"""
    config = get_component_config(component_name)
    return config.get('priority_for_changed_filter', False) if config else False

def should_sync_with_time_panel(component_name: str) -> bool:
    """Проверка нужна ли синхронизация с time_panel"""
    config = get_component_config(component_name)
    return config.get('sync_with_time_panel', False) if config else False

def get_controller_setter_method(component_name: str) -> Optional[str]:
    """Получение метода setter для контроллера"""
    setters = MAIN_INTEGRATION_CONFIG['dependency_injection']['controller_setters']
    return setters.get(component_name)

def get_fallback_attribute_name(component_name: str) -> Optional[str]:
    """Получение fallback имени атрибута"""
    fallbacks = MAIN_INTEGRATION_CONFIG['dependency_injection']['fallback_attributes']
    return fallbacks.get(component_name)

def get_setup_order() -> List[str]:
    """Получение порядка настройки компонентов"""
    return MAIN_INTEGRATION_CONFIG['dependency_injection']['controller_setup_order']

def validate_ui_config() -> Dict[str, Any]:
    """Валидация конфигурации UI"""
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'info': []
    }
    
    # Проверяем приоритеты
    priority_owners = {}
    for filter_type, config in FILTER_PRIORITIES.items():
        owner = config.get('owner_component')
        if owner:
            if owner not in UI_COMPONENT_REGISTRY:
                validation_result['errors'].append(
                    f"Приоритетный компонент '{owner}' для фильтра '{filter_type}' не найден в реестре"
                )
                validation_result['is_valid'] = False
            else:
                priority_owners[filter_type] = owner
    
    # Проверяем дублирование чекбоксов
    changed_only_components = []
    for comp_name, config in UI_COMPONENT_REGISTRY.items():
        if config.get('has_changed_only_checkbox', False):
            changed_only_components.append(comp_name)
    
    if len(changed_only_components) > 1:
        validation_result['errors'].append(
            f"Дублирование чекбокса 'changed_only' в компонентах: {changed_only_components}"
        )
        validation_result['is_valid'] = False
    elif len(changed_only_components) == 1:
        validation_result['info'].append(
            f"Чекбокс 'changed_only' находится в компоненте: {changed_only_components[0]}"
        )
    
    # Проверяем зависимости
    for comp_name, config in UI_COMPONENT_REGISTRY.items():
        dependencies = config.get('dependencies', [])
        for dep in dependencies:
            if dep.endswith('_controller') or dep.endswith('_manager'):
                continue  # Внешние зависимости
            if dep not in UI_COMPONENT_REGISTRY:
                validation_result['warnings'].append(
                    f"Компонент '{comp_name}' зависит от '{dep}', который не найден в реестре"
                )
    
    return validation_result

def export_ui_config() -> Dict[str, Any]:
    """Экспорт полной конфигурации UI"""
    return {
        'timestamp': datetime.now().isoformat(),
        'version': '1.0',
        'component_registry': UI_COMPONENT_REGISTRY,
        'filter_priorities': FILTER_PRIORITIES,
        'main_integration': MAIN_INTEGRATION_CONFIG,
        'layout_config': LAYOUT_CONFIG,
        'events_config': UI_EVENTS_CONFIG,
        'compatibility_config': COMPATIBILITY_CONFIG,
        'performance_config': PERFORMANCE_CONFIG,
        'debug_config': DEBUG_CONFIG,
        'validation_result': validate_ui_config()
    }

def import_ui_config(config_data: Dict[str, Any]) -> bool:
    """Импорт конфигурации UI"""
    try:
        global UI_COMPONENT_REGISTRY, FILTER_PRIORITIES, MAIN_INTEGRATION_CONFIG
        global LAYOUT_CONFIG, UI_EVENTS_CONFIG, COMPATIBILITY_CONFIG
        global PERFORMANCE_CONFIG, DEBUG_CONFIG
        
        if 'component_registry' in config_data:
            UI_COMPONENT_REGISTRY.update(config_data['component_registry'])
        
        if 'filter_priorities' in config_data:
            FILTER_PRIORITIES.update(config_data['filter_priorities'])
        
        if 'main_integration' in config_data:
            MAIN_INTEGRATION_CONFIG.update(config_data['main_integration'])
        
        # Валидируем после импорта
        validation = validate_ui_config()
        return validation['is_valid']
        
    except Exception:
        return False

# === КОНФИГУРАЦИЯ ДЛЯ ИНТЕГРАЦИИ С MAIN.PY ===

def create_application_context_config() -> Dict[str, Any]:
    """Конфигурация для функции create_application_context в main.py"""
    return {
        'priority_setup_required': True,
        'changed_params_priority_component': 'time_panel',
        'components_to_disable_changed_checkbox': ['filter_panel'],
        'dependency_injection_order': get_setup_order(),
        'fallback_strategies': COMPATIBILITY_CONFIG['fallback_strategies'],
        'validation_required': DEBUG_CONFIG['validation']['validate_component_availability']
    }

def get_main_py_integration_instructions() -> Dict[str, Any]:
    """Инструкции для интеграции с main.py"""
    return {
        'setup_instructions': [
            "1. Используйте get_component_config() для получения конфигурации компонентов",
            "2. Применяйте has_priority_for_changed_filter() для настройки приоритетов",
            "3. Используйте get_controller_setter_method() для dependency injection",
            "4. Применяйте validate_ui_config() для проверки конфигурации"
        ],
        'priority_setup_code': """
# В create_application_context добавить:
if has_priority_for_changed_filter('time_panel'):
    if hasattr(mainwindow.ui_components, 'time_panel'):
        time_panel = mainwindow.ui_components.time_panel
        if hasattr(time_panel, 'set_changed_params_priority'):
            time_panel.set_changed_params_priority(True)

# Отключить дублированные чекбоксы
for comp_name in ['filter_panel']:
    if not has_priority_for_changed_filter(comp_name):
        comp = getattr(mainwindow.ui_components, comp_name, None)
        if comp and hasattr(comp, 'disable_changed_only_checkbox'):
            comp.disable_changed_only_checkbox()
        """,
        'dependency_injection_code': """
# Заменить ручную настройку на:
for comp_name in get_setup_order():
    if hasattr(mainwindow.ui_components, comp_name):
        component = getattr(mainwindow.ui_components, comp_name)
        setter_method = get_controller_setter_method(comp_name)
        
        if setter_method and hasattr(maincontroller, setter_method):
            getattr(maincontroller, setter_method)(component)
        else:
            # Fallback
            fallback_attr = get_fallback_attribute_name(comp_name)
            if fallback_attr:
                setattr(maincontroller.view, fallback_attr, component)
        """
    }

# === ЭКСПОРТ ОСНОВНЫХ КОНФИГУРАЦИЙ ===

__all__ = [
    'UI_COMPONENT_REGISTRY',
    'FILTER_PRIORITIES', 
    'MAIN_INTEGRATION_CONFIG',
    'LAYOUT_CONFIG',
    'get_component_config',
    'get_priority_config',
    'has_priority_for_changed_filter',
    'should_sync_with_time_panel',
    'get_controller_setter_method',
    'validate_ui_config',
    'create_application_context_config',
    'get_main_py_integration_instructions'
]
