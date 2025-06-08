"""
Рендеринг SOP в XML формат
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
from typing import Optional

from .sop_builder import SOPDocument

class XMLRenderer:
    """Рендеринг SOP документов в XML"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def render_to_xml(self, sop_doc: SOPDocument, encoding: str = 'windows-1251') -> str:
        """Рендеринг SOP документа в XML строку"""
        try:
            # Создание корневого элемента
            root = ET.Element("dataroot", 
                            format=sop_doc.format_version, 
                            version=sop_doc.version)
            
            # Добавление периода времени
            ET.SubElement(root, "period",
                         begin=sop_doc.period[0].strftime("%Y-%m-%d %H:%M:%S"),
                         end=sop_doc.period[1].strftime("%Y-%m-%d %H:%M:%S"))
            
            # Добавление каналов
            for channel in sop_doc.channels:
                self._add_channel_to_xml(root, channel)
            
            # Форматирование XML
            xml_str = ET.tostring(root, encoding=encoding, xml_declaration=True)
            dom = minidom.parseString(xml_str)
            formatted_xml = dom.toprettyxml(indent="  ", encoding=encoding)
            
            self.logger.info(f"SOP XML сгенерирован: {len(sop_doc.channels)} каналов")
            return formatted_xml.decode(encoding)
            
        except Exception as e:
            self.logger.error(f"Ошибка рендеринга XML: {e}")
            raise
    
    def _add_channel_to_xml(self, root: ET.Element, channel) -> None:
        """Добавление канала в XML"""
        channel_elem = ET.SubElement(root, "channel", 
                                   name=channel.name, 
                                   comment=channel.comment)
        
        for device in channel.devices:
            device_elem = ET.SubElement(channel_elem, "device", 
                                      id=device.id, 
                                      comment=device.comment)
            
            for param in device.parameters:
                ET.SubElement(device_elem, "param").text = param.name
                ET.SubElement(device_elem, "alias").text = param.alias
                ET.SubElement(device_elem, "plot").text = str(param.plot)
    
    def save_to_file(self, sop_doc: SOPDocument, file_path: str, 
                     encoding: str = 'windows-1251') -> bool:
        """Сохранение SOP в файл"""
        try:
            xml_content = self.render_to_xml(sop_doc, encoding)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(xml_content)
            
            self.logger.info(f"SOP сохранен в файл: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения SOP: {e}")
            return False
