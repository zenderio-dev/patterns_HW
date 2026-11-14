from Src.Core.entity_model import entity_model
from Src.Core.validator import validator


"""
Модель склада
"""
class storage_model(entity_model):
    __address:str = ""

    """
    Восстановить склад из подготовленных полей
    """
    @classmethod
    def from_dict(cls, source: dict) -> 'storage_model':
        validator.validate(source, dict)
        result = cls.create(source.get("name"), source.get("address"))
        result.unique_code = source.get("unique_code")
        return result

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
