import tkinter as tk
from tkinter import ttk

class CompactStatusBar(ttk.Frame):
    def __init__(self, parent, controller=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.controller = controller

        self.status_label = ttk.Label(self, text="Готов к загрузке данных", anchor=tk.W, font=('Arial', 9))
        self.status_label.pack(fill=tk.X, side=tk.LEFT, expand=True)

        self.progress = ttk.Progressbar(self, mode='determinate', length=150)
        self.progress.pack(side=tk.RIGHT, padx=5)
        self.progress.grid_remove()

    def set_status(self, message: str):
        self.status_label.config(text=message)
        self.status_label.update_idletasks()

    def show_progress(self, show: bool = True, value: int = 0, maximum: int = 100):
        if show:
            self.progress.config(maximum=maximum, value=value)
            self.progress.grid()
        else:
            self.progress.grid_remove()
        self.progress.update_idletasks()

    def update_progress(self, value: int):
        self.progress.config(value=value)
        self.progress.update_idletasks()
