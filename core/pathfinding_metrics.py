from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
import tracemalloc
from typing import Callable, TypeVar


T = TypeVar("T")


@dataclass
class AlgorithmMetrics:
    runs: int = 0
    total_time_ms: float = 0.0
    last_time_ms: float | None = None
    best_time_ms: float | None = None
    worst_time_ms: float | None = None
    last_memory_kb: float | None = None
    peak_memory_kb: float | None = None
    last_path_length: int | None = None

    @property
    def avg_time_ms(self) -> float | None:
        if self.runs == 0:
            return None
        return self.total_time_ms / self.runs


class PathfindingMetrics:
    def __init__(self) -> None:
        self._metrics = {
            "bfs": AlgorithmMetrics(),
            "dfs": AlgorithmMetrics(),
            "greedy": AlgorithmMetrics(),
            "astar": AlgorithmMetrics(),
        }

    def record(
        self,
        algorithm: str,
        elapsed_ms: float,
        memory_kb: float,
        path_length: int,
        success: bool,
    ) -> None:
        metrics = self._metrics[algorithm]
        metrics.runs += 1
        metrics.total_time_ms += elapsed_ms
        metrics.last_time_ms = elapsed_ms
        metrics.best_time_ms = (
            elapsed_ms
            if metrics.best_time_ms is None
            else min(metrics.best_time_ms, elapsed_ms)
        )
        metrics.worst_time_ms = (
            elapsed_ms
            if metrics.worst_time_ms is None
            else max(metrics.worst_time_ms, elapsed_ms)
        )
        metrics.last_memory_kb = memory_kb
        metrics.peak_memory_kb = (
            memory_kb
            if metrics.peak_memory_kb is None
            else max(metrics.peak_memory_kb, memory_kb)
        )
        metrics.last_path_length = path_length if success else None

    def snapshot(self) -> dict[str, AlgorithmMetrics]:
        return self._metrics.copy()


METRICS = PathfindingMetrics()


def measure_pathfinding(
    algorithm: str,
    callback: Callable[[], list[tuple[int, int]]],
) -> list[tuple[int, int]]:
    was_tracing = tracemalloc.is_tracing()
    if was_tracing:
        tracemalloc.reset_peak()
    else:
        tracemalloc.start()

    start_time = perf_counter()
    path = callback()
    elapsed_ms = (perf_counter() - start_time) * 1000.0
    _, peak_bytes = tracemalloc.get_traced_memory()
    if not was_tracing:
        tracemalloc.stop()

    METRICS.record(
        algorithm,
        elapsed_ms,
        peak_bytes / 1024.0,
        len(path),
        bool(path),
    )
    return path
