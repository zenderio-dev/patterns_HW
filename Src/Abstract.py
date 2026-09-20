from abc import ABC, abstractmethod
from uuid import uuid4


class AbstractModel(ABC):
    """Общий предок справочников и документов предметной области."""

    def __init__(self):
        """Создаёт запись с собственным кодом и пустым названием."""
        self.__code = uuid4().hex
        self.__title = ""

    @property
    def code(self) -> str:
        """Возвращает неизменяемый код записи."""
        return self.__code

    @property
    def title(self) -> str:
        """Возвращает название записи."""
        return self.__title

    @title.setter
    def title(self, value: str):
        """Задаёт название записи, отсекая краевые пробелы."""
        if not value or not value.strip():
            raise ValueError("Название записи не должно быть пустым")

        self.__title = value.strip()

    @abstractmethod
    def describe(self) -> str:
        """Возвращает текстовое представление записи."""
