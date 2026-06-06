from datetime import datetime


class Logger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def info(self, message: str) -> None:
        self.messages.append(self.format_message("INFO", message))

    def warning(self, message: str) -> None:
        self.messages.append(self.format_message("WARNING", message))

    def format_message(self, level: str, message: str) -> str:
        timestamp = datetime.now().strftime("%H:%M:%S")
        return f"[{timestamp}] [{level}] {message}"

