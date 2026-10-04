from Src.Core.abstract_model import abstract_model
from Src.Models.company_model import company_model
from Src.Core.validator import validator, argument_exception

"""
Модель настроек приложения: организация и ответственные лица
"""
class settings_model(abstract_model):
    """Карточка организации"""
    _company:company_model = None
    """Наименование директора"""
    _boss_name:str = ""
    """Наименование главного бухгалтера"""
    _account_name:str = ""


    """
    Наименование организации
    """
    @property
    def company(self) -> company_model:
        return self._company

    @company.setter
    def company(self, value: company_model) -> None:
        validator.validate(value, company_model)
        self._company = value


    """
    Наименование директора
    """
    @property
    def boss_name(self) -> str:
        return self._boss_name

    @boss_name.setter
    def boss_name(self, value: str) -> None:
        validator.validate(value, str, 255)
        self._boss_name = value.strip()

    """
    Наименование главного бухгалтера
    """
    @property
    def account_name(self) -> str:
        return self._account_name

    @account_name.setter
    def account_name(self, value: str) -> None:
        validator.validate(value, str, 255)
        self._account_name = value.strip()