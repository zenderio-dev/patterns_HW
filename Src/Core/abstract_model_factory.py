from abc import ABC, abstractmethod
from Src.Core.abstract_model import abstract_model


"""
Абстрактная фабрика доменных моделей
"""
class abstract_model_factory(ABC):

    """
    Создать модель указанного типа
    """
    @abstractmethod
    def create(self, model_type: str) -> abstract_model:
        pass
