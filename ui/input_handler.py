import pygame

from config import CELL_SIZE
from core.game_controller import GameController
from models.enums import VehicleStatus, VehicleType


class InputHandler:
    def __init__(self, game_controller: GameController) -> None:
        self.gc = game_controller
        self._selected_vehicle_id: int | None = None

    def handle_events(self, events: list[pygame.event.Event]) -> bool:
        for event in events:
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    self.gc.spawn_vehicle(VehicleType.CAR)
                elif event.key == pygame.K_m:
                    self.gc.spawn_vehicle(VehicleType.MOTORBIKE)
                elif event.key == pygame.K_a:
                    self.gc.toggle_auto_spawn()
                elif event.key == pygame.K_RETURN:
                    if self._selected_vehicle_id is not None:
                        self.gc.confirm_parking(self._selected_vehicle_id)
                elif event.key == pygame.K_ESCAPE:
                    self._selected_vehicle_id = None

                if self._selected_vehicle_id is not None:
                    vehicle = self.gc.vehicle_manager.get_vehicle(self._selected_vehicle_id)
                    if vehicle is not None and vehicle.status == VehicleStatus.MANUAL:
                        if event.key in (pygame.K_w, pygame.K_UP):
                            self.gc.move_manual(vehicle.id, (-1, 0))
                        elif event.key in (pygame.K_s, pygame.K_DOWN):
                            self.gc.move_manual(vehicle.id, (1, 0))
                        elif event.key in (pygame.K_a, pygame.K_LEFT):
                            self.gc.move_manual(vehicle.id, (0, -1))
                        elif event.key in (pygame.K_d, pygame.K_RIGHT):
                            self.gc.move_manual(vehicle.id, (0, 1))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = event.pos
                row = y // CELL_SIZE
                col = x // CELL_SIZE
                position = (row, col)

                self._selected_vehicle_id = None
                for vehicle in self.gc.vehicle_manager.get_all_vehicles():
                    if vehicle.position == position:
                        self._selected_vehicle_id = vehicle.id
                        self.gc.set_manual(vehicle.id)
                        break

        return True

    def get_selected_id(self) -> int | None:
        return self._selected_vehicle_id
