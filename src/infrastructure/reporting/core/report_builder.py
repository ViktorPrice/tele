# src/infrastructure/reporting/core/report_builder.py - ПОЛНАЯ ВЕРСИЯ
"""
Построитель структуры отчетов с таблицами изменений
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ReportSection:
    """Секция отчета"""
    title: str
    content: Any
    section_type: str  # 'text', 'plot', 'table', 'summary', 'changes_table'
    metadata: Dict[str, Any] = None

@dataclass
class ReportData:
    """Данные для отчета"""
    title: str
    subtitle: str
    creation_date: datetime
    time_range: tuple[datetime, datetime]
    sections: List[ReportSection]
    metadata: Dict[str, Any]

class ReportTemplate(ABC):
    """Абстрактный шаблон отчета"""
    
    @abstractmethod
    def get_title(self) -> str:
        """Получение заголовка отчета"""
        pass
    
    @abstractmethod
    def build_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """Построение секций отчета"""
        pass
    
    @abstractmethod
    def get_page_layout(self) -> Dict[str, Any]:
        """Получение настроек макета страницы"""
        pass

class TelemetryReportTemplate(ReportTemplate):
    """ИСПРАВЛЕННЫЙ шаблон отчета по телеметрии с таблицами изменений"""
    
    def get_title(self) -> str:
        return "Отчет анализа телеметрических данных"
    
    def build_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """ИСПРАВЛЕННОЕ построение секций отчета телеметрии"""
        sections = []
        
        # Заголовочная секция
        sections.append(ReportSection(
            title="Общая информация",
            content=self._build_header_content(data),
            section_type="text"
        ))
        
        # Секции графиков с таблицами изменений
        plot_blocks = data.get('plot_blocks_data', {})
        for block_id, params in plot_blocks.items():
            if params:
                # График
                sections.append(ReportSection(
                    title=f"График: {block_id}",
                    content={
                        'params': params,
                        'start_time': data.get('start_time'),
                        'end_time': data.get('end_time'),
                        'description': f"График параметров блока {block_id}"
                    },
                    section_type="plot",
                    metadata={'block_id': block_id}
                ))
                
                # ДОБАВЛЯЕМ: Таблица изменений под графиком
                sections.append(ReportSection(
                    title=f"Изменения параметров: {block_id}",
                    content={
                        'params': params,
                        'start_time': data.get('start_time'),
                        'end_time': data.get('end_time'),
                        'data_loader': data.get('data_loader')  # Передаем data_loader
                    },
                    section_type="changes_table",
                    metadata={'block_id': block_id}
                ))
        
        # Аналитическая секция
        sections.append(ReportSection(
            title="Анализ изменений",
            content=self._build_analysis_content(data),
            section_type="summary"
        ))
        
        return sections
    
    def _build_header_content(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Построение содержимого заголовка"""
        return {
            'period': f"{data.get('start_time')} - {data.get('end_time')}",
            'creation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_blocks': str(len(data.get('plot_blocks_data', {}))),
            'total_params': str(sum(len(params) for params in data.get('plot_blocks_data', {}).values()))
        }
    
    def _build_analysis_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Построение аналитического содержимого"""
        return {
            'summary': "Анализ изменений параметров в указанном диапазоне",
            'changes_detected': True,
            'recommendations': [
                "Проверить параметры с наибольшими изменениями",
                "Обратить внимание на аномальные значения",
                "Контролировать критические параметры"
            ],
            'details': "Подробный анализ показывает изменения в выбранном временном диапазоне"
        }
    
    def get_page_layout(self) -> Dict[str, Any]:
        """Настройки макета страницы"""
        return {
            'orientation': 'landscape',
            'margins': {'top': 50, 'bottom': 50, 'left': 50, 'right': 50},
            'font_family': 'DejaVuSans',
            'font_size': 10
        }

class SummaryReportTemplate(ReportTemplate):
    """Шаблон сводного отчета"""
    
    def get_title(self) -> str:
        return "Сводный отчет анализа данных"
    
    def build_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """Построение секций сводного отчета"""
        sections = []
        
        # Сводная таблица
        sections.append(ReportSection(
            title="Сводная статистика",
            content=self._build_summary_table(data),
            section_type="table"
        ))
        
        # Рекомендации
        sections.append(ReportSection(
            title="Рекомендации",
            content=self._build_recommendations(data),
            section_type="text"
        ))
        
        return sections
    
    def _build_summary_table(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Построение сводной таблицы"""
        return [
            {'Параметр': 'Всего блоков', 'Значение': str(len(data.get('plot_blocks_data', {})))},
            {'Параметр': 'Всего параметров', 'Значение': str(sum(len(params) for params in data.get('plot_blocks_data', {}).values()))},
            {'Параметр': 'Период анализа', 'Значение': f"{data.get('start_time')} - {data.get('end_time')}"}
        ]
    
    def _build_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Построение рекомендаций"""
        return [
            "Регулярно проверять критические параметры",
            "Настроить мониторинг для раннего обнаружения аномалий",
            "Создать резервные копии важных конфигураций"
        ]
    
    def get_page_layout(self) -> Dict[str, Any]:
        """Настройки макета страницы"""
        return {
            'orientation': 'portrait',
            'margins': {'top': 50, 'bottom': 50, 'left': 50, 'right': 50},
            'font_family': 'DejaVuSans',
            'font_size': 12
        }

class ReportBuilder:
    """Построитель отчетов с использованием шаблонов"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.templates = {
            'telemetry': TelemetryReportTemplate(),
            'summary': SummaryReportTemplate()
        }
    
    def build_report(self, template_name: str, data: Dict[str, Any]) -> ReportData:
        """Построение отчета по шаблону"""
        try:
            template = self.templates.get(template_name)
            if not template:
                raise ValueError(f"Шаблон '{template_name}' не найден")
            
            # Построение секций
            sections = template.build_sections(data)
            
            # Создание объекта отчета
            report = ReportData(
                title=template.get_title(),
                subtitle=data.get('subtitle', ''),
                creation_date=datetime.now(),
                time_range=(data.get('start_time'), data.get('end_time')),
                sections=sections,
                metadata={
                    'template': template_name,
                    'layout': template.get_page_layout(),
                    **data
                }
            )
            
            self.logger.info(f"Построен отчет '{template_name}' с {len(sections)} секциями")
            return report
            
        except Exception as e:
            self.logger.error(f"Ошибка построения отчета: {e}")
            raise
