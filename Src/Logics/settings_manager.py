from Src.Core.abstract_manager import abstract_manager
from Src.Core.validator import validator, argument_exception
from Src.Logics.deserializer import deserializer
from Src.Models.settings_model import settings_model

"""
Менеджер настроек (singleton). Загружает настройки приложения из JSON-файла
"""
class settings_manager(abstract_manager):
    __deffault_file_name: str = "settings.json"
    __settings: settings_model = None
    __data: dict = None
    __is_loaded: bool = False

    """Singleton. До загрузки файла доступны настройки по умолчанию"""
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(settings_manager, cls).__new__(cls)
            cls.instance.__settings = settings_model()
        return cls.instance

    """
    Загрузка данных. Уже загруженный файл берётся из кэша и повторно не читается.
    force = True - перечитать файл принудительно
    """
    def load (self, file_name = "", force: bool = False):
        inner_file_name = file_name.strip() if file_name and file_name.strip() != "" else self.__deffault_file_name
        validator.validate(inner_file_name, str)

        if self.__is_loaded and self._file_name == inner_file_name and not force:
            return

        self.__data = deserializer.read_json(inner_file_name)

        self.__is_loaded = self.convert()
        self._file_name = inner_file_name

    """
    Преобразование загруженного JSON в модель настроек.
    JSON плоский: поля организации хранятся с префиксом company_ (company_inn и т.д.).
    Ключи, которых нет в файле, пропускаются - остаются значения по умолчанию.
    Если данные некорректны - используются настройки по умолчанию
    """
    def convert(self) -> bool:
        try:
            self.__settings = deserializer().deserialize(self.__data)
            validator.validate(self.__settings, settings_model)
        except argument_exception:
            self.__settings = settings_model()
            return False

        return True

    """
    Модель настроек
    """
    @property
    def settings(self) -> settings_model:
        return self.__settings

    """
    Признак успешной загрузки настроек
    """
    @property
    def is_loaded(self) -> bool:
        return self.__is_loaded
