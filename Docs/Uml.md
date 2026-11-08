# UML-диаграммы менеджеров

Оба менеджера — singleton: сколько раз ни вызывай конструктор, объект будет один.
И оба кэшируют данные: загрузили один раз — дальше отдают из памяти, пока не попросят `load(force=True)`.
На диаграммах показано только то, чем менеджеры пользуются снаружи — без приватных полей.

## settings_manager

Читает `settings.json` и собирает из него настройки с организацией внутри.

```mermaid
classDiagram
    direction LR

    class abstract_manager {
        <<abstract>>
        +load(file_name, force)
        +convert()
    }

    class settings_manager {
        <<singleton>>
        +load(file_name, force)
        +convert()
        +settings
        +is_loaded
    }

    class settings_model {
        +company
        +boss_name
        +account_name
        +first_start
        +response_format
    }

    class company_model {
        +name
        +inn
        +bic
        +corr_account
        +account
        +ownership
    }

    abstract_manager <|-- settings_manager : наследует
    settings_manager --> settings_model : хранит настройки
    settings_model --> company_model : организация

    note for settings_manager "load() читает settings.json один раз и кэширует,<br>повторно — только с force=True.<br>convert() пропускает отсутствующие ключи,<br>при битых данных — настройки по умолчанию"
```

## storage_manager

Хранит справочники и техкарты. Если в настройках включён `first_start`, при первом обращении сам заполняется данными [рецепта](Recipe.md) — через фабричные методы моделей.

```mermaid
classDiagram
    direction LR

    class abstract_manager {
        <<abstract>>
        +load(file_name, force)
        +convert()
    }

    class storage_manager {
        <<singleton>>
        +load(force)
        +convert()
        +get(key)
        +find(key, unique_code)
        +keys()
        +data
        +is_loaded
    }

    class range_model {
        +name
        +value
        +base
        +create_gram()$
        +create_kilogram(base)$
        +create_piece()$
    }

    class group_model {
        +name
        +create(name)$
    }

    class nomenclature_model {
        +name
        +group
        +range
        +create(name, group, range)$
    }

    class storage_model {
        +name
        +address
        +create(name, address)$
    }

    class settings_manager {
        <<singleton>>
        +settings
    }

    abstract_manager <|-- storage_manager : наследует
    storage_manager ..> settings_manager : проверяет first_start
    storage_manager o-- range_model : единицы измерения
    storage_manager o-- group_model : группы
    storage_manager o-- nomenclature_model : номенклатура
    storage_manager o-- storage_model : склады
    storage_manager o-- receipt_model : техкарты
    nomenclature_model --> group_model : входит в группу
    nomenclature_model --> range_model : измеряется в
    range_model --> range_model : базовая единица

    note for storage_manager "При создании сам вызывает load().<br>Если first_start — фабриками создаёт грамм, кг, штуку,<br>группы «Сырьё» и «Упаковка», склад, номенклатуру<br>и техкарты «Творожное тесто» и «Сырники»,<br>иначе справочники пустые.<br>Дальше данные берутся из кэша"
    note for range_model "кг: value = 1000, base = грамм<br>грамм и штука: value = 1, base нет"
```

## Технологическая карта

Рецепт — это `receipt_model` (корень агрегата): строки меняются только через `add_item()` / `remove_item()`. Строка содержит ингредиент **или** другую техкарту (полуфабрикат, «блюдо в блюде»), поэтому брутто и нетто считаются **рекурсивно** через все уровни вложенности. Вложить карту саму в себя нельзя.

```mermaid
classDiagram
    direction LR

    class receipt_model {
        +name
        +portions
        +cooking_time
        +items
        +steps
        +brutto
        +netto
        +add_item(item)
        +remove_item(component)
        +add_step(step)
        +contains(receipt)
        +create(name, portions, cooking_time)$
    }

    class receipt_item_model {
        +nomenclature
        +receipt
        +component
        +range
        +quantity
        +unit_weight
        +waste
        +brutto
        +netto
        +create(nomenclature, range, quantity, unit_weight, waste)$
        +create_from_receipt(receipt, quantity)$
    }

    class nomenclature_model {
        +name
        +group
        +range
    }

    class range_model {
        +name
        +value
        +base
    }

    receipt_model *-- receipt_item_model : строки
    receipt_item_model --> nomenclature_model : ингредиент или упаковка
    receipt_item_model --> receipt_model : полуфабрикат (вложенная карта)
    receipt_item_model --> range_model : единица количества

    note for receipt_model "брутто = сумма брутто строк<br>нетто = сумма нетто строк<br>(рекурсивно через вложенные карты)"
    note for receipt_item_model "ингредиент: брутто = quantity × unit_weight, г<br>нетто = брутто × (100 − waste) / 100<br>полуфабрикат: брутто = quantity × receipt.brutto<br>нетто = quantity × receipt.netto"
```

