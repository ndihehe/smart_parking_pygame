DEBUG_MODE = False


def debug_print(message: str) -> None:
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")
