import os

import pygame

from config import CELL_SIZE


ASSET_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "assets",
        "kenney_pixel_vehicle_pack",
    )
)


class SpriteLoader:
    def __init__(self) -> None:
        self._sprites: dict[str, pygame.Surface] = {}

    def load_entity_sprites(self) -> dict[str, pygame.Surface]:
        if self._sprites:
            return self._sprites

        specs = {
            "car": (os.path.join("cars", "car.png"), CELL_SIZE - 4, CELL_SIZE - 10),
            "car_alt": (os.path.join("cars", "car_alt.png"), CELL_SIZE - 4, CELL_SIZE - 10),
            "motorbike": (
                os.path.join("cars", "motorbike.png"),
                CELL_SIZE - 8,
                CELL_SIZE - 14,
            ),
            "motorbike_alt": (
                os.path.join("cars", "motorbike_alt.png"),
                CELL_SIZE - 8,
                CELL_SIZE - 14,
            ),
            "guard": (
                os.path.join("characters", "guard.png"),
                CELL_SIZE - 12,
                CELL_SIZE - 8,
            ),
            "guard_walk": (
                os.path.join("characters", "guard_walk.png"),
                CELL_SIZE - 12,
                CELL_SIZE - 8,
            ),
            "guard_walk2": (
                os.path.join("characters", "guard_walk2.png"),
                CELL_SIZE - 12,
                CELL_SIZE - 8,
            ),
            "guard_point": (
                os.path.join("characters", "guard_point.png"),
                CELL_SIZE - 8,
                CELL_SIZE - 8,
            ),
            "gate": (
                os.path.join("props", "gate.png"),
                CELL_SIZE,
                CELL_SIZE,
            ),
            "barrier": (
                os.path.join("props", "barrier.png"),
                CELL_SIZE - 6,
                CELL_SIZE - 12,
            ),
            "light": (
                os.path.join("props", "light.png"),
                CELL_SIZE - 14,
                CELL_SIZE - 4,
            ),
            "light_double": (
                os.path.join("props", "light_double.png"),
                CELL_SIZE - 8,
                CELL_SIZE - 4,
            ),
            "sign_red": (
                os.path.join("props", "sign_red.png"),
                CELL_SIZE - 14,
                CELL_SIZE - 6,
            ),
            "sign_blue": (
                os.path.join("props", "sign_blue.png"),
                CELL_SIZE - 14,
                CELL_SIZE - 6,
            ),
        }

        for key, (relative_path, max_width, max_height) in specs.items():
            sprite = self._load_scaled(relative_path, max_width, max_height)
            if sprite is not None:
                self._sprites[key] = sprite

        return self._sprites

    def _load_scaled(
        self,
        relative_path: str,
        max_width: int,
        max_height: int,
    ) -> pygame.Surface | None:
        path = os.path.join(ASSET_ROOT, relative_path)
        if not os.path.exists(path):
            return None

        sprite = pygame.image.load(path).convert_alpha()
        width, height = sprite.get_size()
        scale = min(max_width / width, max_height / height)
        scaled_size = (
            max(1, int(width * scale)),
            max(1, int(height * scale)),
        )
        return pygame.transform.scale(sprite, scaled_size)
