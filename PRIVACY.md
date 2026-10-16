# Privacy notes for the Termux build

The installable artifact wraps a checksum-pinned native Android/Bionic OpenCode
v1.19.3 build from
[bd-loser/opencode-bionic](https://github.com/bd-loser/opencode-bionic/releases/tag/v1.19.3).
It uses that project's Bionic OpenTUI build rather than the glibc OpenTUI library
that caused the earlier transplant artifact to crash at TUI startup.

The launcher sets:
- `OPENCODE_DISABLE_AUTOUPDATE=1`
- `OPENCODE_DISABLE_MODELS_FETCH=1`
- `OTEL_SDK_DISABLED=true`
- `OTEL_TRACES_EXPORTER=none`
- `OTEL_LOGS_EXPORTER=none`
- `OTEL_METRICS_EXPORTER=none`

When no config file exists, it writes `autoupdate: false` and
`experimental.openTelemetry: false`. It does not overwrite an existing
configuration file. If an existing config explicitly enables experimental
OpenTelemetry, review that config manually and set:

```json
{
  "autoupdate": false,
  "experimental": {
    "openTelemetry": false
  }
}
```

This is **runtime privacy hardening**, not a guarantee that every telemetry-
related code path has been removed from the compiled binary or that the
application makes no outbound requests. Requests to a selected model provider,
user-configured MCP servers, plugins, remote auth services, and other configured
integrations still operate and may transmit data required for those features.
Network capture on a real Android device is needed to inventory actual outbound
connections.

## Build verification limits

The workflow pins and verifies the third-party binary and checksum manifest,
then checks ELF architecture, the Android dynamic linker, glibc dependencies
of the main ELF, and version/OpenTUI markers. Its Linux runner cannot execute
the Android/Bionic AArch64 binary. These structural checks do not replace
running `opencode --version` and using the interactive TUI on a real Termux
ARM64 device.

The upstream native release targets Android 10 / API 29 or newer.
