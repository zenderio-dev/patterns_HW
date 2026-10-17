import csv
import io
from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto

"""
Отчет в формате CSV (бинарные данные)
"""
class csv_report(abstract_report):

    """
    Сформировать отчет: CSV с разделителем «;» в кодировке UTF-8
    """
    def build(self, source) -> report_result_dto:
        header, rows = self._table(source)
        stream = io.StringIO()
        writer = csv.writer(stream, delimiter=";", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)

        result = report_result_dto()
        result.binary = stream.getvalue().encode("utf-8")
        return result
