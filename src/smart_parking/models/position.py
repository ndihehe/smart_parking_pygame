from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    row: int
    col: int

    def as_tuple(self) -> tuple[int, int]:
        return (self.row, self.col)

