from Src.Core.entity_model import entity_model
from Src.Core.validator import validator

"""
Модель группы номенклатуры
"""
class group_model(entity_model):

    """
    Восстановить группу из подготовленных полей
    """
    @classmethod
    def from_dict(cls, source: dict) -> 'group_model':
        validator.validate(source, dict)
        result = cls.create(source.get("name"))
        result.unique_code = source.get("unique_code")
        return result

    """
    Фабричный метод. Группа номенклатуры с наименованием name
    """
    @staticmethod
    def create(name: str) -> 'group_model':
        result = group_model()
        result.name = name
        return result
