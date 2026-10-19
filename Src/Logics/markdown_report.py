from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto

"""
Отчет в формате Markdown (бинарные данные)
"""
class markdown_report(abstract_report):

    """
    Сформировать отчет: таблица Markdown на каждый раздел в кодировке UTF-8
    """
    def build(self, source) -> report_result_dto:
        tables = []
        for _, header, rows in self._sections(source):
            lines = [self.__line(header), self.__line(["---"] * len(header))]
            lines += [self.__line(row) for row in rows]
            tables.append("\n".join(lines))

        result = report_result_dto()
        result.binary = "\n\n".join(tables).encode("utf-8")
        return result

    """
    Тип содержимого отчета
    """
    @property
    def content_type(self) -> str:
        return "text/markdown"

    """
    Расширение файла отчета
    """
    @property
    def file_extension(self) -> str:
        return "md"

    """
    Строка таблицы Markdown
    """
    @staticmethod
    def __line(values: list) -> str:
        return "| " + " | ".join(str(value) for value in values) + " |"
