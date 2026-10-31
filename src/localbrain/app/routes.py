"""Explicit feature handler registration; preserve route order and public URLs."""
from fastapi.responses import HTMLResponse
import localbrain.app.web as app_web
import localbrain.usage.web as usage_web
import localbrain.insights.web as insights_web
import localbrain.sessions.web as sessions_web
import localbrain.local_context.web as local_context_web
import localbrain.sources.web as sources_web
import localbrain.persistence.web as persistence_web
import localbrain.resources.web as resources_web
import localbrain.natural_search.web as natural_search_web


def install_routes(app):
    selected = app.state.feature_packages
    if 'auto_work' in selected:
        import localbrain.auto_work.web as auto_work_web
    if 'workstreams' in selected:
        import localbrain.workstreams.web as workstreams_web
    if selected & {"atlassian", "workstreams"}:
        import localbrain.maintenance.web as maintenance_web
    if 'atlassian' in selected:
        import localbrain.atlassian.web as atlassian_web
    if 'workflow' in selected:
        import localbrain.workflow.web as workflow_web
    if 'workstreams' in selected:
        import localbrain.workstreams.resource_web as workstream_resources_web
    if 'atlassian' in selected:
        import localbrain.search.web as search_web
    if 'auto_work' in selected:
        app.get('/auto-work', response_class=HTMLResponse)(auto_work_web.auto_work_page)
        app.post('/auto-work/refresh')(auto_work_web.auto_work_refresh)
    app.get('/', response_class=HTMLResponse)(app_web.dashboard)
    app.get('/sessions-dashboard', response_class=HTMLResponse)(usage_web.sessions_dashboard)
    app.get('/sessions-dashboard/insights', response_class=HTMLResponse)(insights_web.session_insights)
    app.post('/sessions-dashboard/insights/runs', response_class=HTMLResponse)(insights_web.create_insight_run)
    app.post('/sessions-dashboard/insights/runs/{run_id}/cancel')(insights_web.stop_insight_run)
    app.get('/sessions-dashboard/insights/runs/{run_id}/download')(insights_web.download_insight_report)
    app.get('/api/insight-runs/{run_id}')(insights_web.insight_run_status)
    if 'workstreams' in selected:
        app.get('/workstreams', response_class=HTMLResponse)(workstreams_web.workstreams_page)
        app.get('/workstreams/{workstream_id}', response_class=HTMLResponse)(workstreams_web.show_workstream)
    if selected & {"atlassian", "workstreams"}:
        app.get('/runs/{run_id}', response_class=HTMLResponse)(maintenance_web.show_run)
    app.get('/sessions', response_class=HTMLResponse)(sessions_web.sessions_page)
    app.put('/sessions/chart/project-visibility')(sessions_web.save_chart_project_visibility)
    app.get('/context', response_class=HTMLResponse)(local_context_web.context_page)
    if 'atlassian' in selected:
        app.get('/atlassian', response_class=HTMLResponse)(atlassian_web.atlassian_page)
        app.post('/atlassian/sync')(atlassian_web.atlassian_sync)
        app.get('/atlassian/add', response_class=HTMLResponse)(atlassian_web.atlassian_add_page)
        app.get('/atlassian/connections', response_class=HTMLResponse)(atlassian_web.atlassian_connections_page)
        app.post('/atlassian/register', response_class=HTMLResponse)(atlassian_web.atlassian_register)
        app.post('/atlassian/access', response_class=HTMLResponse)(atlassian_web.atlassian_register_access)
        app.get('/api/atlassian/registration-preview')(atlassian_web.atlassian_registration_preview)
        app.post('/atlassian/connections/{source_instance_id}/sites/{site_id}', response_class=HTMLResponse)(atlassian_web.atlassian_update_connection)
        app.post('/atlassian/spaces/discover', response_class=HTMLResponse)(atlassian_web.atlassian_discover_spaces)
        app.post('/atlassian/spaces/register', response_class=HTMLResponse)(atlassian_web.atlassian_register_space_candidate)
        app.get('/atlassian/items/{item_id}', response_class=HTMLResponse)(atlassian_web.atlassian_item_page)
        app.get('/atlassian/references/{reference_id}', response_class=HTMLResponse)(atlassian_web.atlassian_reference_page)
        app.post('/atlassian/items/{item_id}/local', response_class=HTMLResponse)(atlassian_web.atlassian_update_local)
    if {"atlassian", "workstreams"} <= selected:
        app.post('/atlassian/items/{item_id}/links', response_class=HTMLResponse)(atlassian_web.atlassian_add_local_link)
        app.post('/atlassian/items/{item_id}/links/{scope_type}/{scope_id}/{link_id}', response_class=HTMLResponse)(atlassian_web.atlassian_remove_local_link)
    if 'atlassian' in selected:
        app.get('/atlassian/refresh', response_class=HTMLResponse)(atlassian_web.atlassian_refresh_page)
        app.post('/atlassian/refresh', response_class=HTMLResponse)(atlassian_web.atlassian_start_refresh)
    app.get('/projects', response_class=HTMLResponse)(sessions_web.projects_page)
    app.post('/sessions/sync')(sources_web.sync_sessions_page)
    app.post('/sessions/{session_id}/pin')(sessions_web.pin_session_page)
    app.post('/sessions/{session_id}/unpin')(sessions_web.unpin_session_page)
    app.get('/sources', response_class=HTMLResponse)(sources_web.sources_page)
    app.post('/sources/scan')(sources_web.scan_sources_page)
    app.get('/schema', response_class=HTMLResponse)(persistence_web.schema_page)
    app.get('/sessions/{session_id}/chart-activity')(sessions_web.show_session_chart_activity)
    app.get('/sessions/{session_id}', response_class=HTMLResponse)(sessions_web.show_session)
    if 'workflow' in selected:
        app.get('/sessions/{session_id}/workflow', response_class=HTMLResponse)(workflow_web.show_session_workflow)
        app.post('/sessions/{session_id}/workflow/corrections')(workflow_web.correct_session_workflow)
    app.get('/sessions/{session_id}/subsessions/{file_name}', response_class=HTMLResponse)(sessions_web.show_subsession)
    app.get('/sessions/{session_id}/subagents/{file_name}', include_in_schema=False)(sessions_web.redirect_legacy_subagent_route)
    app.get('/documents/{document_id}', response_class=HTMLResponse)(local_context_web.show_document)
    app.get('/local-resources/{resource_id}', response_class=HTMLResponse)(resources_web.show_local_resource)
    app.get('/natural-search', response_class=HTMLResponse)(natural_search_web.natural_search_page)
    app.get('/api/natural-search/status')(natural_search_web.natural_search_status)
    app.post('/natural-search/prepare')(natural_search_web.natural_search_prepare)
    app.post('/natural-search/cancel')(natural_search_web.natural_search_cancel)
    app.get('/natural-search/evidence/{rowid}', response_class=HTMLResponse)(natural_search_web.natural_search_evidence)
    if 'atlassian' in selected:
        app.get('/search', response_class=HTMLResponse, deprecated=True)(search_web.search_page)
    if 'workstreams' in selected:
        app.post('/api/workstreams')(workstreams_web.api_create_workstream)
    app.post('/api/context-roots')(local_context_web.api_add_context_root)
    app.post('/api/context-files')(local_context_web.api_add_context_file)
    app.post('/api/context-sources/apple-notes')(local_context_web.api_add_apple_notes_source)
    app.post('/api/context-sources/order')(local_context_web.api_reorder_context_sources)
    app.delete('/api/context-roots/{root_id}')(local_context_web.api_remove_context_root)
    app.delete('/api/context-sources/{source_id}')(local_context_web.api_remove_context_source)
    if 'workstreams' in selected:
        app.put('/api/workstreams/{workstream_id}')(workstreams_web.api_update_workstream)
        app.post('/api/workstreams/{workstream_id}/threads')(workstreams_web.api_create_thread)
        app.put('/api/threads/{thread_id}')(workstreams_web.api_update_thread)
        app.post('/api/workstreams/{workstream_id}/checkpoints')(workstreams_web.api_create_checkpoint)
        app.post('/api/links')(workstreams_web.api_add_link)
        app.delete('/api/links/{scope_type}/{scope_id}/{link_id}')(workstreams_web.api_remove_link)
        app.post('/api/external-resources')(workstream_resources_web.api_create_external_resource)
        app.post('/api/local-resources')(workstream_resources_web.api_create_local_resource)
        app.post('/api/workstreams/{workstream_id}/suggestions')(workstreams_web.api_generate_suggestions)
        app.post('/api/suggestions/{suggestion_id}/{action}')(workstreams_web.api_resolve_suggestion)
        app.post('/api/workstreams/{workstream_id}/runs')(workstreams_web.api_start_task_run)
    if selected & {"atlassian", "workstreams"}:
        app.get('/api/runs/{run_id}')(maintenance_web.api_run_status)
        app.post('/api/runs/{run_id}/cancel')(maintenance_web.api_cancel_run)
    app.post('/api/scan')(sources_web.scan_sources)
    app.post('/api/sessions/sync')(sources_web.sync_session_sources)
    app.get('/api/sessions/sync/status')(sources_web.session_sync_status)
    app.post('/api/sessions/sync/stream')(sources_web.stream_session_sources)
    app.get('/api/health')(app_web.health)
