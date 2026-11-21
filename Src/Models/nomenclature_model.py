from Src.Core.entity_model import entity_model
from Src.Models.group_model import group_model
from Src.Models.range_model import range_model
from Src.Core.validator import validator

"""
Модель номенклатуры
"""
class nomenclature_model(entity_model):
    __group: group_model = None
    __range: range_model = None

    """Группа и единица измерения номенклатуры."""
    def references(self) -> tuple:
        return self.group, self.range

    """
    Восстановить номенклатуру с готовыми группой и единицей измерения
    """
    @classmethod
    def from_dict(cls, source: dict) -> 'nomenclature_model':
        validator.validate(source, dict)
        result = cls.create(source.get("name"), source.get("group"), source.get("range"))
        result.unique_code = source.get("unique_code")
        return result

   
    """
    Группа номенклатуры
    """
    @property
    def group(self) -> group_model:
        return self.__group

    @group.setter
    def group(self, value: group_model):
        validator.validate(value, group_model)
        self.__group = value    

    """
    Единица измерения
    """
    @property
    def range(self) -> range_model:
        return self.__range
    
    @range.setter
    def range(self, value: range_model):
        validator.validate(value, range_model)
        self.__range = value


    """
    Фабричный метод. Номенклатура с группой и единицей измерения
    """
    @staticmethod
    def create(name: str, group: group_model, range: range_model) -> 'nomenclature_model':
        result = nomenclature_model()
        result.name = name
        result.group = group
        result.range = range
        return result
