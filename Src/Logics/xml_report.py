import xml.etree.ElementTree as ElementTree
from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto

"""
Отчет в формате XML
"""
class xml_report(abstract_report):

    """
    Сформировать отчет: элемент section на раздел, row на строку, field на значение
    """
    def build(self, source) -> report_result_dto:
        root = ElementTree.Element("report")
        for section in self._sections(source):
            section_element = ElementTree.SubElement(root, "section", name=section.name)
            for row in section.rows:
                row_element = ElementTree.SubElement(section_element, "row")
                for field_name, value in zip(section.header, row):
                    field = ElementTree.SubElement(row_element, "field", name=field_name)
                    field.text = str(value)

        result = report_result_dto()
        result.text = ElementTree.tostring(root, encoding="unicode")
        return result

    """
    Тип содержимого отчета
    """
    @property
    def content_type(self) -> str:
        return "application/xml"

    """
    Расширение файла отчета
    """
    @property
    def file_extension(self) -> str:
        return "xml"
