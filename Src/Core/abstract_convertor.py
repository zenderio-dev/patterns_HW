from abc import ABC, abstractmethod

"""
Абстрактный конвертер: формирует по объекту словарь "наименование поля - данные поля"
"""
class abstract_convertor(ABC):

    """
    Сформировать словарь по полям объекта
    """
    @abstractmethod
    def convert(self, source) -> dict:
        pass
