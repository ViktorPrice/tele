import unittest
from src.ui.controllers.state_controller import StateController

class TestStateController(unittest.TestCase):
    def setUp(self):
        self.state_controller = StateController()

    def test_set_loading(self):
        self.state_controller.set_loading(True)
        self.assertTrue(self.state_controller.is_loading)
        self.state_controller.set_loading(False)
        self.assertFalse(self.state_controller.is_loading)

    def test_set_processing(self):
        self.state_controller.set_processing(True)
        self.assertTrue(self.state_controller.is_processing)
        self.state_controller.set_processing(False)
        self.assertFalse(self.state_controller.is_processing)

    def test_cache_operations(self):
        self.state_controller.set_cache("key", "value")
        self.assertEqual(self.state_controller.get_cache("key"), "value")
        self.state_controller.clear_cache()
        self.assertIsNone(self.state_controller.get_cache("key"))

    def test_reset_state(self):
        self.state_controller.set_loading(True)
        self.state_controller.set_processing(True)
        self.state_controller.set_cache("key", "value")
        self.state_controller.reset_state()
        self.assertFalse(self.state_controller.is_loading)
        self.assertFalse(self.state_controller.is_processing)
        self.assertIsNone(self.state_controller.get_cache("key"))

if __name__ == "__main__":
    unittest.main()
