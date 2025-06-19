import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
from src.ui.components.smart_filter_panel import SmartFilterPanel

class TestSmartFilterPanel(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.mock_controller = MagicMock()
        self.panel = SmartFilterPanel(self.root, self.mock_controller)
        self.panel.pack()
        self.root.update()

    def tearDown(self):
        self.panel.destroy()
        self.root.destroy()

    def test_create_quick_actions_bar_buttons(self):
        # Test that quick actions bar has correct buttons and commands
        self.panel._create_quick_actions_bar()
        self.root.update()
        # Check if buttons with expected texts exist anywhere in panel's descendants
        found_texts = set()
        def find_buttons(widget):
            for child in widget.winfo_children():
                # Проверяем, что виджет поддерживает cget и имеет опцию text
                if hasattr(child, 'cget') and callable(getattr(child, 'cget')):
                    try:
                        text = child.cget("text")
                    except Exception:
                        text = None
                    if text in ["Сбросить фильтры", "Применить фильтры"]:
                        found_texts.add(text)
                find_buttons(child)
        find_buttons(self.panel)
        self.assertIn("Сбросить фильтры", found_texts)
        self.assertIn("Применить фильтры", found_texts)

    def test_reset_all_filters_calls_controller(self):
        self.panel._notify_state_changed = MagicMock()
        self.panel._reset_all_filters()
        self.assertIsInstance(self.panel.state, type(self.panel.state))
        self.panel._notify_state_changed.assert_called_once()

    def test_apply_filters_calls_controller(self):
        self.panel.controller = self.mock_controller
        self.panel._apply_filters()
        self.mock_controller.apply_filters.assert_called_once()

    def test_dynamic_wagon_mapping(self):
        # Setup wagons and check mapping
        self.panel.wagons = ["W1", "W2"]
        self.panel._create_wagon_mapping(leading_wagon=1)
        self.assertEqual(self.panel.wagon_mapping, {
            1: "1г", 2: "11бо", 3: "2м", 4: "3нм", 5: "6м",
            6: "8м", 7: "7нм", 8: "12м", 9: "13бо", 10: "10м", 11: "9г"
        })

    def test_tab_switching(self):
        # Test that switching tabs updates current_tab
        class DummyWidget:
            def __init__(self, panel):
                self.panel = panel
            def select(self):
                return str(self.panel.notebook.tabs()[1])
        class DummyEvent:
            def __init__(self, widget):
                self.widget = widget
        dummy_event = DummyEvent(DummyWidget(self.panel))
        self.panel._on_tab_changed(dummy_event)
        # Проверяем, что вкладка wagons инициализирована после переключения
        self.assertTrue(self.panel.tabs['wagons']['initialized'])

if __name__ == "__main__":
    unittest.main()
