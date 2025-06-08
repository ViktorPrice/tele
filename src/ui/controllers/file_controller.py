"""
Контроллер для операций с файлами
"""
import os
import threading
from tkinter import filedialog
from typing import Optional
import logging
from ...core.application.commands.load_file_command import LoadFileCommand
from ...core.application.handlers.file_handler import FileHandler

class FileController:
    """Контроллер операций с файлами"""
    
    def __init__(self, model, ui_facade, event_bus):
        self.model = model
        self.ui_facade = ui_facade
        self.event_bus = event_bus
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Обработчик команд
        self.file_handler = FileHandler(model)
        
        # Состояние
        self.stop_event = threading.Event()
    
    def upload_csv(self) -> None:
        """Загрузка CSV файла"""
        try:
            file_path = filedialog.askopenfilename(
                title="Выберите CSV файл",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if file_path:
                self.ui_facade.start_processing("Загрузка файла...")
                threading.Thread(target=self._load_csv_thread, 
                               args=(file_path,), daemon=True).start()
        except Exception as e:
            self.logger.error(f"Ошибка выбора файла: {e}")
            self.ui_facade.show_error(f"Ошибка выбора файла: {e}")
    
    def _load_csv_thread(self, file_path: str) -> None:
        """Загрузка CSV в отдельном потоке"""
        try:
            command = LoadFileCommand(file_path)
            result = self.file_handler.handle(command)
            
            if result.success:
                self.ui_facade.update_status(f"Файл загружен: {os.path.basename(file_path)}")
                
                # ДОБАВИТЬ: Обновление UI с параметрами
                parameters = self.model.data_loader.parameters
                lines = list(self.model.data_loader.lines)
                
                # Уведомление UI о загруженных данных
                if hasattr(self.ui_facade, 'update_parameters'):
                    self.ui_facade.update_parameters(parameters)
                
                if hasattr(self.ui_facade, 'update_lines'):
                    self.ui_facade.update_lines(lines)
                
                # Публикация события
                self.event_bus.publish('file_loaded', {
                    'file_path': file_path,
                    'parameters': parameters,
                    'lines': lines
                })
            else:
                self.ui_facade.show_error(f"Ошибка загрузки: {result.error}")
                
        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV: {e}")
            self.ui_facade.show_error(f"Ошибка загрузки: {e}")
        finally:
            self.ui_facade.stop_processing()
    
    def cancel_operation(self) -> None:
        """Отмена текущей операции"""
        self.stop_event.set()
        self.ui_facade.update_status("Операция отменена")
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.stop_event.set()
