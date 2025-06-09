import logging

logger = logging.getLogger("ValidationMixin")
logger.info("Модуль validation.py импортирован")

class ValidationMixin:
    """
    Миксин для валидации данных в UI
    """
    logger.info("ValidationMixin класс определён")

    @staticmethod
    def validate_number(value: str, min_val: float = None, max_val: float = None) -> tuple:
        logger.debug(f"Вызов validate_number: value={value}, min_val={min_val}, max_val={max_val}")
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                logger.warning(f"validate_number: {num} < {min_val}")
                return False, f"Значение должно быть >= {min_val}"
            if max_val is not None and num > max_val:
                logger.warning(f"validate_number: {num} > {max_val}")
                return False, f"Значение должно быть <= {max_val}"
            logger.info(f"validate_number: успешно, num={num}")
            return True, num
        except ValueError:
            logger.error(f"validate_number: некорректное числовое значение '{value}'")
            return False, "Некорректное числовое значение"

    @staticmethod
    def validate_datetime_string(value: str) -> tuple:
        logger.debug(f"Вызов validate_datetime_string: value={value}")
        from datetime import datetime
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%d.%m.%Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%d.%m.%Y %H:%M:%S.%f"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                logger.info(f"validate_datetime_string: успешно, формат={fmt}, dt={dt}")
                return True, dt
            except ValueError:
                logger.debug(f"validate_datetime_string: не подошёл формат {fmt}")
                continue
        logger.error(f"validate_datetime_string: неверный формат даты/времени '{value}'")
        return False, "Неверный формат даты и времени"

    @staticmethod
    def validate_file_path(value: str, extensions: list = None) -> tuple:
        import os
        logger.debug(f"Вызов validate_file_path: value={value}, extensions={extensions}")
        if not value:
            logger.warning("validate_file_path: путь к файлу не указан")
            return False, "Путь к файлу не указан"
        if not os.path.exists(value):
            logger.warning(f"validate_file_path: файл не существует: {value}")
            return False, "Файл не существует"
        if extensions:
            ext = os.path.splitext(value)[1].lower()
            if ext not in extensions:
                logger.warning(f"validate_file_path: неподдерживаемое расширение {ext}")
                return False, f"Неподдерживаемое расширение файла. Ожидается: {', '.join(extensions)}"
        logger.info(f"validate_file_path: успешно, путь {value}")
        return True, value
