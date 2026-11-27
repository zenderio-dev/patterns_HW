import io
import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
import flask
import connexion
from connexion.exceptions import ProblemException
from connexion.middleware import MiddlewarePosition
from connexion.resolver import Resolver
from Src.Core.abstract_report import abstract_report
from Src.Core.event_publisher import events, log_operation
from Src.Core.validator import argument_exception, operation_exception, conflict_exception
from Src.Dtos.filter_dto import filter_dto
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_manager import storage_manager
from Src.Logics.report_factory import report_factory
from Src.Logics.convert_factory import convert_factory
from Src.Logics.entity_service import entity_service
from Src.Logics.file_log_observer import file_log_observer
from Src.Logics.deserializer import deserializer
from Src.Logics.turnover_service import turnover_service
from Src.Logics.web_log_middleware import web_log_middleware

api = connexion.FlaskApp(__name__, specification_dir="./")
api.app.json.ensure_ascii = False
log_observer = file_log_observer(Path(__file__).with_name("application.log"))
events.subscribe(log_observer)
api.add_middleware(web_log_middleware, position=MiddlewarePosition.BEFORE_EXCEPTION)
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
def get_report(format: str, entity: str, code: str):
    try:
        report = report_factory(settings_manager().settings).create_by_name(format)
    except argument_exception as ex:
        flask.abort(400, str(ex))
    return build_response(report, entity, code)

"""
Отчет в формате из настроек (create_default) для указанного типа и кода сущности
"""
def get_default_report(entity: str, code: str):
    report = report_factory(settings_manager().settings).create_default()
    return build_response(report, entity, code)

"""
Список сущностей указанного типа: код и наименование
"""
@log_operation("crud", "Список сущностей")
def get_list(entity: str):
    try:
        items = storage_manager().get(entity)
    except operation_exception as ex:
        flask.abort(404, str(ex))
    return flask.jsonify([{"code": item.unique_code, "name": item.name} for item in items])

"""
Список форматов отчетов
"""
def get_formats():
    return flask.jsonify(report_factory(settings_manager().settings).formats())

"""
Список типов сущностей
"""
def get_entities():
    return flask.jsonify(storage_manager().keys())

"""
Сформировать JSON-файл для скачивания по словарю данных
"""
def build_json(source: dict, name: str):
    result = convert_factory().create(source).convert(source)
    data = json.dumps(result, ensure_ascii=False, indent=4)
    return flask.send_file(io.BytesIO(data.encode("utf-8")), mimetype="application/json",
                           as_attachment=True, download_name=f"{name}.json")

"""
Все данные хранилища в одном JSON-файле
"""
def get_json_all():
    return build_json(storage_manager().data, "storage")

"""
Все сущности указанного типа в формате JSON (файл для скачивания)
"""
def get_json(entity: str):
    try:
        items = storage_manager().get(entity)
    except operation_exception as ex:
        flask.abort(404, str(ex))
    return build_json({entity: items}, entity)


"""Вызвать операцию и преобразовать доменные ошибки в HTTP-ответ."""
def run_entity_operation(operation, *args):
    try:
        return operation(*args)
    except conflict_exception as ex:
        raise ProblemException(status=409, title="Конфликт", detail=str(ex)) from ex
    except argument_exception as ex:
        raise ProblemException(status=400, title="Некорректные данные", detail=str(ex)) from ex
    except operation_exception as ex:
        raise ProblemException(status=404, title="Сущность не найдена", detail=str(ex)) from ex


"""Преобразовать модель в JSON через фабрику конвертеров."""
def entity_data(model):
    return convert_factory().create(model).convert(model)


"""Получить сущность по коду."""
@log_operation("crud", "Чтение сущности")
def get_entity(entity: str, code: str):
    return entity_data(run_entity_operation(storage_manager().find, entity, code))


"""Создать сущность."""
def create_entity(entity: str, body: dict):
    return entity_data(run_entity_operation(entity_service(storage_manager()).create, entity, body)), 201


"""Изменить переданные поля сущности."""
def update_entity(entity: str, code: str, body: dict):
    return entity_data(run_entity_operation(entity_service(storage_manager()).update, entity, code, body))


"""Удалить сущность по коду."""
def delete_entity(entity: str, code: str):
    run_entity_operation(entity_service(storage_manager()).delete, entity, code)
    return None, 204


"""Вернуть модели справочника по DTO фильтрации."""
def filter_entities(entity: str, body: dict):
    condition = read_filter(body)
    models = run_entity_operation(entity_service(storage_manager()).filter, entity, condition)
    return [entity_data(model) for model in models]


"""Вернуть ОСВ по фильтру и необязательному периоду."""
def get_turnover(body: dict):
    condition = read_filter(body)
    rows = run_entity_operation(turnover_service(storage_manager()).build, condition)
    return [entity_data({key: float(value) if isinstance(value, Decimal) else value
                         for key, value in asdict(row).items()}) for row in rows]


"""Восстановить DTO из тела запроса через общий десериализатор."""
def read_filter(body: dict) -> filter_dto:
    return run_entity_operation(lambda: deserializer().deserialize(body, dto_type=filter_dto))


"""Разрешить обработчики OpenAPI при импорте и запуске main.py."""
def resolve_operation(operation: str):
    return get_list if operation == "list_entities" else globals()[operation]


api.add_api("openapi.yaml", resolver=Resolver(resolve_operation))

if __name__ == "__main__":
    api.run(host="0.0.0.0", port=8080)
