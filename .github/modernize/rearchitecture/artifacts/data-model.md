# Data Model

This documents the existing SQLAlchemy schema as declared in `app/models.py`; it does not propose schema changes.

## Entities

### `Site` — table `sites`

| Field | SQLAlchemy type | Nullability / key | Default / mapping |
|---|---|---|---|
| `id` | Integer (inferred from `Mapped[int]`) | Primary key, non-null | Database-generated primary key |
| `url` | `String(2048)` | Non-null | — |
| `interval_minutes` | `Integer` | Non-null | Python-side default `5` |
| `consecutive_failures` | `Integer` | Non-null | Python-side default `0` |
| `created_at` | `DateTime` | Non-null | Python-side default `utcnow()` |

### `CheckResult` — table `check_results`

| Field | SQLAlchemy type | Nullability / key | Default / mapping |
|---|---|---|---|
| `id` | Integer (inferred from `Mapped[int]`) | Primary key, non-null | Database-generated primary key |
| `site_id` | Integer (inferred from foreign key) | Non-null; foreign key to `sites.id`; indexed | — |
| `status_code` | `Integer` | Nullable | — |
| `response_time_ms` | `Integer` | Nullable | — |
| `success` | `Boolean` | Non-null | — |
| `error` | `String(500)` | Nullable | — |
| `checked_at` | `DateTime` | Non-null | Python-side default `utcnow()` |

## Relationships and persistence behavior

- Each `CheckResult.site_id` references `Site.id`.
- No ORM `relationship()` is declared in the inspected models. The foreign key is declared without an explicit `ondelete` action.
- The models do not declare explicit database column names apart from the table names and `site_id` foreign-key target; SQLAlchemy’s attribute names are used as column names.
- `created_at` and `checked_at` use a timezone-aware UTC Python default, while the declared SQLAlchemy `DateTime` columns do not set `timezone=True`.
- `Base.metadata.create_all(engine)` runs during application startup. No schema migration tool or migration scripts were found in the inspected project files.
- The check operation commits the new `CheckResult` and updated `Site.consecutive_failures` together. Site creation and deletion also call `commit()` in their HTTP handlers.

## Key entities

1. **Site** — a monitored URL, its check interval, creation time, and current consecutive-failure count.
2. **CheckResult** — one persisted outcome per check, including success, HTTP status, elapsed time, optional error, and check time.
