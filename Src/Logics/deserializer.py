import json
from datetime import date
from uuid import uuid4
from Src.Core.abstract_model import abstract_model
from Src.Core.abstract_model_factory import abstract_model_factory
from Src.Core.validator import validator, argument_exception, operation_exception
from Src.Dtos.filter_dto import filter_dto
from Src.Dtos.filter_type_enum import filter_type_enum
from Src.Logics.model_factory import model_factory
from Src.Models.settings_model import settings_model


"""
Восстановление доменных моделей из JSON с сохранением кодов и общих ссылок
"""
class deserializer:
    __factory: abstract_model_factory = None

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
    Прочитать JSON-файл и восстановить хранилище или отдельную модель
    """
    def load(self, file_name: str):
        return self.deserialize(self.read_json(file_name))

    """Прочитать JSON и сообщить об ошибке файла."""
    @staticmethod
    def read_json(file_name: str):
        validator.validate(file_name, str)
        try:
            with open(file_name, encoding="utf-8") as file:
                return json.load(file)
        except (OSError, UnicodeError, json.JSONDecodeError) as ex:
            raise operation_exception(f"Не удалось прочитать JSON: {file_name}. {ex}") from ex

    """
    Восстановить DTO запроса, модель, настройки или словарь коллекций
    """
    def deserialize(self, source: dict, references: dict = None, *, dto_type=None):
        validator.validate(source, dict)
        if dto_type is filter_dto:
            return self.__restore_filter(source)
        if dto_type is not None:
            raise argument_exception("dto_type", "Неизвестный тип DTO")
        models = {}
        active = set()
        if "model_type" in source:
            return self.__restore(source, models, active, references)
        if settings_model.is_flat(source):
            return self.__factory.create("settings_model", settings_model.flat_fields(source))

        result = {}
        for key, items in source.items():
            validator.validate(items, list)
            result[key] = [self.__restore(item, models, active, references) for item in items]
        return result

    @staticmethod
    def __restore_filter(source: dict) -> filter_dto:
        """Восстановить перечисление и даты из параметров запроса."""
        if source.keys() - {"field", "operation", "value", "date_from", "date_to"}:
            raise argument_exception("source", "Неизвестное поле фильтра")
        try:
            operation = filter_type_enum(source.get("operation", "EQUALS"))
            dates = {}
            for field in ("date_from", "date_to"):
                value = source.get(field)
                if value is not None:
                    validator.validate(value, str)
                    dates[field] = date.fromisoformat(value)
        except (ValueError, TypeError) as ex:
            raise argument_exception("source", "Некорректная операция или дата") from ex
        if len(dates) == 2 and dates["date_from"] > dates["date_to"]:
            raise argument_exception("period", "Начало периода позже окончания")
        return filter_dto(source.get("field"), operation, source.get("value"), **dates)

    """
    Восстановить вложенные поля и передать создание модели фабрике
    """
    def __restore(self, source: dict, models: dict, active: set, references) -> abstract_model:
        validator.validate(source, dict)
        model_type = source.get("model_type")
        validator.validate(model_type, str)
        code = source.get("unique_code")
        validator.validate(code, str)
        code = code.strip()
        if code in active:
            raise argument_exception("unique_code", f"Циклическая ссылка на модель: {code}")
        if code in models:
            saved_source, model = models[code]
            if saved_source != source:
                raise argument_exception("unique_code", f"Противоречащие данные для кода: {code}")
            return model

        active.add(code)
        try:
            fields = {name: self.__restore_value(value, models, active, references)
                      for name, value in source.items() if name != "model_type"}
            model = self.__factory.create(model_type, fields)
        finally:
            active.remove(code)
        models[code] = (source, model)
        return model

    """
    Рекурсивно восстановить модель или список, простое значение оставить как есть
    """
    def __restore_value(self, value, models: dict, active: set, references):
        if isinstance(value, dict):
            if references is not None:
                if value.keys() == {"unique_code"}:
                    code = value["unique_code"]
                    validator.validate(code, str)
                    if code.strip() not in references:
                        raise argument_exception("unique_code", f"Неизвестная ссылка: {code}")
                    return references[code.strip()]
                if "model_type" in value and "unique_code" not in value:
                    value = {**value, "unique_code": uuid4().hex}
            return self.__restore(value, models, active, references)
        if isinstance(value, list):
            return [self.__restore_value(item, models, active, references) for item in value]
        return value
