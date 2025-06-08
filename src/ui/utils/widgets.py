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

class TooltipMixin:
    """Миксин для добавления всплывающих подсказок"""
    
    @staticmethod
    def create_tooltip(widget, text: str):
        """Создание всплывающей подсказки"""
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
