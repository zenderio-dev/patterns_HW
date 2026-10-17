import io
import flask
import connexion
from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_type_enum import report_type_enum
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_manager import storage_manager
from Src.Logics.report_factory import report_factory

api = connexion.FlaskApp(__name__, specification_dir="./")
api.app.json.ensure_ascii = False
settings_manager().load()

entity_keys = {
    "nomenclature": storage_manager.nomenclature_key,
    "range": storage_manager.range_key,
    "receipt": storage_manager.receipt_key,
}
content_types = {
    report_type_enum.CSV: "text/csv",
    report_type_enum.MARKDOWN: "text/markdown",
    report_type_enum.XML: "application/xml",
    report_type_enum.TXT: "text/plain",
    report_type_enum.HTML: "text/html",
}
file_extensions = {
    report_type_enum.CSV: "csv",
    report_type_enum.MARKDOWN: "md",
}

"""
Все сущности указанного типа. Если тип неизвестен - ответ 404
"""
def get_entities(entity: str) -> list:
    if entity not in entity_keys:
        flask.abort(404, f"Неизвестный тип сущности: {entity}")
    return storage_manager().data[entity_keys[entity]]

"""
Найти сущность указанного типа по коду. Если не найдена - ответ 404
"""
def find_entity(entity: str, code: str):
    for item in get_entities(entity):
        if item.unique_code == code:
            return item
    flask.abort(404, f"Не найдена сущность {entity} с кодом {code}")

"""
Сформировать ответ: для CSV и Markdown - скачивание файла, для остальных форматов - текст
"""
def build_response(report: abstract_report, report_type: report_type_enum, entity: str, code: str):
    result = report.build(find_entity(entity, code))
    if len(result.binary) > 0:
        return flask.send_file(io.BytesIO(result.binary), mimetype=content_types[report_type],
                               as_attachment=True, download_name=f"{entity}.{file_extensions[report_type]}")
    return flask.Response(result.text, mimetype=content_types[report_type])

"""
Отчет в указанном формате для указанного типа и кода сущности
"""
@api.route("/api/report/<format>/<entity>/<code>", methods=["GET"])
def get_report(format: str, entity: str, code: str):
    if format.upper() not in report_type_enum.__members__:
        flask.abort(400, f"Неизвестный формат: {format}")
    report_type = report_type_enum[format.upper()]
    report = report_factory(settings_manager().settings).create(report_type)
    return build_response(report, report_type, entity, code)

"""
Отчет в формате из настроек (create_default) для указанного типа и кода сущности
"""
@api.route("/api/report/<entity>/<code>", methods=["GET"])
def get_default_report(entity: str, code: str):
    settings = settings_manager().settings
    report = report_factory(settings).create_default()
    return build_response(report, settings.response_format, entity, code)

"""
Список сущностей указанного типа: код и наименование
"""
@api.route("/api/list/<entity>", methods=["GET"])
def get_list(entity: str):
    return flask.jsonify([{"code": item.unique_code, "name": item.name} for item in get_entities(entity)])

if __name__ == "__main__":
    api.run(host="0.0.0.0", port=8080)
