from abc import ABC
import uuid
from Src.Core.validator import validator

"""
Абстрактный класс для наследования моделей
Содержит в себе только генерацию уникального кода
"""
class abstract_model(ABC):
    __unique_code:str

    """
    Создать модель с новым уникальным кодом
    """
    def __init__(self) -> None:
        super().__init__()
        self.__unique_code = uuid.uuid4().hex

    """
    Уникальный код
    """
    @property
    def unique_code(self) -> str:
        return self.__unique_code
    
    @unique_code.setter
    def unique_code(self, value: str):
        validator.validate(value, str)
        self.__unique_code = value.strip()

    """
    Перегрузка штатного варианта сравнения
    """
    def __eq__(self, value) -> bool:
        if value is  None: return False
        if not isinstance(value, abstract_model): return False

        return self.unique_code == value.unique_code

    """
    Хеш по уникальному коду. Согласован с __eq__: равные модели имеют равный хеш
    """
    def __hash__(self) -> int:
        return hash(self.unique_code)

    """Связанные модели и вложенные части сущности."""
    def references(self) -> tuple:
        return ()

    """Применить проверенное состояние, сохранив ссылки на объект."""
    def replace_state(self, source: 'abstract_model') -> None:
        validator.validate(source, type(self))
        self.__dict__ = vars(source).copy()
