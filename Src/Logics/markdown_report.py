from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto

"""
Отчет в формате Markdown (бинарные данные)
"""
class markdown_report(abstract_report):

    """
    Сформировать отчет: таблица Markdown в кодировке UTF-8
    """
    def build(self, source) -> report_result_dto:
        header, rows = self._table(source)
        lines = [self.__line(header), self.__line(["---"] * len(header))]
        lines += [self.__line(row) for row in rows]

        result = report_result_dto()
        result.binary = "\n".join(lines).encode("utf-8")
        return result

    """
    Строка таблицы Markdown
    """
    @staticmethod
    def __line(values: list) -> str:
        return "| " + " | ".join(str(value) for value in values) + " |"
