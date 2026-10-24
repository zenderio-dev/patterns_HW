from abc import ABC, abstractmethod
from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_type_enum import report_type_enum

"""
Абстрактная фабрика отчетов
"""
class abstract_report_factory(ABC):

    """
    Создать отчет указанного формата
    """
    @abstractmethod
    def create(self, report_type: report_type_enum) -> abstract_report:
        pass

    """
    Создать отчет в формате по умолчанию
    """
    @abstractmethod
    def create_default(self) -> abstract_report:
        pass
