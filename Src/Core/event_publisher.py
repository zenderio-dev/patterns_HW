from datetime import datetime
from functools import wraps
import sys


class event_publisher:
    """Передаёт события подписчикам."""

    def __init__(self):
        """Создать издателя без подписчиков."""
        self.__observers = []

    def subscribe(self, observer) -> None:
        """Подключить подписчика."""
        if observer not in self.__observers:
            self.__observers.append(observer)

    def unsubscribe(self, observer) -> None:
        """Отключить подписчика."""
        self.__observers.remove(observer)

    def publish(self, subsystem: str, level: str, message: str) -> None:
        """Передать подписчикам одну запись с временем события."""
        event = (datetime.now().isoformat(sep=" ", timespec="milliseconds"),
                 subsystem, level, message)
        for observer in tuple(self.__observers):
            try:
                observer(*event)
            except Exception as ex:
                print(f"Ошибка подписчика журнала: {ex}", file=sys.stderr)


events = event_publisher()


def log_operation(subsystem: str, action: str):
    """Записать результат операции, сохранив её возврат и исключения."""
    def decorate(operation):
        """Подключить публикацию событий к операции."""
        @wraps(operation)
        def run(*args, **kwargs):
            """Выполнить операцию и сообщить о её результате."""
            try:
                result = operation(*args, **kwargs)
            except Exception as ex:
                cause = ex.__cause__ or ex
                events.publish(subsystem, "ERROR", f"{action}: {type(cause).__name__}")
                raise

            events.publish(subsystem, "INFO", action)
            return result

        return run

    return decorate
