# DeployWatch Architecture Index

## Scope

This is an evidence-based snapshot of the current application, not a migration or redesign plan. No target stack, cleanup requirement, or user-declared migration seam was provided, so `migration_boundary.yaml` and `seams.yaml` are intentionally absent.

## Implementation Guide

This index is not the full contract. Do not implement from this file alone; follow the artifact paths below.

### Global artifacts

- `unit_graph.yaml`
  - Who reads: all implementation workers.
  - Use for: current entry-point boundaries, source anchors, shared references, and the HTTP/scheduler relationship.
  - How to consume: find the assigned unit and follow its source anchors; anchors document current behavior and are not rewrite instructions.
- `wire_contracts.yaml`
  - Who reads: workers touching HTTP routes, monitored URLs, or Discord notifications.
  - Use for: existing methods, paths, response shapes, error behavior, and outbound HTTP behavior.
  - How to consume: filter by the assigned unit or `global`.
- `shared_modules.yaml`
  - Who reads: workers whose unit uses shared application logic.
  - Use for: shared check engine, database access, models, URL validation, and alert behavior.
  - How to consume: filter rows where `used_by_units` includes the assigned unit; use only the listed `used_fields`.
- `cross_unit_state.yaml`
  - Who reads: workers changing database writes or reads shared between HTTP handlers and scheduled checks.
  - Use for: persisted site and check-result flows between units.
  - How to consume: filter flows where `writer.unit` or `reader.unit` matches the assigned unit.
- `project-structure.md`
  - Who reads: all workers.
  - Use for: application layout, layers, entry points, functional areas, and source counts.
- `tech-stack.md`
  - Who reads: all workers.
  - Use for: declared runtimes, framework, dependencies, and configuration sources.
- `data-model.md`
  - Who reads: workers changing persistence or rendering persisted values.
  - Use for: current SQLAlchemy entities, columns, foreign key, and transaction notes.

### Unit: `http-dashboard-site-management`

- External trigger: HTTP requests to `/health`, `/`, `/sites`, `/sites/{site_id}/check`, `/sites/{site_id}`, and `/sites/{site_id}/delete`; browser requests to `/static/*`.
- Must read:
  - `units/http-dashboard-site-management/behavior.yaml` — route behavior, branches, error outcomes, and database commit scope.
  - `units/http-dashboard-site-management/bindings.yaml` — FastAPI route/static bindings and database configuration.
  - `units/http-dashboard-site-management/unit_decomposition.yaml` — advisory split candidates only; `commit: false`.
- Relevant global rows:
  - `wire_contracts.yaml` rows where `unit` is `http-dashboard-site-management` or `global`.
  - `shared_modules.yaml` rows where `used_by_units` includes `http-dashboard-site-management`.
  - `cross_unit_state.yaml` flows where `writer.unit` or `reader.unit` is `http-dashboard-site-management`.
- Before DONE report: artifact paths read, implemented `must_preserve` items, unresolved/deferred contracts, and test/build/runtime evidence.

### Unit: `scheduled-site-checks`

- External trigger: APScheduler interval job, started during application lifespan; nominal tick every 60 seconds.
- Must read:
  - `units/scheduled-site-checks/behavior.yaml` — due-check criteria, persistence, alert threshold, and scheduler error handling.
  - `units/scheduled-site-checks/bindings.yaml` — scheduler registration, startup/shutdown wiring, and database/alert configuration.
  - `units/scheduled-site-checks/unit_decomposition.yaml` — advisory split candidates only; `commit: false`.
- Relevant global rows:
  - `wire_contracts.yaml` rows where `unit` is `scheduled-site-checks` or `global`.
  - `shared_modules.yaml` rows where `used_by_units` includes `scheduled-site-checks`.
  - `cross_unit_state.yaml` flows where `writer.unit` or `reader.unit` is `scheduled-site-checks`.
- Before DONE report: artifact paths read, implemented `must_preserve` items, unresolved/deferred contracts, and test/build/runtime evidence.

## Analysis Notes

- The HTTP routes are grouped into one unit because they are declared in the single `app/main.py` module; the scheduled worker has its own entry point in `app/scheduler.py`.
- There are no user-declared migration cut points. No seam contract is asserted.
- This snapshot does not assess tests, deployment readiness, or security beyond documenting existing contracts.
