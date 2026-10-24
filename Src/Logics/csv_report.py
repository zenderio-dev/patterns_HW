import csv
import io
from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto

"""
Отчет в формате CSV (бинарные данные)
"""
class csv_report(abstract_report):

    """
    Сформировать отчет: CSV с разделителем ";" в кодировке UTF-8, разделы через пустую строку
    """
    def build(self, source) -> report_result_dto:
        stream = io.StringIO()
        writer = csv.writer(stream, delimiter=";", lineterminator="\n")
        for index, section in enumerate(self._sections(source)):
            if index > 0:
                writer.writerow([])
            writer.writerow(section.header)
            writer.writerows(section.rows)

        result = report_result_dto()
        result.binary = stream.getvalue().encode("utf-8")
        return result

    """
    Тип содержимого отчета
    """
    @property
    def content_type(self) -> str:
        return "text/csv"

    """
    Расширение файла отчета
    """
    @property
    def file_extension(self) -> str:
        return "csv"
