"""
AND-OR Search cho bài toán N-Queens.

Chạy:
    python eight_queens_and_or.py
    python eight_queens_and_or.py 8 all
    python eight_queens_and_or.py 8 first --console

Mặc định chương trình mở cửa sổ Tkinter để mô phỏng trực quan giống file HTML:
- Bàn cờ, ô bị tấn công, hàng đang xét, ô thất bại.
- Thống kê OR/AND/backtrack/thành công.
- Nhật ký thuật toán theo từng bước.
- Danh sách lời giải và điều hướng lời giải.
"""

from __future__ import annotations

import random
import sys
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Optional


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BOARD_SIZE = 8

BG = "#0f1220"
PANEL = "#171b2e"
PANEL_2 = "#1f2438"
TEXT = "#e8eaf3"
MUTED = "#9aa3b8"
ACCENT = "#7bd88f"
ACCENT_2 = "#70d6ff"
ACCENT_3 = "#b388ff"
QUEEN = "#f0a04b"
DANGER = "#e05c5c"
ATTACK = "#3a2530"
LIGHT = "#2a2f42"
DARK = "#161b27"
SELECTED = "#ffd166"


@dataclass(frozen=True)
class SearchStep:
    type: str
    row: int
    col: Optional[int]
    queens: tuple[int, ...]
    message: str


def is_safe(queens: list[int], row: int, col: int) -> bool:
    """AND constraint: quân hậu mới không cùng cột hoặc đường chéo với quân cũ."""
    for queen_row, queen_col in enumerate(queens):
        if queen_col == col:
            return False
        if abs(queen_row - row) == abs(queen_col - col):
            return False
    return True


def or_node(
    queens: list[int],
    row: int,
    n: int,
    find_all: bool,
    solutions: list[list[int]],
    call_count: list[int],
) -> Optional[list[int]]:
    """OR node: chọn một cột khả thi cho hàng hiện tại."""
    call_count[0] += 1

    if row == n:
        solution = queens[:]
        solutions.append(solution)
        if not find_all:
            return solution
        return None

    for col in range(n):
        result = and_node(queens, row, col, n, find_all, solutions, call_count)
        if result is not None and not find_all:
            return result

    return None


def and_node(
    queens: list[int],
    row: int,
    col: int,
    n: int,
    find_all: bool,
    solutions: list[list[int]],
    call_count: list[int],
) -> Optional[list[int]]:
    """AND node: kiểm tra tất cả ràng buộc trước khi đi tiếp."""
    call_count[0] += 1

    if not is_safe(queens, row, col):
        return None

    queens.append(col)
    result = or_node(queens, row + 1, n, find_all, solutions, call_count)
    queens.pop()

    return result


def and_or_search(n: int = BOARD_SIZE, find_all: bool = False) -> tuple[list[list[int]], int]:
    solutions: list[list[int]] = []
    call_count = [0]
    or_node([], 0, n, find_all, solutions, call_count)
    return solutions, call_count[0]


