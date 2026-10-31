"""Read-only current migration contracts used before backup retirement."""

import sqlite3
from localbrain.persistence.migrations.atlassian import _atlassian_site_access_contract_exists
from localbrain.persistence.migrations.maintenance import _maintenance_workstream_fk_exists
from localbrain.persistence.migrations.resources import (
    _external_resource_url_unique_exists,
    shared_resource_contract_current,
)
from localbrain.persistence.migrations.session_revisions import session_revision_contract_current
from localbrain.persistence.migrations.sessions import _maintenance_session_contract_exists
from localbrain.persistence.migrations.sources import _source_provider_identity_contract_exists
from localbrain.persistence.migrations.usage import (
    USAGE_RECORDS_TABLE,
    _usage_attribution_check_exists,
    _usage_contract_table,
)


def migration_contracts_current(connection: sqlite3.Connection) -> bool:
    usage_table = _usage_contract_table(connection)
    return bool(
        _source_provider_identity_contract_exists(connection)
        and _atlassian_site_access_contract_exists(connection)
        and not _external_resource_url_unique_exists(connection)
        and _maintenance_workstream_fk_exists(connection)
        and _maintenance_session_contract_exists(connection)
        and usage_table == USAGE_RECORDS_TABLE
        and _usage_attribution_check_exists(connection, usage_table)
        and session_revision_contract_current(connection)
        and shared_resource_contract_current(connection)
    )
