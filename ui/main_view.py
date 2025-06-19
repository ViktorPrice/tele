# Заглушка для ui/main_view.py
class MainView:
    def __init__(self):
        pass

    def setup(self):
        pass

    def show_error(self, message):
        print(f"Error: {message}")

    def show_warning(self, message):
        print(f"Warning: {message}")

    def show_info(self, title, message):
        print(f"{title}: {message}")
