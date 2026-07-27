import asyncio
import json
from pathlib import Path

import localbrain
from fastapi.staticfiles import StaticFiles


async def fetch(static: StaticFiles, path: str) -> bytes:
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    encoded_path = f"/{path}".encode()
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": f"/{path}",
        "raw_path": encoded_path,
        "query_string": b"",
        "root_path": "",
        "headers": [],
        "client": ("127.0.0.1", 1),
        "server": ("test", 80),
    }
    await static(scope, receive, send)
    if not messages or messages[0].get("status") != 200:
        raise AssertionError(f"Static asset did not return 200: {path}")
    return b"".join(message.get("body", b"") for message in messages)


async def main() -> None:
    package_root = Path(localbrain.__file__).resolve().parent
    static = StaticFiles(directory=package_root / "static")
    bundle, manifest_bytes, adapter, layout_license, elkjs_license = await asyncio.gather(
        fetch(static, "vendor/mermaid/mermaid.esm.min.js"),
        fetch(static, "vendor/mermaid/asset-manifest.json"),
        fetch(static, "mermaid-adapter.js"),
        fetch(static, "vendor/mermaid/layout-elk-LICENSE.txt"),
        fetch(static, "vendor/mermaid/elkjs-LICENSE.txt"),
    )
    if len(bundle) <= 3_000_000:
        raise AssertionError("Installed Mermaid bundle is unexpectedly small.")
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema") != "localbrain.mermaid-assets.v1":
        raise AssertionError("Installed Mermaid asset manifest has the wrong schema.")
    dependencies = manifest.get("dependencies", {})
    if dependencies.get("layoutElk") != {"license": "MIT", "version": "0.2.2"}:
        raise AssertionError("Installed Mermaid ELK loader metadata is invalid.")
    if dependencies.get("elkjs") != {"license": "EPL-2.0", "version": "0.9.3"}:
        raise AssertionError("Installed ELK engine metadata is invalid.")
    if b"MIT License" not in layout_license or b"Eclipse Public License" not in elkjs_license:
        raise AssertionError("Installed Mermaid ELK licenses are missing.")
    if b'securityLevel: "strict"' not in adapter:
        raise AssertionError("Installed Mermaid adapter is missing strict security.")
    if b"registerLayoutLoaders(elkLayouts)" not in adapter:
        raise AssertionError("Installed Mermaid adapter is missing ELK registration.")
    print(f"Installed Mermaid assets verified from {package_root}.")


if __name__ == "__main__":
    asyncio.run(main())
