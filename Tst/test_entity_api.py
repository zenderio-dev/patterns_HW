import pytest

from main import api
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_manager import storage_manager


@pytest.fixture
def client(monkeypatch):
    """Изолировать состояние хранилища для каждого HTTP-сценария."""
    settings_manager().load(force=True)
    storage_manager()
    monkeypatch.delattr(storage_manager, "instance")
    with api.test_client() as test_client:
        yield test_client


"""
<summary>
Проверить создание, чтение, обновление и удаление записи каждого справочника.
</summary>
"""
@pytest.mark.parametrize("entity, fields", [
    ("group", {}),
    ("range", {"value": 1}),
    ("nomenclature", {}),
    ("storage", {"address": "Иркутск"}),
    ("receipt", {"portions": 2, "cooking_time": 10, "items": [], "steps": []}),
])
def test_success_entity_api_crud(client, entity, fields):
    url = f"/api/entities/{entity}"
    fields = {**fields, "name": "Новая запись"}
    if entity == "nomenclature":
        for key in ("group", "range"):
            code = client.get(f"/api/entities/{key}").json()[0]["code"]
            fields[key] = {"unique_code": code}

    created = client.post(url, json=fields)
    assert created.status_code == 201
    code = created.json()["unique_code"]
    item_url = f"{url}/{code}"
    assert client.get(item_url).json()["name"] == "Новая запись"
    updated = client.patch(item_url, json={"name": "Новое имя", "unique_code": "updated-code"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Новое имя"
    assert client.get(item_url).status_code == 404
    assert client.delete(f"{url}/updated-code").status_code == 204
    assert client.get(f"{url}/updated-code").status_code == 404


"""
<summary>
Запретить удаление и смену кода связанной записи, сохранив обычное обновление.
</summary>
"""
@pytest.mark.parametrize("entity", ["group", "range", "nomenclature", "receipt"])
def test_conflict_entity_api_referenced_record(client, entity):
    code = client.get(f"/api/entities/{entity}").json()[0]["code"]
    url = f"/api/entities/{entity}/{code}"
    before = client.get(url).json()
    assert client.delete(url).status_code == 409
    assert client.patch(url, json={"unique_code": "new-code"}).status_code == 409
    assert client.get(url).json() == before
    assert client.patch(url, json={"name": "Новое имя"}).status_code == 200
    assert client.get(url).json()["name"] == "Новое имя"


"""
<summary>
Отклонить неверную ссылку и дубликат кода. Изменение группы должно быть видно в номенклатуре.
</summary>
"""
def test_success_entity_api_validates_and_preserves_links(client):
    code = client.get("/api/entities/nomenclature").json()[0]["code"]
    url = f"/api/entities/nomenclature/{code}"
    before = client.get(url).json()
    group_code = before["group"]["unique_code"]
    assert client.patch(url, json={"group": {"unique_code": "missing"}}).status_code == 400
    assert client.post("/api/entities/group", json={"unique_code": code, "name": "Дубликат"}).status_code == 409
    assert client.get(url).json() == before
    changed = client.patch(f"/api/entities/group/{group_code}", json={"name": "Новая группа"})
    assert changed.status_code == 200
    assert client.get(url).json()["group"]["name"] == "Новая группа"


"""
<summary>
Проверить, что OpenAPI описывает CRUD, а список форматов приходит в JSON.
</summary>
"""
def test_success_openapi_lists_crud_and_formats(client):
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    assert {"get", "patch", "delete"} <= schema.json()["paths"]["/api/entities/{entity}/{code}"].keys()
    assert client.get("/api/formats").json() == ["TXT", "CSV", "MARKDOWN", "XML", "HTML"]


"""
<summary>
Добавить строку через рецепт, пересчитать вес, отклонить цикл и удалить строку.
</summary>
"""
def test_success_entity_api_updates_receipt_items(client):
    receipt_code = client.get("/api/entities/receipt").json()[1]["code"]
    ingredient_code = client.get("/api/entities/nomenclature").json()[0]["code"]
    range_code = client.get("/api/entities/range").json()[0]["code"]
    url = f"/api/entities/receipt/{receipt_code}"
    item = {"model_type": "receipt_item_model", "nomenclature": {"unique_code": ingredient_code},
            "range": {"unique_code": range_code}, "quantity": 100, "waste": 10}

    updated = client.patch(url, json={"items": [item]})
    assert updated.status_code == 200
    assert updated.json()["brutto"] == 100
    assert updated.json()["netto"] == 90
    cycle = {"model_type": "receipt_item_model", "receipt": {"unique_code": receipt_code}, "quantity": 1}
    assert client.patch(url, json={"items": [cycle]}).status_code in (400, 409)
    assert client.get(url).json() == updated.json()
    assert client.patch(url, json={"items": []}).json()["brutto"] == 0


"""
<summary>
Связь с новой группой увеличивает её счётчик. После переноса номенклатуры
в другую группу прежнюю группу можно удалить.
</summary>
"""
def test_equals_storage_repository_counts_after_update(client):
    manager = storage_manager()
    group_url = "/api/entities/group"
    group = client.post(group_url, json={"name": "Временная группа"}).json()
    group_code = group["unique_code"]
    range_code = client.get("/api/entities/range").json()[0]["code"]
    item = client.post("/api/entities/nomenclature", json={
        "name": "Пробный продукт",
        "group": {"unique_code": group_code},
        "range": {"unique_code": range_code},
    })
    assert item.status_code == 201
    assert manager.repository.counts[group_code] == 1
    assert client.delete(f"{group_url}/{group_code}").status_code == 409

    other_code = client.get(group_url).json()[0]["code"]
    item_code = item.json()["unique_code"]
    updated = client.patch(f"/api/entities/nomenclature/{item_code}", json={
        "group": {"unique_code": other_code},
    })
    assert updated.status_code == 200
    assert manager.repository.counts[group_code] == 0
    assert client.delete(f"{group_url}/{group_code}").status_code == 204
    assert group_code not in manager.repository.counts


"""
<summary>
POST-фильтр принимает DTO и возвращает подходящую модель каждого требуемого типа.
</summary>
"""
@pytest.mark.parametrize("entity", ["nomenclature", "group", "range", "receipt"])
def test_equals_filter_api_post_all_models(client, entity):
    before = client.get(f"/api/entities/{entity}").json()
    code = before[0]["code"]
    response = client.post(f"/api/filter/{entity}", json={
        "field": "unique_code", "operation": "EQUALS", "value": code,
    })
    assert response.status_code == 200
    assert [item["unique_code"] for item in response.json()] == [code]
    assert client.get(f"/api/entities/{entity}").json() == before


"""
<summary>
Фильтр проходит по цепочке базовых единиц, а ОСВ рассчитывает период по начальным данным.
</summary>
"""
def test_equals_filter_api_nested_and_turnover(client):
    response = client.post("/api/filter/range", json={
        "field": "base.name", "operation": "EQUALS", "value": "грамм",
    })
    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["кг"]
    balance = client.post("/api/turnover", json={
        "field": "nomenclature.name", "operation": "EQUALS", "value": "Пшеничная мука",
        "date_from": "2026-01-02", "date_to": "2026-01-03",
    })
    assert balance.status_code == 200
    row = balance.json()[0]
    assert (row["opening"], row["income"], row["expense"], row["closing"]) == (1000, 2000, 500, 2500)
    assert client.post("/api/filter/group", json={"field": "name", "value": "Нет"}).json() == []
    assert client.post("/api/turnover", json={"field": "nomenclature.name", "value": "Нет"}).json() == []


"""
<summary>
API отклоняет неверные поля, операции и периоды фильтра внутренней ошибкой 400.
</summary>
"""
@pytest.mark.parametrize("path, body", [
    ("/api/filter/group", {"field": "unknown.name", "value": "x"}),
    ("/api/filter/group", {"field": "name", "operation": "INVALID", "value": "x"}),
    ("/api/filter/group", {"field": "name", "value": 1}),
    ("/api/turnover", {"date_from": "2026-02-01", "date_to": "2026-01-01"}),
])
def test_raise_filter_api_invalid_dto(client, path, body):
    assert client.post(path, json=body).status_code == 400
