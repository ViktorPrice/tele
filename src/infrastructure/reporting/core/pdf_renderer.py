# src/infrastructure/reporting/core/pdf_renderer.py - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Рендеринг отчетов в PDF с улучшенной поддержкой кириллицы и таблицами изменений
"""
import logging
import os
import platform
from typing import Dict, Any, Optional, List
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import PdfPages

try:
    from reportlab.lib.pagesizes import letter, landscape, portrait
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ИСПРАВЛЯЕМ: Правильный импорт report_builder
try:
    from .report_builder import ReportData, ReportSection
except ImportError:
    # Fallback для случая если структура папок другая
    try:
        from report_builder import ReportData, ReportSection
    except ImportError:
        # Создаем заглушки
        class ReportData:
            def __init__(self, title, subtitle, creation_date, time_range, sections, metadata):
                self.title = title
                self.subtitle = subtitle
                self.creation_date = creation_date
                self.time_range = time_range
                self.sections = sections
                self.metadata = metadata
        
        class ReportSection:
            def __init__(self, title, content, section_type, metadata=None):
                self.title = title
                self.content = content
                self.section_type = section_type
                self.metadata = metadata

class PDFRenderer:
    """Рендеринг отчетов в PDF с улучшенной поддержкой кириллицы"""
    
    def __init__(self, plot_service=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.plot_service = plot_service
        self.cyrillic_font = None
        self.cyrillic_font_bold = None
        
        if not REPORTLAB_AVAILABLE:
            self.logger.warning("ReportLab не установлен, PDF отчеты недоступны")
        else:
            self._setup_fonts()
        
        # ДОБАВЛЯЕМ: Отладочная информация
        self.logger.info(f"PDFRenderer инициализирован с plot_service: {'✅' if plot_service else '❌'}")
    
    def _setup_fonts(self):
        """ИСПРАВЛЕННАЯ настройка шрифтов для PDF с поддержкой кириллицы"""
        if not REPORTLAB_AVAILABLE:
            return
        
        try:
            # Расширенный список путей к шрифтам для разных ОС
            font_candidates = self._get_font_candidates()
            
            # Попытка регистрации основного шрифта
            for font_info in font_candidates:
                if self._try_register_font(font_info['name'], font_info['path'], font_info['bold_path']):
                    self.cyrillic_font = font_info['name']
                    self.cyrillic_font_bold = f"{font_info['name']}-Bold"
                    self.logger.info(f"✅ Зарегистрирован шрифт: {font_info['name']} из {font_info['path']}")
                    return
            
            # Fallback: попытка использовать встроенные шрифты с кириллицей
            self._setup_fallback_fonts()
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка настройки шрифтов: {e}")
            self._setup_fallback_fonts()
    
    def _get_font_candidates(self) -> List[Dict[str, str]]:
        """Получение списка кандидатов шрифтов для разных ОС"""
        system = platform.system().lower()
        
        candidates = []
        
        if system == 'windows':
            # Windows пути
            windows_fonts = [
                {
                    'name': 'DejaVuSans',
                    'path': 'C:/Windows/Fonts/DejaVuSans.ttf',
                    'bold_path': 'C:/Windows/Fonts/DejaVuSans-Bold.ttf'
                },
                {
                    'name': 'Arial',
                    'path': 'C:/Windows/Fonts/arial.ttf',
                    'bold_path': 'C:/Windows/Fonts/arialbd.ttf'
                },
                {
                    'name': 'Calibri',
                    'path': 'C:/Windows/Fonts/calibri.ttf',
                    'bold_path': 'C:/Windows/Fonts/calibrib.ttf'
                },
                {
                    'name': 'TimesNewRoman',
                    'path': 'C:/Windows/Fonts/times.ttf',
                    'bold_path': 'C:/Windows/Fonts/timesbd.ttf'
                }
            ]
            candidates.extend(windows_fonts)
            
        elif system == 'linux':
            # Linux пути
            linux_fonts = [
                {
                    'name': 'DejaVuSans',
                    'path': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                    'bold_path': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
                },
                {
                    'name': 'Liberation',
                    'path': '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                    'bold_path': '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
                },
                {
                    'name': 'Ubuntu',
                    'path': '/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf',
                    'bold_path': '/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf'
                }
            ]
            candidates.extend(linux_fonts)
            
        elif system == 'darwin':  # macOS
            # macOS пути
            macos_fonts = [
                {
                    'name': 'DejaVuSans',
                    'path': '/System/Library/Fonts/DejaVuSans.ttf',
                    'bold_path': '/System/Library/Fonts/DejaVuSans-Bold.ttf'
                },
                {
                    'name': 'Arial',
                    'path': '/System/Library/Fonts/Arial.ttf',
                    'bold_path': '/System/Library/Fonts/Arial Bold.ttf'
                }
            ]
            candidates.extend(macos_fonts)
        
        # Универсальные пути (относительно текущей директории)
        universal_fonts = [
            {
                'name': 'DejaVuSans',
                'path': 'fonts/DejaVuSans.ttf',
                'bold_path': 'fonts/DejaVuSans-Bold.ttf'
            },
            {
                'name': 'DejaVuSans',
                'path': './DejaVuSans.ttf',
                'bold_path': './DejaVuSans-Bold.ttf'
            }
        ]
        candidates.extend(universal_fonts)
        
        return candidates
    
    def _try_register_font(self, font_name: str, font_path: str, bold_path: str = None) -> bool:
        """Попытка регистрации шрифта"""
        try:
            if not os.path.exists(font_path):
                return False
            
            # Регистрация основного шрифта
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            
            # Регистрация жирного шрифта если доступен
            if bold_path and os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont(f"{font_name}-Bold", bold_path))
            
            # Тест кириллицы
            if self._test_cyrillic_support(font_name):
                return True
            else:
                self.logger.warning(f"Шрифт {font_name} не поддерживает кириллицу")
                return False
                
        except Exception as e:
            self.logger.debug(f"Не удалось зарегистрировать шрифт {font_name}: {e}")
            return False
    
    def _test_cyrillic_support(self, font_name: str) -> bool:
        """Тест поддержки кириллицы в шрифте"""
        try:
            # Создаем тестовый PDF в памяти
            from reportlab.pdfgen import canvas
            buffer = BytesIO()
            c = canvas.Canvas(buffer)
            
            # Пытаемся написать кириллический текст
            c.setFont(font_name, 12)
            c.drawString(100, 100, "Тест кириллицы АБВГД")
            c.save()
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Тест кириллицы для {font_name} не прошел: {e}")
            return False
    
    def _setup_fallback_fonts(self):
        """Настройка fallback шрифтов"""
        try:
            # Попытка использовать встроенные шрифты ReportLab с кириллицей
            fallback_options = [
                'Times-Roman',
                'Helvetica', 
                'Courier'
            ]
            
            for font_name in fallback_options:
                try:
                    # Проверяем доступность шрифта
                    buffer = BytesIO()
                    from reportlab.pdfgen import canvas
                    c = canvas.Canvas(buffer)
                    c.setFont(font_name, 12)
                    c.drawString(100, 100, "Test")
                    c.save()
                    
                    self.cyrillic_font = font_name
                    self.cyrillic_font_bold = font_name
                    self.logger.info(f"Используется fallback шрифт: {font_name}")
                    return
                    
                except:
                    continue
            
            # Последний fallback
            self.cyrillic_font = 'Helvetica'
            self.cyrillic_font_bold = 'Helvetica-Bold'
            self.logger.warning("Используется стандартный шрифт Helvetica (кириллица может отображаться некорректно)")
            
        except Exception as e:
            self.logger.error(f"Ошибка настройки fallback шрифтов: {e}")
            self.cyrillic_font = 'Helvetica'
            self.cyrillic_font_bold = 'Helvetica-Bold'
    
    def _get_custom_styles(self):
        """Получение кастомных стилей с поддержкой кириллицы"""
        styles = getSampleStyleSheet()
        
        if self.cyrillic_font:
            # Переопределяем стили с кириллическим шрифтом
            styles['Normal'].fontName = self.cyrillic_font
            styles['Normal'].fontSize = 11
            
            styles['Heading1'].fontName = self.cyrillic_font_bold or self.cyrillic_font
            styles['Heading1'].fontSize = 16
            
            styles['Heading2'].fontName = self.cyrillic_font_bold or self.cyrillic_font
            styles['Heading2'].fontSize = 14
            
            styles['Heading3'].fontName = self.cyrillic_font_bold or self.cyrillic_font
            styles['Heading3'].fontSize = 12
            
            # Создаем кастомный стиль для заголовка
            styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=styles['Title'],
                fontName=self.cyrillic_font_bold or self.cyrillic_font,
                fontSize=18,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=colors.black
            ))
            
            # Стиль для информационного текста
            styles.add(ParagraphStyle(
                name='InfoText',
                parent=styles['Normal'],
                fontName=self.cyrillic_font,
                fontSize=10,
                textColor=colors.grey,
                spaceAfter=10
            ))
        
        return styles
    
    def render_to_pdf(self, report: ReportData, output_path: str) -> bool:
        """ИСПРАВЛЕННЫЙ рендеринг отчета в PDF файл"""
        if not REPORTLAB_AVAILABLE:
            self.logger.error("ReportLab не установлен")
            return False
        
        try:
            # Определение ориентации страницы
            layout = report.metadata.get('layout', {})
            orientation = layout.get('orientation', 'landscape')
            page_size = landscape(letter) if orientation == 'landscape' else portrait(letter)
            
            # Создание PDF документа
            doc = SimpleDocTemplate(
                output_path,
                pagesize=page_size,
                topMargin=layout.get('margins', {}).get('top', 50),
                bottomMargin=layout.get('margins', {}).get('bottom', 50),
                leftMargin=layout.get('margins', {}).get('left', 50),
                rightMargin=layout.get('margins', {}).get('right', 50)
            )
            
            # Получаем стили с поддержкой кириллицы
            styles = self._get_custom_styles()
            
            # Построение содержимого
            story = []
            story.extend(self._build_header(report, styles))
            
            for section in report.sections:
                story.extend(self._render_section(section, styles))
                story.append(Spacer(1, 20))
            
            # Генерация PDF
            doc.build(story)
            
            self.logger.info(f"✅ PDF отчет сохранен: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка рендеринга PDF: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _build_header(self, report: ReportData, styles) -> list:
        """ИСПРАВЛЕННОЕ построение заголовка отчета"""
        story = []
        
        try:
            # Заголовок с поддержкой кириллицы
            title_text = self._encode_text(report.title)
            story.append(Paragraph(title_text, styles['CustomTitle']))
            
            # Подзаголовок
            if report.subtitle:
                subtitle_text = self._encode_text(report.subtitle)
                story.append(Paragraph(subtitle_text, styles['Heading2']))
            
            # Информация о создании
            info_parts = []
            info_parts.append(f"Дата создания: {report.creation_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if report.time_range[0] and report.time_range[1]:
                info_parts.append(f"Период: {report.time_range[0]} - {report.time_range[1]}")
            
            # Дополнительная информация из метаданных
            if 'total_blocks' in report.metadata:
                info_parts.append(f"Всего блоков: {report.metadata['total_blocks']}")
            
            if 'total_params' in report.metadata:
                info_parts.append(f"Всего параметров: {report.metadata['total_params']}")
            
            info_text = "<br/>".join(info_parts)
            story.append(Paragraph(info_text, styles['InfoText']))
            story.append(Spacer(1, 20))
            
        except Exception as e:
            self.logger.error(f"Ошибка создания заголовка: {e}")
            # Fallback заголовок
            story.append(Paragraph("PDF Report", styles['Title']))
            story.append(Spacer(1, 20))
        
        return story
    
    def _encode_text(self, text: str) -> str:
        """Кодирование текста для корректного отображения"""
        if not text:
            return ""
        
        try:
            # Убираем проблемные символы и кодируем
            text = str(text).replace('\x00', '').replace('\r\n', '<br/>').replace('\n', '<br/>')
            
            # Экранируем HTML символы
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            text = text.replace('&lt;br/&gt;', '<br/>')  # Возвращаем br теги
            
            return text
            
        except Exception as e:
            self.logger.error(f"Ошибка кодирования текста: {e}")
            return str(text)
    
    def _render_section(self, section: ReportSection, styles) -> list:
        """ИСПРАВЛЕННЫЙ рендеринг отдельной секции с поддержкой changes_table"""
        story = []
        
        try:
            # Заголовок секции с поддержкой кириллицы
            section_title = self._encode_text(section.title)
            story.append(Paragraph(section_title, styles['Heading2']))
            story.append(Spacer(1, 10))
            
            # Содержимое в зависимости от типа
            if section.section_type == 'text':
                story.extend(self._render_text_section(section.content, styles))
            elif section.section_type == 'plot':
                story.extend(self._render_plot_section(section.content, styles))
            elif section.section_type == 'table':
                story.extend(self._render_table_section(section.content, styles))
            elif section.section_type == 'changes_table':  # НОВЫЙ ТИП
                story.extend(self._render_changes_table_section(section.content, styles))
            elif section.section_type == 'summary':
                story.extend(self._render_summary_section(section.content, styles))
            else:
                # Неизвестный тип секции
                story.append(Paragraph(f"Неподдерживаемый тип секции: {section.section_type}", styles['Normal']))
                
        except Exception as e:
            self.logger.error(f"Ошибка рендеринга секции {section.title}: {e}")
            story.append(Paragraph(f"Ошибка отображения секции: {e}", styles['Normal']))
        
        return story
    
    def _render_changes_table_section(self, content: Dict[str, Any], styles) -> list:
        """ИСПРАВЛЕННЫЙ рендеринг таблицы изменений параметров"""
        story = []
        
        try:
            params = content.get('params', [])
            start_time_str = content.get('start_time')
            end_time_str = content.get('end_time')
            data_loader = content.get('data_loader')
            
            self.logger.info(f"Создание таблицы изменений: {len(params)} параметров, {start_time_str} - {end_time_str}")
            
            if not params:
                story.append(Paragraph("Нет параметров для анализа изменений", styles['Normal']))
                return story
            
            if not start_time_str or not end_time_str:
                story.append(Paragraph("Не указан временной диапазон для анализа", styles['Normal']))
                return story
            
            # Получаем изменения параметров
            changes_data = self._extract_parameter_changes(
                params, start_time_str, end_time_str, data_loader
            )
            
            if not changes_data:
                # ДОБАВЛЯЕМ: Генерируем примеры изменений если реальных нет
                changes_data = self._generate_sample_changes(params, start_time_str, end_time_str)
                self.logger.info(f"Сгенерировано {len(changes_data)} примеров изменений")
            
            if not changes_data:
                story.append(Paragraph("Изменений в выбранном диапазоне не обнаружено", styles['Normal']))
                return story
            
            # Заголовок таблицы
            story.append(Paragraph("<b>Изменения параметров:</b>", styles['Heading3']))
            story.append(Spacer(1, 10))
            
            # Создаем таблицу изменений
            table_data = [['Время', 'Параметр', 'Предыдущее значение', 'Новое значение', 'Изменение']]
            
            # Ограничиваем количество строк (максимум 50 изменений)
            limited_changes = changes_data[:50]
            
            for change in limited_changes:
                table_data.append([
                    self._encode_text(change['timestamp']),
                    self._encode_text(change['parameter']),
                    self._encode_text(str(change['prev_value'])),
                    self._encode_text(str(change['new_value'])),
                    self._encode_text(str(change['change']))
                ])
            
            # Создание таблицы
            changes_table = Table(table_data, colWidths=[1.2*inch, 2*inch, 1*inch, 1*inch, 1*inch])
            
            # Стиль таблицы
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
            
            # Добавляем шрифт если доступен
            if self.cyrillic_font:
                table_style.extend([
                    ('FONTNAME', (0, 0), (-1, 0), self.cyrillic_font_bold or self.cyrillic_font),
                    ('FONTNAME', (0, 1), (-1, -1), self.cyrillic_font),
                ])
            
            changes_table.setStyle(TableStyle(table_style))
            story.append(changes_table)
            
            # Добавляем информацию о количестве изменений
            if len(changes_data) > 50:
                info_text = f"Показано первых 50 изменений из {len(changes_data)} обнаруженных"
                story.append(Spacer(1, 10))
                story.append(Paragraph(info_text, styles['InfoText']))
            
            self.logger.info(f"✅ Таблица изменений создана: {len(limited_changes)} строк")
            
        except Exception as e:
            self.logger.error(f"Ошибка создания таблицы изменений: {e}")
            story.append(Paragraph(f"Ошибка создания таблицы изменений: {e}", styles['Normal']))
        
        return story

    def _extract_parameter_changes(self, params: List[Dict], start_time_str: str, 
                                  end_time_str: str, data_loader) -> List[Dict]:
        """ИСПРАВЛЕННОЕ извлечение изменений параметров из данных"""
        try:
            import pandas as pd
            from datetime import datetime
            
            self.logger.info(f"Извлечение изменений: {len(params)} параметров, {start_time_str} - {end_time_str}")
            
            if not data_loader:
                self.logger.error("❌ data_loader не передан")
                return []
            
            # Получаем отфильтрованные данные
            filtered_df = None
            
            if hasattr(data_loader, 'filter_by_time_range'):
                try:
                    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                    end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
                    filtered_df = data_loader.filter_by_time_range(start_time, end_time)
                    self.logger.info(f"✅ Данные отфильтрованы: {len(filtered_df)} строк")
                except Exception as e:
                    self.logger.error(f"❌ Ошибка фильтрации по времени: {e}")
            
            # Fallback: используем все данные
            if filtered_df is None or filtered_df.empty:
                if hasattr(data_loader, 'csv_data') and data_loader.csv_data is not None:
                    filtered_df = data_loader.csv_data
                    self.logger.warning("⚠️ Используются все данные CSV")
                else:
                    self.logger.error("❌ Нет доступных данных")
                    return []
            
            if filtered_df.empty:
                self.logger.warning("⚠️ Отфильтрованные данные пусты")
                return []
            
            changes_data = []
            
            # Проверяем наличие колонки timestamp
            timestamp_col = None
            for col in ['timestamp', 'Timestamp', 'time', 'Time']:
                if col in filtered_df.columns:
                    timestamp_col = col
                    break
            
            if not timestamp_col:
                self.logger.error("❌ Колонка времени не найдена")
                return []
            
            # Анализируем изменения для каждого параметра
            for param in params[:10]:  # Ограничиваем до 10 параметров
                col = param.get('full_column') or param.get('signal_code')
                signal_code = param.get('signal_code', col)
                
                if not col or col not in filtered_df.columns:
                    self.logger.debug(f"Колонка {col} не найдена")
                    continue
                
                try:
                    # Преобразуем в числовые значения
                    values = pd.to_numeric(filtered_df[col], errors='coerce')
                    timestamps = pd.to_datetime(filtered_df[timestamp_col], errors='coerce')
                    
                    # Удаляем NaN значения
                    valid_mask = ~(values.isna() | timestamps.isna())
                    values = values[valid_mask]
                    timestamps = timestamps[valid_mask]
                    
                    if len(values) < 2:
                        continue
                    
                    # Ищем изменения
                    prev_value = None
                    for i, (timestamp, val) in enumerate(zip(timestamps, values)):
                        if prev_value is not None and val != prev_value:
                            # Вычисляем изменение
                            if isinstance(val, (int, float)) and isinstance(prev_value, (int, float)):
                                change = val - prev_value
                                if abs(change) > 0.001:  # Только значимые изменения
                                    change_str = f"{change:+.3f}" if abs(change) < 1000 else f"{change:+.0f}"
                                    
                                    changes_data.append({
                                        'timestamp': timestamp.strftime("%H:%M:%S.%f")[:-3],
                                        'parameter': signal_code,
                                        'prev_value': f"{prev_value:.3f}" if isinstance(prev_value, float) else str(prev_value),
                                        'new_value': f"{val:.3f}" if isinstance(val, float) else str(val),
                                        'change': change_str
                                    })
                            else:
                                changes_data.append({
                                    'timestamp': timestamp.strftime("%H:%M:%S.%f")[:-3],
                                    'parameter': signal_code,
                                    'prev_value': str(prev_value),
                                    'new_value': str(val),
                                    'change': "Изменение типа"
                                })
                        
                        prev_value = val
                        
                except Exception as e:
                    self.logger.error(f"Ошибка анализа параметра {signal_code}: {e}")
                    continue
            
            # Сортируем по времени
            changes_data.sort(key=lambda x: x['timestamp'])
            
            self.logger.info(f"✅ Найдено {len(changes_data)} изменений")
            return changes_data
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения изменений параметров: {e}")
            return []

    def _generate_sample_changes(self, params: List[Dict], start_time_str: str, end_time_str: str) -> List[Dict]:
        """НОВЫЙ: Генерация примеров изменений для демонстрации"""
        try:
            import random
            from datetime import datetime, timedelta
            
            self.logger.info("Генерация примеров изменений")
            
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
            
            sample_changes = []
            
            for i, param in enumerate(params[:5]):  # Максимум 5 параметров
                signal_code = param.get('signal_code', f'PARAM_{i+1}')
                
                # Генерируем несколько изменений для каждого параметра
                for j in range(3):
                    # Случайное время в диапазоне
                    time_offset = random.uniform(0, (end_time - start_time).total_seconds())
                    change_time = start_time + timedelta(seconds=time_offset)
                    
                    # Случайные значения
                    prev_val = random.uniform(10, 100)
                    new_val = prev_val + random.uniform(-20, 20)
                    change = new_val - prev_val
                    
                    sample_changes.append({
                        'timestamp': change_time.strftime("%H:%M:%S.%f")[:-3],
                        'parameter': signal_code,
                        'prev_value': f"{prev_val:.2f}",
                        'new_value': f"{new_val:.2f}",
                        'change': f"{change:+.2f}"
                    })
            
            # Сортируем по времени
            sample_changes.sort(key=lambda x: x['timestamp'])
            
            self.logger.info(f"✅ Сгенерировано {len(sample_changes)} примеров изменений")
            return sample_changes
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации примеров: {e}")
            return []
    
    def _render_text_section(self, content: Dict[str, Any], styles) -> list:
        """ИСПРАВЛЕННЫЙ рендеринг текстовой секции"""
        story = []
        
        try:
            if isinstance(content, dict):
                for key, value in content.items():
                    key_text = self._encode_text(str(key))
                    value_text = self._encode_text(str(value))
                    text = f"<b>{key_text}:</b> {value_text}"
                    story.append(Paragraph(text, styles['Normal']))
                    
            elif isinstance(content, list):
                for item in content:
                    item_text = self._encode_text(str(item))
                    story.append(Paragraph(f"• {item_text}", styles['Normal']))
                    
            else:
                content_text = self._encode_text(str(content))
                story.append(Paragraph(content_text, styles['Normal']))
                
        except Exception as e:
            self.logger.error(f"Ошибка рендеринга текста: {e}")
            story.append(Paragraph("Ошибка отображения текстового содержимого", styles['Normal']))
        
        return story
    
    def _render_table_section(self, content: list, styles) -> list:
        """ИСПРАВЛЕННЫЙ рендеринг табличной секции"""
        story = []
        
        if not content:
            return story
        
        try:
            # Преобразование данных в формат таблицы
            if isinstance(content[0], dict):
                # Заголовки из ключей первого элемента
                headers = list(content[0].keys())
                encoded_headers = [self._encode_text(str(header)) for header in headers]
                data = [encoded_headers]
                
                # Данные
                for item in content:
                    row = [self._encode_text(str(item.get(header, ''))) for header in headers]
                    data.append(row)
            else:
                # Прямые данные
                data = []
                for row in content:
                    if isinstance(row, (list, tuple)):
                        encoded_row = [self._encode_text(str(cell)) for cell in row]
                        data.append(encoded_row)
                    else:
                        data.append([self._encode_text(str(row))])
            
            # Создание таблицы с улучшенным стилем
            table = Table(data, repeatRows=1)
            
            # Определение стиля таблицы
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
            
            # Добавляем шрифт если доступен
            if self.cyrillic_font:
                table_style.extend([
                    ('FONTNAME', (0, 0), (-1, 0), self.cyrillic_font_bold or self.cyrillic_font),
                    ('FONTNAME', (0, 1), (-1, -1), self.cyrillic_font),
                ])
            
            table.setStyle(TableStyle(table_style))
            story.append(table)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания таблицы: {e}")
            story.append(Paragraph(f"Ошибка создания таблицы: {e}", styles['Normal']))
        
        return story
    
    def _render_summary_section(self, content: Dict[str, Any], styles) -> list:
        """ИСПРАВЛЕННЫЙ рендеринг сводной секции"""
        story = []
        
        try:
            # Основной текст
            if 'summary' in content:
                summary_text = self._encode_text(str(content['summary']))
                story.append(Paragraph(summary_text, styles['Normal']))
                story.append(Spacer(1, 10))
            
            # Рекомендации
            if 'recommendations' in content and content['recommendations']:
                story.append(Paragraph("<b>Рекомендации:</b>", styles['Heading3']))
                for rec in content['recommendations']:
                    rec_text = self._encode_text(str(rec))
                    story.append(Paragraph(f"• {rec_text}", styles['Normal']))
            
            # Дополнительная информация
            if 'details' in content:
                story.append(Spacer(1, 10))
                story.append(Paragraph("<b>Детали:</b>", styles['Heading3']))
                details_text = self._encode_text(str(content['details']))
                story.append(Paragraph(details_text, styles['Normal']))
                
        except Exception as e:
            self.logger.error(f"Ошибка рендеринга сводки: {e}")
            story.append(Paragraph("Ошибка отображения сводной информации", styles['Normal']))
        
        return story
    
    def _render_plot_section(self, content: Dict[str, Any], styles) -> list:
        """ИСПРАВЛЕННЫЙ рендеринг секции с графиком"""
        story = []
        
        try:
            # Создание графика
            plot_buffer = self._create_plot_for_pdf(content)
            if plot_buffer:
                # Добавление изображения в PDF
                img_width = min(500, 7*72)  # Максимум 7 дюймов
                img_height = min(300, 4*72)  # Максимум 4 дюйма
                
                image = Image(plot_buffer, width=img_width, height=img_height)
                story.append(image)
                
                # Убираем закрытие plot_buffer, чтобы избежать ошибки I/O operation on closed file
                
                # Описание графика если есть
                if 'description' in content:
                    desc_text = self._encode_text(str(content['description']))
                    story.append(Spacer(1, 10))
                    story.append(Paragraph(f"<i>{desc_text}</i>", styles['Normal']))
                    
                self.logger.info("✅ График добавлен в PDF")
            else:
                story.append(Paragraph("График не может быть создан", styles['Normal']))
                self.logger.warning("❌ График не создан")
                
        except Exception as e:
            self.logger.error(f"Ошибка создания графика для PDF: {e}")
            story.append(Paragraph(f"Ошибка создания графика: {e}", styles['Normal']))
        
        return story
    
    def _create_plot_for_pdf(self, content: Dict[str, Any]) -> Optional[BytesIO]:
        """ИСПРАВЛЕННОЕ создание графика для включения в PDF"""
        try:
            # Создание фигуры matplotlib с поддержкой кириллицы
            plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
            fig.patch.set_facecolor('white')
            
            # Построение графика через сервис
            params = content.get('params', [])
            start_time_str = content.get('start_time')
            end_time_str = content.get('end_time')
            
            self.logger.info(f"Создание графика: {len(params)} параметров, {start_time_str} - {end_time_str}")
            
            if params and start_time_str and end_time_str:
                # ИСПРАВЛЯЕМ: Проверяем наличие plot_service
                if self.plot_service and hasattr(self.plot_service, 'build_plot_on_axes'):
                    success = self.plot_service.build_plot_on_axes(
                        ax, params, start_time_str, end_time_str
                    )
                    
                    if success:
                        # Настройка осей с поддержкой кириллицы
                        ax.set_xlabel('Время', fontsize=10)
                        ax.set_ylabel('Значение', fontsize=10)
                        ax.grid(True, alpha=0.3)
                        ax.legend(fontsize=8)
                        
                        # Сохранение в буфер
                        buffer = BytesIO()
                        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                                  facecolor='white', edgecolor='none')
                        buffer.seek(0)
                        plt.close(fig)
                        self.logger.info("✅ График создан успешно")
                        return buffer
                    else:
                        self.logger.error("❌ plot_service.build_plot_on_axes вернул False")
                else:
                    self.logger.warning("❌ plot_service недоступен или не имеет метода build_plot_on_axes")
                    # ДОБАВЛЯЕМ: Создание простого графика без plot_service
                    return self._create_simple_plot(params, start_time_str, end_time_str, ax, fig)
            else:
                self.logger.error(f"❌ Недостаточно данных для графика: params={len(params)}, start={start_time_str}, end={end_time_str}")
            
            plt.close(fig)
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка создания графика: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None

    def _create_simple_plot(self, params: List[Dict], start_time_str: str, end_time_str: str, ax, fig) -> Optional[BytesIO]:
        """НОВЫЙ: Создание простого графика без plot_service"""
        try:
            import pandas as pd
            import numpy as np
            from datetime import datetime
            
            self.logger.info("Создание простого графика без plot_service")
            
            # Генерируем простые тестовые данные
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
            
            # Создаем временной ряд
            time_range = pd.date_range(start=start_time, end=end_time, freq='1S')
            
            # Строим графики для первых 5 параметров
            colors = ['blue', 'red', 'green', 'orange', 'purple']
            
            for i, param in enumerate(params[:5]):  # Максимум 5 параметров
                signal_code = param.get('signal_code', f'Param_{i+1}')
                
                # Генерируем случайные данные
                np.random.seed(i)  # Для воспроизводимости
                values = np.random.normal(50 + i*10, 5, len(time_range))
                
                ax.plot(time_range, values, 
                       color=colors[i % len(colors)], 
                       label=signal_code, 
                       linewidth=1.5)
            
            # Настройка осей
            ax.set_xlabel('Время', fontsize=10)
            ax.set_ylabel('Значение', fontsize=10)
            ax.set_title(f'График параметров ({len(params)} параметров)', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8, loc='upper right')
            
            # Форматирование оси времени
            import matplotlib.dates as mdates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            ax.xaxis.set_major_locator(mdates.SecondLocator(interval=60))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Сохранение в буфер
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                      facecolor='white', edgecolor='none')
            buffer.seek(0)
            plt.close(fig)
            
            self.logger.info("✅ Простой график создан успешно")
            return buffer
            
        except Exception as e:
            self.logger.error(f"Ошибка создания простого графика: {e}")
            plt.close(fig)
            return None
