"""A local macOS chooser for the browser edition; selection does not import data."""

import json
import subprocess
import sys
import threading

from fastapi import HTTPException


_chooser_lock = threading.Lock()
# Use AppKit in the chooser's own process: no Finder automation permission,
# shell interpolation, filesystem enumeration endpoint or third-party service.
_CHOOSER = """
ObjC.import('AppKit');
function run(args) {
    const app = $.NSApplication.sharedApplication;
    app.setActivationPolicy($.NSApplicationActivationPolicyAccessory);
    const panel = $.NSOpenPanel.openPanel;
    const directory = args[0] === 'directory';
    panel.canChooseDirectories = directory;
    panel.canChooseFiles = !directory;
    panel.allowsMultipleSelection = false;
    panel.canCreateDirectories = false;
    panel.showsHiddenFiles = true;
    panel.title = directory ? 'LocalBrain — 폴더 선택' : 'LocalBrain — 파일 선택';
    panel.directoryURL = $.NSURL.fileURLWithPath($.NSHomeDirectory());
    app.activateIgnoringOtherApps(true);
    const response = panel.runModal;
    if (response === $.NSModalResponseCancel) return JSON.stringify({path: null});
    if (response !== $.NSModalResponseOK) throw new Error('File chooser did not complete');
    return JSON.stringify({path: ObjC.unwrap(panel.URL.path)});
}
"""


def choose_local_path(directory: bool):
    if sys.platform != "darwin":
        raise HTTPException(501, "이 환경에서는 선택창을 열 수 없습니다. 경로를 직접 입력해 주세요.")
    if not _chooser_lock.acquire(blocking=False):
        raise HTTPException(409, "열려 있는 파일·폴더 선택창을 먼저 닫아 주세요.")
    try:
        result = subprocess.run(
            ["/usr/bin/osascript", "-l", "JavaScript", "-e", _CHOOSER,
             "directory" if directory else "file"],
            capture_output=True, text=True, timeout=300, check=True,
        )
        path = json.loads(result.stdout)["path"]
        if path is not None and (not isinstance(path, str) or not path.startswith("/") or "\0" in path):
            raise ValueError("Invalid picker result")
        return path
    except subprocess.TimeoutExpired:
        raise HTTPException(408, "선택 시간이 만료되었습니다. 찾아보기를 다시 눌러 주세요.") from None
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError, TypeError):
        raise HTTPException(503, "파일·폴더 선택창을 열지 못했습니다. 다시 시도하거나 경로를 직접 입력해 주세요.") from None
    finally:
        _chooser_lock.release()
