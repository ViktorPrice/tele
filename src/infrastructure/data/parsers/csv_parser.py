"""
Парсер CSV файлов
"""
import pandas as pd
import logging
from typing import Dict, Any

class CSVParser:
    """Парсер для CSV файлов"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def parse_csv(self, file_path: str, **kwargs) -> pd.DataFrame:
        """Парсинг CSV файла"""
        try:
            return pd.read_csv(file_path, **kwargs)
        except Exception as e:
            self.logger.error(f"Ошибка парсинга CSV: {e}")
            raise
