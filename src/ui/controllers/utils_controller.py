import logging
from typing import List, Dict, Any, Optional

class UtilsController:
    """Утилитный контроллер с общими методами для других контроллеров"""

    def __init__(self, model=None, view=None):
        self.model = model
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)

    def _has_data(self) -> bool:
        """Проверка наличия загруженных данных"""
        try:
            if hasattr(self.model, "data_loader") and self.model.data_loader:
                return (
                    hasattr(self.model.data_loader, "data")
                    and self.model.data_loader.data is not None
                )
            return False
        except Exception as e:
            self.logger.error(f"Ошибка проверки данных: {e}")
            return False

    def _get_all_parameters(self) -> List[Dict[str, Any]]:
        """Получение всех параметров из модели"""
        try:
            if hasattr(self.model, "get_all_parameters"):
                params = self.model.get_all_parameters()
            elif hasattr(self.model, "data_loader") and hasattr(
                self.model.data_loader, "get_parameters"
            ):
                params = self.model.data_loader.get_parameters()
            else:
                self.logger.warning("Не удалось получить параметры из модели")
                return []

            if params and hasattr(params[0], "to_dict"):
                return [param.to_dict() for param in params]
            return params or []

        except Exception as e:
            self.logger.error(f"Ошибка получения всех параметров: {e}")
            return []

    def get_ui_component(self, view, component_name: str):
        """Получение UI компонента из view"""
        try:
            if hasattr(view, "ui_components") and view.ui_components:
                return getattr(view.ui_components, component_name, None)
            if hasattr(view, component_name):
                return getattr(view, component_name, None)
            return None
        except Exception as e:
            self.logger.error(f"Ошибка получения UI компонента {component_name}: {e}")
            return None
