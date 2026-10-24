from Src.Core.validator import argument_exception

"""
Набор общих статических методов
"""
class common:

    """
    Получить список публичных свойств модели
    """
    @staticmethod
    def get_fields(source) -> list:
        if source is None:
            raise argument_exception("source", "Не передана модель")
        return [name for name in dir(type(source))
                if not name.startswith("_") and isinstance(getattr(type(source), name), property)]
