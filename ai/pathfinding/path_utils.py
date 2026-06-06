def reconstruct_path(
    came_from: dict[tuple[int, int], tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    if goal not in came_from and goal != start:
        return []

    path: list[tuple[int, int]] = []
    current = goal

    while current != start:
        path.append(current)
        current = came_from[current]

    path.reverse()
    return path
