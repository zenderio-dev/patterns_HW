from abc import ABC


class abstract_manager(ABC):
    """Общий предок менеджеров справочников и документов предметной области."""
    _file_name:str = ""
    _is_loaded:bool = False
    _data:list = []

    """
    Загрузить данные. Повторная загрузка берёт данные из кэша, force = True - загрузить заново
    """
    def load(self, file_name:str = "", force:bool = False)-> None:
        pass

    """
    Преобразовать исходные данные в модели
    """
    def convert(self) -> bool:
        pass
