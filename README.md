# OpenCode v1.19.3 for Termux (native Android/Bionic)

This repository builds a **native AArch64 Android ELF** from the official OpenCode
Linux ARM64 package using the transplant pipeline maintained by
[Hope2333/opencode-termux](https://github.com/Hope2333/opencode-termux), then
wraps it with conservative privacy defaults.

## Build

1. Open **Actions → Build native OpenCode for Termux → Run workflow**.
2. Keep version set to `1.19.3` (the workflow intentionally rejects other versions).
3. Download the `opencode-termux-v1.19.3` artifact from the completed run.

The build runs on GitHub-hosted Linux, so it cannot execute an Android/Bionic
AArch64 ELF for an end-to-end runtime test. It validates the transplant report,
ELF architecture, embedded version marker and hashes. A real Termux device is
still required for final runtime/TUI acceptance.

## Install on Termux (Android 9+, ARM64)

Download and extract the Actions artifact on your phone, then from its directory:

```bash
pkg update
pkg install coreutils file
bash install-termux.sh ./opencode-native
```

The installer places the native executable under
`$PREFIX/lib/opencode-in-termux/opencode-native` and the privacy launcher at
`$PREFIX/bin/opencode`. Then run:

```bash
opencode --version
opencode
```

The installer is intentionally not a root installer and does not use proot,
Ubuntu, Debian, or glibc.

## Privacy behaviour and limitations

The launcher sets:
- `OPENCODE_DISABLE_AUTOUPDATE=1` — disables automatic update checks;
- `OPENCODE_DISABLE_MODELS_FETCH=1` — disables background remote model-catalog fetches;
- `OTEL_SDK_DISABLED=true`, `OTEL_TRACES_EXPORTER=none`, and
  `OTEL_LOGS_EXPORTER=none` — disables standard OpenTelemetry SDK exporters.

It creates a minimal config with `experimental.openTelemetry: false` only if
you do not already have an OpenCode config. It never overwrites an existing
user config.

This is a **runtime privacy hardening layer**, not a claim that every telemetry
code path was removed from the compiled machine code. Requests to your chosen
AI provider, MCP servers, plugins, and remote configuration/auth services still
work and can transmit data required for those features. Network-level auditing
on a real device is needed to prove the complete set of outbound connections.

## Build provenance

The workflow pins the upstream application to `v1.19.3`, downloads the
official `opencode-linux-arm64@1.19.3` npm package, records the upstream
transplant repository commit, and uploads the transplant report and SHA-256
manifest alongside the executable.

The upstream transplant code is third-party build infrastructure and is
checked out from the `native-android` branch. Review that upstream code before
using the resulting binary if you need a fully reproducible/supply-chain-pinned
build.
