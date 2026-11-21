import pytest

from main import api
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_manager import storage_manager


@pytest.fixture
def client(monkeypatch):
    """Изолировать состояние хранилища для каждого HTTP-сценария."""
    settings_manager().load(force=True)
    manager = storage_manager()
    monkeypatch.setattr(manager, "_storage_manager__data", {})
    monkeypatch.setattr(manager, "_storage_manager__is_loaded", False)
    manager.load(force=True)
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
