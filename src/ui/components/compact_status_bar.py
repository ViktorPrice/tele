import tkinter as tk
from tkinter import ttk
import logging

class CompactStatusBar(ttk.Frame):
    """Статус-бар с индикаторами загрузки и обработки."""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        self.status_var = tk.StringVar(value="Готово")
        self.progress = ttk.Progressbar(self, mode='indeterminate')
        self.label = ttk.Label(self, textvariable=self.status_var)
        self.label.pack(side="left", fill="x", expand=True)
        self.progress.pack(side="right")

    def start_processing(self, message="Обработка..."):
        """Запуск индикатора обработки."""  
        self.status_var.set(message)  
        self.progress.start()  
        self.logger.debug(f"Start: {message}")  

    def stop_processing(self):
        """Остановка индикатора обработки."""  
        self.progress.stop()  
        self.status_var.set("Готово")  
        self.logger.debug("Stop processing")  

    def set_error(self, message):
        """Отобразить сообщение об ошибке."""  
        self.status_var.set(f"Ошибка: {message}")  
        self.logger.error(message)  

    def cleanup(self):
        """Очистка ресурсов статус-бара."""  
        self.controller = None  
        for w in self.winfo_children():  
            w.destroy()  
        self.logger.info("StatusBar cleaned up")  