## Конвертеры

Фабрика только подбирает конвертер по типу значения (по таблице "тип - конвертер", с учетом наследования): простые типы - `basic_convertor`, дата - `datetime_convertor`, модели, списки и словари - `reference_convertor`. `reference_convertor` формирует словарь по всем полям объекта: для каждого поля просит конвертер у фабрики, а ссылки разворачивает рекурсивно. Каждая доменная модель получает метку `model_type` с именем класса; словари коллекций такую метку не получают.

```mermaid
classDiagram
    direction LR

    class abstract_convertor {
        <<abstract>>
        +convert(source) dict
    }

    class basic_convertor {
        +convert(source) dict
    }

    class datetime_convertor {
        +convert(source) dict
    }

    class reference_convertor {
        +factory
        +convert(source) dict
    }

    class abstract_convert_factory {
        <<abstract>>
        +create(value) abstract_convertor
    }

    class convert_factory {
        +create(value) abstract_convertor
    }

    abstract_convertor <|-- basic_convertor : наследует
    abstract_convertor <|-- datetime_convertor : наследует
    abstract_convertor <|-- reference_convertor : наследует
    abstract_convert_factory <|-- convert_factory : наследует
    convert_factory o-- basic_convertor : int, float, str, None
    convert_factory o-- datetime_convertor : datetime
    convert_factory o-- reference_convertor : модель, list, tuple, dict
    reference_convertor --> abstract_convert_factory : подбор конвертера для полей

    note for reference_convertor "простое поле, дата - конвертер из фабрики<br>модель, словарь - вложенный словарь<br>список - список<br>модель получает model_type"
```

## Десериализация

`deserializer.load(file_name)` читает JSON-файл, а `deserialize(source)`
восстанавливает отдельную модель или словарь коллекций. Каждый объект содержит
`model_type`, поэтому его тип не зависит от названия коллекции или поля.
Загрузчик рекурсивно восстанавливает вложенные объекты; повторяющийся
`unique_code` возвращает тот же загруженный экземпляр.

При создании `model_factory` загружает модули из `Src/Models` и через рефлексию
находит конкретные доменные классы с методом `from_dict()`. Фабрика выбирает класс
по `model_type` и передает ему подготовленные поля. Модель создает себя через
свои фабричные методы и сеттеры. Брутто и нетто рассчитываются по составу,
значения этих полей из JSON не присваиваются.

Пример выгрузки: [Json/storage.json](Json/storage.json). Его можно получить
через `GET /api/json`; старые выгрузки без `model_type` нужно сформировать заново.

```mermaid
classDiagram
    direction LR

    class abstract_model_factory {
        <<abstract>>
        +create(model_type, source) abstract_model
    }

    class model_factory {
        +create(model_type, source) abstract_model
    }

    class deserializer {
        +factory
        +load(file_name)
        +deserialize(source)
    }

    class abstract_model {
        +unique_code
    }

    class entity_model {
        +name
    }

    class receipt_model {
        +from_dict(source)$
        +add_item(item)
        +add_step(step)
        +brutto
        +netto
    }

    class receipt_item_model {
        +from_dict(source)$
        +brutto
        +netto
    }

    abstract_model_factory <|-- model_factory : наследует
    deserializer --> abstract_model_factory : создание моделей
    abstract_model <|-- entity_model : наследует
    entity_model <|-- receipt_model : наследует
    abstract_model <|-- receipt_item_model : наследует
    model_factory ..> receipt_model : вызывает from_dict
    model_factory ..> receipt_item_model : вызывает from_dict
    receipt_model *-- receipt_item_model : строки

    note for deserializer "вложенные объекты - рекурсивно<br>общие коды - общие ссылки<br>неизвестные типы и противоречащие данные - ошибка"
    note for model_factory "загружает модули Src/Models<br>находит классы с from_dict через рефлексию<br>выбирает класс по model_type"
    note for receipt_model "модели восстанавливаются через from_dict<br>поля проверяются самой моделью"
```
