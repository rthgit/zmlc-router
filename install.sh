#!/usr/bin/env sh
set -eu

repo="rthgit/zmlc-router"
case "$(uname -s)-$(uname -m)" in
  Linux-x86_64) platform="linux-x64" ;;
  Darwin-arm64) platform="macos-arm64" ;;
  *) echo "Unsupported platform: $(uname -s)-$(uname -m)" >&2; exit 1 ;;
esac
asset="zmlc-router-${platform}.zip"
base="https://github.com/${repo}/releases/latest/download"
install_root="${ZMLC_INSTALL_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/zmlc-router}"
temporary="$(mktemp -d "${TMPDIR:-/tmp}/zmlc-install.XXXXXX")"
trap 'rm -rf "$temporary"' EXIT

for command in curl unzip cosign codex; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "$command is required to install ZMLC safely" >&2
    exit 1
  }
done

curl -fsSL "$base/$asset" -o "$temporary/$asset"
curl -fsSL "$base/$asset.sha256" -o "$temporary/$asset.sha256"
curl -fsSL "$base/$asset.sigstore.json" -o "$temporary/$asset.sigstore.json"
expected="$(awk '{print $1}' "$temporary/$asset.sha256")"
if command -v sha256sum >/dev/null 2>&1; then
  actual="$(sha256sum "$temporary/$asset" | awk '{print $1}')"
else
  actual="$(shasum -a 256 "$temporary/$asset" | awk '{print $1}')"
fi
[ "$actual" = "$expected" ] || { echo "SHA-256 mismatch for $asset" >&2; exit 1; }
cosign verify-blob \
  --bundle "$temporary/$asset.sigstore.json" \
  --certificate-identity-regexp "^https://github.com/${repo}/.github/workflows/release.yml@refs/tags/v.*$" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  "$temporary/$asset"

mkdir -p "$temporary/extracted"
unzip -q "$temporary/$asset" -d "$temporary/extracted"
source_root="$(find "$temporary/extracted" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
[ -n "$source_root" ] || { echo "Release archive has no root directory" >&2; exit 1; }
"$source_root/plugins/zmlc-router/bin/zmlc" doctor
rm -rf "$install_root"
mkdir -p "$(dirname "$install_root")"
mv "$source_root" "$install_root"
codex plugin remove zmlc-router@zmlc-public >/dev/null 2>&1 || true
codex plugin marketplace remove zmlc-public >/dev/null 2>&1 || true
codex plugin marketplace add "$install_root"
codex plugin add zmlc-router@zmlc-public
"$install_root/plugins/zmlc-router/bin/zmlc" doctor
printf '%s\n' "ZMLC installed. Start a new Codex task to load the plugin."
printf '%s\n' "Uninstall: codex plugin remove zmlc-router@zmlc-public && codex plugin marketplace remove zmlc-public"
