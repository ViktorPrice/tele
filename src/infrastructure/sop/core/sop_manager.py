# src/infrastructure/sop/core/sop_manager.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Менеджер SOP БЕЗ legacy зависимостей (только новая архитектура)
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from .sop_builder import SOPBuilder, TelemetrySOPTemplate, SOPDocument
from ..config.wagon_config import WagonConfig
from ..config.line_config import LineConfig

class SOPManager:
    """Менеджер SOP (полностью новая реализация БЕЗ legacy)"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Новые компоненты (БЕЗ legacy)
        self.wagon_config = WagonConfig(data_loader)
        self.line_config = LineConfig()
        self.sop_builder = SOPBuilder()
        
        # История созданных SOP
        self.sop_history = []
        
        self.logger.info("SOPManager (только новая архитектура) инициализирован")
    
    def generate_sop_for_params(self, params: List[Dict[str, Any]], 
                               start_time: datetime, end_time: datetime) -> str:
        """Генерация SOP для параметров (новая реализация)"""
        try:
            self.logger.info(f"Генерация SOP для {len(params)} параметров")
            
            # Создание шаблона
            template = TelemetrySOPTemplate(self.wagon_config, self.line_config)
            
            # Построение SOP документа
            sop_document = self.sop_builder.build_sop('telemetry', {
                'params': params,
                'start_time': start_time,
                'end_time': end_time,
                'template': template
            })
            
            # Преобразование в XML
            xml_string = self._convert_to_xml(sop_document)
            
            # Сохранение в истории
            self.sop_history.append({
                'created_at': datetime.now(),
                'params_count': len(params),
                'time_range': (start_time, end_time),
                'xml_length': len(xml_string)
            })
            
            self.logger.info(f"SOP создан: {len(xml_string)} символов")
            return xml_string
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации SOP: {e}")
            return ""
    
    def _convert_to_xml(self, sop_document: SOPDocument) -> str:
        """Преобразование SOP документа в XML"""
        try:
            # Создание корневого элемента
            root = Element('SOP_CONFIGURATION')
            root.set('format_version', sop_document.format_version)
            root.set('version', sop_document.version)
            
            # Добавление информации о периоде
            period_elem = SubElement(root, 'PERIOD')
            period_elem.set('start', sop_document.period[0].strftime('%Y-%m-%d %H:%M:%S'))
            period_elem.set('end', sop_document.period[1].strftime('%Y-%m-%d %H:%M:%S'))
            
            # Добавление каналов
            channels_elem = SubElement(root, 'CHANNELS')
            
            for channel in sop_document.channels:
                channel_elem = SubElement(channels_elem, 'CHANNEL')
                channel_elem.set('name', channel.name)
                channel_elem.set('comment', channel.comment)
                
                # Добавление устройств
                devices_elem = SubElement(channel_elem, 'DEVICES')
                
                for device in channel.devices:
                    device_elem = SubElement(devices_elem, 'DEVICE')
                    device_elem.set('id', device.id)
                    device_elem.set('comment', device.comment)
                    
                    # Добавление параметров
                    params_elem = SubElement(device_elem, 'PARAMETERS')
                    
                    for param in device.parameters:
                        param_elem = SubElement(params_elem, 'PARAMETER')
                        param_elem.set('name', param.name)
                        param_elem.set('alias', param.alias)
                        param_elem.set('plot', str(param.plot))
                        param_elem.set('channel', param.channel)
                        param_elem.set('device_id', param.device_id)
            
            # Форматирование XML
            rough_string = tostring(root, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            
            # Добавление XML декларации с кодировкой
            xml_declaration = '<?xml version="1.0" encoding="windows-1251"?>\n'
            formatted_xml = reparsed.toprettyxml(indent="  ")[23:]  # Убираем стандартную декларацию
            
            return xml_declaration + formatted_xml
            
        except Exception as e:
            self.logger.error(f"Ошибка преобразования в XML: {e}")
            return ""
    
    def save_sop_to_file(self, sop_xml: str, file_path: str) -> bool:
        """Сохранение SOP в файл"""
        try:
            # Определение кодировки по содержимому
            encoding = 'windows-1251' if 'encoding="windows-1251"' in sop_xml else 'utf-8'
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(sop_xml)
            
            self.logger.info(f"SOP сохранен в файл: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения SOP: {e}")
            return False
    
    def generate_sop_with_template(self, template_name: str, params: List[Dict[str, Any]], 
                                  start_time: datetime, end_time: datetime) -> str:
        """Генерация SOP с использованием конкретного шаблона"""
        try:
            # Создание шаблона по имени
            if template_name == 'telemetry':
                template = TelemetrySOPTemplate(self.wagon_config, self.line_config)
            else:
                self.logger.warning(f"Неизвестный шаблон: {template_name}, используется telemetry")
                template = TelemetrySOPTemplate(self.wagon_config, self.line_config)
            
            # Построение SOP
            sop_document = self.sop_builder.build_sop(template_name, {
                'params': params,
                'start_time': start_time,
                'end_time': end_time,
                'template': template
            })
            
            return self._convert_to_xml(sop_document)
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации SOP с шаблоном {template_name}: {e}")
            return ""
    
    def validate_sop_xml(self, sop_xml: str) -> tuple[bool, str]:
        """Валидация SOP XML"""
        try:
            from xml.etree.ElementTree import fromstring
            
            # Базовая валидация XML
            root = fromstring(sop_xml)
            
            # Проверка обязательных элементов
            if root.tag != 'SOP_CONFIGURATION':
                return False, "Корневой элемент должен быть SOP_CONFIGURATION"
            
            if not root.get('format_version'):
                return False, "Отсутствует атрибут format_version"
            
            channels = root.find('CHANNELS')
            if channels is None:
                return False, "Отсутствует элемент CHANNELS"
            
            # Проверка наличия каналов
            if len(channels) == 0:
                return False, "Нет каналов в конфигурации"
            
            return True, "SOP XML валиден"
            
        except Exception as e:
            return False, f"Ошибка валидации XML: {e}"
    
    def get_sop_statistics(self, sop_xml: str) -> Dict[str, Any]:
        """Получение статистики SOP"""
        try:
            from xml.etree.ElementTree import fromstring
            
            root = fromstring(sop_xml)
            
            channels_count = 0
            devices_count = 0
            parameters_count = 0
            
            channels = root.find('CHANNELS')
            if channels is not None:
                channels_count = len(channels)
                
                for channel in channels:
                    devices = channel.find('DEVICES')
                    if devices is not None:
                        devices_count += len(devices)
                        
                        for device in devices:
                            params = device.find('PARAMETERS')
                            if params is not None:
                                parameters_count += len(params)
            
            return {
                'format_version': root.get('format_version', 'Unknown'),
                'version': root.get('version', 'Unknown'),
                'channels_count': channels_count,
                'devices_count': devices_count,
                'parameters_count': parameters_count,
                'xml_size': len(sop_xml)
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики SOP: {e}")
            return {}
    
    def get_sop_history(self) -> List[Dict[str, Any]]:
        """Получение истории созданных SOP"""
        return self.sop_history.copy()
    
    def clear_sop_history(self):
        """Очистка истории SOP"""
        self.sop_history.clear()
        self.logger.info("История SOP очищена")
    
    def export_sop_template(self, template_name: str, output_path: str) -> bool:
        """Экспорт шаблона SOP в файл"""
        try:
            # Создание пустого SOP с шаблоном
            template = TelemetrySOPTemplate(self.wagon_config, self.line_config)
            
            # Создание минимального SOP документа
            from .sop_builder import SOPDocument, SOPChannel
            
            sop_document = SOPDocument(
                format_version=template.get_format_version(),
                version="1.0",
                period=(datetime.now(), datetime.now()),
                channels=[]
            )
            
            xml_string = self._convert_to_xml(sop_document)
            
            return self.save_sop_to_file(xml_string, output_path)
            
        except Exception as e:
            self.logger.error(f"Ошибка экспорта шаблона SOP: {e}")
            return False
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.sop_history.clear()
            self.logger.info("SOPManager очищен")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки SOPManager: {e}")
