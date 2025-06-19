import unittest
from unittest.mock import MagicMock
from src.ui.controllers.plot_controller import PlotController

class TestPlotController(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.view = MagicMock()
        self.event_emitter = MagicMock()
        self.plot_controller = PlotController(self.model, self.view, self.event_emitter)

    def test_build_plot_no_data(self):
        self.plot_controller._has_data = MagicMock(return_value=False)
        self.plot_controller.build_plot("line", [])
        self.view.show_warning.assert_called_once_with("Нет данных для построения графика")

    def test_export_plot(self):
        self.plot_controller.export_plot("test.png")
        self.event_emitter.assert_called_with("plot_exported", {"file_path": "test.png"})

if __name__ == "__main__":
    unittest.main()
