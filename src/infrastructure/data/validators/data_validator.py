"""
Валидатор данных
"""
import pandas as pd
import logging
from dataclasses import dataclass
from typing import List

@dataclass
class ValidationResult:
    """Результат валидации"""
    is_valid: bool
    warnings: List[str]
    errors: List[str]

class DataValidator:
    """Валидатор данных"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        """Валидация DataFrame"""
        warnings = []
        errors = []
        
        if df.empty:
            errors.append("DataFrame пуст")
        
        if 'timestamp' not in df.columns:
            warnings.append("Отсутствует столбец timestamp")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            warnings=warnings,
            errors=errors
        )
