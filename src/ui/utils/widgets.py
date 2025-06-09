"""
Фабрика виджетов и утилиты для создания UI компонентов
"""
import tkinter as tk
from tkinter import ttk
from typing import Tuple, List, Dict, Any, Optional

class WidgetFactory:
    """Фабрика для создания стандартизированных виджетов"""
    
    @staticmethod
    def create_scrollable_frame(parent) -> Tuple[tk.Canvas, ttk.Scrollbar, ttk.Frame]:
        """Создание прокручиваемого контейнера"""
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)
        
        frame.bind("<Configure>", 
                  lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Привязка прокрутки мышью
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        return canvas, scrollbar, frame
    
    @staticmethod
    def create_labeled_entry(parent, label_text: str, 
                           entry_width: int = 20) -> Tuple[ttk.Label, ttk.Entry]:
        """Создание поля ввода с меткой"""
        label = ttk.Label(parent, text=label_text)
        entry = ttk.Entry(parent, width=entry_width)
        return label, entry
    
    @staticmethod
    def create_button_group(parent, buttons_config: List[Dict[str, Any]]) -> List[ttk.Button]:
        """Создание группы кнопок"""
        buttons = []
        for config in buttons_config:
            btn = ttk.Button(
                parent,
                text=config.get('text', 'Button'),
                command=config.get('command'),
                style=config.get('style', 'TButton')
            )
            buttons.append(btn)
        return buttons
    
    @staticmethod
    def create_info_panel(parent, title: str = "Информация") -> Tuple[ttk.LabelFrame, tk.Text]:
        """Создание информационной панели"""
        frame = ttk.LabelFrame(parent, text=title)
        
        text_widget = tk.Text(
            frame,
            wrap=tk.WORD,
            height=15,
            width=35,
            font=('Consolas', 9),
            bg='#f8f8f8',
            fg='#333333',
            relief='flat',
            borderwidth=1
        )
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        return frame, text_widget
    
    @staticmethod
    def create_visualization_panel(parent) -> tuple:
        """
        Создание панели визуализации с вкладками сверху (аналог старого base_ui.py)
        Возвращает: viz_frame, params_panel, plots_panel, notebook
        """
        viz_frame = ttk.LabelFrame(parent, text="Визуализация и анализ")
        viz_frame.grid_rowconfigure(0, weight=1)
        viz_frame.grid_columnconfigure(0, weight=1)
        paned = tk.PanedWindow(viz_frame, orient=tk.HORIZONTAL)
        paned.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        params_panel = ttk.Frame(paned, width=300)
        paned.add(params_panel, minsize=250)
        plots_panel = ttk.Frame(paned, width=600)
        paned.add(plots_panel, minsize=600)
        notebook = ttk.Notebook(plots_panel)
        notebook.grid(row=0, column=0, sticky="nsew")
        plots_panel.grid_rowconfigure(0, weight=1)
        plots_panel.grid_columnconfigure(0, weight=1)
        return viz_frame, params_panel, plots_panel, notebook

    @staticmethod
    def create_plot_controls(parent, build_command=None, report_command=None, export_command=None) -> ttk.Frame:
        """
        Создание панели управления графиками (аналог base_ui.py)
        """
        controls_frame = ttk.Frame(parent)
        controls_frame.grid_columnconfigure(0, weight=1)
        if build_command:
            ttk.Button(controls_frame, text="Построить графики", command=build_command, style='Accent.TButton').grid(
                row=0, column=0, padx=2, pady=5, sticky="ew")
        if report_command:
            ttk.Button(controls_frame, text="Отчет", command=report_command, style='Success.TButton').grid(
                row=0, column=1, padx=2, pady=5, sticky="ew")
        if export_command:
            ttk.Button(controls_frame, text="Экспорт графиков", command=export_command, style='Warning.TButton').grid(
                row=0, column=2, padx=2, pady=5, sticky="ew")
        return controls_frame

class TooltipMixin:
    """
    Миксин для добавления всплывающих подсказок
    """
    @staticmethod
    def create_tooltip(widget, text: str):
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(
                tooltip,
                text=text,
                background="#ffffe0",
                foreground="#000000",
                relief="solid",
                borderwidth=1,
                font=("Arial", 9)
            )
            label.pack()
            widget.tooltip = tooltip
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

class ProgressManager:
    """
    Менеджер для управления прогресс-барами
    """
    def __init__(self, progress_widget, status_label=None):
        self.progress = progress_widget
        self.status_label = status_label
        self.is_active = False
    def start(self, message: str = "Обработка..."):
        self.is_active = True
        self.progress.configure(mode='indeterminate')
        self.progress.start()
        if self.status_label:
            self.status_label.config(text=message)
    def update(self, value: int, message: str = None):
        if not self.is_active:
            return
        self.progress.configure(mode='determinate')
        self.progress['value'] = value
        if message and self.status_label:
            self.status_label.config(text=message)
    def stop(self, message: str = "Готово"):
        self.is_active = False
        self.progress.stop()
        self.progress['value'] = 0
        if self.status_label:
            self.status_label.config(text=message)
