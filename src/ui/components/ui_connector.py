# ui_connector.py

import threading
import logging
import json
import requests

class UIConnector:
    """Интерфейс для взаимодействия UI с внешними сервисами."""

    def __init__(self, controller, endpoint):
        self.controller = controller
        self.endpoint = endpoint
        self.logger = logging.getLogger(self.__class__.__name__)

    def send_event(self, event_type, data):
        """Отправка события на REST API."""
        try:
            url = f"{self.endpoint}/events"
            payload = {'type': event_type, 'data': data}
            threading.Thread(target=requests.post, args=(url, json.dumps(payload))).start()
            self.logger.debug(f"Sent event: {event_type}")
        except Exception as e:
            self.logger.error(f"Error sending event: {e}")

    def start_ws(self):
        """Запуск WebSocket-клиента для реального времени."""
        # Реализация зависит от выбранной библиотеки, например websocket-client
        self.logger.info("WebSocket started (stub)")
