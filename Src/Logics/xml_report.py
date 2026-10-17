import xml.etree.ElementTree as ElementTree
from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto

"""
Отчет в формате XML
"""
class xml_report(abstract_report):

    """
    Сформировать отчет: элемент row на каждую строку, field на каждое значение
    """
    def build(self, source) -> report_result_dto:
        header, rows = self._table(source)
        root = ElementTree.Element("report")
        for row in rows:
            row_element = ElementTree.SubElement(root, "row")
            for name, value in zip(header, row):
                field = ElementTree.SubElement(row_element, "field", name=name)
                field.text = str(value)

        result = report_result_dto()
        result.text = ElementTree.tostring(root, encoding="unicode")
        return result
