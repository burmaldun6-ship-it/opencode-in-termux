#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
SOURCE="${1:-./opencode-native}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="$SCRIPT_DIR/scripts/termux-launcher.sh"

if [[ "$(uname -m)" != "aarch64" ]]; then
  echo "ERROR: this build targets Android ARM64 (aarch64); found $(uname -m)." >&2
  exit 1
fi
if [[ ! -f "$SOURCE" ]]; then
  echo "ERROR: native binary not found: $SOURCE" >&2
  exit 1
fi
if [[ ! -f "$LAUNCHER" ]]; then
  echo "ERROR: launcher script missing: $LAUNCHER" >&2
  exit 1
fi
if [[ -n "${ANDROID_VERSION:-}" ]] && (( ANDROID_VERSION < 9 )); then
  echo "ERROR: Android 9/API 28 or newer is required by the native build." >&2
  exit 1
fi

mkdir -p "$PREFIX/lib/opencode-in-termux" "$PREFIX/bin"
install -m 755 "$SOURCE" "$PREFIX/lib/opencode-in-termux/opencode-native"
install -m 755 "$LAUNCHER" "$PREFIX/bin/opencode"

echo "Installed native OpenCode binary to $PREFIX/lib/opencode-in-termux/opencode-native"
echo "Launcher installed to $PREFIX/bin/opencode"
echo "Try: opencode --version"
