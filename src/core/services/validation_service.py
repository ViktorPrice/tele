"""
Сервис валидации данных
"""
from datetime import datetime
from typing import Tuple, Union, Optional
import os

class ValidationService:
    """Централизованный сервис валидации"""
    
    @staticmethod
    def validate_number(value: str, min_val: Optional[float] = None, 
                       max_val: Optional[float] = None) -> Tuple[bool, Union[float, str]]:
        """Валидация числового значения"""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False, f"Значение должно быть >= {min_val}"
            if max_val is not None and num > max_val:
                return False, f"Значение должно быть <= {max_val}"
            return True, num
        except ValueError:
            return False, "Некорректное числовое значение"
    
    @staticmethod
    def validate_datetime_string(value: str) -> Tuple[bool, Union[datetime, str]]:
        """Валидация строки даты и времени"""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%d.%m.%Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%d.%m.%Y %H:%M:%S.%f"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                return True, dt
            except ValueError:
                continue
        
        return False, "Неверный формат даты и времени"
    
    @staticmethod
    def validate_file_path(value: str, extensions: Optional[List[str]] = None) -> Tuple[bool, Union[str, str]]:
        """Валидация пути к файлу"""
        if not value:
            return False, "Путь к файлу не указан"
        
        if not os.path.exists(value):
            return False, "Файл не существует"
        
        if extensions:
            ext = os.path.splitext(value)[1].lower()
            if ext not in extensions:
                return False, f"Неподдерживаемое расширение. Ожидается: {', '.join(extensions)}"
        
        return True, value
