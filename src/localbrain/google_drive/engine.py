"""Two directional mirrors with per-item checkpoints and explicit source authority."""

import hashlib
import os
import shutil
import stat
import tempfile
import threading
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import ExitStack
from itertools import groupby
from pathlib import Path

from .policy import (DriveError, FOLDER, MAX_FILE_BYTES, PUBLISH_WORKERS, local_inventory,
                     local_path, name_key, private_dir, safe_name, stamp)


def content_hash(path):
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def remote_inventory(api, folder):
    entries, seen, pending = {}, {folder}, [(folder, "")]
    while pending:
        parent, prefix = pending.pop()
        names = set()
        for item in api.children(parent):
            name = safe_name(item["name"])
            if name_key(name) in names or item["id"] in seen:
                raise DriveError("duplicate_path", "원격 폴더의 중복 이름·경로를 안전하게 동기화할 수 없습니다.")
            names.add(name_key(name))
            seen.add(item["id"])
            relative = prefix + name
            entries[item["id"]] = {**item, "path": relative, "kind": "folder" if item["mimeType"] == FOLDER else "file"}
            if item["mimeType"] == FOLDER:
                if item.get("capabilities", {}).get("canListChildren") is False:
                    raise DriveError("partial_listing", "읽을 수 없는 하위 폴더가 있어 기존 사본을 보존합니다.")
                pending.append((item["id"], relative + "/"))
    return entries


