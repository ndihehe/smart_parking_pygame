import pygame

from core.game_controller import GameController
from core.simulation_state import VehiclePlan
from models.enums import AlgorithmType, VehicleStatus, VehicleType
from ui.sidebar import (
    ACTION_ALGORITHM_PREFIX,
    ACTION_MAIN_MENU,
    ACTION_PLACE,
    ACTION_PLAN_ENTERING,
    ACTION_PLAN_EXITING,
    ACTION_NEXT_STEP,
    ACTION_PREVIOUS_STEP,
    ACTION_RESET,
    ACTION_SPEED_NORMAL,
    ACTION_SPEED_SLOW,
    ACTION_STEP_MODE,
    ACTION_TRAFFIC_JAM,
    ACTION_TYPE_CAR,
    ACTION_TYPE_MOTORBIKE,
    sidebar_action_at_position,
)
from ui.view_transform import screen_to_map_pixel


class InputHandler:
    def __init__(self, game_controller: GameController) -> None:
        self.gc = game_controller
        self._selected_vehicle_id: int | None = None
        self.request_main_menu = False

    def handle_events(self, events: list[pygame.event.Event]) -> bool:
        for event in events:
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    self._handle_vehicle_type_action(VehicleType.CAR)
                elif event.key == pygame.K_m:
                    self._handle_vehicle_type_action(VehicleType.MOTORBIKE)
                elif event.key == pygame.K_t:
                    self.gc.toggle_auto_spawn()
                elif event.key == pygame.K_j:
                    self.gc.prepare_traffic_jam_scenario()
                elif event.key == pygame.K_r:
                    self.gc.reset_simulation()
                    self._selected_vehicle_id = None
                elif event.key == pygame.K_n:
                    self.gc.request_next_step()
                elif event.key == pygame.K_p:
                    self.gc.request_previous_step()
                elif event.key == pygame.K_1:
                    self.gc.set_pathfinding_algorithm(AlgorithmType.BFS)
                elif event.key == pygame.K_2:
                    self.gc.set_pathfinding_algorithm(AlgorithmType.DFS)
                elif event.key == pygame.K_3:
                    self.gc.set_pathfinding_algorithm(AlgorithmType.GREEDY)
                elif event.key == pygame.K_4:
                    self.gc.set_pathfinding_algorithm(AlgorithmType.ASTAR)
                elif event.key == pygame.K_RETURN:
                    if self.gc.simulation_status.value == "READY":
                        self.gc.start_simulation()
                    elif self._selected_vehicle_id is not None:
                        vehicle = self.gc.vehicle_manager.get_vehicle(
                            self._selected_vehicle_id
                        )
                        if vehicle is not None and vehicle.status == VehicleStatus.MANUAL:
                            self.gc.confirm_parking(self._selected_vehicle_id)
                elif event.key == pygame.K_ESCAPE:
                    if self._selected_vehicle_id is not None:
                        self.gc.cancel_manual(self._selected_vehicle_id)
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

            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                screen = pygame.display.get_surface()
                if screen is None:
                    map_pixel = event.pos
                else:
                    map_state = self.gc.map_manager.get_state()
                    if event.button == 1:
                        action = sidebar_action_at_position(
                            screen.get_size(),
                            event.pos,
                            map_state,
                            self.gc.current_algorithm,
                            self.gc.simulation_status,
                            self.gc.placement_vehicle_type,
                            self.gc.placement_plan,
                            self.gc.simulation_speed,
                            self.gc.step_mode_enabled,
                        )
                        if action is not None:
                            self._handle_sidebar_action(action)
                            continue

                    map_pixel = screen_to_map_pixel(
                        map_state,
                        screen.get_size(),
                        event.pos,
                    )
                    if map_pixel is None:
                        continue

                position = self.gc.map_manager.get_cell_at_pixel(*map_pixel)
                raw_position = self.gc.map_manager.get_cell_at_pixel(*event.pos)
                if position is None:
                    position = raw_position
                if position is None:
                    continue

                if self.gc.simulation_status.value == "PLACING_VEHICLE":
                    if self.gc.place_vehicle_at(position):
                        self._selected_vehicle_id = None
                    continue

                self._selected_vehicle_id = None
                vehicles = self.gc.vehicle_manager.get_all_vehicles()
                selected_vehicle = next(
                    (vehicle for vehicle in vehicles if vehicle.position == position),
                    None,
                )
                if selected_vehicle is None and raw_position is not None:
                    selected_vehicle = next(
                        (vehicle for vehicle in vehicles if vehicle.position == raw_position),
                        None,
                    )

                if selected_vehicle is not None:
                    self._selected_vehicle_id = selected_vehicle.id
                    if event.button == 1:
                        self.gc.set_manual(selected_vehicle.id)
                    else:
                        self.gc.start_exit(selected_vehicle.id)

        return True

    def get_selected_id(self) -> int | None:
        return self._selected_vehicle_id

    def _handle_sidebar_action(self, action: str) -> None:
        if action.startswith(ACTION_ALGORITHM_PREFIX):
            self.gc.set_pathfinding_algorithm(
                AlgorithmType(action.split(":", 1)[1])
            )
        elif action == ACTION_TRAFFIC_JAM:
            self.gc.prepare_traffic_jam_scenario()
            self._selected_vehicle_id = None
        elif action == ACTION_RESET:
            self.gc.reset_simulation()
            self._selected_vehicle_id = None
        elif action == ACTION_PLACE:
            self.gc.begin_vehicle_placement()
            self._selected_vehicle_id = None
        elif action == ACTION_TYPE_CAR:
            self._handle_vehicle_type_action(VehicleType.CAR)
        elif action == ACTION_TYPE_MOTORBIKE:
            self._handle_vehicle_type_action(VehicleType.MOTORBIKE)
        elif action == ACTION_PLAN_ENTERING:
            self.gc.set_placement_plan(VehiclePlan.ENTERING)
        elif action == ACTION_PLAN_EXITING:
            self.gc.set_placement_plan(VehiclePlan.EXITING)
        elif action == ACTION_SPEED_NORMAL:
            self.gc.set_simulation_speed(1.0)
        elif action == ACTION_SPEED_SLOW:
            self.gc.set_simulation_speed(0.25)
        elif action == ACTION_STEP_MODE:
            self.gc.toggle_step_mode()
        elif action == ACTION_NEXT_STEP:
            self.gc.request_next_step()
        elif action == ACTION_PREVIOUS_STEP:
            self.gc.request_previous_step()
        elif action == ACTION_MAIN_MENU:
            self.request_main_menu = True

    def _handle_vehicle_type_action(self, vehicle_type: VehicleType) -> None:
        if self.gc.simulation_status.value == "PLACING_VEHICLE":
            self.gc.set_placement_vehicle_type(vehicle_type)
        else:
            self.gc.spawn_vehicle(vehicle_type)
