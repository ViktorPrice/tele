"""
Строители виджетов для устранения дублирования
"""
import tkinter as tk
from tkinter import ttk
import logging

class WidgetBuilder:
    """Строитель виджетов для устранения дублирования кода"""
    
    @staticmethod
    def create_simple_panel(parent, title: str):
        """Создание простой панели-заглушки"""
        frame = ttk.LabelFrame(parent, text=title)
        label = ttk.Label(frame, text=f"{title} (заглушка)")
        label.pack(padx=20, pady=20)
        
        def grid(**kwargs):
            frame.grid(**kwargs)
        frame.grid = grid
        
        return frame
    
    @staticmethod
    def wrap_with_grid_method(component):
        """Добавление метода grid к компоненту"""
        if not hasattr(component, 'grid'):
            def grid(**kwargs):
                if hasattr(component, 'frame') and component.frame:
                    component.frame.grid(**kwargs)
                else:
                    logging.getLogger('WidgetBuilder').warning(
                        f"Не найден frame для {component.__class__.__name__}"
                    )
            component.grid = grid
        return component

class ComponentWrapper:
    """Обертка для добавления методов совместимости"""
    
    @staticmethod
    def add_compatibility_methods(component, method_names: list):
        """Добавление методов совместимости к компоненту"""
        for method_name in method_names:
            if not hasattr(component, method_name):
                # Создаем заглушку метода
                def dummy_method(*args, **kwargs):
                    logging.getLogger('ComponentWrapper').info(
                        f"Вызван метод-заглушка {method_name}"
                    )
                
                setattr(component, method_name, dummy_method)
        
        return component