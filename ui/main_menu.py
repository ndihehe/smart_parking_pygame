from pathlib import Path

import pygame

from ui.button import UIButton


ACTION_PLAY = "play"
ACTION_EXIT = "exit"
BACKGROUND_PATH = Path("assets/ui/main_menu_background.png")
CREDIT_TEXT = "Produced by: Tong Hoang Tung - Vo Thi Hong Gam - Bui Nguyen Nhat Duy"


class MainMenu:
    def __init__(self) -> None:
        self.font_title = pygame.font.SysFont("monospace", 28, bold=True)
        self.font_button = pygame.font.SysFont("monospace", 22, bold=True)
        self.font_credit = pygame.font.SysFont("monospace", 18, bold=True)
        self._background = self._load_background()
        self._credit_x: float | None = None

    def handle_events(self, events: list[pygame.event.Event], screen_size: tuple[int, int]) -> str | None:
        buttons = self._build_buttons(screen_size)
        for event in events:
            if event.type == pygame.QUIT:
                return ACTION_EXIT
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return ACTION_PLAY
                if event.key == pygame.K_ESCAPE:
                    return ACTION_EXIT
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button.rect.collidepoint(event.pos):
                        return button.action
        return None

    def update(self, delta_time: float, screen_size: tuple[int, int]) -> None:
        credit_surface = self.font_credit.render(CREDIT_TEXT, True, (246, 236, 194))
        if self._credit_x is None:
            self._credit_x = float(screen_size[0])
        self._credit_x -= 80 * delta_time
        if self._credit_x < -credit_surface.get_width():
            self._credit_x = float(screen_size[0])

    def render(self, screen: pygame.Surface) -> None:
        screen_size = screen.get_size()
        self._draw_background(screen)
        self._draw_buttons(screen)
        self._draw_credits(screen)

    def _load_background(self) -> pygame.Surface | None:
        if not BACKGROUND_PATH.exists():
            return None
        return pygame.image.load(str(BACKGROUND_PATH)).convert()

    def _draw_background(self, screen: pygame.Surface) -> None:
        if self._background is None:
            screen.fill((18, 26, 28))
            return

        screen_width, screen_height = screen.get_size()
        bg_width, bg_height = self._background.get_size()
        scale = max(screen_width / bg_width, screen_height / bg_height)
        scaled_size = (int(bg_width * scale), int(bg_height * scale))
        scaled_background = pygame.transform.smoothscale(self._background, scaled_size)
        x = (screen_width - scaled_size[0]) // 2
        y = (screen_height - scaled_size[1]) // 2
        screen.blit(scaled_background, (x, y))

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 72))
        screen.blit(overlay, (0, 0))

    def _draw_buttons(self, screen: pygame.Surface) -> None:
        mouse_pos = pygame.mouse.get_pos()
        for button in self._build_buttons(screen.get_size()):
            button.draw(screen, self.font_button, mouse_pos)

    def _build_buttons(self, screen_size: tuple[int, int]) -> list[UIButton]:
        screen_width, screen_height = screen_size
        button_width = 260
        button_height = 58
        center_x = screen_width // 2
        top = int(screen_height * 0.52)
        return [
            UIButton(
                ACTION_PLAY,
                "PLAY",
                pygame.Rect(center_x - button_width // 2, top, button_width, button_height),
            ),
            UIButton(
                ACTION_EXIT,
                "EXIT",
                pygame.Rect(
                    center_x - button_width // 2,
                    top + button_height + 22,
                    button_width,
                    button_height,
                ),
            ),
        ]

    def _draw_credits(self, screen: pygame.Surface) -> None:
        screen_width, screen_height = screen.get_size()
        strip_height = 46
        strip = pygame.Surface((screen_width, strip_height), pygame.SRCALPHA)
        strip.fill((12, 14, 18, 178))
        screen.blit(strip, (0, screen_height - strip_height))
        pygame.draw.line(
            screen,
            (130, 106, 70),
            (0, screen_height - strip_height),
            (screen_width, screen_height - strip_height),
            2,
        )

        text = self.font_credit.render(CREDIT_TEXT, True, (246, 236, 194))
        x = int(self._credit_x if self._credit_x is not None else screen_width)
        y = screen_height - strip_height + (strip_height - text.get_height()) // 2
        screen.blit(text, (x, y))
