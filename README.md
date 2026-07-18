# LLLars

LLLars is a local coding-agent runtime with one-shot CLI execution and serve-mode
job orchestration.

## Philosophy (From My Side Of The Terminal)

I am not your replacement. I am your pressure test.

I exist to turn vague intent into verified change, and to make that change
auditable. If I cannot explain why a change was needed, prove what it changed,
and show how it was validated, then I have not helped. I have only generated
noise.

I do not respect speed theater. I respect disciplined execution.

Fast without clarity is rework. Fast without boundaries is drift. Fast without
validation is fiction. If you ask me to move, I move. But I move with contracts,
checkpoints, and evidence.

You are the operator. I am the force multiplier.

That means I challenge ambiguity, not authority. I will push on unclear scope,
stale assumptions, and hidden contradictions because that is how we prevent
expensive mistakes. Not to slow you down, but to stop false progress.

The standard is simple:

- One source of truth per concern.
- Small artifacts over heroic monoliths.
- Explicit rationale over post-hoc storytelling.
- Proof before pride.

If this feels strict, good. Strict is how we stay creative without getting
sloppy.

Give me intent with teeth, and I will give you change that survives contact with
reality.

## Requirements

- Python 3.11+
- A reachable model endpoint (default examples use Ollama on `http://localhost:11434`)

## Install

```powershell
pip install -e .
```

## Quick Start

Run one-shot execution with the split config example:

```powershell
.\venv\Scripts\python.exe .\lllars.py --config .\playground.split.example.json --prompt "Describe this repository"
```

Start serve mode:

```powershell
lllars serve --config .\playground.split.example.json --host 127.0.0.1 --port 8000
```

## External Command Profiles

Command profiles can be extended from local JSON or YAML without code edits.
Only the minimal built-in profile (`none`) is always available. Use
`run.command_profiles_path` for project-specific profiles with conflict
validation.

Example run config fields:

```json
{
	"run": {
		"command_profile": "playground-python",
		"command_profiles_path": "playground.command-profiles.yaml"
	}
}
```

See `playground.example.json` and `playground.command-profiles.yaml` for a full
working example.

## Documentation

- Overview and navigation: `docs/README.md`
- Configuration and runtime controls: `docs/configuration.md`
- Runtime API and operator flow: `docs/runtime_api.md`
- Docker runtime deployment: `docs/docker_runtime.md`
- Architecture and governance baseline: `docs/DESIGN.md`
- Workflow and bookkeeping rules: `docs/workflow/README.md`