from Src.Core.validator import validator
from Src.Core.entity_model import entity_model
from Src.Core.common import common
from Src.Core.event_publisher import events

###############################################
# Модель организации
class company_model(entity_model):
    __inn:int = 0
    __bic:int = 0
    __corr_account:int = 0
    __account:int = 0
    __ownership:str = ""
    """Признак того, что организация входит в действующие настройки."""
    __track_changes = False

    def track_changes(self, enabled: bool) -> None:
        """Включить журнал изменений действующей организации."""
        self.__track_changes = enabled

    def parameters(self) -> dict:
        """Вернуть поля организации в формате настроек."""
        return {f"company_{field}": getattr(self, field)
                for field in common.get_fields(self) if field != "unique_code"}

    def __notify_change(self, field: str, previous) -> None:
        """Сообщить об изменении поля после его обновления."""
        if self.__track_changes and previous != getattr(self, field):
            events.publish("settings", "INFO", f"Изменён параметр: company_{field}")

    @entity_model.name.setter
    def name(self, value: str) -> None:
        """Изменить наименование организации."""
        previous = self.name
        entity_model.name.fset(self, value)
        self.__notify_change("name", previous)

    """Восстановить организацию из полей настроек."""
    @classmethod
    def from_dict(cls, source: dict) -> 'company_model':
        result = cls()
        for field, value in source.items():
            if not isinstance(getattr(cls, field, None), property):
                continue
            setattr(result, field, value)
        return result

    # ИНН : 12 симв
    # Счет 11 симв
    # Корреспондентский счет 11 симв
    # БИК 9 симв
    # Наименование
    # Вид собственности 5 симв

    # ИНН
    @property
    def inn(self) -> int:
        return self.__inn
    
    @inn.setter
    def inn(self, value:int):
        validator.validate(value, int, 12)
        previous = self.__inn
        self.__inn = value
        self.__notify_change("inn", previous)

    # КПП
    @property
    def bic(self) -> int:
        return self.__bic

    @bic.setter
    def bic(self, value:int):
        validator.validate(value, int, 9)
        previous = self.__bic
        self.__bic = value
        self.__notify_change("bic", previous)

    # Корреспондентский счет
    @property
    def corr_account(self) -> int:
        return self.__corr_account
        
    @corr_account.setter
    def corr_account(self, value:int):
        validator.validate(value, int, 11)
        previous = self.__corr_account
        self.__corr_account = value
        self.__notify_change("corr_account", previous)

    # Банковский счет
    @property
    def account(self) -> int:
        return self.__account
    
    @account.setter
    def account(self, value:int):
        validator.validate(value, int, 11)
        previous = self.__account
        self.__account = value
        self.__notify_change("account", previous)

    # Вид собственности
    @property
    def ownership(self) -> str:
        return self.__ownership
    
    @ownership.setter
    def ownership(self, value:str):
        validator.validate(value, str, 5)
        previous = self.__ownership
        self.__ownership = value.strip()
        self.__notify_change("ownership", previous)

 

       


