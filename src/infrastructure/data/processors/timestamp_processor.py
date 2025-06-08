"""
Обработчик временных меток
"""
import pandas as pd
import logging
from datetime import datetime
from typing import Tuple

class TimestampProcessor:
    """Обработчик временных меток"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def process_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Обработка временных меток"""
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    def get_time_range(self, df: pd.DataFrame) -> Tuple[datetime, datetime]:
        """Получение временного диапазона"""
        if 'timestamp' in df.columns:
            return df['timestamp'].min(), df['timestamp'].max()
        return datetime.now(), datetime.now()
