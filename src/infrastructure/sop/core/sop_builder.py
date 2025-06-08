# src/infrastructure/sop/core/sop_builder.py - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Построитель структуры SOP с использованием шаблонов БЕЗ legacy зависимостей
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class SOPParameter:
    """Параметр SOP"""
    name: str
    alias: str
    plot: int
    channel: str
    device_id: str = "0x0000"

@dataclass
class SOPChannel:
    """Канал SOP"""
    name: str
    comment: str
    devices: List['SOPDevice']

@dataclass
class SOPDevice:
    """Устройство SOP"""
    id: str
    comment: str
    parameters: List[SOPParameter]

@dataclass
class SOPDocument:
    """Документ SOP"""
    format_version: str
    version: str
    period: tuple[datetime, datetime]
    channels: List[SOPChannel]

class SOPTemplate(ABC):
    """Абстрактный шаблон SOP"""
    
    @abstractmethod
    def get_format_version(self) -> str:
        """Получение версии формата"""
        pass
    
    @abstractmethod
    def group_parameters(self, params: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Группировка параметров по каналам"""
        pass
    
    @abstractmethod
    def create_channels(self, grouped_params: Dict[str, List[Dict[str, Any]]]) -> List[SOPChannel]:
        """Создание каналов из сгруппированных параметров"""
        pass
    
    @abstractmethod
    def get_line_comments(self) -> Dict[str, str]:
        """Получение комментариев для линий"""
        pass

class TelemetrySOPTemplate(SOPTemplate):
    """Шаблон SOP для телеметрии"""
    
    def __init__(self, wagon_config, line_config):
        self.wagon_config = wagon_config
        self.line_config = line_config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_params_per_plot = 20
    
    def get_format_version(self) -> str:
        return "2ES5S_REC_TRACE_CFG"
    
    def group_parameters(self, params: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Группировка параметров по линиям связи"""
        line_groups = {}
        
        for param in params:
            line = param.get('line', 'UNKNOWN')
            if line not in line_groups:
                line_groups[line] = []
            line_groups[line].append(param)
        
        # Сортировка для стабильного порядка
        return dict(sorted(line_groups.items()))
    
    def create_channels(self, grouped_params: Dict[str, List[Dict[str, Any]]]) -> List[SOPChannel]:
        """Создание каналов из сгруппированных параметров"""
        channels = []
        line_comments = self.get_line_comments()
        
        for line, line_params in grouped_params.items():
            comment = line_comments.get(line, line)
            
            # Группировка по типу данных внутри линии
            type_groups = self._group_by_data_type(line_params)
            
            devices = []
            plot_number = 1
            
            for data_type, group_params in type_groups.items():
                # Разбиение на блоки по max_params_per_plot
                for i in range(0, len(group_params), self.max_params_per_plot):
                    chunk = group_params[i:i+self.max_params_per_plot]
                    
                    parameters = []
                    for param in chunk:
                        sop_param = SOPParameter(
                            name=param.get('signal_code', ''),
                            alias=param.get('description', ''),
                            plot=plot_number,
                            channel=line,
                            device_id="0x0000"
                        )
                        parameters.append(sop_param)
                    
                    device = SOPDevice(
                        id=f"0x{plot_number:04X}",
                        comment=f"{data_type} блок {plot_number}",
                        parameters=parameters
                    )
                    devices.append(device)
                    plot_number += 1
            
            if devices:
                channel = SOPChannel(
                    name=line,
                    comment=comment,
                    devices=devices
                )
                channels.append(channel)
        
        return channels
    
    def _group_by_data_type(self, params: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Группировка параметров по типу данных"""
        type_groups = {}
        
        for param in params:
            signal_code = param.get('signal_code', '')
            if signal_code:
                data_type = signal_code.split('_')[0] if '_' in signal_code else 'UNKNOWN'
            else:
                data_type = 'UNKNOWN'
            
            if data_type not in type_groups:
                type_groups[data_type] = []
            type_groups[data_type].append(param)
        
        return type_groups
    
    def get_line_comments(self) -> Dict[str, str]:
        """Получение комментариев для линий"""
        if self.line_config:
            return self.line_config.get_line_comments()
        
        # Fallback комментарии
        return {
            'L_LCU_BIM1_CH': 'Линия БИМ1 - БУР',
            'L_LCU_BIM2_CH': 'Линия БИМ2 - БУР',
            'T_TV_MAIN_CH_A': 'Общая линия МСС (ТВ - БУР) канал A',
            'T_TV_MAIN_CH_B': 'Общая линия МСС (ТВ - БУР) канал B',
            'L_CAN_BLOK_CH': 'Линия CAN блокировки',
            'L_CAN_ICU_CH_A': 'Линия CAN ICU канал A',
            'L_CAN_ICU_CH_B': 'Линия CAN ICU канал B',
            'L_TV_MAIN_CH_A': 'Линия ТВ основная канал A',
            'L_TV_MAIN_CH_B': 'Линия ТВ основная канал B',
            'L_LCUP_CH_A': 'Линия LCUP канал A',
            'L_LCUP_CH_B': 'Линия LCUP канал B',
            'L_REC_CH_A': 'Линия записи канал A',
            'L_REC_CH_B': 'Линия записи канал B',
            'L_CAN_POS_CH': 'Линия CAN позиционирования'
        }
    
    def create_device_for_parameters(self, params: List[Dict[str, Any]], 
                                   device_id: str, plot_number: int,
                                   channel_name: str) -> SOPDevice:
        """Создание устройства для группы параметров"""
        parameters = []
        
        for param in params:
            sop_param = SOPParameter(
                name=param.get('signal_code', ''),
                alias=param.get('description', ''),
                plot=plot_number,
                channel=channel_name,
                device_id=device_id
            )
            parameters.append(sop_param)
        
        # Определение типа устройства по параметрам
        device_type = self._determine_device_type(params)
        
        return SOPDevice(
            id=device_id,
            comment=f"{device_type} устройство {plot_number}",
            parameters=parameters
        )
    
    def _determine_device_type(self, params: List[Dict[str, Any]]) -> str:
        """Определение типа устройства по параметрам"""
        if not params:
            return "UNKNOWN"
        
        # Анализ типов сигналов в группе
        signal_types = set()
        for param in params:
            signal_code = param.get('signal_code', '')
            if signal_code and '_' in signal_code:
                signal_types.add(signal_code.split('_')[0])
        
        # Определение типа устройства
        if 'B' in signal_types:
            return "BOOLEAN"
        elif 'BY' in signal_types:
            return "BYTE"
        elif 'W' in signal_types:
            return "WORD"
        elif 'DW' in signal_types:
            return "DWORD"
        elif 'F' in signal_types:
            return "FLOAT"
        else:
            return "MIXED"

class MinimalSOPTemplate(SOPTemplate):
    """Минимальный шаблон SOP для простых случаев"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_format_version(self) -> str:
        return "MINIMAL_SOP_CFG"
    
    def group_parameters(self, params: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Простая группировка - все параметры в одну группу"""
        return {"DEFAULT_CHANNEL": params}
    
    def create_channels(self, grouped_params: Dict[str, List[Dict[str, Any]]]) -> List[SOPChannel]:
        """Создание одного канала со всеми параметрами"""
        channels = []
        
        for channel_name, params in grouped_params.items():
            if not params:
                continue
            
            # Создание одного устройства со всеми параметрами
            sop_params = []
            for i, param in enumerate(params, 1):
                sop_param = SOPParameter(
                    name=param.get('signal_code', f'PARAM_{i}'),
                    alias=param.get('description', f'Parameter {i}'),
                    plot=1,
                    channel=channel_name,
                    device_id="0x0001"
                )
                sop_params.append(sop_param)
            
            device = SOPDevice(
                id="0x0001",
                comment="Основное устройство",
                parameters=sop_params
            )
            
            channel = SOPChannel(
                name=channel_name,
                comment="Основной канал",
                devices=[device]
            )
            
            channels.append(channel)
        
        return channels
    
    def get_line_comments(self) -> Dict[str, str]:
        """Базовые комментарии"""
        return {"DEFAULT_CHANNEL": "Основной канал связи"}

class SOPBuilder:
    """Построитель SOP документов"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.templates = {}
    
    def register_template(self, name: str, template: SOPTemplate):
        """Регистрация шаблона"""
        self.templates[name] = template
        self.logger.info(f"Зарегистрирован шаблон SOP: {name}")
    
    def build_sop(self, template_name: str, data: Dict[str, Any]) -> SOPDocument:
        """Построение SOP документа"""
        try:
            template = data.get('template')
            if not template:
                # Попытка получить шаблон по имени
                template = self.templates.get(template_name)
                if not template:
                    self.logger.warning(f"Шаблон {template_name} не найден, используем минимальный")
                    template = MinimalSOPTemplate()
            
            params = data.get('params', [])
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            
            if not params:
                self.logger.warning("Нет параметров для создания SOP")
                params = []
            
            if not start_time or not end_time:
                # Используем текущее время как fallback
                from datetime import datetime
                now = datetime.now()
                start_time = start_time or now
                end_time = end_time or now
            
            # Группировка параметров
            grouped_params = template.group_parameters(params)
            
            # Создание каналов
            channels = template.create_channels(grouped_params)
            
            # Создание документа
            sop_document = SOPDocument(
                format_version=template.get_format_version(),
                version="1.0",
                period=(start_time, end_time),
                channels=channels
            )
            
            self.logger.info(f"SOP документ построен: {len(channels)} каналов, {sum(len(ch.devices) for ch in channels)} устройств")
            return sop_document
            
        except Exception as e:
            self.logger.error(f"Ошибка построения SOP: {e}")
            # Возвращаем минимальный документ при ошибке
            return SOPDocument(
                format_version="ERROR_SOP_CFG",
                version="1.0",
                period=(datetime.now(), datetime.now()),
                channels=[]
            )
    
    def validate_sop_document(self, sop_document: SOPDocument) -> tuple[bool, List[str]]:
        """Валидация SOP документа"""
        errors = []
        
        # Проверка базовых полей
        if not sop_document.format_version:
            errors.append("Отсутствует версия формата")
        
        if not sop_document.version:
            errors.append("Отсутствует версия документа")
        
        if not sop_document.channels:
            errors.append("Нет каналов в документе")
        
        # Проверка каналов
        for i, channel in enumerate(sop_document.channels):
            if not channel.name:
                errors.append(f"Канал {i+1}: отсутствует имя")
            
            if not channel.devices:
                errors.append(f"Канал {i+1}: нет устройств")
            
            # Проверка устройств
            for j, device in enumerate(channel.devices):
                if not device.id:
                    errors.append(f"Канал {i+1}, устройство {j+1}: отсутствует ID")
                
                if not device.parameters:
                    errors.append(f"Канал {i+1}, устройство {j+1}: нет параметров")
                
                # Проверка параметров
                for k, param in enumerate(device.parameters):
                    if not param.name:
                        errors.append(f"Канал {i+1}, устройство {j+1}, параметр {k+1}: отсутствует имя")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_sop_statistics(self, sop_document: SOPDocument) -> Dict[str, Any]:
        """Получение статистики SOP документа"""
        try:
            channels_count = len(sop_document.channels)
            devices_count = sum(len(ch.devices) for ch in sop_document.channels)
            parameters_count = sum(
                len(dev.parameters) 
                for ch in sop_document.channels 
                for dev in ch.devices
            )
            
            # Анализ типов параметров
            param_types = {}
            for channel in sop_document.channels:
                for device in channel.devices:
                    for param in device.parameters:
                        param_type = param.name.split('_')[0] if '_' in param.name else 'UNKNOWN'
                        param_types[param_type] = param_types.get(param_type, 0) + 1
            
            return {
                'format_version': sop_document.format_version,
                'version': sop_document.version,
                'channels_count': channels_count,
                'devices_count': devices_count,
                'parameters_count': parameters_count,
                'parameter_types': param_types,
                'period_start': sop_document.period[0].strftime('%Y-%m-%d %H:%M:%S'),
                'period_end': sop_document.period[1].strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики SOP: {e}")
            return {}
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.templates.clear()
        self.logger.info("SOPBuilder очищен")