def build_steps_for_solution(solution: list[int]) -> list[SearchStep]:
    """
    Tạo trace mô phỏng ngắn, dễ nhìn cho một lời giải cụ thể.

    Trace này giữ đúng vai trò AND-OR:
    - OR: ở mỗi hàng, có nhiều cột để chọn.
    - AND: mỗi cột thử phải thỏa tất cả ràng buộc.
    - Fail/backtrack: minh họa các nhánh bị loại trước khi đi theo lời giải.
    """
    n = len(solution)
    steps: list[SearchStep] = []
    queens: list[int] = []

    def safe(row: int, col: int) -> bool:
        return is_safe(queens, row, col)

    def walk(row: int) -> bool:
        steps.append(
            SearchStep(
                "or",
                row,
                None,
                tuple(queens),
                f"OR node: hàng {row}, thử các cột 0..{n - 1}",
            )
        )
        if row == n:
            steps.append(
                SearchStep(
                    "solution",
                    row,
                    None,
                    tuple(queens),
                    f" Tìm thấy lời giải: queens = {list(queens)}",
                )
            )
            return True

        target_col = solution[row]
        start_col = max(0, target_col - 2)
        for col in range(start_col, target_col + 1):
            steps.append(
                SearchStep(
                    "and",
                    row,
                    col,
                    tuple(queens),
                    f"AND node: thử đặt hậu tại hàng {row}, cột {col}",
                )
            )
            if safe(row, col):
                queens.append(col)
                steps.append(
                    SearchStep(
                        "place",
                        row,
                        col,
                        tuple(queens),
                        f" AND thỏa: đặt hậu tại ({row}, {col})",
                    )
                )
                if col == target_col and walk(row + 1):
                    return True
                queens.pop()
                steps.append(
                    SearchStep(
                        "backtrack",
                        row,
                        col,
                        tuple(queens),
                        f" Backtrack: bỏ hậu tại ({row}, {col})",
                    )
                )
            else:
                steps.append(
                    SearchStep(
                        "fail",
                        row,
                        col,
                        tuple(queens),
                        f" AND thất bại tại ({row}, {col})",
                    )
                )
        return False

    walk(0)
    return steps


def print_board(solution: list[int], index: int) -> None:
    n = len(solution)
    print(f"\n  Lời giải #{index + 1}: {solution}")
    print("  " + "─" * (n * 4 + 1))
    for row in range(n):
        line = "  |"
        for col in range(n):
            line += " Q |" if solution[row] == col else "   |"
        print(line)
    print("  " + "─" * (n * 4 + 1))


