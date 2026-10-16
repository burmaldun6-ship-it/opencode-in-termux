# OpenCode v1.19.3 for Termux (native Android/Bionic)

This repository packages a pinned **native AArch64 Android/Bionic ELF** for Termux
and adds a launcher with conservative privacy defaults. The previous transplant
build used the Linux package's glibc OpenTUI library and failed when the TUI
loaded on Android. The workflow now uses an independently published native
Termux build with Bionic OpenTUI instead of transplanting that broken library.

## Build

1. Open **Actions → Build native OpenCode for Termux → Run workflow**.
2. Keep version set to `1.19.3` (the workflow intentionally rejects other versions).
3. Download the `opencode-termux-v1.19.3` artifact from the completed run.

The workflow downloads the native binary from
[`bd-loser/opencode-bionic` release `v1.19.3`](https://github.com/bd-loser/opencode-bionic/releases/tag/v1.19.3).
It pins the source tag's commit and the published checksum-manifest and binary
SHA-256 digests, then checks the AArch64 ELF header, Android dynamic linker,
main-ELF glibc dependencies, and embedded OpenTUI/version markers. The package
step fails closed if these checks drift.

**Important provenance note:** this workflow packages a checksum-pinned,
third-party native build; it does not rebuild the OpenCode machine code from
source in this repository. The source project pins upstream OpenCode v1.19.3
and `@androidtui/core-android-arm64` v0.5.17. CI on Linux cannot execute an
Android ELF end-to-end, so the final TUI still needs to be checked on a real
Termux ARM64 device.

## Install on Termux (Android 10+, ARM64)

Download and extract the Actions artifact on your phone, then from its directory:

```bash
pkg update
pkg install coreutils libc++
bash install-termux.sh ./opencode-native
```

The installer places the native executable under
`$PREFIX/lib/opencode-in-termux/opencode-native` and the privacy launcher at
`$PREFIX/bin/opencode`. Then run:

```bash
opencode --version
opencode
```

The binary targets Android API 29 or newer. Installation runs inside Termux;
no proot, chroot, Ubuntu, Debian userspace, or glibc installation is needed.

## Privacy behaviour and limitations

The launcher sets:
- `OPENCODE_DISABLE_AUTOUPDATE=1` — disables automatic update checks;
- `OPENCODE_DISABLE_MODELS_FETCH=1` — disables background remote model-catalog fetches;
- `OTEL_SDK_DISABLED=true`, `OTEL_TRACES_EXPORTER=none`,
  `OTEL_LOGS_EXPORTER=none`, and `OTEL_METRICS_EXPORTER=none` — disables
  standard OpenTelemetry SDK exporters.

It creates a minimal config with `autoupdate: false` and
`experimental.openTelemetry: false` only if you do not already have an
OpenCode config. It never overwrites an existing user config.

This is a **runtime privacy hardening layer**, not a claim that every telemetry
code path was removed from the compiled machine code. Requests to your chosen
AI provider, MCP servers, plugins, and remote configuration/auth services still
work and can transmit data required by those features. Network-level auditing
on a real device is needed to prove the complete set of outbound connections.

## Build provenance

- Native source release: [`v1.19.3`](https://github.com/bd-loser/opencode-bionic/releases/tag/v1.19.3)
- Source repository commit: `52c794391531fe18469bcb435ba910057161b4a8`
- Native ELF SHA-256: `b7a4c266988700732164fa6c02396ae805dc6bab3bfcbb790a5a632fcf71fa0f`
- Bionic OpenTUI package version: `@androidtui/core-android-arm64@0.5.17`

The Actions artifact includes `build-report.json`, source version pins, ELF
inspection output, a local `SHA256SUMS` file, and the upstream release manifest.
