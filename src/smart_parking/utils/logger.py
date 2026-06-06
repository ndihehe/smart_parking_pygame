from datetime import datetime


class EventLogger:
    def __init__(self) -> None:
        self.entries: list[str] = []

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.entries.append(f"[{timestamp}] {message}")

    def latest(self, limit: int = 10) -> list[str]:
        return self.entries[-limit:]

