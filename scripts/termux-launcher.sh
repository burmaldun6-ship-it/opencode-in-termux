#!/data/data/com.termux/files/usr/bin/sh
set -eu

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
APP_DIR="$PREFIX/lib/opencode-in-termux"
NATIVE="$APP_DIR/opencode-native"

if [ ! -x "$NATIVE" ]; then
  echo "opencode: native binary not found: $NATIVE" >&2
  echo "Reinstall using install-termux.sh from the build artifact." >&2
  exit 127
fi

# Privacy defaults: no automatic update checks, no background model catalogue
# refresh, and no standard OpenTelemetry SDK exporters.
export OPENCODE_DISABLE_AUTOUPDATE=1
export OPENCODE_DISABLE_MODELS_FETCH=1
export OTEL_SDK_DISABLED=true
export OTEL_TRACES_EXPORTER=none
export OTEL_LOGS_EXPORTER=none
export OTEL_METRICS_EXPORTER=none

# OpenCode's experimental OTEL integration is opt-in. Seed a minimal config
# only when the user has no config yet; never clobber a user's existing config.
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
CONFIG_DIR="$CONFIG_HOME/opencode"
CONFIG_FILE="$CONFIG_DIR/opencode.json"
if [ ! -e "$CONFIG_FILE" ]; then
  mkdir -p "$CONFIG_DIR"
  cat > "$CONFIG_FILE" <<'JSON'
{
  "$schema": "https://opencode.ai/config.json",
  "autoupdate": false,
  "experimental": {
    "openTelemetry": false
  }
}
JSON
fi

exec "$NATIVE" "$@"
