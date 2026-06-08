import os

from ui.pygame_app import PygameApp


if __name__ == "__main__":
    map_path = os.path.join("data", "map_layout.json")
    app = PygameApp(map_path)
    app.run()
