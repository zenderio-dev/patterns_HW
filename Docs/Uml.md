# UML-диаграммы проекта

Оба менеджера — singleton: сколько раз ни вызывай конструктор, объект будет один.
И оба кэшируют данные: загрузили один раз — дальше отдают из памяти, пока не попросят `load(force=True)`.
Диаграммы показывают публичные методы, свойства и связи классов.

## settings_manager

Читает `settings.json` и передаёт плоский словарь в `deserializer`. Тот восстанавливает настройки и карточку организации из полей с префиксом `company_`.

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
    settings_manager ..> deserializer : передаёт исходные данные
    settings_manager --> settings_model : хранит настройки
    settings_model --> company_model : организация

    note for settings_manager "load() читает settings.json один раз и кэширует,<br>повторно — только с force=True.<br>convert() пропускает отсутствующие ключи,<br>при битых данных — настройки по умолчанию"
```

## storage_manager

Хранит справочники, техкарты и складские движения. Если включён `first_start`, менеджер создаёт начальные данные [рецепта](Recipe.md) и учебные движения для ОСВ. Репозиторий индексирует объекты по коду и считает входящие ссылки, включая ссылки из строк рецептов и складских движений. `entity_service` использует репозиторий при создании, изменении и удалении моделей. Удаление используемого объекта и смена его кода возвращают HTTP 409.

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
        +repository
        +transactions
        +is_loaded
    }

    class storage_repository {
        +data
        +counts
        +registry(source)
        +registry_range(items)
        +get(code)
        +can_delete(source)
        +delete(source)
        +replace(source, replacement)
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
    storage_manager *-- storage_repository : индекс и счётчики
    storage_manager o-- transaction_model : складские движения
    storage_manager o-- range_model : единицы измерения
    storage_manager o-- group_model : группы
    storage_manager o-- nomenclature_model : номенклатура
    storage_manager o-- storage_model : склады
    storage_manager o-- receipt_model : техкарты
    nomenclature_model --> group_model : входит в группу
    nomenclature_model --> range_model : измеряется в
    range_model --> range_model : базовая единица

    note for storage_manager "При создании вызывает load().<br>Если first_start включён, создаёт справочники,<br>техкарты и движения для ОСВ.<br>При load(force=True) данные и индекс создаются заново."
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
    convert_factory o-- datetime_convertor : date и datetime
    convert_factory o-- reference_convertor : модель, list, tuple, dict
    reference_convertor --> abstract_convert_factory : подбор конвертера для полей

    note for reference_convertor "простое поле, дата - конвертер из фабрики<br>модель, словарь - вложенный словарь<br>список - список<br>модель получает model_type"
```

## Десериализация

`deserializer.load(file_name)` читает JSON-файл, а `deserialize(source, references)`
восстанавливает отдельную модель, словарь коллекций или плоские настройки.
В выгрузках тип каждой модели задан полем `model_type`. При записи через API
объект вида `{"unique_code": "код"}` разрешается по индексу существующих моделей.
Загрузчик рекурсивно восстанавливает вложенные объекты; повторяющийся
`unique_code` возвращает тот же загруженный экземпляр.

При создании `model_factory` загружает модули из `Src/Models` и через рефлексию
находит конкретные доменные классы с методом `from_dict()`. Фабрика выбирает класс
по `model_type` и передает ему подготовленные поля. Модель создает себя через
свои фабричные методы и сеттеры. Брутто и нетто рассчитываются по составу,
значения этих полей из JSON не присваиваются.

Пример [Json/storage.json](Json/storage.json) показывает пять справочников из
`GET /api/json`. Складские движения хранятся в `storage_manager.transactions`.

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
        +deserialize(source, references)
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

## Фильтрация и ОСВ

`entity_service` создаёт прототип из данных хранилища. Вызов `clone(condition)`
возвращает другой прототип с отобранным набором. К нему можно применить следующий
фильтр. API восстанавливает `filter_dto` через общий десериализатор.
Для ОСВ `turnover_service` получает движения из хранилища и через
`filter_prototype` делает две выборки. Сервис считает начальные остатки
и обороты отдельно и объединяет суммы в строки `turnover_row_dto`.

```mermaid
classDiagram
    direction LR

    class abstract_prototype {
        <<abstract>>
        +clone(condition)
    }
    class filter_prototype {
        +data
        +clone(condition)
        +clone_period(start, end, include_end)
    }
    class turnover_service {
        +build(condition)
    }
    class turnover_row_dto {
        +storage_code
        +nomenclature_code
        +range_code
        +opening
        +income
        +expense
        +closing
    }
    class filter_dto {
        +field
        +operation
        +value
        +date_from
        +date_to
    }
    class filter_type_enum {
        <<enumeration>>
        EQUALS
        LIKE
    }
    class transaction_model {
        +nomenclature
        +storage
        +range
        +value
        +date
        +base_unit()
        +base_value()
    }

    abstract_prototype <|-- filter_prototype
    deserializer ..> filter_dto : восстанавливает параметры
    filter_prototype ..> filter_dto : условие отбора
    filter_dto --> filter_type_enum : операция
    entity_service ..> storage_manager : читает данные
    entity_service ..> filter_prototype : фильтрует справочник
    turnover_service ..> storage_manager : получает движения
    turnover_service ..> filter_prototype : отбирает движения по датам
    turnover_service ..> transaction_model : суммирует движения
    turnover_service ..> turnover_row_dto : формирует строки
    transaction_model --> storage_model : склад
    transaction_model --> nomenclature_model : номенклатура
    transaction_model --> range_model : единица измерения
```

### Фильтр справочника

`POST /api/filter/{entity}` принимает `nomenclature`, `group`, `range` или
`receipt` в маршруте и условие в JSON. `field` указывает на `name` или
`unique_code`, в том числе по пути через связанные модели и списки, например
`items.nomenclature.group.name`. `EQUALS` проверяет точное совпадение с учётом
регистра и применяется по умолчанию. `LIKE` ищет подстроку без учёта регистра.
Пустой объект возвращает весь справочник, при отсутствии совпадений API возвращает `[]`.

Запрос `POST /api/filter/range` ниже возвращает килограмм, у которого базовая
единица называется «грамм».

```json
{"field": "base.name", "operation": "EQUALS", "value": "грамм"}
```

### Оборотно-сальдовая ведомость

`POST /api/turnover` принимает тот же фильтр и необязательные границы периода
`date_from` и `date_to`. Движения до начала периода формируют начальный
остаток. Внутри периода границы включены, а движения после окончания
игнорируются. Без начальной даты `opening` равен нулю. Без конечной даты
верхней границы нет.

Строки ведомости сгруппированы по складу и номенклатуре. Количества приведены
к базовой единице. `expense` показывает величину расхода, а
`closing = opening + income - expense`.

```json
{
  "field": "nomenclature.name",
  "operation": "EQUALS",
  "value": "Пшеничная мука",
  "date_from": "2026-01-02",
  "date_to": "2026-01-03"
}
```

На учебных данных этот запрос возвращает начальный остаток 1000 г, приход
2000 г, расход 500 г и конечный остаток 2500 г. Спецификация обоих маршрутов
находится в [openapi.yaml](../openapi.yaml).
