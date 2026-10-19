import io
import flask
import connexion
from Src.Core.abstract_report import abstract_report
from Src.Core.validator import argument_exception, operation_exception
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_manager import storage_manager
from Src.Logics.report_factory import report_factory

api = connexion.FlaskApp(__name__, specification_dir="./")
api.app.json.ensure_ascii = False
settings_manager().load()

"""
Сформировать ответ по отчету: для бинарных данных - скачивание файла, иначе - текст
"""
def build_response(report: abstract_report, entity: str, code: str):
    try:
        result = report.build(storage_manager().find(entity, code))
    except operation_exception as ex:
        flask.abort(404, str(ex))
    if len(result.binary) > 0:
        return flask.send_file(io.BytesIO(result.binary), mimetype=report.content_type,
                               as_attachment=True, download_name=f"{entity}.{report.file_extension}")
    return flask.Response(result.text, mimetype=report.content_type)

"""
Отчет в указанном формате для указанного типа и кода сущности
"""
@api.route("/api/report/<format>/<entity>/<code>", methods=["GET"])
def get_report(format: str, entity: str, code: str):
    try:
        report = report_factory(settings_manager().settings).create_by_name(format)
    except argument_exception as ex:
        flask.abort(400, str(ex))
    return build_response(report, entity, code)

"""
Отчет в формате из настроек (create_default) для указанного типа и кода сущности
"""
@api.route("/api/report/<entity>/<code>", methods=["GET"])
def get_default_report(entity: str, code: str):
    report = report_factory(settings_manager().settings).create_default()
    return build_response(report, entity, code)

"""
Список сущностей указанного типа: код и наименование
"""
@api.route("/api/list/<entity>", methods=["GET"])
def get_list(entity: str):
    try:
        items = storage_manager().get(entity)
    except operation_exception as ex:
        flask.abort(404, str(ex))
    return flask.jsonify([{"code": item.unique_code, "name": item.name} for item in items])

if __name__ == "__main__":
    api.run(host="0.0.0.0", port=8080)
