from Src.Core.abstract_model import abstract_model
from Src.Core.abstract_model_factory import abstract_model_factory
from Src.Core.validator import validator, argument_exception
from Src.Models.group_model import group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.receipt_item_model import receipt_item_model
from Src.Models.receipt_model import receipt_model
from Src.Models.storage_model import storage_model


"""
Фабрика моделей для восстановления данных хранилища
"""
class model_factory(abstract_model_factory):
    __mapping: dict = {
        "group": group_model,
        "range": range_model,
        "nomenclature": nomenclature_model,
        "storage": storage_model,
        "receipt": receipt_model,
        "receipt_item": receipt_item_model,
    }

    """
    Создать пустую модель по названию типа
    """
    def create(self, model_type: str) -> abstract_model:
        validator.validate(model_type, str)
        if model_type not in self.__mapping:
            raise argument_exception("model_type", f"Неизвестный тип модели: {model_type}")
        return self.__mapping[model_type]()
