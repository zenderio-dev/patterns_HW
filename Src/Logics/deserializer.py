import math
from Src.Core.abstract_model import abstract_model
from Src.Core.abstract_model_factory import abstract_model_factory
from Src.Core.validator import validator, argument_exception
from Src.Logics.model_factory import model_factory


"""
Восстановление доменных моделей из JSON с сохранением кодов и общих ссылок
"""
class deserializer:
    __factory: abstract_model_factory = None
    __entity_fields: dict = {"unique_code": str, "name": str}
    __fields: dict = {
        "group": __entity_fields,
        "range": {**__entity_fields, "value": int, "base": "range"},
        "nomenclature": {**__entity_fields, "group": "group", "range": "range"},
        "storage": {**__entity_fields, "address": str},
        "receipt": {
            **__entity_fields,
            "portions": int,
            "cooking_time": int,
            "items": ["receipt_item"],
            "steps": [str],
        },
        "receipt_item": {
            "unique_code": str,
            "nomenclature": "nomenclature",
            "receipt": "receipt",
            "range": "range",
            "quantity": (int, float),
            "unit_weight": (int, float),
            "waste": (int, float),
        },
    }

    """
    Создать десериализатор с фабрикой моделей
    """
    def __init__(self, factory: abstract_model_factory = None):
        self.__factory = model_factory() if factory is None else factory
        validator.validate(self.__factory, abstract_model_factory)

    """
    Фабрика моделей
    """
    @property
    def factory(self) -> abstract_model_factory:
        return self.__factory


    """
    Восстановить словарь справочников или отдельную модель.
    Для отдельной модели model_type обязателен, для хранилища тип задается ключом
    """
    def deserialize(self, source: dict, model_type: str = ""):
        validator.validate(source, dict)
        if not isinstance(model_type, str):
            raise argument_exception("model_type", "Тип модели должен быть строкой")
        models = {}
        active = set()
        if model_type:
            return self.__restore(source, model_type, models, active)

        result = {}
        for key, items in source.items():
            self.__check_type(key)
            validator.validate(items, list)
            result[key] = [self.__restore(item, key, models, active) for item in items]
        return result

    """
    Проверить наличие описания типа модели
    """
    def __check_type(self, model_type: str) -> None:
        validator.validate(model_type, str)
        if model_type not in self.__fields:
            raise argument_exception("model_type", f"Неизвестный тип модели: {model_type}")

    """
    Рекурсивно восстановить модель. Повторный код должен иметь те же тип и данные
    """
    def __restore(self, source: dict, model_type: str, models: dict, active: set) -> abstract_model:
        self.__check_type(model_type)
        validator.validate(source, dict)
        fields = self.__fields[model_type]
        if not fields.keys() <= source.keys():
            raise argument_exception("source", f"Не хватает полей модели: {model_type}")
        code = source["unique_code"]
        validator.validate(code, str)
        code = code.strip()
        if code in active:
            raise argument_exception("unique_code", f"Циклическая ссылка на модель: {code}")
        if code in models:
            saved_type, saved_source, model = models[code]
            if saved_type != model_type or saved_source != source:
                raise argument_exception("unique_code", f"Противоречащие данные для кода: {code}")
            return model

        model = self.__factory.create(model_type)
        for name in source.keys() - fields.keys():
            attribute = getattr(type(model), name, None) if isinstance(name, str) else None
            if not isinstance(attribute, property) or attribute.fset is not None:
                raise argument_exception("source", f"Неизвестное поле модели: {name}")

        active.add(code)
        try:
            for name, field_type in fields.items():
                value = self.__restore_value(source[name], field_type, models, active)
                if name == "items":
                    for item in value:
                        model.add_item(item)
                elif name == "steps":
                    for step in value:
                        model.add_step(step)
                elif value is not None:
                    setattr(model, name, value)
            if model_type == "receipt_item" and model.component is None:
                raise argument_exception("source", "В строке не указан ингредиент или полуфабрикат")
        finally:
            active.remove(code)

        models[code] = (model_type, source, model)
        return model

    """
    Восстановить ссылку, список или простое значение согласно описанию поля
    """
    def __restore_value(self, value, field_type, models: dict, active: set):
        if isinstance(field_type, str):
            return None if value is None else self.__restore(value, field_type, models, active)
        if isinstance(field_type, list):
            validator.validate(value, list)
            return [self.__restore_value(item, field_type[0], models, active) for item in value]
        validator.validate(value, field_type)
        if isinstance(value, bool) or (isinstance(value, float) and not math.isfinite(value)):
            raise argument_exception("value", "Ожидается конечное число или строка")
        return value
