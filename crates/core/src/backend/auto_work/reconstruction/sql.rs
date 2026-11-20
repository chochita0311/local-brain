//! Verbatim bounded reconstruction source queries.
pub(super) const INPUT_TEXT_0: &str = r########"SELECT length({}) FROM {} WHERE {} = ?"########;
pub(super) const INPUT_TEXT_1: &str =
    r########"SELECT substr({},{},?) FROM {} WHERE {} = ?"########;
pub(super) const INPUT_LOAD_SNAPSHOTS_0: &str = r########"SELECT s.id, s.source_id, s.external_id, s.session_class,
                    s.session_role, s.index_policy, s.event_count
                    FROM sessions s JOIN sources ON sources.id = s.source_id WHERE s.id = ?"########;
pub(super) const INPUT_LOAD_SNAPSHOTS_1: &str = r########"SELECT id, session_id, occurred_at, event_type, role
                    FROM activity_events WHERE id = ?"########;
pub(super) const INPUT_LOAD_SNAPSHOTS_2: &str = r########"SELECT d.id, d.imported_at,
                    r.enabled, r.readable, r.status FROM context_documents d
                    JOIN context_roots r ON r.id = d.context_root_id WHERE d.id = ?"########;
pub(super) const INPUT_LOAD_SNAPSHOTS_3: &str = r########"SELECT i.coverage,
                    coalesce(i.source_instance_id, s.source_instance_id) AS source_instance_id, e.enabled,
                    c.applied_at FROM atlassian_items i
                    JOIN external_resource_content c ON c.external_resource_id = i.external_resource_id
                    JOIN atlassian_sites s ON s.id = i.site_id
                    LEFT JOIN external_source_instances e ON e.id = coalesce(i.source_instance_id, s.source_instance_id)
                    WHERE i.external_resource_id = ?"########;
pub(super) const INPUT_LOAD_SNAPSHOTS_4: &str =
    r########"SELECT updated_at, {} AS owner FROM {} WHERE id = ?"########;
pub(super) const INPUT_LOAD_SNAPSHOTS_5: &str = r########"SELECT workstream_id, entity_type, entity_id, linked_by, created_at
                    FROM workstream_links WHERE id = ?"########;
pub(super) const INPUT_REFERENCES_0: &str =
    r########"SELECT status FROM session_reference_scans WHERE session_id = ?"########;
pub(super) const INPUT_REFERENCES_1: &str = r########"SELECT e.id, e.target_key, e.normalized_url,
            d.document_id AS context_document_id, link.external_resource_id,
            CASE WHEN r.kind != 'url' THEN 'context_document'
                 WHEN link.external_resource_id IS NOT NULL THEN 'atlassian_item'
                 ELSE 'url' END AS target_kind,
            e.evidence_kind, e.read_outcome, e.observed_at
            FROM session_reference_evidence e
            JOIN reference_resources r ON r.id=e.resource_id
            LEFT JOIN resource_documents d ON d.resource_id=r.id
            LEFT JOIN (
                SELECT b.resource_id, MIN(b.external_resource_id) AS external_resource_id
                FROM resource_external_links b
                JOIN atlassian_items i ON i.external_resource_id=b.external_resource_id
                GROUP BY b.resource_id HAVING COUNT(*)=1
            ) link ON link.resource_id=r.id
            WHERE e.session_id = ? ORDER BY e.id LIMIT ?"########;
pub(super) const INPUT_CANONICAL_REFERENCE_0: &str = r########"SELECT d.relative_path, r.path, s.id AS source_id FROM context_documents d
            JOIN context_roots r ON r.id = d.context_root_id
            JOIN sources s ON s.id = d.source_id WHERE d.id = ?"########;
pub(super) const INPUT_CANONICAL_REFERENCE_1: &str = r########"SELECT i.service, i.remote_id, i.remote_key, s.normalized_domain
            FROM atlassian_items i JOIN atlassian_sites s ON s.id = i.site_id
            WHERE i.external_resource_id = ?"########;
pub(super) const PREPARATION_PREFIX_0: &str =
    r########"SELECT substr({},1,?) FROM {} WHERE {}=?"########;
pub(super) const PREPARATION_PREPARE_CURRENT_0: &str = r########"SELECT id,source_id,at FROM (
            SELECT s.id,s.source_id,e.occurred_at AS at,
                row_number() OVER (PARTITION BY s.id ORDER BY julianday(e.occurred_at),e.sequence,e.id) AS ordinal
            FROM sessions s JOIN sources ON sources.id=s.source_id
            JOIN activity_events e ON e.session_id=s.id
            WHERE s.session_class='work' AND s.session_role='primary' AND s.index_policy='full'
                AND e.event_type='message' AND e.role IN ('user','assistant')
                AND (julianday(e.occurred_at)<=julianday(?) OR julianday(e.occurred_at) IS NULL)
            ) WHERE ordinal=1"########;
pub(super) const PREPARATION_PREPARE_CURRENT_1: &str = r########"SELECT id,session_id,occurred_at AS at,length(text) AS size
                FROM activity_events WHERE session_id=? AND event_type='message'
                AND role IN ('user','assistant')"########;
pub(super) const PREPARATION_PREPARE_CURRENT_2: &str = r########"SELECT DISTINCT d.id,d.imported_at AS at,length(d.body) AS size
            FROM context_documents d JOIN context_roots r ON r.id=d.context_root_id
            JOIN resource_documents rd ON rd.document_id=d.id
            JOIN session_reference_evidence e ON e.resource_id=rd.resource_id
            WHERE r.enabled=1 AND r.readable=1 AND r.status='ready'
                AND e.session_id IN ({}) AND julianday(e.observed_at)<=julianday(?)"########;
pub(super) const PREPARATION_PREPARE_CURRENT_3: &str = r########"SELECT DISTINCT i.external_resource_id AS id,c.applied_at AS at,
            length(c.normalized_text) AS size FROM atlassian_items i
            JOIN external_resource_content c ON c.external_resource_id=i.external_resource_id
            JOIN atlassian_sites s ON s.id=i.site_id
            LEFT JOIN external_source_instances b ON b.id=coalesce(i.source_instance_id,s.source_instance_id)
            JOIN resource_external_links rl ON rl.external_resource_id=i.external_resource_id
            JOIN session_reference_evidence e ON e.resource_id=rl.resource_id
            WHERE i.coverage='indexed' AND (coalesce(i.source_instance_id,s.source_instance_id) IS NULL OR b.enabled=1)
                AND e.session_id IN ({}) AND julianday(e.observed_at)<=julianday(?)"########;
pub(super) const PREPARATION_PREPARE_CURRENT_4: &str = r########"SELECT id,workstream_id,entity_id AS session_id,created_at AS at
            FROM workstream_links WHERE linked_by='user' AND entity_type='session'
                AND entity_id IN ({})"########;
pub(super) const PREPARATION_PREPARE_CURRENT_5: &str = r########"SELECT id,updated_at AS at,length({}) AS size,{} AS workstream_id FROM {} WHERE {} IN ({})"########;
