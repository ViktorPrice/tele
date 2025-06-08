"""
Менеджер размещения компонентов UI
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional

class LayoutManager:
    """Менеджер для управления размещением UI компонентов"""
    
    def __init__(self, root):
        self.root = root
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Контейнеры для компонентов
        self.containers: Dict[str, ttk.Frame] = {}
        self.main_container = None
        
    def create_main_layout(self):
        """Создание основного layout с прокруткой"""
        # Создание прокручиваемого контейнера
        self.canvas = tk.Canvas(self.root, borderwidth=0, background="#f0f0f0")
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.main_container = ttk.Frame(self.canvas)
        
        # Настройка прокрутки
        self.main_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.main_container, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Размещение
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Настройка прокрутки колесом мыши
        self._setup_mouse_wheel()
        
        # Создание контейнеров для компонентов
        self._create_component_containers()
    
    def _setup_mouse_wheel(self):
        """Настройка прокрутки колесом мыши"""
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
    
    def _create_component_containers(self):
        """Создание контейнеров для различных компонентов"""
        # Настройка растягивания главного контейнера
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Создание именованных контейнеров
        container_names = [
            'upload', 'time', 'filters', 'parameters', 'actions', 'visualization'
        ]
        
        for i, name in enumerate(container_names):
            container = ttk.Frame(self.main_container)
            container.grid_columnconfigure(0, weight=1)
            self.containers[name] = container
            
            # Настройка растягивания для параметров и визуализации
            if name in ['parameters', 'visualization']:
                self.main_container.grid_rowconfigure(i, weight=1)
    
    def get_container(self, name: str) -> Optional[ttk.Frame]:
        """Получение контейнера по имени"""
        return self.containers.get(name)
    
    def place_components(self, components: Dict[str, Any], layout_config: Dict[str, Dict]):
        """Размещение компонентов согласно конфигурации"""
        for component_name, component in components.items():
            container = self.containers.get(component_name)
            config = layout_config.get(component_name, {})
            
            if container and hasattr(component, 'grid'):
                # Размещаем компонент в его контейнере
                component.grid(row=0, column=0, sticky="nsew")
                
                # Размещаем контейнер в главном контейнере
                container.grid(**config)
                
                self.logger.debug(f"Размещен компонент {component_name}")
    
    def update_layout(self, responsive: bool = True):
        """Обновление layout (для адаптивности)"""
        if responsive:
            self._apply_responsive_layout()
    
    def _apply_responsive_layout(self):
        """Применение адаптивного layout"""
        # Получаем размер окна
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Адаптируем layout в зависимости от размера
        if window_width < 1200:
            # Компактный режим для маленьких экранов
            self._apply_compact_layout()
        else:
            # Полный режим для больших экранов
            self._apply_full_layout()
    
    def _apply_compact_layout(self):
        """Компактный layout для маленьких экранов"""
        # Уменьшаем отступы
        for container in self.containers.values():
            container.configure(padding=(5, 2))
    
    def _apply_full_layout(self):
        """Полный layout для больших экранов"""
        # Стандартные отступы
        for container in self.containers.values():
            container.configure(padding=(10, 5))
