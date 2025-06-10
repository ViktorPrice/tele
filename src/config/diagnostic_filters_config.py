# src/config/diagnostic_filters_config.py
"""
Конфигурация диагностических фильтров для анализа телеметрии электропоезда
"""
from typing import Dict, List, Any

# Фильтры по критичности
CRITICAL_FILTERS = {
    'emergency': {
        'patterns': ['EMERGENCY', 'EMER_', 'FAULT', 'FAIL', 'ERR_', 'ALARM', 'FIRE'],
        'color': '#FF0000',  # Красный
        'priority': 1,
        'description': 'Аварийные ситуации и критические неисправности',
        'examples': ['B_EMERGENCY_BRAKING', 'B_FIRE_ALARM', 'B_BCU_FAULT']
    },
    'safety': {
        'patterns': ['SAFETY_LOOP', 'FIRE_', 'SECURITY_', 'GUARD_', 'PROTECTION'],
        'color': '#FF6600',  # Оранжевый
        'priority': 2,
        'description': 'Системы безопасности и защиты',
        'examples': ['BY_SECURITY_LOOP_N1', 'B_FIRE_INDICATOR', 'B_SAFETY_LOOP_OK']
    },
    'power_critical': {
        'patterns': ['3000V', 'QF1_', 'PSN_', 'PANTO_', 'VOLTAGE_FAULT', 'CURRENT_FAULT'],
        'color': '#FF9900',  # Желто-оранжевый
        'priority': 3,
        'description': 'Критические неисправности энергосистемы',
        'examples': ['B_WAGON_3000V_OK', 'B_QF1_EMERGENCY', 'F_U3000']
    },
    'brake_critical': {
        'patterns': ['BCU_FAULT', 'BRAKE_FAIL', 'PRESSURE_LOW', 'VALVE_FAULT'],
        'color': '#FFCC00',  # Желтый
        'priority': 4,
        'description': 'Критические неисправности тормозной системы',
        'examples': ['B_BCU_FAULT', 'F_R_PRESSURE_LOW', 'B_BRAKE_CYLINDER_FAULT']
    }
}

# Фильтры по системам
SYSTEM_FILTERS = {
    'traction': {
        'patterns': ['PST_', 'INV', 'TRACTION_', 'MOTOR_', 'EFFORT_', 'TORQUE_'],
        'subsystems': ['inverters', 'motors', 'effort_control'],
        'description': 'Тяговая система и управление тягой',
        'examples': ['S_EFFORT_SETUP_INV1', 'B_INVERTER1_READY', 'F_MOTOR_CURRENT']
    },
    'brakes': {
        'patterns': ['BCU_', 'BRAKE_', 'PRESSURE_', 'VALVE_', 'SLIDING_', 'KNORR'],
        'subsystems': ['bcu_knorr', 'pneumatic', 'wheel_slide', 'brake_cylinders'],
        'description': 'Тормозная система и пневматика',
        'examples': ['BY_BCU_FAIL_CODE', 'F_C_PRESSURE_AXLE1_MPA', 'B_SLIDING_PROTECTION']
    },
    'doors': {
        'patterns': ['BUD', 'DOOR_', 'HINDRANCE', 'OPENED', 'CLOSED'],
        'subsystems': ['bud_controllers', 'door_states', 'safety_locks'],
        'description': 'Система дверей и контроллеры BUD',
        'examples': ['B_BUD1_ISOPENED', 'B_DOOR1_ISCLOSED', 'B_DOOR_HINDRANCE']
    },
    'power': {
        'patterns': ['PSN_', 'QF', 'U3000', 'VOLTAGE', 'CURRENT', 'KPSN'],
        'subsystems': ['high_voltage', 'converters', 'protection', 'contactors'],
        'description': 'Энергоснабжение и электрооборудование',
        'examples': ['F_U3000', 'B_QF1_TRIP', 'S_PSN_CURRENT']
    },
    'climate': {
        'patterns': ['SOM_', 'KSK_', 'GOR_', 'TEMP', 'HEAT', 'COOL'],
        'subsystems': ['heating', 'cooling', 'ventilation', 'temperature'],
        'description': 'Климатическая система и отопление',
        'examples': ['S_OUTSIDE_TEMP', 'B_KSK_MODE_HEAT', 'F_GOR_TEMPERATURE']
    },
    'info_systems': {
        'patterns': ['BIM', 'BUIK_', 'ANNOUNCEMENT', 'DISPLAY', 'SOUND'],
        'subsystems': ['passenger_info', 'announcements', 'displays'],
        'description': 'Информационные системы для пассажиров',
        'examples': ['BY_BIM1_KEY_CODE', 'BY_BUIK_MODE', 'B_ANNOUNCEMENT_READY']
    },
    'communication': {
        'patterns': ['RADIO_', 'GSM_', 'WIFI_', 'ETHERNET_', 'CAN_'],
        'subsystems': ['radio', 'gsm', 'ethernet', 'can_bus'],
        'description': 'Системы связи и передачи данных',
        'examples': ['B_RADIO_CONNECTED', 'B_GSM_SIGNAL_OK', 'BY_CAN_STATUS']
    },
    'unknown': {
        'patterns': ['Banner#', 'Coord#'],
        'description': 'Неизвестные сигналы'
    }
}

