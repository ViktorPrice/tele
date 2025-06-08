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
        """Настройка доступных тем"""
        self.themes = {
            'light': {
                'bg': '#ffffff',
                'fg': '#000000',
                'accent': '#0078d4',
                'success': '#107c10',
                'warning': '#ff8c00',
                'error': '#d13438'
            },
            'dark': {
                'bg': '#2d2d2d',
                'fg': '#ffffff',
                'accent': '#0078d4',
                'success': '#107c10',
                'warning': '#ff8c00',
                'error': '#d13438'
            }
        }
    
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
        
        self.logger.info(f"Применена тема: {theme_name}")
    
    def _configure_buttons(self, theme: Dict[str, str]):
        """Настройка стилей кнопок"""
        self.style.configure('Accent.TButton',
                           background=theme['accent'],
                           foreground='white')
        
        self.style.configure('Success.TButton',
                           background=theme['success'],
                           foreground='white')
        
        self.style.configure('Warning.TButton',
                           background=theme['warning'],
                           foreground='white')
        
        self.style.configure('Error.TButton',
                           background=theme['error'],
                           foreground='white')
    
    def _configure_labels(self, theme: Dict[str, str]):
        """Настройка стилей меток"""
        self.style.configure('TLabel',
                           background=theme['bg'],
                           foreground=theme['fg'])
    
    def _configure_frames(self, theme: Dict[str, str]):
        """Настройка стилей фреймов"""
        self.style.configure('TFrame',
                           background=theme['bg'])
    
    def _configure_notebook(self, theme: Dict[str, str]):
        """Настройка стилей вкладок"""
        self.style.configure('TNotebook',
                           background=theme['bg'])
        
        self.style.configure('TNotebook.Tab',
                           padding=[12, 8])
