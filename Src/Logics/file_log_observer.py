from pathlib import Path
from threading import Lock


class file_log_observer:
    """Подписчик, который дописывает события в текстовый журнал."""

    def __init__(self, path: Path):
        """Запомнить путь и подготовить блокировку записи."""
        self._path = path
        self.__lock = Lock()

    def __call__(self, timestamp: str, subsystem: str, level: str, message: str) -> None:
        """Добавить одну строку, экранируя символы-разделители."""
        message = message.replace("\t", r"\t").replace("\r", r"\r").replace("\n", r"\n")
        with self.__lock, self._path.open("a", encoding="utf-8") as file:
            file.write(f"{timestamp}\t{subsystem}\t{level}\t{message}\n")
