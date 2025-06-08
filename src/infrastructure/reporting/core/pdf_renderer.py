"""
Рендеринг отчетов в PDF
"""
import logging
from typing import Dict, Any, Optional
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
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from .report_builder import ReportData, ReportSection

class PDFRenderer:
    """Рендеринг отчетов в PDF с поддержкой различных элементов"""
    
    def __init__(self, plot_service=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.plot_service = plot_service
        
        if not REPORTLAB_AVAILABLE:
            self.logger.warning("ReportLab не установлен, PDF отчеты недоступны")
        
        self._setup_fonts()
    
    def _setup_fonts(self):
        """Настройка шрифтов для PDF"""
        if not REPORTLAB_AVAILABLE:
            return
        
        try:
            # Попытка регистрации DejaVu Sans для кириллицы
            font_paths = [
                'DejaVuSans.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                'C:/Windows/Fonts/DejaVuSans.ttf'
            ]
            
            for font_path in font_paths:
                try:
                    import os
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
                        self.logger.info(f"Зарегистрирован шрифт: {font_path}")
                        return
                except Exception as e:
                    self.logger.debug(f"Не удалось загрузить шрифт {font_path}: {e}")
            
            self.logger.info("Используется стандартный шрифт")
            
        except Exception as e:
            self.logger.warning(f"Ошибка настройки шрифтов: {e}")
    
    def render_to_pdf(self, report: ReportData, output_path: str) -> bool:
        """Рендеринг отчета в PDF файл"""
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
            
            # Построение содержимого
            story = []
            story.extend(self._build_header(report))
            
            for section in report.sections:
                story.extend(self._render_section(section))
                story.append(Spacer(1, 20))
            
            # Генерация PDF
            doc.build(story)
            
            self.logger.info(f"PDF отчет сохранен: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка рендеринга PDF: {e}")
            return False
    
    def _build_header(self, report: ReportData) -> list:
        """Построение заголовка отчета"""
        styles = getSampleStyleSheet()
        story = []
        
        # Заголовок
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=20,
            alignment=1  # Центрирование
        )
        story.append(Paragraph(report.title, title_style))
        
        # Подзаголовок
        if report.subtitle:
            story.append(Paragraph(report.subtitle, styles['Heading2']))
        
        # Информация о создании
        info_text = f"Дата создания: {report.creation_date.strftime('%Y-%m-%d %H:%M:%S')}"
        if report.time_range[0] and report.time_range[1]:
            info_text += f"<br/>Период: {report.time_range[0]} - {report.time_range[1]}"
        
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _render_section(self, section: ReportSection) -> list:
        """Рендеринг отдельной секции"""
        styles = getSampleStyleSheet()
        story = []
        
        # Заголовок секции
        story.append(Paragraph(section.title, styles['Heading2']))
        story.append(Spacer(1, 10))
        
        # Содержимое в зависимости от типа
        if section.section_type == 'text':
            story.extend(self._render_text_section(section.content, styles))
        elif section.section_type == 'plot':
            story.extend(self._render_plot_section(section.content, styles))
        elif section.section_type == 'table':
            story.extend(self._render_table_section(section.content, styles))
        elif section.section_type == 'summary':
            story.extend(self._render_summary_section(section.content, styles))
        
        return story
    
    def _render_text_section(self, content: Dict[str, Any], styles) -> list:
        """Рендеринг текстовой секции"""
        story = []
        
        if isinstance(content, dict):
            for key, value in content.items():
                text = f"<b>{key}:</b> {value}"
                story.append(Paragraph(text, styles['Normal']))
        elif isinstance(content, list):
            for item in content:
                story.append(Paragraph(f"• {item}", styles['Normal']))
        else:
            story.append(Paragraph(str(content), styles['Normal']))
        
        return story
    
    def _render_plot_section(self, content: Dict[str, Any], styles) -> list:
        """Рендеринг секции с графиком"""
        story = []
        
        try:
            # Создание графика
            plot_buffer = self._create_plot_for_pdf(content)
            if plot_buffer:
                # Добавление изображения в PDF
                img = ImageReader(plot_buffer)
                from reportlab.platypus import Image
                
                # Определение размера изображения
                img_width = 500
                img_height = 300
                
                image = Image(plot_buffer, width=img_width, height=img_height)
                story.append(image)
                
                plot_buffer.close()
            else:
                story.append(Paragraph("График не может быть создан", styles['Normal']))
                
        except Exception as e:
            self.logger.error(f"Ошибка создания графика для PDF: {e}")
            story.append(Paragraph(f"Ошибка создания графика: {e}", styles['Normal']))
        
        return story
    
    def _render_table_section(self, content: list, styles) -> list:
        """Рендеринг табличной секции"""
        story = []
        
        if not content:
            return story
        
        try:
            # Преобразование данных в формат таблицы
            if isinstance(content[0], dict):
                # Заголовки из ключей первого элемента
                headers = list(content[0].keys())
                data = [headers]
                
                # Данные
                for item in content:
                    row = [str(item.get(header, '')) for header in headers]
                    data.append(row)
            else:
                data = content
            
            # Создание таблицы
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания таблицы: {e}")
            story.append(Paragraph(f"Ошибка создания таблицы: {e}", styles['Normal']))
        
        return story
    
    def _render_summary_section(self, content: Dict[str, Any], styles) -> list:
        """Рендеринг сводной секции"""
        story = []
        
        # Основной текст
        if 'summary' in content:
            story.append(Paragraph(content['summary'], styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Рекомендации
        if 'recommendations' in content:
            story.append(Paragraph("<b>Рекомендации:</b>", styles['Heading3']))
            for rec in content['recommendations']:
                story.append(Paragraph(f"• {rec}", styles['Normal']))
        
        return story
    
    def _create_plot_for_pdf(self, content: Dict[str, Any]) -> Optional[BytesIO]:
        """Создание графика для включения в PDF"""
        if not self.plot_service:
            return None
        
        try:
            # Создание фигуры matplotlib
            fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
            fig.patch.set_facecolor('white')
            
            # Построение графика через сервис
            params = content.get('params', [])
            start_time = content.get('start_time')
            end_time = content.get('end_time')
            
            if params and start_time and end_time:
                success = self.plot_service.build_plot_on_axes(
                    ax, params, start_time, end_time
                )
                
                if success:
                    # Сохранение в буфер
                    buffer = BytesIO()
                    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                              facecolor='white', edgecolor='none')
                    buffer.seek(0)
                    plt.close(fig)
                    return buffer
            
            plt.close(fig)
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка создания графика: {e}")
            return None
