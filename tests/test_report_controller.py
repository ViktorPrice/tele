import unittest
from unittest.mock import MagicMock
from src.ui.controllers.report_controller import ReportController

class TestReportController(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.view = MagicMock()
        self.event_emitter = MagicMock()
        self.report_controller = ReportController(self.model, self.view, self.event_emitter)

    def test_generate_report(self):
        self.report_controller.generate_report("summary", {"param": "value"})
        self.event_emitter.assert_called_with("report_generated", {"report_type": "summary", "parameters": {"param": "value"}})

if __name__ == "__main__":
    unittest.main()
