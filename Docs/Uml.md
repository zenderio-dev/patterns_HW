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

`convert_factory` превращает любой объект в набор словарей по его структуре (например, для JSON). По типу значения поля фабрика выбирает конвертер: простые типы — `basic_convertor`, дата — `datetime_convertor`, ссылки на модели и списки — `reference_convertor`, который вложенные объекты снова отдаёт фабрике.

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
        +convert(source) dict
    }

    class convert_factory {
        +create(value) abstract_convertor
        +convert(source)
    }

    abstract_convertor <|-- basic_convertor : наследует
    abstract_convertor <|-- datetime_convertor : наследует
    abstract_convertor <|-- reference_convertor : наследует
    convert_factory o-- basic_convertor : числа, строки
    convert_factory o-- datetime_convertor : дата
    convert_factory o-- reference_convertor : ссылки, списки
    reference_convertor --> convert_factory : вложенные объекты

    note for convert_factory "простое значение - как есть<br>дата - строка ISO<br>список - список<br>объект - словарь по полям"
```
