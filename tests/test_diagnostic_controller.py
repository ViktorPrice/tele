import unittest
from unittest.mock import MagicMock
from src.ui.controllers.diagnostic_controller import DiagnosticController

class TestDiagnosticController(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.view = MagicMock()
        self.event_emitter = MagicMock()
        self.ui_controller = MagicMock()
        self.diagnostic_controller = DiagnosticController(self.model, self.view, self.event_emitter, self.ui_controller)

    def test_apply_diagnostic_filters_no_data(self):
        self.diagnostic_controller._has_data = MagicMock(return_value=False)
        self.diagnostic_controller.apply_diagnostic_filters({"criticality": [], "systems": [], "functions": []})
        self.view.show_warning.assert_called_once_with("Нет данных для диагностического анализа")

    def test_reset_diagnostic_filters(self):
        self.diagnostic_controller._has_data = MagicMock(return_value=True)
        self.diagnostic_controller._get_all_parameters = MagicMock(return_value=[])
        self.diagnostic_controller._update_ui_with_filtered_params = MagicMock()
        self.diagnostic_controller.reset_diagnostic_filters()
        self.diagnostic_controller._update_ui_with_filtered_params.assert_called_once()

if __name__ == "__main__":
    unittest.main()
