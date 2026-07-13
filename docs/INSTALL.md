# Installation

## Codex plugin: release bundle

Download the archive matching your operating system from the latest GitHub release,
verify its SHA-256 file and Sigstore bundle, then extract it to a stable directory.
The archive contains the plugin manifest, skill, standalone MCP executable, and the
`zmlc` preflight CLI. It does not require Python, an API key, or a local model.

Install the extracted marketplace and plugin:

```bash
codex plugin marketplace add /path/to/zmlc-router-<platform>
codex plugin add zmlc-router@zmlc-public
```

Start a new Codex task after installation so the skill and MCP server are loaded.

For actual model-call avoidance, run the executable from the extracted bundle:

```bash
./plugins/zmlc-router/bin/zmlc codex "What is 25% of 80?"
./plugins/zmlc-router/bin/zmlc codex "Review this repository" --cd .
```

On Windows, use `zmlc.exe`. The command finds Codex Desktop or the Codex CLI
automatically; `CODEX_BIN` remains available as an explicit override.

## Framework library

```bash
python -m pip install zmlc-router
```

For a source checkout:

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

## Offline behavior

Deterministic solvers, verifiers, prompt compilation, routing, and telemetry are fully
offline. Unsupported tasks return `host_model` with `delegate_to_codex`; the plugin
does not call another model or configure an external provider. `zmlc codex` delegates
unsupported work only to the user's existing Codex installation.

## Uninstall

```bash
codex plugin remove zmlc-router@zmlc-public
codex plugin marketplace remove zmlc-public
```

Then delete the extracted release directory. ZMLC does not create a model cache or
credential store. To roll back, install an older signed release archive with the same
two commands; versioned Codex plugin caches keep releases isolated.
