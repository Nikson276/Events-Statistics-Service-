
# Схема данных хранилища Clickhouse

## Table `Events`

```sql
CREATE TABLE example.events (
    id String,
    user_id String,
    track_id String,
    timestamp DateTime64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (timestamp, id)
PARTITION BY toYYYYMM(timestamp);
```

> Пояснение выбора:
>
> - `String` для ID — гибкость.
> - `DateTime64(3, 'UTC')`— точность до миллисекунд + явная зона.
> - `ORDER BY (timestamp, id)` — оптимизация для временных запросов.
> - `PARTITION BY toYYYYMM` — упрощает удаление старых данных.



- Добавить метку времени вставки 
- 