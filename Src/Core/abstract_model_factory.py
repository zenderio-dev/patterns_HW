from abc import ABC, abstractmethod
from Src.Core.abstract_model import abstract_model


"""
Абстрактная фабрика доменных моделей
"""
class abstract_model_factory(ABC):

    """
    Восстановить модель указанного типа из подготовленных полей
    """
    @abstractmethod
    def create(self, model_type: str, source: dict) -> abstract_model:
        pass
