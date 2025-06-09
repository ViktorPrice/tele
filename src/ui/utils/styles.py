"""
Управление стилями и темами оформления
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any

class StyleManager:
    """Синглтон для управления стилями приложения"""
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.style = ttk.Style()
        self.current_theme = 'light'
        self._setup_themes()
        self._initialized = True
    
    def _setup_themes(self):
        """
        Настройка доступных тем (старая светлая тема)
        """
        self.themes = {
            'light': {
                'bg': '#f0f0f0',
                'fg': '#333333',
                'accent': '#0078d4',
                'success': '#107c10',
                'warning': '#ff8c00',
                'error': '#d13438',
                'select_bg': '#0078d4',
                'select_fg': '#ffffff',
                'notebook_tab_active': '#e1ecf4',
                'notebook_tab_selected': '#0078d4',
                'notebook_tab_fg': '#333333',
                'progress_trough': '#f0f0f0',
            },
            'dark': {
                'bg': '#2d2d2d',
                'fg': '#ffffff',
                'accent': '#0078d4',
                'success': '#107c10',
                'warning': '#ff8c00',
                'error': '#d13438',
                'select_bg': '#0078d4',
                'select_fg': '#ffffff',
                'notebook_tab_active': '#444444',
                'notebook_tab_selected': '#0078d4',
                'notebook_tab_fg': '#ffffff',
                'progress_trough': '#2d2d2d',
            }
        }
    
    def _configure_buttons(self, theme: Dict[str, str]):
        """Настройка стилей кнопок"""
        self.style.configure('Accent.TButton',
            background=theme['accent'],
            foreground='white',
            borderwidth=1,
            focuscolor='none')
        self.style.map('Accent.TButton',
            background=[('active', '#106ebe'), ('pressed', '#005a9e')])
        self.style.configure('Success.TButton',
            background=theme['success'],
            foreground='white',
            borderwidth=1)
        self.style.configure('Warning.TButton',
            background=theme['warning'],
            foreground='white',
            borderwidth=1)
        self.style.configure('Error.TButton',
            background=theme['error'],
            foreground='white',
            borderwidth=1)
    
    def _configure_labels(self, theme: Dict[str, str]):
        """Настройка стилей меток"""
        self.style.configure('TLabel',
            background=theme['bg'],
            foreground=theme['fg'])
        self.style.configure('Success.TLabel',
            foreground=theme['success'])
        self.style.configure('Warning.TLabel',
            foreground=theme['warning'])
        self.style.configure('Error.TLabel',
            foreground=theme['error'])
    
    def _configure_frames(self, theme: Dict[str, str]):
        """Настройка стилей фреймов"""
        self.style.configure('TFrame',
            background=theme['bg'])
    
    def _configure_notebook(self, theme: Dict[str, str]):
        """Настройка стилей вкладок"""
        self.style.configure('TNotebook',
            background=theme['bg'],
            borderwidth=1)
        self.style.configure('TNotebook.Tab',
            background=theme['bg'],
            foreground=theme['notebook_tab_fg'],
            padding=[12, 8])
        self.style.map('TNotebook.Tab',
            background=[('selected', theme['notebook_tab_selected']),
                        ('active', theme['notebook_tab_active'])])
    
    def _configure_progressbar(self, theme: Dict[str, str]):
        """Настройка стилей индикатора прогресса"""
        self.style.configure('TProgressbar',
            background=theme['accent'],
            troughcolor=theme['progress_trough'],
            borderwidth=1,
            lightcolor=theme['accent'],
            darkcolor=theme['accent'])
    
    def apply_theme(self, theme_name: str = 'light'):
        """Применение темы оформления"""
        if theme_name not in self.themes:
            theme_name = 'light'
        
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            self.style.theme_use('default')
        
        # Настройка компонентов
        self._configure_buttons(theme)
        self._configure_labels(theme)
        self._configure_frames(theme)
        self._configure_notebook(theme)
        self._configure_progressbar(theme)
        
        self.logger.info(f"Применена тема: {theme_name}")