class QueensVisualizer(tk.Tk):
    def __init__(self, n: int, find_all: bool) -> None:
        super().__init__()
        self.n = n
        self.find_all = find_all
        self.solutions, self.total_calls = and_or_search(n, True)
        self.current_solution_index = 0
        self.steps: list[SearchStep] = []
        self.step_index = 0
        self.timer_id: Optional[str] = None
        self.paused = False
        self.or_count = 0
        self.and_count = 0
        self.ok_count = 0
        self.backtrack_count = 0

        self.title(f"AND-OR Search — {n}-Queens Visualizer")
        self.configure(bg=BG)
        self.geometry("1180x760")
        self.minsize(980, 680)

        self._configure_style()
        self._build_layout()
        self._render_solution_list()
        self._load_solution(0)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 22, "bold"))
        style.configure("PanelTitle.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 12, "bold"))
        style.configure("Stat.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 18, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)

    def _build_layout(self) -> None:
        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True)

        page_scrollbar = ttk.Scrollbar(outer, orient="vertical")
        page_scrollbar.pack(side="right", fill="y")

        self.page_canvas = tk.Canvas(outer, bg=BG, highlightthickness=0, yscrollcommand=page_scrollbar.set)
        self.page_canvas.pack(side="left", fill="both", expand=True)
        page_scrollbar.configure(command=self.page_canvas.yview)

        page = ttk.Frame(self.page_canvas)
        page_window = self.page_canvas.create_window((0, 0), window=page, anchor="nw")

        def update_scroll_region(_event: tk.Event) -> None:
            self.page_canvas.configure(scrollregion=self.page_canvas.bbox("all"))

        def update_page_width(event: tk.Event) -> None:
            self.page_canvas.itemconfigure(page_window, width=event.width)

        def scroll_with_mousewheel(event: tk.Event) -> None:
            self.page_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        page.bind("<Configure>", update_scroll_region)
        self.page_canvas.bind("<Configure>", update_page_width)
        self.bind_all("<MouseWheel>", scroll_with_mousewheel)

        header = ttk.Frame(page)
        header.pack(fill="x", padx=18, pady=(14, 8))
        ttk.Label(header, text="AND-OR Search", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="OR node chọn cột; AND node kiểm tra toàn bộ ràng buộc cột và đường chéo.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        self.stats_frame = ttk.Frame(page, style="Panel.TFrame")
        self.stats_frame.pack(fill="x", padx=18, pady=8)
        self.stat_labels: dict[str, ttk.Label] = {}
        for key, label in [
            ("solutions", "Tổng lời giải"),
            ("current", "Lời giải hiện tại"),
            ("step", "Bước hiện tại"),
            ("calls", "Gọi OR+AND"),
            ("backtrack", "Backtrack"),
        ]:
            card = ttk.Frame(self.stats_frame, style="Panel.TFrame")
            card.pack(side="left", expand=True, fill="x", padx=8, pady=10)
            ttk.Label(card, text=label, background=PANEL, foreground=MUTED).pack(anchor="w")
            value = ttk.Label(card, text="0", style="Stat.TLabel")
            value.pack(anchor="w")
            self.stat_labels[key] = value

        content = ttk.Frame(page)
        content.pack(fill="both", expand=True, padx=18, pady=(4, 18))

        left = ttk.Frame(content, style="Panel.TFrame")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = ttk.Frame(content, style="Panel.TFrame", width=330)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        controls = ttk.Frame(left, style="Panel.TFrame")
        controls.pack(fill="x", padx=12, pady=12)
        ttk.Button(controls, text=" Mô phỏng", command=self.start_animation).pack(side="left", padx=(0, 6))
        self.pause_button = ttk.Button(controls, text=" Tạm dừng", command=self.toggle_pause)
        self.pause_button.pack(side="left", padx=6)
        ttk.Button(controls, text=" Reset", command=self.reset_animation).pack(side="left", padx=6)
        ttk.Button(controls, text=" Bước tiếp", command=self.step_forward).pack(side="left", padx=6)
        ttk.Label(controls, text="Tốc độ", background=PANEL, foreground=MUTED).pack(side="left", padx=(18, 6))
        self.speed = tk.IntVar(value=6)
        ttk.Scale(controls, from_=1, to=10, variable=self.speed, orient="horizontal", length=120).pack(side="left")

        nav = ttk.Frame(left, style="Panel.TFrame")
        nav.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Button(nav, text="<-", command=self.previous_solution).pack(side="left")
        self.solution_label = ttk.Label(nav, text="", background=PANEL, foreground=TEXT, font=("Segoe UI", 11, "bold"))
        self.solution_label.pack(side="left", padx=12)
        ttk.Button(nav, text="->", command=self.next_solution).pack(side="left")
        ttk.Button(nav, text=" Ngẫu nhiên", command=self.random_solution).pack(side="left", padx=8)

        self.board_canvas = tk.Canvas(left, height=430, bg=PANEL, highlightthickness=0)
        self.board_canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.board_canvas.bind("<Configure>", lambda _event: self._render_board())

        array_frame = ttk.Frame(left, style="Panel.TFrame")
        array_frame.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Label(array_frame, text="Mảng queens[row] = col", style="PanelTitle.TLabel").pack(anchor="w")
        self.array_canvas = tk.Canvas(array_frame, height=58, bg=PANEL, highlightthickness=0)
        self.array_canvas.pack(fill="x", pady=(6, 0))

        log_frame = ttk.Frame(left, style="Panel.TFrame")
        log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        ttk.Label(log_frame, text="Nhật ký thuật toán", style="PanelTitle.TLabel").pack(anchor="w")
        log_body = ttk.Frame(log_frame, style="Panel.TFrame")
        log_body.pack(fill="both", expand=True, pady=(6, 0))
        log_scrollbar = ttk.Scrollbar(log_body, orient="vertical")
        self.log_text = tk.Text(
            log_body,
            height=12,
            bg="#111523",
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Consolas", 10),
            wrap="word",
            yscrollcommand=log_scrollbar.set,
        )
        log_scrollbar.configure(command=self.log_text.yview)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        self.log_text.tag_configure("or", foreground=ACCENT_3)
        self.log_text.tag_configure("and", foreground=ACCENT_2)
        self.log_text.tag_configure("place", foreground=ACCENT)
        self.log_text.tag_configure("fail", foreground=DANGER)
        self.log_text.tag_configure("solution", foreground=QUEEN)

        ttk.Label(right, text="Cấu trúc AND-OR", style="PanelTitle.TLabel").pack(anchor="w", padx=12, pady=(12, 4))
        info = (
            "OR node: chọn một cột cho hàng hiện tại.\n"
            "AND node: tất cả ràng buộc phải đồng thời đúng.\n"
            "Nếu AND thất bại, nhánh bị loại và backtrack."
        )
        ttk.Label(right, text=info, background=PANEL, foreground=MUTED, justify="left", wraplength=290).pack(
            anchor="w", padx=12
        )

        self.counter_label = ttk.Label(right, text="", background=PANEL, foreground=TEXT, justify="left")
        self.counter_label.pack(anchor="w", padx=12, pady=(12, 10))

        ttk.Label(right, text=f"Tất cả {len(self.solutions)} lời giải", style="PanelTitle.TLabel").pack(
            anchor="w", padx=12, pady=(6, 4)
        )
        list_frame = ttk.Frame(right, style="Panel.TFrame")
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.solution_list = tk.Listbox(
            list_frame,
            bg="#111523",
            fg=TEXT,
            selectbackground=ACCENT_3,
            selectforeground="#ffffff",
            relief="flat",
            activestyle="none",
            font=("Consolas", 9),
            yscrollcommand=scrollbar.set,
        )
        scrollbar.configure(command=self.solution_list.yview)
        self.solution_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.solution_list.bind("<<ListboxSelect>>", self._on_solution_selected)

    def _render_solution_list(self) -> None:
        self.solution_list.delete(0, tk.END)
        for index, solution in enumerate(self.solutions, start=1):
            self.solution_list.insert(tk.END, f"{index:02d}: {solution}")

    def _load_solution(self, index: int) -> None:
        if not self.solutions:
            self.steps = []
            self.solution_label.configure(text="Không có lời giải")
            self._render_board(())
            return

        self.current_solution_index = index % len(self.solutions)
        self.steps = build_steps_for_solution(self.solutions[self.current_solution_index])
        self.reset_animation(clear_steps=False)
        self.solution_list.selection_clear(0, tk.END)
        self.solution_list.selection_set(self.current_solution_index)
        self.solution_list.see(self.current_solution_index)
        self.solution_label.configure(
            text=f"Lời giải {self.current_solution_index + 1}/{len(self.solutions)}: "
            f"{self.solutions[self.current_solution_index]}"
        )
        self._render_board(tuple(self.solutions[self.current_solution_index]))
        self._render_array(tuple(self.solutions[self.current_solution_index]))
        self._update_stats()

    def _on_solution_selected(self, _event: tk.Event) -> None:
        selection = self.solution_list.curselection()
        if selection:
            self._load_solution(selection[0])

    def previous_solution(self) -> None:
        self._load_solution(self.current_solution_index - 1)

    def next_solution(self) -> None:
        self._load_solution(self.current_solution_index + 1)

    def random_solution(self) -> None:
        if self.solutions:
            self._load_solution(random.randrange(len(self.solutions)))

    def start_animation(self) -> None:
        self.reset_animation(clear_steps=False)
        self.paused = False
        self.pause_button.configure(text=" Tạm dừng")
        self._schedule_next_step()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.pause_button.configure(text=" Tiếp tục" if self.paused else " Tạm dừng")
        if not self.paused and self.timer_id is None:
            self._schedule_next_step()

    def reset_animation(self, clear_steps: bool = True) -> None:
        if self.timer_id is not None:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        if clear_steps and self.solutions:
            self.steps = build_steps_for_solution(self.solutions[self.current_solution_index])
        self.step_index = 0
        self.paused = False
        self.or_count = 0
        self.and_count = 0
        self.ok_count = 0
        self.backtrack_count = 0
        self.pause_button.configure(text=" Tạm dừng")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")
        self._render_board(())
        self._render_array(())
        self._update_stats()

    def step_forward(self) -> None:
        if self.step_index >= len(self.steps):
            return
        self._apply_step(self.steps[self.step_index])
        self.step_index += 1

    def _schedule_next_step(self) -> None:
        if self.paused:
            self.timer_id = None
            return
        if self.step_index >= len(self.steps):
            self.timer_id = None
            return
        self.step_forward()
        delay = max(40, 680 - int(self.speed.get()) * 60)
        self.timer_id = self.after(delay, self._schedule_next_step)

    def _apply_step(self, step: SearchStep) -> None:
        if step.type == "or":
            self.or_count += 1
        elif step.type == "and":
            self.and_count += 1
        elif step.type == "place":
            self.ok_count += 1
        elif step.type in {"fail", "backtrack"}:
            self.backtrack_count += 1

        self._append_log(step)
        fail_col = step.col if step.type == "fail" else None
        highlight_row = step.row if step.type in {"or", "and", "place", "fail", "backtrack"} else None
        self._render_board(step.queens, highlight_row, fail_col)
        self._render_array(step.queens, highlight_row)
        self._update_stats()

    def _append_log(self, step: SearchStep) -> None:
        tag = step.type
        if tag == "backtrack":
            tag = "fail"
        step_number = self.step_index + 1
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, f"{step_number:03d}  ", "default")
        self.log_text.insert(tk.END, step.message + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _update_stats(self) -> None:
        self.stat_labels["solutions"].configure(text=str(len(self.solutions)))
        current = self.current_solution_index + 1 if self.solutions else 0
        self.stat_labels["current"].configure(text=str(current))
        self.stat_labels["step"].configure(text=str(self.step_index))
        self.stat_labels["calls"].configure(text=str(self.or_count + self.and_count))
        self.stat_labels["backtrack"].configure(text=str(self.backtrack_count))
        self.counter_label.configure(
            text=(
                f"OR gọi: {self.or_count}\n"
                f"AND gọi: {self.and_count}\n"
                f"Thành công: {self.ok_count}\n"
                f"Backtrack: {self.backtrack_count}\n"
                f"Tổng lời gọi khi tìm toàn bộ: {self.total_calls}"
            )
        )

    def _render_board(
        self,
        queens: tuple[int, ...] = (),
        highlight_row: Optional[int] = None,
        fail_col: Optional[int] = None,
    ) -> None:
        canvas = self.board_canvas
        canvas.delete("all")
        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        board_side = min(width - 24, height - 24)
        if board_side <= 0:
            return
        cell = board_side / self.n
        left = (width - board_side) / 2
        top = (height - board_side) / 2

        attacked = self._attacked_cells(queens)
        for row in range(self.n):
            for col in range(self.n):
                x1 = left + col * cell
                y1 = top + row * cell
                x2 = x1 + cell
                y2 = y1 + cell
                color = LIGHT if (row + col) % 2 == 0 else DARK
                if (row, col) in attacked:
                    color = ATTACK
                if highlight_row == row:
                    color = self._blend(color, SELECTED, 0.24)
                if highlight_row == row and fail_col == col:
                    color = DANGER
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#343a55", width=1)

        for row, col in enumerate(queens):
            x = left + col * cell + cell / 2
            y = top + row * cell + cell / 2
            color = QUEEN if row == len(queens) - 1 else "#c58a54"
            canvas.create_text(x, y, text="♛", fill=color, font=("Segoe UI Symbol", max(18, int(cell * 0.58)), "bold"))

        if highlight_row is not None and 0 <= highlight_row < self.n:
            y1 = top + highlight_row * cell
            canvas.create_rectangle(left, y1, left + board_side, y1 + cell, outline=SELECTED, width=3)

        if fail_col is not None and highlight_row is not None:
            x = left + fail_col * cell + cell / 2
            y = top + highlight_row * cell + cell / 2
            canvas.create_text(x, y, text="✕", fill="#ffffff", font=("Segoe UI", max(16, int(cell * 0.45)), "bold"))

    def _render_array(self, queens: tuple[int, ...], active_row: Optional[int] = None) -> None:
        canvas = self.array_canvas
        canvas.delete("all")
        width = max(1, canvas.winfo_width())
        cell_width = max(58, min(86, (width - 12) / max(1, self.n)))
        for row in range(self.n):
            x1 = 6 + row * cell_width
            x2 = x1 + cell_width - 6
            y1 = 7
            y2 = 52
            fill = PANEL_2 if row != active_row else "#313958"
            canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#343a55")
            canvas.create_text((x1 + x2) / 2, 19, text=f"r{row}", fill=MUTED, font=("Segoe UI", 8))
            value = str(queens[row]) if row < len(queens) else "·"
            color = ACCENT if row < len(queens) else MUTED
            canvas.create_text((x1 + x2) / 2, 38, text=value, fill=color, font=("Segoe UI", 13, "bold"))

    def _attacked_cells(self, queens: tuple[int, ...]) -> set[tuple[int, int]]:
        attacked: set[tuple[int, int]] = set()
        for queen_row, queen_col in enumerate(queens):
            for row in range(self.n):
                for col in range(self.n):
                    same_col = col == queen_col
                    same_diag = abs(row - queen_row) == abs(col - queen_col)
                    if row != queen_row and (same_col or same_diag):
                        attacked.add((row, col))
        return attacked

    @staticmethod
    def _blend(hex_a: str, hex_b: str, amount: float) -> str:
        def parse(hex_color: str) -> tuple[int, int, int]:
            hex_color = hex_color.lstrip("#")
            return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

        a = parse(hex_a)
        b = parse(hex_b)
        mixed = tuple(round(a[index] * (1 - amount) + b[index] * amount) for index in range(3))
        return f"#{mixed[0]:02x}{mixed[1]:02x}{mixed[2]:02x}"


def run_console(n: int, find_all: bool) -> None:
    print(f"\n{'=' * 58}")
    mode = "Tất cả lời giải" if find_all else "Lời giải đầu tiên"
    print(f"  AND-OR Search | {n}-Queens | Chế độ: {mode}")
    print(f"{'=' * 58}")

    solutions, calls = and_or_search(n, find_all)
    if not solutions:
        print(f"  Không có lời giải cho {n}-Queens!")
    else:
        limit = len(solutions) if find_all else 1
        for index in range(min(limit, len(solutions))):
            print_board(solutions[index], index)
        if not find_all:
            print(f"\n  Dùng: python {sys.argv[0]} {n} all --console để tìm tất cả lời giải.")

    print(f"\n  Tổng lời giải      : {len(solutions)}")
    print(f"  Số lần gọi đệ quy : {calls}")
    print()


def parse_args(argv: list[str]) -> tuple[int, bool, bool]:
    n = BOARD_SIZE
    mode = "all"
    console = False

    for arg in argv[1:]:
        if arg.isdigit():
            n = int(arg)
        elif arg in {"first", "all"}:
            mode = arg
        elif arg == "--console":
            console = True
        else:
            raise SystemExit(f"Tham số không hợp lệ: {arg}")

    return n, mode == "all", console


def main() -> None:
    n, find_all, console = parse_args(sys.argv)
    if console:
        run_console(n, find_all)
        return
    app = QueensVisualizer(n, find_all)
    app.mainloop()


if __name__ == "__main__":
    main()
