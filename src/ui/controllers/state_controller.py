import logging

class StateController:
    """Контроллер для управления состояниями загрузки, обработки и кэшами"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_loading = False
        self.is_processing = False
        self.cache = {}

    def set_loading(self, loading: bool):
        self.is_loading = loading
        self.logger.info(f"Состояние загрузки установлено в {loading}")

    def set_processing(self, processing: bool):
        self.is_processing = processing
        self.logger.info(f"Состояние обработки установлено в {processing}")

    def clear_cache(self):
        self.cache.clear()
        self.logger.info("Кэш очищен")

    def get_cache(self, key):
        return self.cache.get(key)

    def set_cache(self, key, value):
        self.cache[key] = value
        self.logger.info(f"Кэш обновлен: {key}")

    def reset_state(self):
        self.is_loading = False
        self.is_processing = False
        self.clear_cache()
        self.logger.info("Состояния и кэш сброшены")

    def cleanup(self):
        """Очистка ресурсов StateController"""
        self.reset_state()
        self.logger.info("StateController очищен")
