import unittest
from unittest.mock import MagicMock
from src.ui.controllers.ui_controller import UIController

class TestUIController(unittest.TestCase):
    def setUp(self):
        self.mock_view = MagicMock()
        self.mock_event_emitter = MagicMock()
        self.controller = UIController(self.mock_view, self.mock_event_emitter)

    def test_set_ui_components(self):
        mock_ui_components = MagicMock()
        self.controller.set_ui_components(mock_ui_components)
        self.assertEqual(self.mock_view.ui_components, mock_ui_components)

    def test_add_and_emit_event(self):
        callback = MagicMock()
        self.controller.add_ui_callback("data_loaded", callback)
        self.controller.emit_event("data_loaded", {"key": "value"})
        callback.assert_called_once_with({"key": "value"})

    def test_update_parameters_calls_panel_and_emits(self):
        mock_parameter_panel = MagicMock()
        mock_parameter_panel.update_parameters = MagicMock()
        self.mock_view.ui_components = MagicMock()
        self.controller._ui_registry["parameter_panel"] = mock_parameter_panel
        self.mock_view.update_parameter_count = MagicMock()

        params = [{"param": 1}]
        self.controller.update_parameters(params, emit_event=True)

        mock_parameter_panel.update_parameters.assert_called_once_with(params)
        self.mock_view.update_parameter_count.assert_called_once_with(len(params))

    def test_refresh_ui_registry_clears_and_registers(self):
        self.mock_view.ui_components = MagicMock()
        self.mock_view.ui_components.is_initialized = True
        self.controller.refresh_ui_registry()
        self.assertIn("time_panel", self.controller._ui_registry)
        self.assertIn("parameter_panel", self.controller._ui_registry)

if __name__ == "__main__":
    unittest.main()
