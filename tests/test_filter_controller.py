import unittest
from unittest.mock import MagicMock
from src.ui.controllers.filter_controller import FilterController

class TestFilterController(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.view = MagicMock()
        self.event_emitter = MagicMock()
        self.ui_controller = MagicMock()
        self.filter_controller = FilterController(self.model, self.view, self.event_emitter, self.ui_controller)

    def test_apply_filters_no_data(self):
        self.filter_controller._has_data = MagicMock(return_value=False)
        self.filter_controller._show_no_data_message = MagicMock()
        self.filter_controller.apply_filters()
        self.filter_controller._show_no_data_message.assert_called_once()

    def test_clear_all_filters(self):
        self.filter_controller._get_all_parameters = MagicMock(return_value=[])
        self.filter_controller._update_ui_with_filtered_params = MagicMock()
        self.filter_controller.clear_all_filters()
        self.filter_controller._update_ui_with_filtered_params.assert_called_once()

if __name__ == "__main__":
    unittest.main()
