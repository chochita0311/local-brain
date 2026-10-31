"""Database initialization order, preflight backups and commit boundary."""

import sqlite3
from localbrain.persistence.migrations.atlassian import (
    _atlassian_site_access_contract_exists,
    _ensure_atlassian_site_access_backup,
    _repair_atlassian_site_access_contract,
    _validate_preexisting_structure_reference_contract,
    _validate_structure_reference_contract,
)
from localbrain.persistence.migrations.compatible import _run_compatible_migrations
from localbrain.persistence.migrations.maintenance import (
    _ensure_maintenance_workstream_fk_backup,
    _maintenance_workstream_fk_exists,
)
from localbrain.persistence.migrations.resources import (
    _ensure_external_resource_url_scope_backup,
    _external_resource_url_unique_exists,
    ensure_shared_resource_backup,
    migrate_shared_resources,
    shared_resource_migration_required,
)
from localbrain.persistence.migrations.session_revisions import prepare_session_revision_migration
from localbrain.persistence.migrations.sessions import (
    _ensure_maintenance_session_contract_backup,
    _maintenance_session_contract_exists,
    _migrate_skill_observation_contract,
)
from localbrain.persistence.migrations.sources import (
    _ensure_source_provider_identity_backup,
    _repair_source_provider_identity_contract,
    _source_provider_identity_contract_exists,
)
from localbrain.persistence.migrations.support import SCHEMA_PATH, _table_sql
from localbrain.persistence.migrations.usage import (
    _ensure_usage_attribution_backup,
    _migrate_legacy_usage_table_name,
    _usage_attribution_check_exists,
    _usage_contract_table,
)
from localbrain.persistence.storage import maintain_migration_backups


def initialize_database(connection: sqlite3.Connection, config) -> None:
    with connection:
        if shared_resource_migration_required(connection):
            ensure_shared_resource_backup(connection, config.database_path)
        prepare_session_revision_migration(connection, config.database_path)
        _validate_preexisting_structure_reference_contract(connection)
        source_provider_identity_needs_repair = bool(
            _table_sql(connection, "sources")
            and not _source_provider_identity_contract_exists(connection)
        )
        if source_provider_identity_needs_repair:
            _ensure_source_provider_identity_backup(
                connection, config.database_path
            )
        atlassian_site_access_needs_repair = bool(
            _table_sql(connection, "atlassian_sites")
            and not _atlassian_site_access_contract_exists(connection)
        )
        if atlassian_site_access_needs_repair:
            _ensure_atlassian_site_access_backup(
                connection, config.database_path
            )
        external_resource_url_scope_needs_repair = bool(
            _table_sql(connection, "external_resources")
            and _external_resource_url_unique_exists(connection)
        )
        if external_resource_url_scope_needs_repair:
            _ensure_external_resource_url_scope_backup(
                connection, config.database_path
            )
        usage_contract_table = _usage_contract_table(connection)
        usage_contract_exists = usage_contract_table is not None
        maintenance_workstream_fk_needs_repair = bool(
            _table_sql(connection, "maintenance_runs")
            and not _maintenance_workstream_fk_exists(connection)
        )
        if maintenance_workstream_fk_needs_repair:
            _ensure_maintenance_workstream_fk_backup(
                connection, config.database_path
            )
        session_contract_needs_repair = bool(
            _table_sql(connection, "sessions")
            and not _maintenance_session_contract_exists(connection)
        )
        if session_contract_needs_repair:
            _ensure_maintenance_session_contract_backup(
                connection, config.database_path
            )
        if usage_contract_exists and not _usage_attribution_check_exists(
            connection, usage_contract_table
        ):
            _ensure_usage_attribution_backup(connection, config.database_path)
        _migrate_legacy_usage_table_name(connection)
        _repair_source_provider_identity_contract(connection, config)
        _migrate_skill_observation_contract(connection)
        migrate_shared_resources(connection)
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _validate_structure_reference_contract(connection)
        if atlassian_site_access_needs_repair:
            _repair_atlassian_site_access_contract(connection)
        _run_compatible_migrations(connection, config=config)
        from localbrain.usage.records import (
            ensure_default_price_snapshot,
            ensure_official_price_snapshots,
            price_existing_partial_fast_long_context_records,
            price_existing_unpriced_spark_records,
            price_existing_unpriced_sol_6_1_records,
        )

        ensure_default_price_snapshot(connection)
        ensure_official_price_snapshots(connection)
        price_existing_unpriced_spark_records(connection)
        price_existing_unpriced_sol_6_1_records(connection)
        price_existing_partial_fast_long_context_records(connection)
        if not usage_contract_exists:
            connection.execute(
                """
                UPDATE source_files
                SET status = 'stale'
                WHERE source_id IN (
                    SELECT id FROM sources
                    WHERE provider_kind IN ('claude', 'codex')
                )
                """
            )
    # The transaction committed successfully. Failed initialization keeps recovery
    # copies; ordinary starts do not accumulate indefinite versioned backups.
    try:
        maintain_migration_backups(config.database_path, connection)
    finally:
        connection.close()
