import os
import re
from pathlib import Path

import pygame

from config import CELL_SIZE


PROJECT_ROOT = Path(__file__).resolve().parent.parent
KENNEY_ASSET_ROOT = PROJECT_ROOT / "assets" / "kenney_pixel_vehicle_pack"
CAR_ASSET_ROOT = PROJECT_ROOT / "assets" / "vehicles" / "cars"
MOTORBIKE_ASSET_ROOT = PROJECT_ROOT / "assets" / "vehicles" / "motorbikes"
SPRITE_CACHE_ROOT = PROJECT_ROOT / "assets" / "generated" / "sprite_cache"
VEHICLE_DIRECTIONS = (
    "east",
    "west",
    "north",
    "south",
    "northeast",
    "northwest",
    "southeast",
    "southwest",
)
MOTORBIKE_FRAME_SPECS = {
    "classic": {
        "west": True,
    },
    "vespa": {
        "northeast": True,
    },
}


class SpriteLoader:
    def __init__(self) -> None:
        self._sprites: dict[str, pygame.Surface] = {}

    def load_entity_sprites(self) -> dict[str, pygame.Surface]:
        if self._sprites:
            return self._sprites

        specs = {
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

        self._load_car_frame_sprites()
        self._load_motorbike_frame_sprites()
        return self._sprites

    def _load_car_frame_sprites(self) -> None:
        if not CAR_ASSET_ROOT.exists():
            return

        variants = [
            path
            for path in sorted(CAR_ASSET_ROOT.iterdir())
            if path.is_dir()
        ]
        for index, variant_path in enumerate(variants):
            for direction in VEHICLE_DIRECTIONS:
                sprite = self._load_scaled_from_path(
                    variant_path / f"{direction}.png",
                    CELL_SIZE - 2,
                    CELL_SIZE - 4,
                )
                if sprite is not None:
                    self._sprites[f"car_topdown_{index:03d}_{direction}"] = sprite

    def _load_motorbike_frame_sprites(self) -> None:
        if not MOTORBIKE_ASSET_ROOT.exists():
            return

        variants = [
            path
            for path in sorted(MOTORBIKE_ASSET_ROOT.iterdir())
            if path.is_dir()
        ]
        for index, variant_path in enumerate(variants):
            flip_flags = MOTORBIKE_FRAME_SPECS.get(variant_path.name, {})
            for direction in VEHICLE_DIRECTIONS:
                sprite = self._load_scaled_from_path(
                    variant_path / f"{direction}.png",
                    CELL_SIZE - 4,
                    CELL_SIZE - 8,
                    remove_light_background=True,
                    flip_horizontal=flip_flags.get(direction, False),
                )
                if sprite is not None:
                    self._sprites[f"motorbike_topdown_{index:03d}_{direction}"] = sprite

    def _load_scaled(
        self,
        relative_path: str,
        max_width: int,
        max_height: int,
    ) -> pygame.Surface | None:
        return self._load_scaled_from_path(
            KENNEY_ASSET_ROOT / relative_path,
            max_width,
            max_height,
        )

    def _load_scaled_from_path(
        self,
        path: Path,
        max_width: int,
        max_height: int,
        remove_light_background: bool = False,
        flip_horizontal: bool = False,
    ) -> pygame.Surface | None:
        if not path.exists():
            return None

        cache_path = self._cache_path_for(
            path,
            max_width,
            max_height,
            remove_light_background,
            flip_horizontal,
        )
        if cache_path.exists() and cache_path.stat().st_mtime >= path.stat().st_mtime:
            return pygame.image.load(str(cache_path)).convert_alpha()

        sprite = pygame.image.load(str(path)).convert_alpha()
        if remove_light_background:
            sprite = self._remove_connected_light_background(sprite)
        sprite = self._trim_transparent(sprite)
        if flip_horizontal:
            sprite = pygame.transform.flip(sprite, True, False)
        width, height = sprite.get_size()
        scale = min(max_width / width, max_height / height)
        scaled_size = (
            max(1, int(width * scale)),
            max(1, int(height * scale)),
        )
        scaled = pygame.transform.smoothscale(sprite, scaled_size)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(scaled, str(cache_path))
        return scaled

    def _cache_path_for(
        self,
        source_path: Path,
        max_width: int,
        max_height: int,
        remove_light_background: bool,
        flip_horizontal: bool,
    ) -> Path:
        relative_path = source_path
        try:
            relative_path = source_path.relative_to(PROJECT_ROOT)
        except ValueError:
            pass
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(relative_path))
        flags = []
        if remove_light_background:
            flags.append("bg")
        if flip_horizontal:
            flags.append("flip")
        flag_label = "_".join(flags) if flags else "plain"
        return SPRITE_CACHE_ROOT / f"{safe_name}_{max_width}x{max_height}_{flag_label}.png"

    def _trim_transparent(self, sprite: pygame.Surface) -> pygame.Surface:
        bounds = sprite.get_bounding_rect(min_alpha=1)
        if bounds.width == 0 or bounds.height == 0:
            return sprite
        return sprite.subsurface(bounds).copy()

    def _remove_connected_light_background(self, sprite: pygame.Surface) -> pygame.Surface:
        width, height = sprite.get_size()
        output = sprite.copy()
        visited = bytearray(width * height)
        stack: list[int] = []

        for x in range(width):
            stack.append(x)
            stack.append((height - 1) * width + x)
        for y in range(height):
            stack.append(y * width)
            stack.append(y * width + width - 1)

        while stack:
            index = stack.pop()
            if index < 0 or index >= len(visited) or visited[index]:
                continue
            visited[index] = 1
            x = index % width
            y = index // width
            color = output.get_at((x, y))
            if not self._is_light_background_color(color):
                continue

            output.set_at((x, y), (color.r, color.g, color.b, 0))
            if x + 1 < width:
                stack.append(index + 1)
            if x > 0:
                stack.append(index - 1)
            if y + 1 < height:
                stack.append(index + width)
            if y > 0:
                stack.append(index - width)

        return output

    def _is_light_background_color(self, color: pygame.Color) -> bool:
        return (
            color.r >= 220
            and color.g >= 220
            and color.b >= 220
            and abs(color.r - color.g) <= 10
            and abs(color.r - color.b) <= 10
        )
