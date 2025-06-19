import logging
from typing import Any, Dict, List

class PlotController:
    """Контроллер для построения графиков и управления графиками"""

    def __init__(self, model, view, event_emitter):
        self.model = model
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_emitter = event_emitter  # Функция или объект для эмиссии событий

    def build_plot(self, plot_type: str, parameters: List[Dict[str, Any]], **kwargs):
        """Построение графика заданного типа с параметрами"""
        try:
            self.logger.info(f"Построение графика типа {plot_type} с параметрами {kwargs}")

            if not self._has_data():
                self.logger.warning("Нет данных для построения графика")
                if hasattr(self.view, "show_warning"):
                    self.view.show_warning("Нет данных для построения графика")
                return

            # Логика построения графика должна быть реализована во внешнем контроллере
            # Здесь можно вызвать методы модели или инфраструктуры построения графиков

            if self.event_emitter:
                self.event_emitter("plot_built", {"plot_type": plot_type, "parameters": parameters})

            self.logger.info("Построение графика завершено")

        except Exception as e:
            self.logger.error(f"Ошибка построения графика: {e}")

    def export_plot(self, file_path: str):
        """Экспорт построенного графика в файл"""
        try:
            self.logger.info(f"Экспорт графика в файл {file_path}")

            # Логика экспорта графика должна быть реализована во внешнем контроллере

            if self.event_emitter:
                self.event_emitter("plot_exported", {"file_path": file_path})

            self.logger.info("Экспорт графика завершен")

        except Exception as e:
            self.logger.error(f"Ошибка экспорта графика: {e}")

    def _has_data(self) -> bool:
        """Проверка наличия данных для построения графика"""
        try:
            if hasattr(self.model, "data_loader") and self.model.data_loader:
                return (
                    hasattr(self.model.data_loader, "data")
                    and self.model.data_loader.data is not None
                )
            return False
        except Exception as e:
            self.logger.error(f"Ошибка проверки данных для графика: {e}")
            return False
