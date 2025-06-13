# src/infrastructure/reporting/core/report_manager.py - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Менеджер отчетов с поддержкой таблиц изменений
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# ИСПРАВЛЯЕМ: Правильные импорты
try:
    from .report_builder import ReportBuilder
    from .pdf_renderer import PDFRenderer
except ImportError:
    # Fallback для случая если структура папок другая
    try:
        from report_builder import ReportBuilder
        from pdf_renderer import PDFRenderer
    except ImportError:
        logging.error("Не удалось импортировать ReportBuilder или PDFRenderer")
        ReportBuilder = None
        PDFRenderer = None

class ReportManager:
    """Менеджер отчетов с полной функциональностью"""
    
    def __init__(self, data_loader=None, plot_service=None):
        self.data_loader = data_loader
        self.plot_service = plot_service
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Инициализация компонентов с проверкой
        if ReportBuilder is None or PDFRenderer is None:
            self.logger.error("ReportBuilder или PDFRenderer недоступны")
            self.report_builder = None
            self.pdf_renderer = None
        else:
            self.report_builder = ReportBuilder()
            self.pdf_renderer = PDFRenderer(plot_service)
        
        self.logger.info("ReportManager (только новая архитектура) инициализирован")
    
    def generate_telemetry_report(self, selected_params: List[Dict[str, Any]], 
                                start_time: datetime, end_time: datetime, 
                                output_path: str) -> bool:
        """ИСПРАВЛЕННАЯ генерация отчета по телеметрии с проверками"""
        try:
            if not self.report_builder or not self.pdf_renderer:
                self.logger.error("ReportBuilder или PDFRenderer не инициализированы")
                return False
                
            self.logger.info(f"Генерация отчета: {len(selected_params)} параметров, период {start_time} - {end_time}")
            
            # Подготовка данных для отчета
            report_data = {
                'plot_blocks_data': {'selected_params': selected_params},
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'subtitle': f"Период: {start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%Y-%m-%d %H:%M:%S')}",
                'data_loader': self.data_loader,  # ДОБАВЛЯЕМ data_loader
                'total_blocks': 1,
                'total_params': len(selected_params)
            }
            
            # Построение отчета
            report = self.report_builder.build_report('telemetry', report_data)
            
            # Рендеринг в PDF
            success = self.pdf_renderer.render_to_pdf(report, output_path)
            
            if success:
                self.logger.info(f"Отчет по телеметрии создан: {output_path}")
            else:
                self.logger.error("Ошибка создания отчета")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета по телеметрии: {e}")
            return False
    
    def generate_full_report(self, plot_blocks_data: Dict[str, Any], 
                           start_time: datetime, end_time: datetime, 
                           output_path: str) -> bool:
        """НОВЫЙ метод для совместимости со старым интерфейсом"""
        try:
            # Извлекаем параметры из plot_blocks_data
            if isinstance(plot_blocks_data, dict):
                selected_params = plot_blocks_data.get('selected_params', [])
            else:
                selected_params = plot_blocks_data
            
            return self.generate_telemetry_report(selected_params, start_time, end_time, output_path)
            
        except Exception as e:
            self.logger.error(f"Ошибка generate_full_report: {e}")
            return False
    
    def generate_summary_report(self, data: Dict[str, Any], output_path: str) -> bool:
        """Генерация сводного отчета"""
        try:
            # Построение отчета
            report = self.report_builder.build_report('summary', data)
            
            # Рендеринг в PDF
            success = self.pdf_renderer.render_to_pdf(report, output_path)
            
            if success:
                self.logger.info(f"Сводный отчет создан: {output_path}")
            else:
                self.logger.error("Ошибка создания сводного отчета")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации сводного отчета: {e}")
            return False
    
    def export_changes_to_csv(self, params: List[Dict[str, Any]], 
                             start_time: datetime, end_time: datetime, 
                             save_path: str) -> bool:
        """Экспорт изменений параметров в CSV"""
        try:
            if not self.data_loader:
                self.logger.error("data_loader не установлен")
                return False
            
            import pandas as pd
            
            filtered_df = self.data_loader.filter_by_time_range(start_time, end_time)
            changes_data = []
            
            for param in params:
                col = param.get('full_column')
                signal_code = param.get('signal_code', col)
                
                if col not in filtered_df.columns:
                    continue
                    
                values = pd.to_numeric(filtered_df[col], errors='coerce')
                if values.dropna().empty:
                    continue
                
                prev_value = None
                for i, val in enumerate(values):
                    if pd.isna(val):
                        continue
                        
                    if prev_value is not None and val != prev_value:
                        timestamp = filtered_df['timestamp'].iloc[i]
                        changes_data.append({
                            'Время': timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                            'Параметр': signal_code,
                            'Описание': param.get('description', ''),
                            'Предыдущее значение': prev_value,
                            'Новое значение': val,
                            'Изменение': val - prev_value if isinstance(val, (int, float)) and isinstance(prev_value, (int, float)) else 'N/A'
                        })
                    
                    prev_value = val
            
            if changes_data:
                changes_df = pd.DataFrame(changes_data)
                changes_df.to_csv(save_path, index=False, encoding='utf-8-sig')
                self.logger.info(f"Изменения экспортированы в CSV: {save_path}")
                return True
            else:
                self.logger.warning("Нет изменений для экспорта")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка экспорта изменений в CSV: {e}")
            return False

    def get_report_summary(self, plot_blocks_data: Dict[str, List[str]]) -> Dict[str, Any]:
        """Получение сводки по отчету"""
        try:
            total_blocks = len(plot_blocks_data)
            total_params = sum(len(params) for params in plot_blocks_data.values())
            
            summary = {
                'total_blocks': total_blocks,
                'total_parameters': total_params,
                'data_rows': len(self.data_loader.csv_data) if self.data_loader and self.data_loader.csv_data is not None else 0,
                'lines_count': len(self.data_loader.lines) if self.data_loader else 0,
                'blocks_info': {
                    block_id: {
                        'param_count': len(param_codes),
                        'param_codes': param_codes
                    }
                    for block_id, param_codes in plot_blocks_data.items()
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Ошибка получения сводки отчета: {e}")
            return {}

    def validate_report_data(self, plot_blocks_data: Dict[str, List[str]], 
                           start_time: datetime, end_time: datetime) -> tuple:
        """Валидация данных для генерации отчета"""
        try:
            issues = []
            
            if not plot_blocks_data:
                issues.append("Нет данных для отчета")
            
            if not self.data_loader or not self.data_loader.csv_data or self.data_loader.csv_data.empty:
                issues.append("Отсутствуют данные CSV")
            
            if start_time >= end_time:
                issues.append("Некорректный временной диапазон")
            
            # Проверка существования параметров
            missing_params = []
            if self.data_loader and hasattr(self.data_loader, 'parameters'):
                for block_id, param_codes in plot_blocks_data.items():
                    for param_code in param_codes:
                        if not any(p.get('signal_code') == param_code for p in self.data_loader.parameters):
                            missing_params.append(param_code)
            
            if missing_params:
                issues.append(f"Параметры не найдены: {', '.join(missing_params[:5])}")
            
            is_valid = len(issues) == 0
            return is_valid, issues
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации данных отчета: {e}")
            return False, [str(e)]
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.data_loader = None
            self.plot_service = None
            self.logger.info("ReportManager очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки ReportManager: {e}")
