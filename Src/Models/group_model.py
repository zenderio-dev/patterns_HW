from Src.Core.entity_model import entity_model

"""
Модель группы номенклатуры
"""
class group_model(entity_model):

    """
    Фабричный метод. Группа номенклатуры с наименованием name
    """
    @staticmethod
    def create(name: str) -> 'group_model':
        result = group_model()
        result.name = name
        return result
