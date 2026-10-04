from abc import ABC


class abstract_manager(ABC):
    """Общий предок менеджеров справочников и документов предметной области."""
    _file_name:str = ""
    _is_loaded:bool = False
    _data:list = []

    """
    Загрузить данные
    """
    def load(self, file_name:str = "")-> None:
        pass

    """
    Преобразовать исходные данные в модели
    """
    def convert(self) -> bool:
        pass
