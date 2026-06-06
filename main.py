import os

from ui.pygame_app import PygameApp


if __name__ == "__main__":
    map_path = os.path.join("data", "maps", "default_map.txt")
    app = PygameApp(map_path)
    app.run()
