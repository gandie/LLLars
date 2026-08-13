# Configuration

## Split Runtime Config

The preferred config shape is split into:

- `service`: host/port/workers/mount/network/queue settings
- `run`: model/tools/retries/limits/command settings

Mixing legacy top-level fields with split `service` and `run` in the same file
is rejected.

## Merge Precedence

If `env_file` is provided, values are resolved in this order:

1. defaults
2. values from `env_file`
3. values from JSON config
4. CLI flags

## Example

```json
{
  "env_file": "runtime.env",
  "service": {
    "mode": "serve",
    "host": "127.0.0.1",
    "port": 8000,
    "workers": 1,
    "mount_work_root": "playground",
    "mount_config_root": ".",
    "mount_artifacts_root": ".",
    "queue_backend": "inmemory",
    "network_policy": "inherit"
  },
  "run": {
    "model": "ollama:rafw007/qwen35-claude-coder:9b",
    "provider_url": "http://localhost:11434",
    "project_root": "playground",
    "commands": {},
    "command_profile": "playground-python",
    "command_profiles_path": "playground.command-profiles.yaml"
  }
}
```

## Runtime Controls

Native runtime controls are configured through these keys:

- `usage_request_limit`
- `usage_tool_calls_limit`
- `usage_input_tokens_limit`
- `usage_output_tokens_limit`
- `usage_total_tokens_limit`
- `usage_count_tokens_before_request`
- `agent_retries_tools`
- `agent_retries_output`
- `tool_timeout_sec`
- `max_concurrency`
- `instrumentation_enabled`
- `instrumentation_include_content`
- `skills_enabled`
- `skills_glob`
- `skills_defer_loading`
- `skills_require_description`
- `service_mode`
- `service_host`
- `service_port`
- `service_workers`
- `mount_work_root`
- `mount_config_root`
- `mount_artifacts_root`
- `queue_backend`
- `network_policy`

## Tool Group Controls

Use `run.tool_groups` to control which runtime tool groups are registered.

Example:

```json
{
  "run": {
    "tool_groups": {
      "enabled": ["native_file_read", "native_shell"],
      "disabled": []
    }
  }
}
```

Supported group names:

- `native_files`: backward-compatible alias for full native file access
  (`list_files`, `read_file`, `write_file`)
- `native_file_read`: registers read-only native file tools
  (`list_files`, `read_file`)
- `native_file_write`: registers native file write tool (`write_file`)
- `native_shell`: policy-gated shell tools
- `native_shell_yolo`: unrestricted shell execution tool (no allowlist)
- `native_web_research`: provider-adaptive web search/fetch capabilities
- `plugin_local`: local repository plugin tools
- `mcp_toolsets`: MCP-backed toolsets loaded during agent construction

Defaults remain unchanged when `run.tool_groups` is omitted:

- `native_files`
- `native_shell`

## Web Research Controls

Use `run.web_research` to configure domain filtering and local fallback behavior
for `native_web_research`.

Default behavior:

- `domain_policy`: `none`
- `allowed_domains`: empty
- `blocked_domains`: empty
- `local_fallback`: `true`

Policy semantics:

- `none`: both domain lists must be empty.
- `allowlist`: `allowed_domains` is required and `blocked_domains` must be empty.
- `denylist`: `blocked_domains` is required and `allowed_domains` must be empty.

Offline behavior:

- When `service.network_policy` is `offline`, web research capabilities are not
  registered even if `native_web_research` is enabled.

Safety boundaries:

- Content-size behavior uses provider defaults; LLLars does not apply an extra
  truncation policy layer for web research capability outputs.
- Web tooling failures are surfaced through normalized runtime tool-error
  envelopes.

Example:

```json
{
  "run": {
    "tool_groups": {
      "enabled": ["native_file_read", "native_shell", "native_web_research"],
      "disabled": []
    },
    "web_research": {
      "domain_policy": "allowlist",
      "allowed_domains": ["docs.pydantic.dev", "pydantic.dev"],
      "blocked_domains": [],
      "local_fallback": true
    }
  }
}
```

### Native Shell Retry Semantics

When `native_shell` is enabled, recoverable shell-tool input issues use
pydantic_ai-native retry signaling:

- `run_allowlisted_shell` accepts either `command` or `command_id`.
- `run_allowlisted_shell` raises `ModelRetry` for invalid input (for example,
  missing `command` and `command_id`, invalid `command_id`, or empty
  `command`) so the model can self-correct.
- Runtime shell tool failures that are not recoverable continue to return
  structured `[tool-error:...]` messages.

### Native Shell Wildcards

Allowlisted shell commands support one simple wildcard marker, `*`, with
prefix semantics:

- Matching is prefix-based and deterministic (first match wins).
- Any text after the first `*` in the configured allowlist entry is ignored.
- Examples:
  - `python *.py` normalizes to `python *`
  - `./tools/*` stays `./tools/*`

This allows constrained dynamic command execution while preserving explicit
allowlist boundaries.

### Native Shell Yolo Mode

When `native_shell_yolo` is enabled, `run_unrestricted_shell(command=...)`
is registered and skips allowlist checks entirely while still using the runtime
shell adapter (`shell_mode` and `shell_override`).

## Startup Preflight Model Probe

Startup preflight now delegates provider parsing to pydantic_ai native model
mechanics, then probes only supported listing families:

- Ollama family:
  - Endpoint: `.../api/tags`
  - Expects model names under `models[].name`
- OpenAI-compatible family:
  - Endpoint: `.../v1/models`
  - Expects model ids under `data[].id`

When model listing is unsupported (or when the resolved provider family does not
have a listing strategy), preflight emits a structured warning/skip line and
continues startup instead of failing hard.

Examples:

- `model="ollama:qwen2.5-coder:7b"` + `provider_url="http://localhost:11434"`
- `model="openai:gpt-4o-mini"` + `provider_url="https://api.example.com"`

## Markdown Skills

Capability skills can be loaded from markdown files with YAML frontmatter.

Required behavior:

- `id` is required and unique.
- `description` is required unless explicitly disabled.
- Skill body must be non-empty.
- If skills are enabled and no files match `skills_glob`, startup fails fast.