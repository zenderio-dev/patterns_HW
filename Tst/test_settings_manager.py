from Src.Logics.settings_manager import settings_manager
from Src.Core.validator import operation_exception

"""
<summary>
Загрузка файла настроек по умолчанию (settings.json) выполняется без исключений
</summary>
"""
def test_not_raise_settings_manager_load():
    # Подготовка
    manager = settings_manager()

    # Действие и проверка
    try:
        manager.load()
        assert True
    except operation_exception:
        assert False
    except:
        assert False

"""
<summary>
После загрузки файла настроек модель настроек заполнена
</summary>
"""
def test_not_empty_settings_manager_load():
    # Подготовка
    manager = settings_manager()

    # Действие
    try:
        manager.load()
    except:
        assert False

    # Проверка
    assert manager.settings is not None

"""
<summary>
Проверка шаблона singleton: два вызова конструктора возвращают один и тот же объект
</summary>
"""
def test_equals_settings_manager_create():
    # Подготовка
    instance1 = settings_manager()
    instance2 = settings_manager()

    # Действие

    # Проверка
    assert instance1 == instance2

"""
<summary>
После загрузки файла настроек выставляется признак is_loaded
</summary>
"""
def test_is_loaded_settings_manager_true():
    # Подготовка
    manager = settings_manager()

    # Действие
    try:
        manager.load()
    except:
        assert False

    # Проверка
    assert manager.is_loaded

"""
<summary>
Настройки загружаются через первый экземпляр и читаются через второй.
Благодаря singleton оба экземпляра возвращают один и тот же объект настроек
</summary>
"""
def test_equals_settings_manager_settings_two_instances():
    # Подготовка
    instance1 = settings_manager()

    # Действие
    instance1.load()
    instance2 = settings_manager()

    # Проверка
    assert instance2.settings is not None
    assert instance1.settings is instance2.settings

"""
<summary>
Метод convert переносит данные из settings.json в модель настроек:
организацию с реквизитами, директора и главного бухгалтера
</summary>
"""
def test_equals_settings_manager_convert_values_from_file():
    # Подготовка
    manager = settings_manager()

    # Действие
    manager.load()
    settings = manager.settings

    # Проверка
    assert settings.company.name == "Ромашка"
    assert settings.company.inn == 380100000000
    assert settings.company.bic == 44525225
    assert settings.company.ownership == "ООО"
    assert settings.boss_name == "Иванов Иван Иванович"
    assert settings.account_name == "Петрова Анна Сергеевна"

"""
<summary>
Загрузка несуществующего файла настроек приводит к исключению operation_exception
</summary>
"""
def test_raise_settings_manager_load_file_not_found():
    # Подготовка
    manager = settings_manager()

    # Действие и проверка
    try:
        manager.load("not_exists.json")
        assert False
    except operation_exception:
        assert True

"""
<summary>
Кэширование: повторная загрузка того же файла не перечитывает его,
а возвращает уже загруженный объект настроек
</summary>
"""
def test_equals_settings_manager_load_cached():
    # Подготовка
    manager = settings_manager()
    manager.load()
    cached = manager.settings

    # Действие
    manager.load()

    # Проверка
    assert manager.settings is cached

"""
<summary>
Кэширование: load(force=True) перечитывает файл и создаёт новый объект настроек
</summary>
"""
def test_not_equals_settings_manager_load_force():
    # Подготовка
    manager = settings_manager()
    manager.load()
    cached = manager.settings

    # Действие
    manager.load(force=True)

    # Проверка
    assert manager.settings is not cached
    assert manager.settings.company.name == cached.company.name

"""
<summary>
В settings.json нет ключей организации (company_*): загрузка не падает, организация остаётся
по умолчанию, остальные ключи загружаются
</summary>
"""
def test_not_raise_settings_manager_load_without_company(tmp_path):
    # Подготовка
    file_name = tmp_path / "settings.json"
    file_name.write_text('{"boss_name": "Иванов Иван Иванович"}', encoding="utf-8")
    manager = settings_manager()

    # Действие
    manager.load(str(file_name))

    # Проверка
    assert manager.is_loaded
    assert manager.settings.company is not None
    assert manager.settings.company.name == ""
    assert manager.settings.boss_name == "Иванов Иван Иванович"

"""
<summary>
В settings.json некорректные данные (ИНН строкой): загрузка не падает,
используются настройки по умолчанию, признак is_loaded = False
</summary>
"""
def test_default_settings_manager_load_invalid_data(tmp_path):
    # Подготовка
    file_name = tmp_path / "settings.json"
    file_name.write_text('{"company_inn": "не число", "boss_name": "Иванов"}', encoding="utf-8")
    manager = settings_manager()

    # Действие
    manager.load(str(file_name))

    # Проверка
    assert not manager.is_loaded
    assert manager.settings is not None
    assert manager.settings.boss_name == ""
    assert manager.settings.first_start
