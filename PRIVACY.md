# Privacy notes for the Termux build

This project does not claim to remove every telemetry-related code path from
the OpenCode binary. The workflow builds the upstream v1.19.3 module graph and
uses a launcher to disable automatic catalogue refresh, update checks, and
standard OpenTelemetry exporters.

Before calling the build telemetry-free, review the exact upstream version and
perform network capture on a real Android device. The launcher cannot prevent
the selected model provider, user-configured MCP servers, plugins, remote auth
services, or other configured integrations from making network requests.

The launcher intentionally preserves the user's existing OpenCode config.
If an existing config explicitly enables experimental OpenTelemetry, review
that config manually and set:

```json
{
  "experimental": {
    "openTelemetry": false
  }
}
```

The build's GitHub Actions runner is x86_64 Linux and cannot execute the
Android/Bionic AArch64 result. Artifact checks are structural, not a substitute
for running `opencode --version` and the interactive TUI on a real Termux
ARM64 device.
