from datetime import datetime

from config import LOG_MAX_LINES


class Logger:
    _logs: list[str] = []

    @staticmethod
    def log(message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        Logger._logs.append(entry)
        if len(Logger._logs) > LOG_MAX_LINES:
            Logger._logs.pop(0)
        print(entry)

    @staticmethod
    def get_logs() -> list[str]:
        return Logger._logs.copy()

    @staticmethod
    def clear() -> None:
        Logger._logs.clear()
