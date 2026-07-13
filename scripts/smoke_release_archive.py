from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def verify_checksum(archive: Path, checksum: Path) -> None:
    expected = checksum.read_text(encoding="ascii").split()[0].lower()
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"archive checksum mismatch: expected {expected}, received {actual}")


def safe_members(bundle: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = bundle.infolist()
    for member in members:
        path = PurePosixPath(member.filename)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit(f"unsafe archive member: {member.filename}")
        if os.name != "nt" and "/bin/zmlc" in member.filename and not member.is_dir():
            mode = member.external_attr >> 16
            if not mode & 0o111:
                raise SystemExit(f"release binary is not executable: {member.filename}")
    return members


def restore_permissions(extracted: Path, members: list[zipfile.ZipInfo]) -> None:
    if os.name == "nt":
        return
    for member in members:
        mode = member.external_attr >> 16
        if mode:
            (extracted / member.filename).chmod(mode)


def bundle_root(extracted: Path) -> Path:
    roots = [path for path in extracted.iterdir() if path.is_dir()]
    if len(roots) != 1:
        raise SystemExit(f"release archive must contain one root directory, found {len(roots)}")
    return roots[0]


def verify_metadata(root: Path, expected_version: str | None) -> None:
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    if marketplace.get("name") != "zmlc-public":
        raise SystemExit("release marketplace name must be zmlc-public")
    if (marketplace.get("interface") or {}).get("displayName") != "ZMLC Public":
        raise SystemExit("release marketplace display name must be ZMLC Public")
    plugins = marketplace.get("plugins") or []
    if len(plugins) != 1 or plugins[0].get("name") != "zmlc-router":
        raise SystemExit("release marketplace must contain exactly the zmlc-router plugin")
    entry = plugins[0]
    if (entry.get("source") or {}).get("path") != "./plugins/zmlc-router":
        raise SystemExit("release marketplace plugin path is invalid")
    policy = entry.get("policy") or {}
    if policy != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}:
        raise SystemExit(f"release marketplace policy is invalid: {policy}")

    plugin = root / "plugins" / "zmlc-router"
    manifest = json.loads(
        (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    if manifest.get("name") != "zmlc-router":
        raise SystemExit("release plugin manifest name is invalid")
    version = str(manifest.get("version", ""))
    if expected_version and version.split("+", 1)[0] != expected_version:
        raise SystemExit(
            f"release plugin version is not {expected_version}: {manifest.get('version')}"
        )
    for name in ("zmlc-router-64.png", "zmlc-router-512.png"):
        icon = plugin / "assets" / name
        if not icon.is_file() or not icon.read_bytes().startswith(PNG_SIGNATURE):
            raise SystemExit(f"release icon is missing or invalid: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the exact ZMLC release archive")
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--sha256", type=Path, required=True)
    parser.add_argument("--expected-version")
    args = parser.parse_args()
    archive = args.archive.resolve()
    checksum = args.sha256.resolve()
    verify_checksum(archive, checksum)

    with tempfile.TemporaryDirectory(prefix="zmlc-release-") as temporary:
        extracted = Path(temporary)
        with zipfile.ZipFile(archive) as bundle:
            members = safe_members(bundle)
            bundle.extractall(extracted)
        restore_permissions(extracted, members)
        root = bundle_root(extracted)
        verify_metadata(root, args.expected_version)
        subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("smoke_standalone.py")),
                "--root",
                str(root),
            ],
            check=True,
        )

    print("RELEASE ARCHIVE SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
