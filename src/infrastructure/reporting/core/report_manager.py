# src/infrastructure/reporting/core/report_manager.py - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Менеджер отчетов БЕЗ legacy зависимостей (только новая архитектура)
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd

from .report_builder import ReportBuilder, TelemetryReportTemplate
from .pdf_renderer import PDFRenderer

class ReportManager:
    """Менеджер отчетов (полностью новая реализация БЕЗ legacy)"""
    
    def __init__(self, data_loader, plot_service=None):
        self.data_loader = data_loader
        self.plot_service = plot_service
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Новые компоненты (БЕЗ legacy)
        self.report_builder = ReportBuilder()
        self.pdf_renderer = PDFRenderer(plot_service)
        
        # История созданных отчетов
        self.report_history = []
        
        self.logger.info("ReportManager (только новая архитектура) инициализирован")
    
    def generate_full_report(self, plot_blocks_data: Dict[str, list], 
                           start_time: datetime, end_time: datetime, 
                           save_path: str) -> bool:
        """Генерация полного отчета (новая реализация)"""
        try:
            self.logger.info(f"Генерация полного отчета: {save_path}")
            
            # Подготовка данных для отчета
            report_data = {
                'plot_blocks_data': plot_blocks_data,
                'start_time': start_time,
                'end_time': end_time,
                'subtitle': f'Период: {start_time.strftime("%Y-%m-%d %H:%M:%S")} - {end_time.strftime("%Y-%m-%d %H:%M:%S")}'
            }
            
            # Построение отчета через новый builder
            report = self.report_builder.build_report('telemetry', report_data)
            
            # Определение формата по расширению файла
            file_path = Path(save_path)
            
            if file_path.suffix.lower() == '.pdf':
                success = self.pdf_renderer.render_to_pdf(report, save_path)
            elif file_path.suffix.lower() in ['.txt', '.log']:
                success = self._generate_text_report(report, save_path)
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                success = self._generate_excel_report(plot_blocks_data, start_time, end_time, save_path)
            else:
                # По умолчанию текстовый отчет
                success = self._generate_text_report(report, save_path)
            
            if success:
                # Сохранение в истории
                self.report_history.append({
                    'path': save_path,
                    'type': 'full_report',
                    'created_at': datetime.now(),
                    'parameters_count': sum(len(params) for params in plot_blocks_data.values()),
                    'time_range': (start_time, end_time)
                })
                
                self.logger.info(f"Полный отчет успешно создан: {save_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации полного отчета: {e}")
            return False
    
    def _generate_text_report(self, report, save_path: str) -> bool:
        """Генерация текстового отчета"""
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                # Заголовок
                f.write(f"{report.title}\n")
                f.write("=" * len(report.title) + "\n\n")
                
                if report.subtitle:
                    f.write(f"{report.subtitle}\n\n")
                
                f.write(f"Дата создания: {report.creation_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Период: {report.time_range[0]} - {report.time_range[1]}\n\n")
                
                # Секции
                for section in report.sections:
                    f.write(f"{section.title}\n")
                    f.write("-" * len(section.title) + "\n")
                    
                    if section.section_type == 'text':
                        if isinstance(section.content, dict):
                            for key, value in section.content.items():
                                f.write(f"{key}: {value}\n")
                        elif isinstance(section.content, list):
                            for item in section.content:
                                f.write(f"• {item}\n")
                        else:
                            f.write(f"{section.content}\n")
                    
                    elif section.section_type == 'plot':
                        f.write("График включен в отчет\n")
                        params = section.content.get('params', [])
                        f.write(f"Параметры ({len(params)}):\n")
                        for param in params:
                            if isinstance(param, dict):
                                f.write(f"  - {param.get('signal_code', 'Unknown')}: {param.get('description', '')}\n")
                            else:
                                f.write(f"  - {param}\n")
                    
                    elif section.section_type == 'summary':
                        if isinstance(section.content, dict):
                            summary = section.content.get('summary', '')
                            if summary:
                                f.write(f"{summary}\n")
                            
                            recommendations = section.content.get('recommendations', [])
                            if recommendations:
                                f.write("\nРекомендации:\n")
                                for rec in recommendations:
                                    f.write(f"• {rec}\n")
                    
                    f.write("\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка создания текстового отчета: {e}")
            return False
    
    def _generate_excel_report(self, plot_blocks_data: Dict[str, list], 
                             start_time: datetime, end_time: datetime, 
                             save_path: str) -> bool:
        """Генерация Excel отчета"""
        try:
            # Получение отфильтрованных данных
            if hasattr(self.data_loader, 'filter_by_time_range'):
                filtered_df = self.data_loader.filter_by_time_range(start_time, end_time)
            elif hasattr(self.data_loader, 'data'):
                # Фильтрация вручную
                data = self.data_loader.data
                time_mask = (data['timestamp'] >= start_time) & (data['timestamp'] <= end_time)
                filtered_df = data[time_mask]
            else:
                self.logger.error("Не удалось получить данные для Excel отчета")
                return False
            
            if filtered_df.empty:
                self.logger.warning("Нет данных для Excel отчета")
                return False
            
            # Получение всех параметров из блоков
            all_param_codes = set()
            for param_codes in plot_blocks_data.values():
                if isinstance(param_codes, list):
                    for param in param_codes:
                        if isinstance(param, dict):
                            all_param_codes.add(param.get('signal_code', ''))
                        else:
                            all_param_codes.add(str(param))
                else:
                    all_param_codes.update(param_codes)
            
            # Формирование столбцов для экспорта
            columns_to_export = ['timestamp']
            
            # Поиск соответствующих столбцов в данных
            for param_code in all_param_codes:
                if not param_code:
                    continue
                    
                # Поиск параметра в загруженных данных
                if hasattr(self.data_loader, 'parameters'):
                    param = next((p for p in self.data_loader.parameters 
                                 if p.get('signal_code') == param_code), None)
                    if param and param.get('full_column') in filtered_df.columns:
                        columns_to_export.append(param['full_column'])
                else:
                    # Прямой поиск в столбцах
                    if param_code in filtered_df.columns:
                        columns_to_export.append(param_code)
            
            # Экспорт в Excel
            export_df = filtered_df[columns_to_export]
            
            # Создание Excel файла с несколькими листами
            with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                # Основные данные
                export_df.to_excel(writer, sheet_name='Данные', index=False)
                
                # Сводная информация
                summary_data = {
                    'Параметр': [
                        'Период анализа',
                        'Количество записей',
                        'Количество параметров',
                        'Время создания отчета'
                    ],
                    'Значение': [
                        f"{start_time} - {end_time}",
                        len(export_df),
                        len(columns_to_export) - 1,  # -1 для timestamp
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Сводка', index=False)
                
                # Список параметров
                if hasattr(self.data_loader, 'parameters'):
                    params_data = []
                    for param_code in all_param_codes:
                        if not param_code:
                            continue
                        param = next((p for p in self.data_loader.parameters 
                                     if p.get('signal_code') == param_code), None)
                        if param:
                            params_data.append({
                                'Код сигнала': param.get('signal_code', ''),
                                'Описание': param.get('description', ''),
                                'Линия': param.get('line', ''),
                                'Вагон': param.get('wagon', ''),
                                'Полное имя столбца': param.get('full_column', '')
                            })
                    
                    if params_data:
                        params_df = pd.DataFrame(params_data)
                        params_df.to_excel(writer, sheet_name='Параметры', index=False)
            
            self.logger.info(f"Excel отчет создан: {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка создания Excel отчета: {e}")
            return False
    
    def generate_summary_report(self, data: Dict[str, Any], save_path: str) -> bool:
        """Генерация сводного отчета"""
        try:
            # Подготовка данных для сводного отчета
            summary_data = {
                'total_blocks': len(data.get('plot_blocks_data', {})),
                'total_params': sum(len(params) for params in data.get('plot_blocks_data', {}).values()),
                'time_range': f"{data.get('start_time')} - {data.get('end_time')}",
                'creation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Построение отчета
            report = self.report_builder.build_report('summary', summary_data)
            
            # Рендеринг
            if save_path.endswith('.pdf'):
                success = self.pdf_renderer.render_to_pdf(report, save_path)
            else:
                success = self._generate_text_report(report, save_path)
            
            if success:
                self.report_history.append({
                    'path': save_path,
                    'type': 'summary_report',
                    'created_at': datetime.now(),
                    'data': summary_data
                })
                
                self.logger.info(f"Сводный отчет создан: {save_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации сводного отчета: {e}")
            return False
    
    def generate_changes_report(self, param_codes: list, 
                              start_time: datetime, end_time: datetime,
                              save_path: str) -> bool:
        """Генерация отчета об изменениях параметров"""
        try:
            self.logger.info(f"Генерация отчета об изменениях для {len(param_codes)} параметров")
            
            # Получение отфильтрованных данных
            if hasattr(self.data_loader, 'filter_by_time_range'):
                filtered_df = self.data_loader.filter_by_time_range(start_time, end_time)
            elif hasattr(self.data_loader, 'data'):
                data = self.data_loader.data
                time_mask = (data['timestamp'] >= start_time) & (data['timestamp'] <= end_time)
                filtered_df = data[time_mask]
            else:
                self.logger.error("Не удалось получить данные")
                return False
            
            if filtered_df.empty:
                self.logger.warning("Нет данных в указанном диапазоне")
                return False
            
            # Анализ изменений
            changes_data = []
            
            for param_code in param_codes:
                if not param_code:
                    continue
                
                # Поиск параметра
                param = None
                if hasattr(self.data_loader, 'parameters'):
                    param = next((p for p in self.data_loader.parameters 
                                 if p.get('signal_code') == param_code), None)
                
                # Определение имени столбца
                if param and param.get('full_column') in filtered_df.columns:
                    column = param['full_column']
                elif param_code in filtered_df.columns:
                    column = param_code
                else:
                    continue
                
                # Анализ значений
                values = pd.to_numeric(filtered_df[column], errors='coerce').dropna()
                
                if len(values) > 1:
                    # Подсчет изменений
                    changes_count = (values.diff() != 0).sum()
                    unique_values = values.nunique()
                    
                    changes_data.append({
                        'Код параметра': param_code,
                        'Описание': param.get('description', '') if param else '',
                        'Линия': param.get('line', '') if param else '',
                        'Вагон': param.get('wagon', '') if param else '',
                        'Минимальное значение': values.min(),
                        'Максимальное значение': values.max(),
                        'Среднее значение': values.mean(),
                        'Количество изменений': changes_count,
                        'Уникальных значений': unique_values,
                        'Процент изменений': (changes_count / len(values)) * 100
                    })
            
            if not changes_data:
                self.logger.warning("Нет изменений для отчета")
                return False
            
            # Сохранение отчета
            if save_path.endswith('.xlsx'):
                changes_df = pd.DataFrame(changes_data)
                changes_df.to_excel(save_path, index=False, engine='openpyxl')
            else:
                changes_df = pd.DataFrame(changes_data)
                changes_df.to_csv(save_path, index=False, encoding='utf-8-sig')
            
            # Сохранение в истории
            self.report_history.append({
                'path': save_path,
                'type': 'changes_report',
                'created_at': datetime.now(),
                'parameters_analyzed': len(param_codes),
                'changes_found': len(changes_data)
            })
            
            self.logger.info(f"Отчет об изменениях сохранен: {save_path}")
            return True
                
        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета об изменениях: {e}")
            return False
    
    def export_sop_to_file(self, sop_xml: str, file_path: str) -> bool:
        """Экспорт SOP в файл"""
        try:
            # Определение кодировки по содержимому
            encoding = 'windows-1251' if 'encoding="windows-1251"' in sop_xml else 'utf-8'
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(sop_xml)
            
            self.logger.info(f"SOP экспортирован в файл: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка экспорта SOP: {e}")
            return False
    
    def get_report_history(self) -> List[Dict[str, Any]]:
        """Получение истории созданных отчетов"""
        return self.report_history.copy()
    
    def clear_report_history(self):
        """Очистка истории отчетов"""
        self.report_history.clear()
        self.logger.info("История отчетов очищена")
    
    def validate_data_for_report(self, plot_blocks_data: Dict[str, list], 
                               start_time: datetime, end_time: datetime) -> tuple[bool, str]:
        """Валидация данных для создания отчета"""
        try:
            # Проверка временного диапазона
            if start_time >= end_time:
                return False, "Время начала должно быть раньше времени окончания"
            
            # Проверка наличия данных
            if not plot_blocks_data:
                return False, "Нет данных для создания отчета"
            
            # Проверка наличия параметров
            total_params = sum(len(params) for params in plot_blocks_data.values())
            if total_params == 0:
                return False, "Нет параметров для анализа"
            
            # Проверка доступности данных в data_loader
            if not hasattr(self.data_loader, 'data') or self.data_loader.data is None:
                return False, "Данные не загружены в data_loader"
            
            return True, ""
            
        except Exception as e:
            return False, f"Ошибка валидации: {e}"
    
    def get_available_formats(self) -> List[str]:
        """Получение списка доступных форматов отчетов"""
        formats = ['txt', 'csv']
        
        # Проверка доступности Excel
        try:
            import openpyxl
            formats.append('xlsx')
        except ImportError:
            pass
        
        # Проверка доступности PDF
        try:
            from reportlab.pdfgen import canvas
            formats.append('pdf')
        except ImportError:
            pass
        
        return formats
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            if self.pdf_renderer:
                if hasattr(self.pdf_renderer, 'cleanup'):
                    self.pdf_renderer.cleanup()
            
            self.report_history.clear()
            self.logger.info("ReportManager очищен")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки ReportManager: {e}")
