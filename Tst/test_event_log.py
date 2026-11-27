import pytest

from Src.Core.event_publisher import event_publisher
from Src.Core.validator import operation_exception
from Src.Dtos.report_type_enum import report_type_enum
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_manager import storage_manager


@pytest.mark.unit
def test_equals_event_publisher_notifies_subscribers(capsys):
    """
    <summary>
    Сбой первого подписчика не мешает второму получить событие.
    После отписки второй подписчик больше не получает события.
    </summary>
    """
    received = []

    def fail(*event):
        """Имитировать сбой подписчика."""
        raise RuntimeError("Журнал недоступен")

    def collect(*event):
        """Сохранить полученное событие."""
        received.append(event)

    publisher = event_publisher()
    publisher.subscribe(fail)
    publisher.subscribe(collect)
    publisher.publish("crud", "INFO", "Сущность создана")
    publisher.unsubscribe(collect)
    publisher.publish("crud", "ERROR", "После отписки")

    event, = received
    timestamp, subsystem, level, message = event
    assert timestamp
    assert (subsystem, level, message) == ("crud", "INFO", "Сущность создана")
    assert "Журнал недоступен" in capsys.readouterr().err


@pytest.mark.integration
def test_success_event_log_records_application_operations(tmp_path, monkeypatch):
    """
    <summary>
    Проверить журнал CRUD, начальных движений и HTTP-ответа 404 после удаления.
    Проверить изменение настроек, повторную установку значения и ошибку чтения файла.
    </summary>
    """
    from main import api, log_observer

    storage_manager()
    monkeypatch.delattr(storage_manager, "instance")
    monkeypatch.delattr(settings_manager, "instance")
    config = tmp_path / "settings.json"
    config.write_text('{"first_start": true}', encoding="utf-8")
    manager = settings_manager()
    manager.load(str(config))

    path = tmp_path / "application.log"
    monkeypatch.setattr(log_observer, "_path", path)
    manager.settings.response_format = report_type_enum.XML
    manager.settings.response_format = report_type_enum.XML
    manager.settings.company.ownership = "АО"
    with pytest.raises(operation_exception):
        manager.load(str(tmp_path / "missing.json"))
    with api.test_client() as client:
        url = "/api/entities/group"
        response = client.post(url, json={"name": "Проверка журнала"})
        assert response.status_code == 201
        item_url = f"{url}/{response.json()['unique_code']}"
        assert client.get(item_url).status_code == 200
        assert client.patch(item_url, json={"name": "Группа обновлена"}).status_code == 200
        assert client.delete(item_url).status_code == 204
        assert client.get(item_url).status_code == 404
        assert client.post("/api/turnover", json={}).status_code == 200

    records = [line.split("\t", 3)[1:] for line in path.read_text(encoding="utf-8").splitlines()]
    assert ["crud", "INFO", "Создание сущности"] in records
    assert ["crud", "INFO", "Чтение сущности"] in records
    assert ["crud", "INFO", "Изменение сущности"] in records
    assert ["crud", "INFO", "Удаление сущности"] in records
    assert ["crud", "ERROR", "Чтение сущности: operation_exception"] in records
    assert ["web", "INFO", f"POST {url} 201"] in records
    assert ["web", "ERROR", f"GET {item_url} 404"] in records
    assert ["storage", "INFO", "Расчёт ОСВ"] in records
    assert any(subsystem == "storage" and message.startswith("Начальные данные, приход:")
               for subsystem, _, message in records)
    assert any(subsystem == "storage" and message.startswith("Начальные данные, расход:")
               for subsystem, _, message in records)
    assert records.count(["settings", "INFO", "Изменён параметр: response_format"]) == 1
    assert ["settings", "INFO", "Изменён параметр: company_ownership"] in records
    assert ["settings", "ERROR", "Не удалось прочитать файл настроек"] in records
