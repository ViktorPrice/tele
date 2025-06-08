"""
Команда для регулировки времени
"""
from datetime import datetime, timedelta
from typing import Optional
import logging

class TimeAdjustmentCommand:
    """Команда для регулировки времени"""
    
    def __init__(self, current_time_str: str, seconds_delta: int):
        self.current_time_str = current_time_str
        self.seconds_delta = seconds_delta
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Результат выполнения
        self.result_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
    
    def execute(self) -> bool:
        """Выполнение команды регулировки времени"""
        try:
            # Парсинг текущего времени
            current_time = self._parse_time_string(self.current_time_str)
            if not current_time:
                self.error_message = "Неверный формат времени"
                return False
            
            # Регулировка времени
            self.result_time = current_time + timedelta(seconds=self.seconds_delta)
            
            self.logger.debug(f"Время изменено с {current_time} на {self.result_time}")
            return True
            
        except Exception as e:
            self.error_message = f"Ошибка регулировки времени: {e}"
            self.logger.error(self.error_message)
            return False
    
    def _parse_time_string(self, time_str: str) -> Optional[datetime]:
        """Парсинг строки времени"""
        if not time_str or not isinstance(time_str, str):
            return None
        
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%d.%m.%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def get_result_string(self) -> str:
        """Получение результата как строки"""
        if self.result_time:
            return self.result_time.strftime("%Y-%m-%d %H:%M:%S")
        return ""
