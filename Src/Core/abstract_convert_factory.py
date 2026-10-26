from abc import ABC, abstractmethod
from Src.Core.abstract_convertor import abstract_convertor

"""
Абстрактная фабрика конвертеров
"""
class abstract_convert_factory(ABC):

    """
    Подобрать конвертер по типу значения
    """
    @abstractmethod
    def create(self, value) -> abstract_convertor:
        pass