class Engine:
    def __init__(self, store, data_dir):
        self.store, self.data_dir = store, data_dir
        self.stage = private_dir(store.root / "staging")
        # Immutable snapshots have no durable authority; checkpoints/session URLs do.
        # Remove only known snapshots left by a previous interrupted backend.
        for file in self.stage.glob("snapshot-*"):
            if file.is_file() and not file.is_symlink():
                file.unlink()
        pending = store.get("download-staging", [])
        copies = data_dir / "external-sources" / "google-drive"
        for name in pending:
            file = Path(name)
            if file.is_relative_to(copies) and file.name.startswith(".localbrain-drive-"):
                try:
                    checked = local_path(copies, str(file.relative_to(copies)))
                    if not checked.exists() or (checked.is_file() and checked.stat().st_nlink == 1 and checked.stat().st_uid == os.getuid()):
                        checked.unlink(missing_ok=True)
                except DriveError:
                    pass  # A replaced path is no longer an owned cleanup target.
        store.put("download-staging", [])
        self.recover_commit()

    def recover_commit(self):
        """Recover a crash between atomic file replacement and its SQLite checkpoint."""
        pending = self.store.get("receive-commit")
        if not pending:
            return
        root = self.data_dir / "external-sources" / "google-drive" / pending["connection_id"] / pending["publisher_id"]
        target = local_path(root, pending["record"]["path"])
        if target.is_file() and target.stat().st_size <= MAX_FILE_BYTES and content_hash(target) == pending["record"]["hash"]:
            manifest = self.store.manifest(pending["connection_id"], pending["job"])
            manifest[pending["file_id"]] = pending["record"]
            self.store.checkpoint(pending["connection_id"], pending["job"], manifest)
        self.store.put("receive-commit", None)

    def snapshot(self, entry, *, stage=True):
        """Hash a stable bounded source, staging bytes only when needed for upload."""
        path = Path(entry["local"])
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise DriveError("local_changed", "로컬 경로가 링크로 바뀌었습니다. 기존 사본을 보존합니다.")
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        destination = None
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or tuple(entry["stamp"]) != stamp(info):
                raise DriveError("source_changed", "전송 전에 로컬 원본이 바뀌었습니다. 다시 비교해 주세요.", True)
            if info.st_size > MAX_FILE_BYTES:
                raise DriveError("too_large", "앱의 파일당 100MB 제한을 초과합니다.")
            digest, total = hashlib.md5(), 0
            with ExitStack() as resources:
                source = resources.enter_context(os.fdopen(fd, "rb", closefd=False))
                output = None
                if stage:
                    out, name = tempfile.mkstemp(prefix="snapshot-", dir=self.stage)
                    destination = Path(name)
                    output = resources.enter_context(os.fdopen(out, "wb"))
                while True:
                    chunk = source.read(min(1024 * 1024, MAX_FILE_BYTES - total + 1))
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_FILE_BYTES:
                        raise DriveError("too_large", "읽는 중 파일당 100MB 제한을 초과했습니다.")
                    digest.update(chunk)
                    if output is not None:
                        output.write(chunk)
            if stamp(os.fstat(fd)) != tuple(entry["stamp"]) or stamp(path.lstat()) != tuple(entry["stamp"]):
                raise DriveError("source_changed", "읽는 중 로컬 원본이 바뀌었습니다. 기존 사본을 보존합니다.", True)
            return destination, digest.hexdigest()
        except BaseException:
            if destination:
                destination.unlink(missing_ok=True)
            raise
        finally:
            os.close(fd)

    def publish(self, connection, sources, api, progress=lambda **values: None):
        progress(stage="scanning", processed=0, total=None, current="", current_bytes=0, file_bytes=0)
        inventory, errors = local_inventory(sources, api.cancel)
        progress(stage="preparing", total=len(inventory), transferred=0, changed=0, excluded=len(errors))
        manifest = self.store.manifest(connection["id"], "upload")
        root = api.get(connection["root_id"])
        if root.get("trashed") or root.get("mimeType") != FOLDER:
            raise DriveError("root", "공유 루트 폴더를 확인할 수 없습니다. 기존 사본을 보존합니다.")
        if not connection.get("target_id"):
            # Look up only this exact configured child name; same-publisher collision is out of scope.
            targets = [c for c in api.children(root["id"]) if c["name"] == connection["target"]]
            if len(targets) > 1 or any(t["mimeType"] != FOLDER for t in targets):
                raise DriveError("duplicate_path", "내 대상 폴더 이름이 겹칩니다. 이름을 확인해 주세요.")
            connection["target_id"] = targets[0]["id"] if targets else api.new_id()
            connection["target_pending"] = not bool(targets)
            self.store.update_connection(connection)
        if connection.get("target_pending"):
            api.create_folder(connection["target_id"], connection["target"], root["id"])
            connection["target_pending"] = False
            self.store.update_connection(connection)
        target = api.get(connection["target_id"])
        if root["id"] not in target.get("parents", []) or target.get("trashed"):
            raise DriveError("target_changed", "내 대상 폴더의 위치·휴지통 상태를 확인해 주세요.")
        selected_ids = {str(source["id"]) for source in sources}
        known_ids = [entry["remote_id"] for entry in manifest.values()
                     if entry.get("source_id") in selected_ids and entry.get("remote_id")]
        if known_ids:
            progress(stage="remote", current="", remote_checked=0, remote_total=len(set(known_ids)))
            api.prefetch(known_ids, progress=lambda checked, total: progress(remote_checked=checked, remote_total=total))
        identities = Counter((item.get("source_id"), item.get("identity")) for item in inventory.values())
        prior = {}
        for key, item in manifest.items():
            prior.setdefault((item.get("source_id"), item.get("identity")), []).append(key)
        used, changed, copied, processed, active = set(), 0, 0, 0, 0
        verified_parents, failed_parents = set(), set()
        lock = threading.RLock()
        listing_lock = threading.Lock()
        parents, listings = {target["id"]: target}, {}
        ordered = sorted(inventory.items(), key=lambda pair: (pair[1]["path"].count("/"), pair[1]["kind"] != "folder", pair[1]["path"]))

        def can_rebuild(file_id, name, parent):
            # A 404 alone is not deletion evidence. Only add a new managed copy;
            # never remove the inaccessible old object or overwrite a name conflict.
            capabilities = parents[parent].get("capabilities", {})
            if capabilities.get("canListChildren") is not True or capabilities.get("canAddChildren") is not True:
                return False
            with listing_lock:
                if parent not in listings:
                    listings[parent] = api.children(parent)
                return not any(child["id"] == file_id or name_key(child["name"]) == name_key(name)
                               for child in listings[parent])

        def sync_item(pair):
            nonlocal changed, copied, processed, active
            key, item = pair
            api.check()
            with lock:
                active += 1
                progress(stage="syncing", processed=processed, current=item["path"], current_bytes=0,
                         uploading=False, active_items=active,
                         file_bytes=item["size"] if item["kind"] == "file" else 0,
                         transferred=copied, changed=changed, excluded=len(errors))
            old_key, record, replacement = None, {}, None

            def save_record():
                with lock:
                    # Other workers checkpoint copies, never this mutable upload state.
                    if manifest.get(key) != record:
                        manifest[key] = dict(record)
                    if manifest.dirty:
                        self.store.checkpoint(connection["id"], "upload", manifest, key)

            def received(sent, size):
                with lock:
                    progress(current=item["path"], uploading=True, current_bytes=sent, file_bytes=size,
                             active_items=active)

            try:
                with lock:
                    if item["error"]:
                        candidates = prior.get((item["source_id"], item["identity"]), [])
                        if key not in manifest and len(candidates) == 1 and identities[(item["source_id"], item["identity"])] == 1:
                            manifest[key] = {**manifest.pop(candidates[0]), "path": item["path"]}
                            self.store.checkpoint(connection["id"], "upload", manifest, key)
                        used.add(key)
                        return
                    old_key = key if key in manifest else None
                    if old_key is None:
                        candidates = prior.get((item["source_id"], item["identity"]), [])
                        if len(candidates) == 1 and identities[(item["source_id"], item["identity"])] == 1 and candidates[0] not in used:
                            old_key = candidates[0]
                    old = dict(manifest.get(old_key, {}))
                    if old_key:
                        used.add(old_key)  # Preserve the prior copy if preparation fails.
                    parent_path = item["path"].rpartition("/")[0]
                    parent_key = item["source_id"] + ":" + parent_path
                    parent = connection["target_id"] if not parent_path else manifest[parent_key]["remote_id"]
                    if parent_path and parent_key not in verified_parents:
                        raise DriveError("parent_incomplete", "상위 폴더의 동기화를 먼저 완료해야 합니다.")
                    replacement = old if old and old["kind"] != item["kind"] else None
                    if replacement:
                        old = {}
                    record = {**old, "source_id": item["source_id"], "identity": item["identity"],
                              "path": item["path"], "kind": item["kind"]}
                    newly_allocated = not record.get("remote_id")
                    if newly_allocated:
                        record.update(remote_id=api.new_id(), complete=False)
                    if replacement:
                        manifest["retired:" + replacement["remote_id"]] = {**replacement, "replacement": key}
                    if old_key and old_key != key:
                        manifest.pop(old_key)
                    used.add(key)
                    save_record()  # Assigned identity is durable before any remote mutation.
                current = None
                name = item["path"].rsplit("/", 1)[-1]
                if not newly_allocated:
                    try:
                        current = api.get(record["remote_id"])
                    except DriveError as error:
                        if error.code != "unavailable":
                            raise
                        if record.get("complete"):
                            if not can_rebuild(record["remote_id"], name, parent):
                                raise
                            with lock:
                                record.update(remote_id=api.new_id(), complete=False)
                                newly_allocated = True
                                for field in ("hash", "version", "session", "upload_hash"):
                                    record.pop(field, None)
                                save_record()  # Replacement ID is durable before create.
                if current and (current["mimeType"] == FOLDER) != (item["kind"] == "folder"):
                    raise DriveError("type_changed", "파일·폴더 유형이 바뀌었습니다. 기존 사본을 보존합니다.")
                restored = bool(current and current.get("trashed"))
                if current and (current["name"] != name or current.get("parents") != [parent] or current.get("trashed")):
                    current = api.metadata(record["remote_id"], name, parent, current)
                    with lock:
                        changed += 1
                if item["kind"] == "folder":
                    if not current:
                        current = api.create_folder(record["remote_id"], name, parent)
                        if newly_allocated:
                            with listing_lock:
                                listings[record["remote_id"]] = []
                        with lock:
                            changed += 1
                    if restored:
                        with lock:
                            descendants = [value["remote_id"] for value in manifest.values()
                                           if value.get("source_id") == item["source_id"]
                                           and value.get("path", "").startswith(item["path"] + "/")]
                        api.invalidate(descendants)
                else:
                    digest = None
                    if current and current.get("md5Checksum") and int(current.get("size", -1)) == item["size"]:
                        _, digest = self.snapshot(item, stage=False)
                    if digest is None or current.get("md5Checksum") != digest:
                        staged, digest = self.snapshot(item)
                        try:
                            received(0, item["size"])
                            current = api.upload(record["remote_id"], name, parent, staged, digest, bool(current), record, save_record,
                                                 progress=received)
                            with lock:
                                copied += 1
                        finally:
                            staged.unlink(missing_ok=True)
                    record["hash"] = digest
                record.update(complete=True, version=current.get("version"))
                save_record()
                if item["kind"] == "folder":
                    with lock:
                        verified_parents.add(key)
                        parents[record["remote_id"]] = current
            except (DriveError, OSError, KeyError) as error:
                if isinstance(error, DriveError) and error.code == "cancelled":
                    raise
                with lock:
                    errors.append(dict(path=item["path"], message=str(error) if isinstance(error, DriveError) else "로컬 항목을 처리하지 못했습니다. 기존 사본을 보존합니다."))
                    if item["kind"] == "folder" or (replacement and replacement["kind"] == "folder"):
                        failed_parents.add(item["path"])
            finally:
                with lock:
                    processed += 1
                    active -= 1
                    progress(processed=processed, current=item["path"], uploading=False, current_bytes=0,
                             file_bytes=0, active_items=active, transferred=copied, changed=changed, excluded=len(errors))

        with ThreadPoolExecutor(max_workers=PUBLISH_WORKERS, thread_name_prefix="drive-publish") as pool:
            def run_group(entries):
                iterator, pending, exhausted = iter(entries), set(), False
                while pending or not exhausted:
                    api.check()
                    while not exhausted and len(pending) < PUBLISH_WORKERS:
                        try:
                            pair = next(iterator)
                        except StopIteration:
                            exhausted = True
                        else:
                            pending.add(pool.submit(sync_item, pair))
                    if pending:
                        done, pending = wait(pending, return_when=FIRST_COMPLETED)
                        for future in done:
                            future.result()

            folders = [pair for pair in ordered if pair[1]["kind"] == "folder"]
            for _, group in groupby(folders, key=lambda pair: pair[1]["path"].count("/")):
                run_group(group)
            run_group(pair for pair in ordered if pair[1]["kind"] != "folder")
        # A stopped context is preserved. Only a complete, stable selected scan authorizes trash.
        progress(stage="checking", processed=len(inventory), current="", current_bytes=0, file_bytes=0, uploading=False, active_items=0,
                 transferred=copied, changed=changed, excluded=len(errors))
        fresh, _ = local_inventory(sources, api.cancel)
        stable = {k: (v["stamp"], v["kind"]) for k, v in fresh.items()} == {k: (v["stamp"], v["kind"]) for k, v in inventory.items()}
        if not stable:
            errors.append(dict(path="", message="동기화 중 로컬 구성이 바뀌어 삭제 반영을 보류했습니다."))
        blocked = [v["path"] for v in inventory.values() if v["error"]] + list(failed_parents)
        stale = [(key, item) for key, item in manifest.items()
                 if item.get("source_id") in selected_ids and key not in inventory and key not in used
                 and not any(item["path"] == p or item["path"].startswith(p + "/") for p in blocked)]
        if stable:
            for key, item in sorted(stale, key=lambda pair: pair[1]["path"].count("/"), reverse=True):
                api.check()
                if item.get("replacement") and not manifest.get(item["replacement"], {}).get("complete"):
                    continue
                # Do not trash a directory that still contains a preserved, stopped source.
                if item["kind"] == "folder" and any(v["path"].startswith(item["path"] + "/") for k, v in manifest.items() if k != key):
                    continue
                try:
                    progress(stage="cleanup", current=item["path"], changed=changed, excluded=len(errors))
                    if item["kind"] == "folder" and api.children(item["remote_id"]):
                        raise DriveError("unmanaged_children", "원격 폴더에 남은 항목이 있어 폴더의 휴지통 이동을 보류했습니다.")
                    api.trash(item["remote_id"])
                    manifest.pop(key)
                    self.store.checkpoint(connection["id"], "upload", manifest, key)
                    changed += 1
                except DriveError as error:
                    errors.append(dict(path=item["path"], message=str(error)))
        progress(stage="finishing", current="", transferred=copied, changed=changed, excluded=len(errors))
        return dict(transferred=copied, changed=changed, excluded=len(errors), errors=errors)

    def receive(self, connection, publisher_id, api):
        self.recover_commit()
        job = "receive:" + publisher_id
        manifest = self.store.manifest(connection["id"], job)
        save = lambda: self.store.checkpoint(connection["id"], job, manifest, file_id)
        publisher = api.get(publisher_id)
        if publisher.get("mimeType") != FOLDER or connection["root_id"] not in publisher.get("parents", []):
            raise DriveError("publisher_changed", "선택한 폴더의 공유 루트와 위치를 확인해 주세요. 기존 사본을 보존합니다.")
        if publisher.get("capabilities", {}).get("canListChildren") is False and not publisher.get("trashed"):
            raise DriveError("partial_listing", "수신 폴더의 하위 목록을 읽을 수 없습니다. 기존 사본을 보존합니다.")
        entries = {} if publisher.get("trashed") else remote_inventory(api, publisher_id)
        destination = private_dir(self.data_dir / "external-sources" / "google-drive" / connection["id"] / publisher_id)
        errors, changed, copied = [], 0, 0
        old_paths = [(v["prior_path"], v["kind"]) for v in manifest.values() if v.get("prior_path")]
        owned_paths = {v["path"] for v in manifest.values()}
        final_paths = {v["path"] for v in entries.values()}
        # Missing list entries may mean permission loss, not deletion. Verify each missing ID.
        confirmed_deleted = set()
        known_folders = {key for key, value in manifest.items() if value["kind"] == "folder"}

        def still_inside(value, visited=None):
            if value.get("trashed"):
                return False
            visited = set(visited or ())
            if value["id"] in visited:
                raise DriveError("partial_listing", "원격 폴더 위치를 확인하지 못했습니다.")
            visited.add(value["id"])
            for parent in value.get("parents", []):
                if parent == publisher_id or parent in entries:
                    return True
                if parent in known_folders and still_inside(api.get(parent), visited):
                    return True
            return False

        for file_id in set(manifest) - set(entries):
            api.check()
            if publisher.get("trashed"):
                confirmed_deleted.add(file_id)
                continue
            try:
                value = api.get(file_id)
                if not still_inside(value):
                    confirmed_deleted.add(file_id)
                else:
                    errors.append(dict(path=manifest[file_id]["path"], message="원격 목록과 항목의 위치가 일치하지 않아 기존 사본을 보존합니다."))
            except DriveError as error:
                errors.append(dict(path=manifest[file_id]["path"], message=str(error)))
        succeeded = set()

        def remove_replaced(relative):
            # Only individually confirmed source removals may clear a type conflict.
            candidates = [key for key in confirmed_deleted if key in manifest
                          and (manifest[key]["path"] == relative or manifest[key]["path"].startswith(relative + "/"))]
            for key in sorted(candidates, key=lambda k: manifest[k]["path"].count("/"), reverse=True):
                old_item = manifest[key]
                self.remove_owned(local_path(destination, old_item["path"]), old_item["kind"])
                manifest.pop(key)
                save()

        for file_id, item in sorted(entries.items(), key=lambda pair: (pair[1]["path"].count("/"), pair[1]["kind"] != "folder", pair[1]["path"])):
            api.check()
            old = manifest.get(file_id, {})
            target = None
            try:
                target = local_path(destination, item["path"])
                if target.exists() and item["path"] not in owned_paths and not (item["kind"] == "folder" and target.is_dir()):
                    raise DriveError("unmanaged_path", "수신 경로에 별도로 만든 항목이 있어 덮어쓰지 않았습니다.")
                if item["kind"] == "folder":
                    if target.is_file():
                        remove_replaced(item["path"])
                    private_dir(target)
                else:
                    if item["mimeType"].startswith("application/vnd.google-apps."):
                        raise DriveError("unsupported", "Google 고유 문서·바로가기는 파일 내보내기를 자동 추가하지 않습니다.")
                    if item.get("size") is not None and int(item["size"]) > MAX_FILE_BYTES:
                        raise DriveError("too_large", "앱의 파일당 100MB 제한을 초과합니다. 기존 사본을 보존합니다.")
                    original = local_path(destination, old["path"]) if old else None
                    digest = item.get("md5Checksum")
                    reusable = bool(original and original.is_file() and original.stat().st_size <= MAX_FILE_BYTES and digest and content_hash(original) == digest)
                    if reusable and original == target:
                        pass
                    else:
                        private_dir(target.parent)
                        fd, temporary = tempfile.mkstemp(prefix=".localbrain-drive-", dir=target.parent)
                        os.close(fd)
                        temp = Path(temporary)
                        self.store.put("download-staging", [str(temp)])
                        try:
                            if reusable:
                                shutil.copyfile(original, temp)
                                # A local edit during copying cannot create an unverified checkpoint.
                                if content_hash(temp) != digest:
                                    raise DriveError("local_changed", "수신 사본이 변경되어 다시 비교해야 합니다.")
                            else:
                                digest = api.download(item, temp)
                                copied += 1
                            api.check()
                            # Re-check links immediately before replacement.
                            local_path(destination, item["path"])
                            temp.chmod(0o600)
                            with temp.open("rb") as completed:
                                os.fsync(completed.fileno())
                            if target.is_dir():
                                remove_replaced(item["path"])
                            record = dict(path=item["path"], kind="file", hash=digest, version=item.get("version"), complete=True)
                            if old and old["path"] != item["path"]:
                                record["prior_path"] = old["path"]
                            self.store.put("receive-commit", dict(connection_id=connection["id"], publisher_id=publisher_id,
                                           job=job, file_id=file_id, record=record))
                            os.replace(temp, target)
                            if os.name == "posix":
                                parent_fd = os.open(target.parent, os.O_RDONLY)
                                try:
                                    os.fsync(parent_fd)
                                finally:
                                    os.close(parent_fd)
                            changed += 1
                        finally:
                            temp.unlink(missing_ok=True)
                            self.store.put("download-staging", [])
                if old and old["path"] != item["path"]:
                    old_paths.append((old["path"], old["kind"]))
                manifest[file_id] = dict(path=item["path"], kind=item["kind"], hash=item.get("md5Checksum"), version=item.get("version"), complete=True)
                if old and old["path"] != item["path"]:
                    manifest[file_id]["prior_path"] = old["path"]
                save()
                self.store.put("receive-commit", None)
                succeeded.add(item["path"])
                owned_paths.add(item["path"])
            except (DriveError, OSError, ValueError) as error:
                errors.append(dict(path=item["path"], message=str(error) if isinstance(error, DriveError) else "수신 항목을 저장하지 못했습니다. 기존 사본을 보존합니다."))
        for file_id in sorted(confirmed_deleted.intersection(manifest), key=lambda key: manifest[key]["path"].count("/"), reverse=True):
            api.check()
            item = manifest[file_id]
            try:
                path = local_path(destination, item["path"])
                if item["path"] not in final_paths:
                    self.remove_owned(path, item["kind"])
                    changed += 1
                elif item["path"] not in succeeded:
                    continue
                manifest.pop(file_id)
                save()
            except (DriveError, OSError) as error:
                errors.append(dict(path=item["path"], message=str(error) if isinstance(error, DriveError) else "수신 항목을 제거하지 못했습니다."))
        # A renamed folder is removed only when empty; unrelated user files survive.
        for relative, kind in sorted(old_paths, key=lambda p: p[0].count("/"), reverse=True):
            if relative not in final_paths:
                try:
                    self.remove_owned(local_path(destination, relative), kind)
                    for key, value in list(manifest.items()):
                        if value.get("prior_path") == relative:
                            manifest[key] = {k: v for k, v in value.items() if k != "prior_path"}
                    self.store.checkpoint(connection["id"], job, manifest)
                except (DriveError, OSError):
                    errors.append(dict(path=relative, message="이전 수신 경로를 정리하지 못했습니다. 별도 파일이 있는지 확인해 주세요."))
        return dict(transferred=copied, changed=changed, excluded=len(errors), errors=errors, destination=str(destination))

    @staticmethod
    def remove_owned(path, kind):
        if kind == "folder":
            if path.exists():
                path.rmdir()  # Never recursively erase files the manifest does not own.
        else:
            if path.exists() and not path.is_file():
                raise DriveError("type_changed", "로컬 사본의 유형이 바뀌어 보존했습니다.")
            path.unlink(missing_ok=True)