# Функциональные фильтры
FUNCTIONAL_FILTERS = {
    'faults': {
        'patterns': ['FAULT', 'FAIL', 'ERROR', 'ERR_', 'TRIP', 'BLOCK'],
        'description': 'Неисправности и ошибки'
    },
    'states': {
        'patterns': ['STATE', 'STATUS', 'MODE', 'READY', 'OK', 'AVAILABLE'],
        'description': 'Состояния систем и оборудования'
    },
    'measurements': {
        'patterns': ['TEMP', 'PRESSURE', 'VOLTAGE', 'CURRENT', 'SPEED', 'LEVEL'],
        'description': 'Измерительные параметры'
    },
    'controls': {
        'patterns': ['CTRL', 'COMMAND', 'SET', 'RESET', 'ENABLE', 'DISABLE'],
        'description': 'Команды управления'
    },
    'diagnostics': {
        'patterns': ['HEARTBEAT', 'VERSION', 'SW_VER', 'AVAIL', 'CONNECT', 'DIAG'],
        'description': 'Диагностические параметры'
    }
}

# Причинно-следственные связи
CAUSAL_RELATIONSHIPS = {
    # Энергосистема
    'power_chain': {
        'root_causes': ['F_U3000', 'B_WAGON_3000V_OK', 'B_PANTO_UP'],
        'effects': ['B_PSN_CONNECTED', 'B_PST_CONNECTED', 'B_INVERTER1_READY'],
        'description': 'Отсутствие 3кВ → отключение преобразователей → отказ тяги',
        'severity': 'critical'
    },
    
    # Тормозная система
    'brake_pressure_chain': {
        'root_causes': ['F_R_PRESSURE_MPA', 'B_R_PRESSURE_LOW'],
        'effects': ['B_BCU_FAULT', 'B_BRAKE_APPLIED', 'B_EMERGENCY_BRAKING'],
        'description': 'Низкое давление R → отказ BCU → экстренное торможение',
        'severity': 'critical'
    },
    
    # Двери
    'door_safety_chain': {
        'root_causes': ['B_BUD1_HINDRANCE', 'B_DOOR1_ISCLOSED'],
        'effects': ['B_ALL_DOORS_CLOSED', 'B_TRAIN_IS_MOVING_PERMIT'],
        'description': 'Препятствие в двери → блокировка движения',
        'severity': 'high'
    },
    
    # Пантограф
    'pantograph_chain': {
        'root_causes': ['B_PANTO_UP', 'B_PANTO_BLOCKED'],
        'effects': ['F_U3000', 'B_QF1_TRIP', 'B_PST_CONNECTED'],
        'description': 'Пантограф опущен → нет 3кВ → отключение тяги',
        'severity': 'critical'
    },
    
    # Инверторы
    'inverter_chain': {
        'root_causes': ['B_INVERTER1_READY', 'B_PST_CONNECTED'],
        'effects': ['S_EFFORT_SETUP_INV1', 'F_MOTOR_CURRENT', 'B_TRACTION_AVAILABLE'],
        'description': 'Отказ инвертора → потеря тяги → снижение мощности',
        'severity': 'high'
    }
}

# Маппинг компонентов
COMPONENT_MAPPING = {
    'PST': 'Преобразователь статический тяговый',
    'PSN': 'Преобразователь статический низковольтный', 
    'BCU': 'Блок управления тормозами (Knorr)',
    'BUD': 'Блок управления дверьми',
    'BIM': 'Бортовая информационная машина',
    'BUIK': 'Блок управления информацией к пассажирам',
    'SOM': 'Система обеспечения микроклимата',
    'KSK': 'Климатическая система кузова',
    'GOR': 'Горячее водоснабжение',
    'QF': 'Автоматический выключатель',
    'QS': 'Разъединитель',
    'INV': 'Инвертор тяговый'
}

# Конфигурация уровней серьезности
SEVERITY_LEVELS = {
    'critical': {
        'color': '#FF0000',
        'priority': 1,
        'notification': True,
        'sound_alert': True
    },
    'high': {
        'color': '#FF6600', 
        'priority': 2,
        'notification': True,
        'sound_alert': False
    },
    'medium': {
        'color': '#FFB000',
        'priority': 3,
        'notification': False,
        'sound_alert': False
    },
    'low': {
        'color': '#00AA00',
        'priority': 4,
        'notification': False,
        'sound_alert': False
    }
}
