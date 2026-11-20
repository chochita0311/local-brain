#!/usr/bin/env python3
"""Verify Mermaid assets in an explicit native web root or loopback server."""

import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler, Request


VENDOR = "vendor/mermaid/"
REQUIRED_OUTPUTS = frozenset((
    "mermaid.esm.min.js", "mermaid-LICENSE.txt", "layout-elk-LICENSE.txt",
    "elkjs-LICENSE.txt", "esbuild-LICENSE.txt",
))


def filesystem_fetch(web_root):
    """Read assets beneath the caller's selected apps/web-style root."""
    static = (Path(web_root) / "static").resolve(strict=True)
    if not static.is_dir():
        raise ValueError("The selected web root must contain a static directory")

    def fetch(asset):
        path = (static / asset).resolve(strict=True)
        if not path.is_relative_to(static):
            raise ValueError("Static asset escapes the selected web root")
        return path.read_bytes()

    return fetch


def loopback_url(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Select an HTTP or HTTPS loopback server URL")
    try:
        local = ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        local = parsed.hostname == "localhost"
    if not local or parsed.username is not None or parsed.password is not None:
        raise ValueError("Select an HTTP or HTTPS loopback server URL without userinfo")
    if parsed.query or parsed.fragment:
        raise ValueError("Use a server root URL without query or fragment; use --token-env for authentication")
    # Force malformed port validation before constructing an opener/request.
    parsed.port
    return parsed


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        raise ValueError("Static asset redirects are not permitted")


def loopback_fetch(url, token=None):
    """Fetch only from the explicit origin, without proxies or redirects."""
    parsed = loopback_url(url)
    # A builder's proxy settings must not forward local assets or launch tokens.
    opener = build_opener(ProxyHandler({}), NoRedirect())
    headers = {"Authorization": "Bearer " + token} if token else {}

    def fetch(asset):
        path = parsed.path.rstrip("/") + "/static/" + quote(asset, safe="/")
        request = Request(urlunsplit((parsed.scheme, parsed.netloc, path, "", "")), headers=headers)
        try:
            with opener.open(request, timeout=10) as response:
                if response.status != 200:
                    raise AssertionError("Static asset did not return 200: " + asset)
                return response.read()
        except HTTPError as error:
            raise AssertionError("Static asset did not return 200: " + asset) from error

    return fetch


def verify_assets(fetch):
    """Check the shipped bundle, recorded hashes, licenses and adapter policy."""
    bundle = fetch(VENDOR + "mermaid.esm.min.js")
    manifest_bytes = fetch(VENDOR + "asset-manifest.json")
    adapter = fetch("mermaid-adapter.js")
    layout_license = fetch(VENDOR + "layout-elk-LICENSE.txt")
    elkjs_license = fetch(VENDOR + "elkjs-LICENSE.txt")
    if len(bundle) <= 3_000_000:
        raise AssertionError("Installed Mermaid bundle is unexpectedly small.")
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict) or manifest.get("schema") != "localbrain.mermaid-assets.v1":
        raise AssertionError("Installed Mermaid asset manifest has the wrong schema.")
    dependencies = manifest.get("dependencies", {})
    if not isinstance(dependencies, dict) or dependencies.get("layoutElk") != {"license": "MIT", "version": "0.2.2"}:
        raise AssertionError("Installed Mermaid ELK loader metadata is invalid.")
    if dependencies.get("elkjs") != {"license": "EPL-2.0", "version": "0.9.3"}:
        raise AssertionError("Installed ELK engine metadata is invalid.")
    if b"MIT License" not in layout_license or b"Eclipse Public License" not in elkjs_license:
        raise AssertionError("Installed Mermaid ELK licenses are missing.")
    if b'securityLevel: "strict"' not in adapter:
        raise AssertionError("Installed Mermaid adapter is missing strict security.")
    if b"registerLayoutLoaders(elkLayouts)" not in adapter:
        raise AssertionError("Installed Mermaid adapter is missing ELK registration.")
    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict) or not REQUIRED_OUTPUTS.issubset(outputs):
        raise AssertionError("Installed Mermaid asset manifest is missing output hashes.")
    known = {
        "mermaid.esm.min.js": bundle,
        "layout-elk-LICENSE.txt": layout_license,
        "elkjs-LICENSE.txt": elkjs_license,
    }
    for name, digest in outputs.items():
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or name in (".", ".."):
            raise AssertionError("Installed Mermaid manifest has an invalid output name.")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise AssertionError("Installed Mermaid manifest has an invalid output hash.")
        content = known[name] if name in known else fetch(VENDOR + name)
        if hashlib.sha256(content).hexdigest() != digest:
            raise AssertionError("Installed Mermaid output hash does not match: " + name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--web-root", type=Path, help="Explicit native web root containing static/")
    target.add_argument("--url", help="Explicit loopback server root; reads its /static/ assets")
    parser.add_argument("--token-env", metavar="NAME", help="Environment variable holding a Bearer token for --url")
    args = parser.parse_args(argv)
    if args.token_env and not args.url:
        parser.error("--token-env requires --url")
    token = None
    if args.token_env:
        token = os.environ.get(args.token_env)
        if not token:
            parser.error("The selected token environment variable is unset or empty")
    if args.web_root:
        fetch = filesystem_fetch(args.web_root)
        source = str(args.web_root)
    else:
        fetch = loopback_fetch(args.url, token)
        source = args.url
    verify_assets(fetch)
    print("Mermaid assets verified from " + source + ".")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
