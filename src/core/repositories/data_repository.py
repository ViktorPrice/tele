# src/core/repositories/data_repository.py - НОВЫЙ ФАЙЛ
"""
Репозиторий для работы с данными телеметрии
"""
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import pandas as pd

from ..domain.entities.telemetry_data import TelemetryData

class DataRepository(ABC):
    """Абстрактный репозиторий данных"""
    
    @abstractmethod
    def load_data(self, source: str) -> Optional[TelemetryData]:
        """Загрузка данных из источника"""
        pass
    
    @abstractmethod
    def save_data(self, data: TelemetryData, destination: str) -> bool:
        """Сохранение данных в назначение"""
        pass

class CSVDataRepository(DataRepository):
    """Репозиторий для работы с CSV данными"""
    
    def __init__(self, csv_loader):
        self.csv_loader = csv_loader
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load_data(self, source: str) -> Optional[TelemetryData]:
        """Загрузка данных из CSV файла"""
        try:
            return self.csv_loader.load_csv(source)
        except Exception as e:
            self.logger.error(f"Ошибка загрузки данных: {e}")
            return None
    
    def save_data(self, data: TelemetryData, destination: str) -> bool:
        """Сохранение данных в CSV файл"""
        try:
            data.data.to_csv(destination, index=False)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения данных: {e}")
            return False
