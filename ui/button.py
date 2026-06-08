from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class UIButton:
    action: str
    label: str
    rect: pygame.Rect
    selected: bool = False
    enabled: bool = True

    def draw(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        mouse_pos: tuple[int, int] | None = None,
    ) -> None:
        hovered = mouse_pos is not None and self.rect.collidepoint(mouse_pos)
        if not self.enabled:
            fill = (26, 28, 34)
            border = (56, 58, 64)
            text_color = (108, 112, 122)
        elif self.selected:
            fill = (92, 143, 72)
            border = (220, 238, 160)
            text_color = (255, 255, 230)
        elif hovered:
            fill = (54, 61, 72)
            border = (176, 194, 150)
            text_color = (245, 248, 220)
        else:
            fill = (34, 38, 48)
            border = (98, 110, 92)
            text_color = (214, 220, 198)

        pygame.draw.rect(screen, (8, 10, 14), self.rect.inflate(4, 4))
        pygame.draw.rect(screen, fill, self.rect)
        pygame.draw.rect(screen, border, self.rect, 2)
        pygame.draw.line(
            screen,
            (255, 255, 255, 42),
            (self.rect.left + 3, self.rect.top + 3),
            (self.rect.right - 4, self.rect.top + 3),
            1,
        )
        text = font.render(self.label, True, text_color)
        screen.blit(text, text.get_rect(center=self.rect.center))
