from Src.Core.entity_model import entity_model
from Src.Core.validator import validator


"""
Модель склада
"""
class storage_model(entity_model):
    __address:str = ""

    """
    Адрес
    """
    @property
    def address(self) -> str:
        return self.__address.strip()
    
    @address.setter
    def address(self, value:str):
        validator.validate(value, str)
        self.__address = value.strip()


    """
    Фабричный метод. Склад с наименованием и адресом
    """
    @staticmethod
    def create(name: str, address: str) -> 'storage_model':
        result = storage_model()
        result.name = name
        result.address = address
        return result
