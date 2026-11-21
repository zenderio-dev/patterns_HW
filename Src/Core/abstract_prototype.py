from abc import ABC, abstractmethod

from Src.Dtos.filter_dto import filter_dto


class abstract_prototype(ABC):
    """Прототип набора данных, создающий отфильтрованную копию."""

    @abstractmethod
    def clone(self, condition: filter_dto) -> 'abstract_prototype':
        """Вернуть отдельный прототип по условию отбора."""
        pass
