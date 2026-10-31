import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool
from localbrain.foundation.config import cache_directory, settings
from localbrain.app.edition import DESKTOP
from localbrain.sources.session_sync import SessionSyncService
from localbrain.sources.context_sync import ContextSyncService
from localbrain.persistence.db import connect, init_db, transaction
from localbrain.ingest.scanner import scan_context_sources, scan_session_sources
from localbrain.sources.registry import load_and_reconcile_session_sources
from localbrain.insights.runs import reconcile_interrupted_insight_runs, shutdown_insight_runs
from localbrain.natural_search.service import SearchService
from localbrain.app.reference_integrations import with_ingestion_observers


@asynccontextmanager
async def lifespan(app: FastAPI):
    from localbrain.app.storage.recovery import backend_storage_lease
    with backend_storage_lease(settings):
        init_db()
        from localbrain.sources.settings import recover_source_reconnect, migrate_source_settings
        recover_source_reconnect(settings)
        migrate_source_settings(settings)
        if app.state.maintain_feature_cache is not None:
            app.state.maintain_feature_cache(cache_directory(settings))
        with transaction() as connection:
            app.state.session_source_registry = load_and_reconcile_session_sources(
                connection, settings
            )
        if not (settings.data_dir / "settings.toml").exists():
            # Upgrading an already configured local installation does not force a setup loop.
            from localbrain.foundation.preferences import read_preferences, save_preferences, PreferencesError
            with connect() as connection:
                has_context = connection.execute("SELECT 1 FROM context_roots WHERE enabled=1 LIMIT 1").fetchone()
            try:
                saved = read_preferences(settings)
                existing = bool(app.state.session_source_registry.settings.entries or has_context)
                # Save the fresh incomplete state too, so a partially configured
                # first run is not mistaken for a legacy install after restart.
                save_preferences({"onboarding_completed": existing}, saved["revision"], settings)
            except PreferencesError:
                pass  # The settings view reports the preserved file error.
        if not DESKTOP:
            if app.state.task_runner is not None:
                app.state.task_runner.reconcile_interrupted_runs()
            reconcile_interrupted_insight_runs()
        app.state.natural_search = SearchService(settings)
        app.state.natural_search.start()
        app.state.session_sync = SessionSyncService(settings, with_ingestion_observers(
            scan_session_sources, app.state.ingestion_observers,
        ))
        app.state.session_sync.start()
        app.state.context_sync = ContextSyncService(settings, with_ingestion_observers(
            scan_context_sources, app.state.ingestion_observers,
        ))
        app.state.context_sync.start()
        from localbrain.models.setup import ModelSetupService
        app.state.model_setup = ModelSetupService(settings, app.state.natural_search)
        from localbrain.google_drive.service import DriveService
        from localbrain.google_drive.policy import DriveError
        try:
            app.state.google_drive = DriveService(settings)
            app.state.google_drive.start()
        except (DriveError, OSError, sqlite3.DatabaseError):
            # Drive state failure must not take unrelated local sources offline.
            app.state.google_drive = None
        app.state.context_search = None
        if app.state.context_search_factory is not None:
            app.state.context_search = app.state.context_search_factory(
                settings, app.state.google_drive.store if app.state.google_drive else None,
            )
        try:
            yield
        finally:
            if app.state.context_search is not None:
                await run_in_threadpool(app.state.context_search.stop)
            if app.state.google_drive is not None:
                await run_in_threadpool(app.state.google_drive.stop)
            await run_in_threadpool(app.state.model_setup.stop)
            await run_in_threadpool(app.state.context_sync.stop)
            await run_in_threadpool(app.state.session_sync.stop)
            await run_in_threadpool(app.state.natural_search.stop)
            if not DESKTOP:
                if app.state.task_runner is not None:
                    await app.state.task_runner.shutdown_runs()
                await shutdown_insight_runs()
